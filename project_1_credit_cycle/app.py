import streamlit as st
import matplotlib.pyplot as plt
from utils import get_credit_to_gdp, compute_credit_gap, add_ews_flag

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(
    page_title="Macro-Financial Risk Dashboard",
    layout="wide"
)

# ======================
# SIDEBAR
# ======================
st.sidebar.header("📊 Dashboard Controls")

country = st.sidebar.selectbox(
    "Country", ["IDN", "MYS", "THA", "PHL", "VNM"]
)

year_range = st.sidebar.slider(
    "Year range", 2000, 2024, (2010, 2024)
)

forecast_horizon = st.sidebar.slider(
    "Forecast periods", 1, 8, 4
)

ews_threshold = st.sidebar.number_input(
    "EWS gap threshold (%)", value=2.0
)

# ======================
# HEADER
# ======================
st.title("📉 Macro-Financial Early Warning System")

st.markdown("""
Dashboard untuk monitoring risiko sistem keuangan berbasis:
- Credit-to-GDP Gap (BIS)
- Early Warning Signal (EWS)
""")

# ======================
# DATA
# ======================
df = get_credit_to_gdp(country)
df = compute_credit_gap(df)
df = add_ews_flag(df, threshold=ews_threshold)

# filter tahun
df = df[(df["date"] >= year_range[0]) & (df["date"] <= year_range[1])]

# ======================
# METRIC CARDS
# ======================
if len(df) < 2:
    st.warning("Not enough data.")
    st.stop()
    
gap = df["gap"].iloc[-1]
prev_gap = df["gap"].iloc[-2]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Credit Gap",
        f"{gap:.2f} pp",
        delta=f"{gap - prev_gap:.2f} pp"
    )

with col2:
    st.metric("Trend Credit", f"{df['trend'].iloc[-1]:.2f}")

with col3:
    st.metric("Observations", len(df))

with col4:
    risk_label = "HIGH" if gap > ews_threshold else "LOW"
    st.metric("Risk Level", risk_label)

# ======================
# CHART
# ======================
# fig, ax = plt.subplots(figsize=(10, 5))

# # Main series
# ax.plot(df["date"], df["value"], label="Credit-to-GDP", linewidth=2.5, color="#1f77b4")
# ax.plot(df["date"], df["trend"], label="Trend", linewidth=2.5, linestyle="--", color="#ff7f0e")

# # Zero / baseline line
# ax.axhline(y=0, linestyle="--", color="gray", linewidth=1)

# # Grid biar lebih clean
# ax.grid(True, linestyle="--", alpha=0.4)

# # Title & labels
# ax.set_title("Credit-to-GDP Gap vs Trend", fontsize=14, fontweight="bold")
# ax.set_xlabel("Date")
# ax.set_ylabel("Value")

# # Legend lebih rapi
# ax.legend(frameon=False)

# plt.xticks(rotation=45)

# st.pyplot(fig)

# import matplotlib.pyplot as plt

# fig, ax = plt.subplots(figsize=(11, 5))

import plotly.graph_objects as go

fig = go.Figure()

# ======================
# VALUE LINE
# ======================
fig.add_trace(go.Scatter(
    x=df["date"],
    y=df["value"],
    name="Credit-to-GDP",
    mode="lines+text",
    text=[f"{v:.1f}" for v in df["value"]],
    textposition="top center",
    textfont=dict(size=15, color="white"),
    line=dict(color="#1f77b4", width=3)
))

# ======================
# TREND LINE
# ======================
fig.add_trace(go.Scatter(
    x=df["date"],
    y=df["trend"],
    name="Trend",
    # mode="lines",
    line=dict(color="#ff7f0e", width=3, dash="dash")
))

# ======================
# ZERO LINE
# ======================
fig.add_hline(y=0, line_dash="dash", line_color="gray")

