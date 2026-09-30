import streamlit as st
import json
import pandas as pd
from pull_reviews import compute_defect_rates, iterative_3sigma, date_to_unix, patch_dates

with open("reviews_checkpoint.json", "r") as f:
    reviews = json.load(f)

patch_dates_unix = [date_to_unix(d) for d in patch_dates]
rates = compute_defect_rates(reviews, patch_dates_unix)
result = iterative_3sigma(rates)
baseline, ucl, lcl = result

st.title("Helldivers 2 Patch Quality Control Chart")
st.write("Applying statistical process control to player review data to detect statistically abnormal patches.")

chart_data = pd.DataFrame({
    "defect_rate": rates,
    "ucl": [ucl] * len(rates),
    "lcl": [lcl] * len(rates),
})

st.subheader("Defect Rate by Patch Window")
st.line_chart(chart_data)

st.subheader("Control Limits")
st.write(f"Upper Control Limit (UCL): {ucl:.3f}")
st.write(f"Lower Control Limit (LCL): {lcl:.3f}")

outliers = [r for r in rates if r > ucl or r < lcl]
st.subheader("Flagged Disaster Patches")
st.write(f"{len(outliers)} patch window(s) flagged as statistically out of control:")
st.write(outliers)