import streamlit as st
import matplotlib.pyplot as plt
from utils import get_credit_to_gdp, compute_credit_gap, add_ews_flag, run_forecast
import pandas as pd

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
    "Country", ["IDN", "MYS", "THA", "PHL", "VNM", "SGP", "BRN", "LAO", "MMR", "KHM"]
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

Menteri Keuangan Purbaya Yudhi Sadewa pada akhir 2025 hingga awal 2026 
menempatkan dan mengelola uang negara (Saldo Anggaran Lebih/SAL) 
senilai ratusan triliun rupiah di bank-bank Himbara (BRI, BNI, Mandiri, BTN, BSI). 
Kebijakan ini bertujuan meningkatkan likuiditas perbankan, mendorong penyaluran kredit, 
dan menggerakkan ekonomi riil.

Proyek Macro-Financial Early Warning System (EWS) Dashboard ini dirancang untuk 
menjembatani kebutuhan antara kebijakan ekspansi kredit dan mitigasi risiko sistemik. 
Pentingnya dashboard ini semakin nyata jika dikaitkan dengan kebijakan Menteri Keuangan, Purbaya Yudhi Sadewa.
1. **Monitoring Dampak Injeksi Likuiditas**: Kebijakan Menkeu Purbaya bertujuan untuk memastikan likuiditas perbankan melimpah agar penyaluran kredit ke sektor riil bisa dipacu hingga mencapai target 10%. Dashboard ini berperan untuk memantau apakah injeksi likuiditas tersebut benar-benar terserap secara produktif atau justru menciptakan excessive credit yang berbahaya.
2. **Analisis Credit-to-GDP Gap Akibat Stimulus**: Dengan mengalirnya dana pemerintah dari BI ke Himbara, angka Credit-to-GDP Ratio Indonesia dipastikan akan naik. Dashboard ini akan menghitung selisih antara realisasi kredit tersebut dengan tren fundamentalnya ($Gap = Ratio_t - Trend_t$). Jika Gap menyentuh ambang batas tertentu, EWS akan memberikan sinyal bahwa stimulus tersebut mulai memicu risiko panas berlebih (overheating) pada sektor keuangan.
3. **Sinergi Kebijakan Makroprudensial**: Proyek ini mensimulasikan peran analis data dalam membantu regulator (seperti BI dan OJK) serta manajemen risiko di bank besar (seperti Mandiri) untuk tetap waspada. Meskipun secara fiskal pemerintah memberikan "gas" melalui penempatan dana di Himbara, secara makroprudensial kita tetap membutuhkan "rem" berupa monitoring EWS yang akurat.
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
# SCENARIO ANALYSIS
# ======================
st.subheader("🧪 Scenario Analysis")

# Kita ubah slidernya menjadi penambahan Percentage Points (pp) per tahun, bukan % majemuk.
# Historisnya, kredit Indonesia paling naik/turun 1-3 pp per tahun.
scenario_growth_pp = st.slider(
    "Simulate ratio change (Percentage Points / year)",
    -3.0, 5.0, 1.0, step=0.1
)

def simulate_credit_gap_linear(
    current_ratio: float,
    annual_change_pp: float,
    periods: int,
    trend_annual_change_pp: float = 0.5   # Historis tren jangka panjang tumbuhnya lambat
) -> float:
    """Project credit-to-GDP gap forward using linear percentage point changes."""
    proj = current_ratio + (annual_change_pp * periods)
    proj_trend = current_ratio + (trend_annual_change_pp * periods)
    return proj - proj_trend

# Hitung gap masa depan
projected_gap = simulate_credit_gap_linear(
    current_ratio=df["value"].iloc[-1],
    annual_change_pp=scenario_growth_pp,
    periods=forecast_horizon
)

if projected_gap > ews_threshold:
    st.error(f"Projected gap {projected_gap:.2f}pp exceeds threshold!")
else:
    st.success(f"Projected gap {projected_gap:.2f}pp still safe.")
    
# ======================
# PROPHET FORECAST
# ======================
forecast_df = run_forecast(df, forecast_horizon)

last_date = int(df["date"].max())   # ✅ pastikan integer
last_value = df[df["date"] == last_date]["value"].values[0]

forecast_df["year"] = forecast_df["year"].astype(int)  # ✅ samakan tipe

forecast_future = forecast_df[forecast_df["year"] > last_date]

# Anchor titik awal dari 2024
anchor = pd.DataFrame({
    "year": [last_date],
    "yhat": [last_value]
})

forecast_connected = pd.concat([anchor, forecast_future], ignore_index=True)

try:
    forecast_df = run_forecast(df, forecast_horizon)
    forecast_df["year"] = forecast_df["year"].astype(int)
except Exception as e:
    st.error(f"Forecast error: {e}")
    st.stop()
    
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

# ======================
# PLOTLY CHART
# ======================
import plotly.graph_objects as go

fig = go.Figure()

# ======================
# ACTUAL
# ======================
fig.add_trace(go.Scatter(
    x=df["date"],
    y=df["value"],
    name="Actual Credit",
    mode="lines+markers+text",
    text=[f"{v:.1f}" for v in df["value"]],
    textposition="top center",
    textfont=dict(size=11),
    line=dict(color="#1f77b4", width=3),
))

# ======================
# TREND
# ======================
fig.add_trace(go.Scatter(
    x=df["date"],
    y=df["trend"],
    name="Trend (HP Filter)",
    mode="lines",
    line=dict(color="#ff7f0e", width=3, dash="dash"),
))

# ======================
# PROPHET FORECAST (ONLY FUTURE)
# ======================
# Ambil titik 2024 dari data aktual sebagai anchor
anchor = pd.DataFrame({
    "year": [last_date],
    "yhat": [last_value]
})

# Gabungkan anchor + future forecast
forecast_connected = pd.concat([anchor, forecast_future], ignore_index=True)

# Plot dengan data yang sudah nyambung
fig.add_trace(go.Scatter(
    x=forecast_connected["year"],
    y=forecast_connected["yhat"],
    name="Forecast (Prophet)",
    mode="lines+markers",
    line=dict(color="cyan", width=4),
))

# ======================
# FORECAST START LINE
# ======================
fig.add_vline(
    x=last_date,
    line_dash="dash",
    line_color="gray",
    annotation_text="Forecast Start"
)

# ======================
# LAYOUT
# ======================
fig.update_layout(
    title="Credit-to-GDP with Trend & Forecast",
    hovermode="x unified",
    height=500
)

st.plotly_chart(fig, use_container_width=True)

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
    "Vietnam": get_latest_gap("VNM"),
    "Singapore": get_latest_gap("SGP"),
    "Brunei": get_latest_gap("BRN"),
    "Laos": get_latest_gap("LAO"),
    "Myanmar": get_latest_gap("MMR"),
    "Cambodia": get_latest_gap("KHM")
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

# ======================
# SUMBER DATA
# ======================  
st.divider()
st.caption("**Source**: [World Bank - Domestic credit to private sector (% of GDP)](https://data.worldbank.org/indicator/FS.AST.PRVT.GD.ZS)")
st.caption("**Note**: Indicators are calculated based on the Hodrick-Prescott (HP) Filter methodology according to BIS standards.")
st.caption("**Disclaimer**: Data as of 2024 and this Dashboard is for educational/analytical purpose and does not constitute financial advice")