# ======================
# LAYOUT (IMPORTANT)
# ======================
fig.update_layout(
    title="Credit-to-GDP Gap vs Trend (EWS View)",
    template="plotly_white",
    hovermode="x unified",
    height=500,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

# ======================
# SHOW IN STREAMLIT
# ======================
st.plotly_chart(fig, use_container_width=True)

# fig, ax = plt.subplots()

# ax.plot(df["date"], df["value"], label="Credit-to-GDP")
# ax.plot(df["date"], df["trend"], label="Trend")
# ax.axhline(y=0, linestyle="--")

# ax.legend()

# st.pyplot(fig)

# ======================
# COMPARISON ASEAN
# ======================
import plotly.express as px

st.subheader("🌏 ASEAN Comparison")

def get_latest_gap(country_code):
    df_temp = get_credit_to_gdp(country_code)
    df_temp = compute_credit_gap(df_temp)
    return df_temp["gap"].iloc[-1]

peer_data = {
    "Indonesia": get_latest_gap("IDN"),
    "Malaysia": get_latest_gap("MYS"),
    "Thailand": get_latest_gap("THA"),
    "Philippines": get_latest_gap("PHL"),
    "Vietnam": get_latest_gap("VNM")
}

def color_rule(v):
    if v > 4:
        return "CRITICAL"
    elif v > 3:
        return "WARNING"
    elif v > 2:
        return "WATCH"
    elif v < -2:
        return "CREDIT CRUNCH"
    else:
        return "NORMAL"

colors = [color_rule(v) for v in peer_data.values()]

# fig = px.bar(
#     x=list(peer_data.keys()),
#     y=list(peer_data.values()),
#     color=colors,
#     text=list(peer_data.values()),   # <- ini penting
#     color_discrete_map={True: "red", False: "green"},
#     title="Credit Gap ASEAN Comparison"
# )
fig = px.bar(
    x=list(peer_data.keys()),
    y=list(peer_data.values()),
    color=colors,
    text=list(peer_data.values()),
    color_discrete_map={
        "CRITICAL":         "#E24B4A",
        "WARNING":          "#EF9F27",
        "WATCH":            "#378ADD",
        "NORMAL":           "#1D9E75",
        "CREDIT CRUNCH":    "#7F77DD"
    },
    title="Credit Gap ASEAN Comparison"
)

fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')

fig.add_hline(y=2.0, line_dash="dash", line_color="red")
fig.add_hline(y=-2.0, line_dash="dash", line_color="blue")

fig.add_annotation(
    x=0,
    y=2.0,
    text="EWS Threshold",
    showarrow=False,
    yshift=10
)

st.plotly_chart(fig, use_container_width=True)

# ======================
# SCENARIO ANALYSIS
# ======================
st.subheader("🧪 Scenario Analysis")

scenario_growth = st.slider(
    "Simulate credit growth (%/year)",
    -5.0, 30.0, 10.0
)

def simulate_credit_gap(
    current_ratio: float,
    growth_rate: float,
    periods: int,
    trend_growth: float = 5.0   # default: assume 5% annual trend growth
) -> float:
    """Project credit-to-GDP gap forward under a simulated growth rate.

    Args:
        current_ratio: current credit-to-GDP value (%)
        growth_rate:   simulated annual credit growth rate (%)
        periods:       number of years to project forward
        trend_growth:  assumed trend growth rate (%) — default 5.0
    """
    proj = current_ratio * ((1 + growth_rate / 100) ** periods)
    proj_trend = current_ratio * ((1 + trend_growth / 100) ** periods)
    return proj - proj_trend

projected_gap = simulate_credit_gap(
    current_ratio=df["value"].iloc[-1],
    growth_rate=scenario_growth,
    periods=forecast_horizon
)

if projected_gap > ews_threshold:
    st.error(
        f"Projected gap {projected_gap:.2f}pp exceeds threshold!"
    )
else:
    st.success(
        f"Projected gap {projected_gap:.2f}pp still safe"
    )

# ======================
# EWS TABLE
# ======================
st.subheader("⚠️ Early Warning Signals")

st.markdown("""
**Definition:**  
EWS (Early Warning System) is based on BIS credit-to-GDP gap methodology with a threshold of **2.0 percentage points**.

It helps identify early signs of:
- Credit overheating
- Financial stress
- Credit contraction risks
""")

#st.dataframe(df[df["ews"] == 1])

#st.subheader("Distribusi EWS")
#st.dataframe(df["ews"].value_counts().reset_index())

#st.subheader("EWS Trend")
#st.line_chart(df.set_index("date")["ews"])

latest_ews = df["ews_label"].iloc[-1]

color_map = {
    "CRITICAL":      "#E24B4A",
    "WARNING":       "#EF9F27",
    "WATCH":         "#378ADD",
    "NORMAL":        "#1D9E75",
    "CREDIT CRUNCH": "#7F77DD"
}

color = color_map.get(latest_ews, "#888")
st.markdown(
    f"<div style='background:{color};color:white;padding:8px 16px;"
    f"border-radius:8px;font-weight:500;font-size:14px;"
    f"display:inline-block'>{latest_ews}</div>",
    unsafe_allow_html=True
)

st.subheader("Early Warning Signal History")
ews_df = df[df["ews"] != 0][["date", "value", "gap", "ews_label"]]
st.dataframe(
    ews_df.rename(columns={
        "date": "Year",
        "value": "Credit/GDP (%)",
        "gap": "Gap (pp)",
        "ews_label": "Signal"
    }),
    use_container_width=True
)

with st.expander("⚠️ EWS Signal Legend Table"):
    st.dataframe({
        "Signal": ["CRITICAL", "WARNING", "WATCH", "NORMAL", "CREDIT CRUNCH"],
        "Meaning": [
            "Extreme overheating risk",
            "High expansion, monitor closely",
            "Early imbalance signal",
            "Stable condition",
            "Credit contraction / liquidity tightening"
        ]
    })

# ======================
# RAW DATA
# ======================
with st.expander("🔍 Show Raw Data"):
    st.dataframe(df)