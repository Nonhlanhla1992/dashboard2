import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

DB_PATH = "civ_dash.db"

st.set_page_config(page_title="Civil Society Dashboard (MVP)", layout="wide")

@st.cache_data
def load_data():
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM labour_gender_gap ORDER BY year", con)
    con.close()
    return df

df = load_data()

# --- Simple "model": rolling trend + anomaly flags ---
# Trend: rolling average (3-year)
df["gap_trend_3y"] = df["gap_male_minus_female"].rolling(3, min_periods=1).mean()

# Anomaly: flag points that deviate strongly from recent behaviour
# (simple: compare to rolling mean and std over a 5-year window)
window = 5
roll_mean = df["gap_male_minus_female"].rolling(window, min_periods=3).mean()
roll_std  = df["gap_male_minus_female"].rolling(window, min_periods=3).std()

df["anomaly"] = (df["gap_male_minus_female"] > (roll_mean + 2 * roll_std)) | (
    df["gap_male_minus_female"] < (roll_mean - 2 * roll_std)
)

latest_year = int(df["year"].max())
latest = df[df["year"] == latest_year].iloc[0]

st.title("Civil Society Dashboard (MVP)")
st.caption("Open data → simple model signals → explainable visuals")

col1, col2, col3 = st.columns(3)
col1.metric("Latest year", f"{latest_year}")
col2.metric("Latest gender gap (M−F)", f"{latest['gap_male_minus_female']:.1f} pp")
col3.metric("Anomaly flagged?", "Yes" if bool(latest["anomaly"]) else "No")

st.divider()

# --- Chart 1: female vs male ---
fig1 = plt.figure(figsize=(10, 4))
plt.plot(df["year"], df["female"], marker="o", label="Female (%)")
plt.plot(df["year"], df["male"], marker="o", label="Male (%)")
plt.title("Labour force participation rate (15+) — Female vs Male")
plt.xlabel("Year")
plt.ylabel("Rate (%)")
plt.grid(True, alpha=0.25)
plt.legend()
st.pyplot(fig1)

# --- Chart 2: gap + trend + anomalies ---
fig2 = plt.figure(figsize=(10, 4))
plt.plot(df["year"], df["gap_male_minus_female"], marker="o", label="Gap (M−F)")
plt.plot(df["year"], df["gap_trend_3y"], linewidth=2, label="Trend (3y rolling avg)")

# mark anomalies
anoms = df[df["anomaly"]]
plt.scatter(anoms["year"], anoms["gap_male_minus_female"], s=120, label="Anomaly")

plt.axhline(0, linewidth=1)
plt.title("Gender gap (M−F) with trend + anomaly flags")
plt.xlabel("Year")
plt.ylabel("Gap (percentage points)")
plt.grid(True, alpha=0.25)
plt.legend()
st.pyplot(fig2)

with st.expander("See the underlying data table"):
    st.dataframe(df, use_container_width=True)
