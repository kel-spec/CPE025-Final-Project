import os
import joblib
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

BUNDLE_PATH = "models/random_forest_bundle.pkl"

# Needed so joblib can unpickle the bundle created with a custom class.
class TrainedModelBundle:
    pass

@st.cache_resource
def load_bundle():
    if not os.path.exists(BUNDLE_PATH):
        return None
    return joblib.load(BUNDLE_PATH)

def month_add(date_str: str, k: int = 1) -> str:
    # date_str format: YYYY-MM-01
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    y = dt.year
    m = dt.month + k
    y += (m - 1) // 12
    m = ((m - 1) % 12) + 1
    return f"{y:04d}-{m:02d}-01"

def make_static_onehots(bundle, vehicle_model: str) -> dict:
    """
    Produces one-hot columns:
      vehicle_model_*
      vehicle_category_*
      powertrain_type_*
      price_band_*
    based on bundle.static_info
    """
    static = bundle.static_info.copy()
    row = static[static["vehicle_model"] == vehicle_model]
    if row.empty:
        # fallback to first row
        row = static.iloc[[0]]
    row = row.iloc[0]

    out = {}

    # vehicle_model one-hot
    for v in static["vehicle_model"].unique():
        out[f"vehicle_model_{v}"] = 1 if v == vehicle_model else 0

    # category one-hot
    for c in static["vehicle_category"].unique():
        out[f"vehicle_category_{c}"] = 1 if c == row["vehicle_category"] else 0

    # powertrain one-hot
    for p in static["powertrain_type"].unique():
        out[f"powertrain_type_{p}"] = 1 if p == row["powertrain_type"] else 0

    # price band one-hot
    for b in static["price_band"].unique():
        out[f"price_band_{b}"] = 1 if b == row["price_band"] else 0

    return out

def get_month_defaults(bundle, month_int: int) -> dict:
    """
    Pulls industry totals + flags for the given month from monthly_defaults table.
    """
    df = bundle.monthly_defaults
    r = df[df["month"] == month_int]
    if r.empty:
        r = df.iloc[[0]]
    r = r.iloc[0].to_dict()
    return {
        "industry_total_sales": float(r["industry_total_sales"]),
        "industry_passenger_sales": float(r["industry_passenger_sales"]),
        "industry_commercial_sales": float(r["industry_commercial_sales"]),
        "promo_flag": int(r["promo_flag"]),
        "holiday_season_flag": int(r["holiday_season_flag"]),
        "launch_flag": int(r["launch_flag"]),
        "month": int(month_int),
        "quarter": int(((month_int - 1) // 3) + 1),
    }

def build_feature_row(bundle, vehicle_model: str, target_date: str, sales_history: list[float], trend_index: int) -> pd.DataFrame:
    """
    Builds a single-row DataFrame matching bundle.feature_columns.
    sales_history includes actual + predicted up to previous month.
    """
    month_int = int(target_date[5:7])
    year_int = int(target_date[0:4])

    base = get_month_defaults(bundle, month_int)
    base["year"] = year_int

    # Lags
    # If not enough history, pad with last known or 0.
    def lag(i):
        if len(sales_history) >= i:
            return float(sales_history[-i])
        return float(sales_history[-1]) if sales_history else 0.0

    base["lag_1"] = lag(1)
    base["lag_2"] = lag(2)
    base["lag_3"] = lag(3)

    # Rolling means
    last3 = sales_history[-3:] if len(sales_history) >= 3 else sales_history
    last6 = sales_history[-6:] if len(sales_history) >= 6 else sales_history
    base["rolling_mean_3"] = float(np.mean(last3)) if last3 else 0.0
    base["rolling_mean_6"] = float(np.mean(last6)) if last6 else 0.0

    # Trend
    base["trend_index"] = int(trend_index)

    # One-hot static columns
    onehots = make_static_onehots(bundle, vehicle_model)
    base.update(onehots)

    # Ensure column order exactly matches training
    cols = bundle.feature_columns
    row = {c: base.get(c, 0) for c in cols}
    return pd.DataFrame([row], columns=cols)

def forecast(bundle, vehicle_model: str, horizon: int) -> pd.DataFrame:
    """
    Sequential forecasting:
    - start date = next month after last_date_by_vehicle
    - each step uses predicted value to update future lags/rolling means
    """
    estimator = bundle.estimator
    last_date = bundle.last_date_by_vehicle.get(vehicle_model, bundle.last_dataset_month)

    # history list is stored in bundle.history_by_vehicle[vehicle_model]
    hist = bundle.history_by_vehicle.get(vehicle_model, [])
    sales_history = [float(x) for x in hist] if isinstance(hist, (list, tuple)) else []

    # trend index continues from history length
    trend = max(len(sales_history), 1)

    rows = []
    cur_date = month_add(last_date, 1)

    for i in range(horizon):
        X = build_feature_row(bundle, vehicle_model, cur_date, sales_history, trend + i + 1)
        y = estimator.predict(X)[0]
        y = float(max(y, 0.0))  # clamp to >= 0
        rows.append({"date": cur_date, "forecast": y})

        # update history for next step
        sales_history.append(y)
        cur_date = month_add(cur_date, 1)

    return pd.DataFrame(rows)

def render():
    st.markdown(
        """
        <div class="dss-section">
          <div class="dss-section-head">Sales Forecasting</div>
          <div class="dss-section-body">
        """,
        unsafe_allow_html=True,
    )

    bundle = load_bundle()
    if bundle is None:
        st.error("Model bundle not found. Put it at: models/random_forest_bundle.pkl")
        st.markdown("</div></div>", unsafe_allow_html=True)
        return

    vehicle_list = sorted(list(bundle.static_info["vehicle_model"].unique()))
    c1, c2 = st.columns([2, 1])
    with c1:
        vehicle_model = st.selectbox("Select Vehicle Model", vehicle_list, index=0)
    with c2:
        horizon = st.selectbox("Forecast Horizon (months)", [1, 3, 6, 12], index=3)

    if st.button("Generate Forecast", use_container_width=True):
        df = forecast(bundle, vehicle_model, int(horizon))

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["date"], y=df["forecast"], mode="lines+markers", name="Forecast"))
        fig.update_layout(
            height=420,
            margin=dict(l=10, r=10, t=35, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            title=f"Sales Forecast — {vehicle_model}",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="dss-card">', unsafe_allow_html=True)
        st.write("Forecast Table")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.caption(f"Model: {getattr(bundle, 'model_name', 'Random Forest')} | Features: {len(bundle.feature_columns)}")

    st.markdown("</div></div>", unsafe_allow_html=True)
