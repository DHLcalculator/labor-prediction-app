# --- labor_calculator_app.py ---
import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------
# CONFIG
# ------------------------
CORRECT_PASSWORD = "DHL111"  # Change for production
productive_hours_per_shift = 7.0  # Hours per person per shift

# Hours per unit (updated from latest numbers)
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

target_columns = list(hours_per_unit.keys())

# ------------------------
# FUNCTIONS
# ------------------------
def predict_labor(volumes):
    """Predict hours and FTEs from input volumes using hours_per_unit."""
    hours = [volumes[func] * hours_per_unit[func] for func in target_columns]
    ftes = [h / productive_hours_per_shift for h in hours]
    return hours, ftes

# ------------------------
# AUTHENTICATION
# ------------------------
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

# ------------------------
# MAIN APP
# ------------------------
else:
    st.title("📊 Labor Prediction Dashboard")
    st.info("Please input the required volumes below so we can generate your prediction.")

    # Inputs
    volumes = {}
    for func in target_columns:
        volumes[func] = st.number_input(f"{func} Volume", min_value=0.0, value=0.0)

    # Prediction button
    if st.button("Predict Labor Needs"):
        hours, ftes = predict_labor(volumes)
        total_hours = sum(hours)
        total_fte = sum(ftes)

        # Save results for overtime calculation
        st.session_state.total_fte = total_fte
        st.session_state.last_prediction = {"hours": hours, "ftes": ftes}

        # Summary table
        summary_df = pd.DataFrame({
            "Function": target_columns,
            "Labor Hours": hours,
            "FTE": ftes
        })
        summary_df.loc["Total"] = ["Total", total_hours, total_fte]
        st.subheader("📋 Prediction Summary Table")
        st.dataframe(summary_df, use_container_width=True)

        # Plotly charts for Labor Hours & FTE
        fig_hours = px.bar(summary_df.iloc[:-1], x="Function", y="Labor Hours",
                           title="Labor Hours by Function", text="Labor Hours")
        st.plotly_chart(fig_hours, use_container_width=True)

        fig_fte = px.bar(summary_df.iloc[:-1], x="Function", y="FTE",
                         title="FTE by Function", text="FTE")
        st.plotly_chart(fig_fte, use_container_width=True)

    # ------------------------
    # Overtime Estimation
    # ------------------------
    st.markdown("---")
    st.markdown("### 🕒 Overtime Estimation")
    ot_threshold = st.number_input("Enter FTE Threshold (e.g., 40):", min_value=0.0, value=40.0)

    if st.button("Estimate Overtime Workers"):
        if "total_fte" in st.session_state and "last_prediction" in st.session_state:
            total_fte = st.session_state.total_fte
            pred = st.session_state.last_prediction
            hours = pred["hours"]
            ftes = pred["ftes"]

            expected_ot_fte = max(0, total_fte - ot_threshold)

            if expected_ot_fte > 0:
                st.warning(f"⚠️ You may need **{expected_ot_fte:.2f}** overtime FTEs.")

                # Distribute overtime hours proportionally
                total_hours_all = sum(hours)
                ot_hours_total = expected_ot_fte * productive_hours_per_shift
                ot_hours_by_function = []
                for func, h in zip(target_columns, hours):
                    if h > 0:
                        func_ot_hours = (h / total_hours_all) * ot_hours_total
                        if func_ot_hours > 0:
                            ot_hours_by_function.append((func, func_ot_hours))

                if ot_hours_by_function:
                    breakdown_df = pd.DataFrame(ot_hours_by_function, columns=["Function", "Overtime Hours Needed"])
                    st.subheader("📋 Overtime Hours Breakdown by Function")
                    st.dataframe(breakdown_df, use_container_width=True)

                    # Plotly chart for overtime hours
                    fig_ot = px.bar(breakdown_df, x="Function", y="Overtime Hours Needed",
                                    title="Overtime Hours by Function", text="Overtime Hours Needed")
                    st.plotly_chart(fig_ot, use_container_width=True)
                else:
                    st.success("✅ No overtime hours needed for any specific function.")
            else:
                st.success("✅ No overtime workers needed based on this input.")
        else:
            st.info("ℹ️ Please run a prediction first.")
