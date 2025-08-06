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

    # Labor multipliers from Excel
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
        for i, (col, _) in enumerate(volume_columns):
            hours = volume_list[i] * hours_per_unit[col]
            labor_hours.append(hours)
        return labor_hours, [round(h / 6.8, 2) for h in labor_hours]  # 6.8 = productive hrs per shift

    if st.button("Predict Labor Needs"):
        hours, ftes = predict_labor_manual(volumes)
        total_hours = round(sum(hours), 2)
        total_fte = round(sum(ftes), 2)
        st.session_state.total_fte = total_fte
        st.session_state.last_prediction = (hours, ftes) 

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

    # --- Overtime Estimation ---
    st.markdown("---")
    st.markdown("### 🕒 Overtime Estimation")
    ot_threshold = st.number_input("Enter FTE Threshold (e.g., 40):", min_value=0.0, value=40.0)

    if st.button("Estimate Overtime Workers"):
        if "total_fte" in st.session_state and "last_prediction" in st.session_state:
            total_fte = st.session_state.total_fte
            hours, ftes = st.session_state.last_prediction

            expected_ot_fte = max(0, total_fte - ot_threshold)
        
            if expected_ot_fte > 0:
                st.warning(f"⚠️ You may need **{round(expected_ot_fte, 2)}** overtime FTEs.")

                productive_hours_per_shift = 6.8  # Change if your shift hours differ

                # Calculate overtime hours only for functions that exceed threshold
                ot_hours_by_function = []
                for func, f in zip(target_columns, ftes):
                    func_hours = round(f * productive_hours_per_shift, 2)
                    if func_hours > 0:
                        ot_hours_by_function.append((func, func_hours))

                if ot_hours_by_function:
                    breakdown_df = pd.DataFrame(ot_hours_by_function, columns=["Function", "Overtime Hours Needed"])
                    st.subheader("📋 Overtime Hours Breakdown")
                    st.dataframe(breakdown_df, use_container_width=True)
                else:
                    st.success("✅ No overtime hours needed for any specific function.")

            else:
                st.success("✅ No overtime workers needed based on this input.")
        else:
            st.info("ℹ️ Please run a prediction first.")
