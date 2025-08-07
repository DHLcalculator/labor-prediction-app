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

    # Labor multipliers (updated)
    hours_per_unit = {
        "Receiving": 0.0252,         # 6.3 / 250
        "Case Picking": 0.00667,     # 66 / 9900
        "Putaway": 0.05273,          # 11.6 / 220
        "Replenishment": 0.06667,    # 4.0 / 60
        "Full Pallet": 0.05,         # 11 / 220
        "Loading": 0.025,            # 12 / 480
        "Layer Picking": 0.004,      # 10 / 2500
        "Unloading": 0.02507         # 9.4 / 375
    }

    # Predict labor
    def predict_labor_manual(volume_list):
        labor_hours = []
        ftes = []
        for i, (col, _) in enumerate(volume_columns):
            hours = volume_list[i] * hours_per_unit[col]
            fte = hours / 7.0
            labor_hours.append(hours)
            ftes.append(fte)
        return labor_hours, ftes

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
            "Labor Hours": hours,
            "FTE": ftes
        })
        summary_df.loc["Total"] = ["Total", total_hours, total_fte]
        st.dataframe(summary_df, use_container_width=True)

        # FTE Bar Chart
        chart_df = summary_df[summary_df["Function"] != "Total"]
        fig = px.bar(chart_df, x="Function", y="FTE", color="Function", title="FTE by Function")
        st.plotly_chart(fig, use_container_width=True)

    # --- Overtime Estimation ---
    st.markdown("---")
    st.markdown("### 🕒 Overtime Estimation")
    ot_threshold = st.number_input("Enter FTE Threshold (e.g., 20):", min_value=0.0, value=16.0)

    if st.button("Estimate Overtime Workers"):
        if "total_fte" in st.session_state:
            total_fte = st.session_state.total_fte
            if total_fte > ot_threshold:
                st.warning(f"⚠️ You may need **{round(total_fte - ot_threshold, 2)}** overtime FTEs.")

                # Calculate and display OT hours by function
                available_fte = ot_threshold
                ftes = st.session_state.ftes
                hours = st.session_state.hours
                ot_by_function = {}
                for i, (col, _) in enumerate(volume_columns):
                    if available_fte >= ftes[i]:
                        available_fte -= ftes[i]
                    else:
                        ot_hours = hours[i] - (available_fte * 7.0)
                        ot_by_function[col] = round(ot_hours, 2)
                        available_fte = 0

                if ot_by_function:
                    st.subheader("🛠 Overtime Hours Needed by Function")
                    st.write(pd.DataFrame({
                        "Function": list(ot_by_function.keys()),
                        "OT Hours": list(ot_by_function.values())
                    }))
            else:
                st.success("✅ No overtime workers needed.")
        else:
            st.info("ℹ️ Please run a prediction first.")

