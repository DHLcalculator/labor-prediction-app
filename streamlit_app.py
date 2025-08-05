import streamlit as st
import pandas as pd
import plotly.express as px

# --- Authentication ---
CORRECT_PASSWORD = "DHLdhl11!!"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("Welcome to the Labor Prediction Dashboard")
    password = st.text_input("Enter Password:", type="password")
    if password == CORRECT_PASSWORD:
        st.session_state.authenticated = True
        st.success("Access granted! 🎉")
        st.rerun()
    elif password:
        st.error("Incorrect password. Try again.")
else:
    st.title("📊 Labor Prediction Dashboard")
    st.info("Input volume data to estimate labor hours and FTEs")

    # --- Inputs ---
    day = st.selectbox("Day of Week", ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
    shift = st.selectbox("Shift", ['AM', 'PM'])

    volume_columns = [
        ("Receiving", "pallets"),
        ("Case Picking", "cases"),
        ("Putaway", "pallets"),
        ("Replenishment", "pallets"),
        ("Full Pallet", "pallets"),
        ("Loading", "pallets"),
        ("Layer Picking", "cases"),
        ("Unloading", "pallets"),
    ]

    volumes = []
    for col, unit in volume_columns:
        val = st.number_input(f"{col} Volume ({unit})", min_value=0, value=0)
        volumes.append(val)

    # Labor multipliers from Excel photo
    hours_per_unit = {
        "Receiving": 0.025,          # 12.5 / 500
        "Case Picking": 0.00769,     # 76.9 / 10000
        "Putaway": 0.0527,           # 23.2 / 440
        "Replenishment": 0.0667,     # 6.0 / 90
        "Full Pallet": 0.05,         # 11.5 / 230
        "Loading": 0.0167,           # 8.0 / 480
        "Layer Picking": 0.004,      # 10.0 / 2500
        "Unloading": 0.0126          # 5.4 / 430
    }

    # Predict labor
    def predict_labor_manual(volume_list):
        labor_hours = []
        for i, (col, _) in enumerate(volume_columns):
            hours = volume_list[i] * hours_per_unit[col]
            labor_hours.append(hours)
        return labor_hours, [round(h / 6.8, 2) for h in labor_hours]  # 6.8 = productive hrs per shift

    if st.button("Predict Labor Needs"):
        hours, ftes = predict_labor_manual(volumes)
        total_hours = round(sum(hours), 2)
        total_fte = round(sum(ftes), 2)
        st.session_state.total_fte = total_fte

        st.subheader("📋 Prediction Summary Table")
        summary_df = pd.DataFrame({
            "Function": [col for col, _ in volume_columns],
            "Labor Hours": [round(h, 2) for h in hours],
            "FTE": [round(f, 2) for f in ftes]
        })
        summary_df.loc["Total"] = ["Total", total_hours, total_fte]
        st.dataframe(summary_df, use_container_width=True)

        # FTE Bar Chart
        chart_df = summary_df[summary_df["Function"] != "Total"]
        fig = px.bar(chart_df, x="Function", y="FTE", color="Function", title="FTE by Function")
        st.plotly_chart(fig, use_container_width=True)

    # Overtime Estimation
    st.markdown("---")
    st.markdown("### 🕒 Overtime Estimation")
    ot_threshold = st.number_input("Enter FTE Threshold (e.g., 40):", min_value=0.0, value=40.0)

    if st.button("Estimate Overtime Workers"):
        if "total_fte" in st.session_state:
            expected_ot = max(0, st.session_state.total_fte - ot_threshold)
            if expected_ot > 0:
                st.warning(f"⚠️ You may need **{round(expected_ot, 2)}** overtime FTEs.")
            else:
                st.success("✅ No overtime workers needed.")
        else:
            st.info("ℹ️ Please run a prediction first.")
