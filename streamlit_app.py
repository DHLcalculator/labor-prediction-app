import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------- AUTHENTICATION ----------------------
PASSWORD = "DHLdhl11!!"
user_password = st.text_input("Enter password to access the labor calculator:", type="password")
if user_password != PASSWORD:
    st.warning("Incorrect password. Access denied.")
    st.stop()

st.title("Labor Prediction & Overtime Estimator")

# ---------------------- USER INPUTS ----------------------
st.header("Enter Volume by Function")

# Dictionary for entering volume by function
volume_inputs = {}
functions = [
    "Unloading",
    "Receiving",
    "Putaway",
    "Case Picking",
    "Full Pallet",
    "Layer Picking",
    "Loading",
    "Replenishment"
]

for function in functions:
    volume_inputs[function] = st.number_input(f"{function} Volume", min_value=0, value=0)

# ---------------------- PRODUCTIVE HOURS PER SHIFT ----------------------
# Assuming 7.0 productive hours in a shift (can be adjusted later)
productive_hours_per_day = 7.0

# ---------------------- HOURS PER UNIT (BASED ON OPERATIONAL STUDY) ----------------------
# These are estimated labor standards or historical productivity rates.
# Format: "Function": hours_required / units_handled
hours_per_unit = {
    "Unloading": 6.3 / 250,          # 0.0252 hrs/pallet
    "Receiving": 6.3 / 250,          # 0.0252 hrs/pallet
    "Putaway": 15.8 / 300,           # 0.0527 hrs/pallet
    "Case Picking": 66 / 9900,       # 0.00667 hrs/case
    "Full Pallet": 11 / 220,         # 0.05 hrs/pallet
    "Layer Picking": 10 / 2500,      # 0.004 hrs/case
    "Loading": 12 / 480,             # 0.025 hrs/pallet
    "Replenishment": 4.0 / 60        # 0.0667 hrs/pallet
}

# ---------------------- LABOR PREDICTION CALCULATION ----------------------
results = []
total_hours = 0

for function in functions:
    volume = volume_inputs[function]
    hrs_per_unit = hours_per_unit[function]
    labor_hours = volume * hrs_per_unit
    fte_required = labor_hours / productive_hours_per_day
    total_hours += labor_hours

    results.append({
        "Function": function,
        "Volume": volume,
        "Hours per Unit": round(hrs_per_unit, 5),
        "Labor Hours": round(labor_hours, 2),
        "FTE Required": round(fte_required, 2)
    })

# Convert to DataFrame for display
df = pd.DataFrame(results)

# ---------------------- TOTAL FTE ----------------------
total_fte = total_hours / productive_hours_per_day
st.subheader("Labor Summary")
st.dataframe(df)
st.markdown(f"**Total Labor Hours:** {total_hours:.2f}")
st.markdown(f"**Total FTE Required:** {total_fte:.2f}")

# ---------------------- OVERTIME ESTIMATION ----------------------
st.header("Overtime Estimation")
fte_threshold = st.number_input("Enter available daily FTEs before OT is needed", min_value=0.0, value=16.0)

if total_fte > fte_threshold:
    overtime_hours = (total_fte - fte_threshold) * productive_hours_per_day
    st.markdown(f"### ⚠️ Overtime Needed: {overtime_hours:.2f} hours")

    # Proportional breakdown by function
    overtime_breakdown = []
    for row in df.itertuples():
        share = row._4 / total_hours  # row._4 = Labor Hours
        function_ot_hours = share * overtime_hours
        overtime_breakdown.append({
            "Function": row.Function,
            "OT Hours": round(function_ot_hours, 2)
        })

    df_ot = pd.DataFrame(overtime_breakdown)
    df_ot.loc[len(df_ot.index)] = ["Total OT", df_ot["OT Hours"].sum()]
    st.subheader("Overtime by Function")
    st.dataframe(df_ot)
else:
    st.success("✅ No overtime needed based on current FTE threshold.")

# ---------------------- CHART ----------------------
st.header("FTE by Function")
fig = px.bar(df, x="Function", y="FTE Required", title="FTE Requirement by Function", text="FTE Required")
fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig)
