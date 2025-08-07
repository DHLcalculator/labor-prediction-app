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

    # Reordered functions and units
    volume_columns = [
        ("Unloading", "pallets"),
        ("Receiving", "pallets"),
        ("Putaway", "pallets"),
        ("Case Picking", "cases"),
        ("Full Pallet", "pallets"),
        ("Layer Picking", "cases"),
        ("Loading", "pallets"),
        ("Replenishment", "pallets")
    ]

    volumes = []
    for col, unit in volume_columns:
        val = st.number_input(f"{col} Volume ({unit})", min_value=0, value=0)
        volumes.append(val)

    # Labor multipliers based on updated data
    hours_per_unit = {
        "Unloading": 0.02507,        # 9.4 / 375
        "Receiving": 0.0252,         # 6.3 / 250
        "Putaway": 0.05267,          # 15.8 / 300 
        "Case Picking": 0.00667,     # 66 / 9900
        "Full Pallet": 0.05,         # 11 / 220
        "Layer Picking": 0.004,      # 10 / 2500
        "Loading": 0.025,            # 12 / 480
        "Replenishment": 0.06667     # 4 / 60
    }

    # Predict labor
    def predict_labor_manual(volume_list):
        labor_hours = []
        for i, (col, _) in enumerate(volume_columns):
            hours = volume_list[i] * hours_per_unit[col]
            labor_hours.append(hours)
        return labor_hours, [h / 7.0 for h in labor_hours]  # 7.0 = productive hrs per shift

    if st.button("Predict Labor Needs"):
        hours, ftes = predict_labor_manual(volumes)
        total_hours = sum(hours)
        total_fte = sum(ftes)
        st.session_state.total_fte = total_fte
        st.session_state.ftes = ftes
        st.session_state.hours = hours

        st.subheader("📋 Prediction Summary Table")
        summary_df = pd.DataFrame({
            "Function": [col for col, _ in volume_columns],
            "Labor Hours": [round(h, 2) for h in hours],
            "FTE": [round(f, 2) for f in ftes]
        })
        summary_df.loc["Total"] = ["Total", round(total_hours, 2), round(total_fte, 2)]
        st.dataframe(summary_df, use_container_width=True)

        # FTE Bar Chart
        chart_df = summary_df[summary_df["Function"] != "Total"]
        fig = px.bar(chart_df, x="Function", y="FTE", color="Function", title="FTE by Function")
        st.plotly_chart(fig, use_container_width=True)

    # Overtime Estimation
    st.markdown("---")
    st.markdown("### 🕒 Overtime Estimation")
    ot_threshold = st.number_input("Enter FTE Threshold (e.g., 20):", min_value=0.0, value=16.0)

    if st.button("Estimate Overtime Workers"):
        if "total_fte" in st.session_state and "ftes" in st.session_state:
            expected_ot = st.session_state.total_fte - ot_threshold
            if expected_ot > 0:
                st.warning(f"⚠️ You may need **{round(expected_ot, 2)}** overtime FTEs.")
                
                st.markdown("#### Breakdown of Overtime by Function")
                overtime_details = []
                for i, (col, _) in enumerate(volume_columns):
                    if st.session_state.ftes[i] > 0:
                        overtime_details.append((col, round(st.session_state.hours[i], 2)))
                ot_df = pd.DataFrame(overtime_details, columns=["Function", "Labor Hours Needed"])
                st.dataframe(ot_df, use_container_width=True)
            else:
                st.success("✅ No overtime workers needed.")
        else:
            st.info("ℹ️ Please run a prediction first.")
