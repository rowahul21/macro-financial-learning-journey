import requests
import pandas as pd
from statsmodels.tsa.filters.hp_filter import hpfilter

# 1. Ambil data dari World Bank
def get_credit_to_gdp(country="IDN"):
    url = f"https://api.worldbank.org/v2/country/{country}/indicator/FS.AST.PRVT.GD.ZS?format=json"
    response = requests.get(url)
    data = response.json()[1]

    df = pd.DataFrame(data)[["date", "value"]]
    df = df.dropna()
    df["date"] = df["date"].astype(int)
    df = df.sort_values("date")

    return df

# 2. Hitung credit gap (HP Filter)
def compute_credit_gap(df):
    cycle, trend = hpfilter(df["value"], lamb=1600)
    df["trend"] = trend
    df["gap"] = cycle
    return df
# lamb=100 for annual data
# lamb=1600 for quarterly
# lamb=14400 for monthly

# 3. Early Warning Signal (EWS)
#def add_ews_flag(df, threshold=2):
#    df["ews"] = df["gap"].apply(lambda x: 1 if x > threshold else 0)
#    return df

def add_ews_flag(df: pd.DataFrame, threshold: float = 2.0) -> pd.DataFrame:
    """Add tiered Early Warning Signal based on BIS credit gap methodology.

    Signal levels:
        0 = Normal        (gap within ±threshold)
        1 = Watch         (gap > threshold, below 1.5x)
        2 = Warning       (gap > 1.5x threshold)
        3 = Critical      (gap > 2x threshold)
       -1 = Credit crunch (gap < -threshold, contraction risk)

    Args:
        df:        DataFrame with a 'gap' column (output of compute_credit_gap)
        threshold: BIS baseline threshold in percentage points (default 2.0pp)

    Returns:
        DataFrame with added 'ews' and 'ews_label' columns
    """
    df = df.copy()

    def classify(gap):
        if gap > threshold * 2:
            return 2        # Critical
        elif gap > threshold * 1.5:
            return 1        # Warning
        elif gap > threshold:
            return 0.5      # Watch
        elif gap < -threshold:
            return -1       # Credit crunch
        else:
            return 0        # Normal

    label_map = {
        2:    "CRITICAL",
        1:    "WARNING",
        0.5:  "WATCH",
        0:    "NORMAL",
        -1:   "CREDIT CRUNCH"
    }

    df["ews"] = df["gap"].apply(classify)
    df["ews_label"] = df["ews"].map(label_map)

    return df

# 4. Forecast
from prophet import Prophet
import pandas as pd

def run_forecast(df, periods):
    prophet_df = df[["date", "value"]].copy().rename(
        columns={"date": "ds", "value": "y"}
    )
    
    # ✅ Konversi integer year ke datetime (Prophet wajib datetime)
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"], format="%Y")
    
    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.1,
        growth="linear"
    )
    
    model.fit(prophet_df)
    
    future = model.make_future_dataframe(periods=periods, freq="A")
    forecast = model.predict(future)
    
    # ✅ Kembalikan sebagai integer year agar konsisten dengan df["date"]
    forecast["year"] = forecast["ds"].dt.year
    
    return forecast[["year", "yhat", "yhat_lower", "yhat_upper"]]