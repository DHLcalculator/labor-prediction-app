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
    ot_threshold = st.number_input("Enter FTE On Site (e.g., 12 on AM Shift, 26 on PM Shift):", min_value=0, value=0)

    if st.button("Estimate Overtime Hours Needed"):
        if "hours" in st.session_state:
            total_hours = sum(st.session_state.hours)
            allowed_hours = ot_threshold * 7  # productive hours per FTE
            overtime_hours = total_hours - allowed_hours

            if overtime_hours > 0:
                st.warning(f"⚠️ Total overtime hours needed: **{round(overtime_hours, 2)}** hours (above threshold of {allowed_hours} hours)")

                st.markdown("#### Breakdown of Functions Contributing to Overtime")
                # Show functions where hours contribute proportionally to the overtime
                # For simplicity, show all functions with hours > 0 and calculate their share of overtime:
                overtime_details = []
                for i, (col, _) in enumerate(volume_columns):
                    func_hours = st.session_state.hours[i]
                    # Calculate proportion of total hours this function consumes
                    proportion = func_hours / total_hours if total_hours > 0 else 0
                    func_overtime = proportion * overtime_hours if overtime_hours > 0 else 0
                    if func_overtime > 0:
                        overtime_details.append((col, round(func_overtime, 2)))
                ot_df = pd.DataFrame(overtime_details, columns=["Function", "Overtime Hours Needed"])
                st.dataframe(ot_df, use_container_width=True)
            else:
                st.success("✅ No overtime hours needed. Total hours within threshold.")
        else:
            st.info("ℹ️ Please run a prediction first.")

    # VTO Estimation
    st.markdown("---")
    st.markdown("### 🏖 Voluntary Time Off (VTO) Estimation")

    num_employees = st.number_input("Enter Number of Employees On Site:", min_value=0, value=0)

    if st.button("Estimate VTO Hours"):
        if "total_fte" in st.session_state:
            predicted_fte_needed = st.session_state.total_fte
            if num_employees > predicted_fte_needed:
                # Calculate extra FTEs available
                extra_fte = num_employees - predicted_fte_needed
                # Convert FTEs to hours (7 productive hours per shift)
                total_vto_hours = extra_fte * 7
                # Hours per person for VTO
                vto_per_person = total_vto_hours / num_employees if num_employees > 0 else 0

                st.info(f"💡 Total VTO available: **{round(total_vto_hours, 2)}** hours")
                st.info(f"💡 VTO per person: **{round(vto_per_person, 2)}** hours")
            else:
                st.success("✅ No VTO available. Staffing matches or is below predicted need.")
        else:
            st.info("ℹ️ Please run a prediction first.")
