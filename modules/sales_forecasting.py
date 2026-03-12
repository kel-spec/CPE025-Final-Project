import os
import re
import sys
import types
import joblib
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

BUNDLE_PATH = "models/random_forest_bundle.pkl"

@st.cache_resource
def load_bundle():
    if not os.path.exists(BUNDLE_PATH):
        return None

    try:
        return joblib.load(BUNDLE_PATH)

    except AttributeError as e:
        # Typical message:
        # "Can't get attribute 'SomeClass' on <module 'some.module' ...>"
        msg = str(e)

        m = re.search(r"Can't get attribute '([^']+)' on <module '([^']+)'", msg)
        if not m:
            # If it doesn't match expected pattern, re-raise to see logs
            raise

        missing_class = m.group(1)
        missing_module = m.group(2)

        # Create the missing module if not present
        if missing_module not in sys.modules:
            sys.modules[missing_module] = types.ModuleType(missing_module)

        mod = sys.modules[missing_module]

        # Create a dummy class with the exact missing name and register it
        Dummy = type(missing_class, (), {})
        Dummy.__module__ = missing_module
        setattr(mod, missing_class, Dummy)

        # Retry load
        return joblib.load(BUNDLE_PATH)


def month_add(date_str: str, k: int = 1) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    y = dt.year
    m = dt.month + k
    y += (m - 1) // 12
    m = ((m - 1) % 12) + 1
    return f"{y:04d}-{m:02d}-01"


def make_static_onehots(bundle, vehicle_model: str) -> dict:
    static = bundle.static_info.copy()
    row = static[static["vehicle_model"] == vehicle_model]
    if row.empty:
        row = static.iloc[[0]]
    row = row.iloc[0]

    out = {}
    for v in static["vehicle_model"].unique():
        out[f"vehicle_model_{v}"] = 1 if v == vehicle_model else 0
    for c in static["vehicle_category"].unique():
        out[f"vehicle_category_{c}"] = 1 if c == row["vehicle_category"] else 0
    for p in static["powertrain_type"].unique():
        out[f"powertrain_type_{p}"] = 1 if p == row["powertrain_type"] else 0
    for b in static["price_band"].unique():
        out[f"price_band_{b}"] = 1 if b == row["price_band"] else 0

    return out


def get_month_defaults(bundle, month_int: int) -> dict:
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
    month_int = int(target_date[5:7])
    year_int = int(target_date[0:4])

    base = get_month_defaults(bundle, month_int)
    base["year"] = year_int

    def lag(i):
        if len(sales_history) >= i:
            return float(sales_history[-i])
        return float(sales_history[-1]) if sales_history else 0.0

    base["lag_1"] = lag(1)
    base["lag_2"] = lag(2)
    base["lag_3"] = lag(3)

    last3 = sales_history[-3:] if len(sales_history) >= 3 else sales_history
    last6 = sales_history[-6:] if len(sales_history) >= 6 else sales_history
    base["rolling_mean_3"] = float(np.mean(last3)) if last3 else 0.0
    base["rolling_mean_6"] = float(np.mean(last6)) if last6 else 0.0

    base["trend_index"] = int(trend_index)

    base.update(make_static_onehots(bundle, vehicle_model))

    cols = bundle.feature_columns
    row = {c: base.get(c, 0) for c in cols}
    return pd.DataFrame([row], columns=cols)


def forecast(bundle, vehicle_model: str, horizon: int) -> pd.DataFrame:
    estimator = bundle.estimator

    last_date = bundle.last_date_by_vehicle.get(
        vehicle_model,
        getattr(bundle, "last_dataset_month", "2025-01-01"),
    )

    hist = bundle.history_by_vehicle.get(vehicle_model, [])
    sales_history = [float(x) for x in hist] if isinstance(hist, (list, tuple)) else []
    trend = max(len(sales_history), 1)

    rows = []
    cur_date = month_add(last_date, 1)

    for i in range(horizon):
        X = build_feature_row(bundle, vehicle_model, cur_date, sales_history, trend + i + 1)
        y = estimator.predict(X)[0]
        y = float(max(y, 0.0))
        rows.append({"date": cur_date, "forecast": y})

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

    try:
        bundle = load_bundle()
    except Exception as e:
        st.error(f"Model load failed: {e}")
        st.markdown("</div></div>", unsafe_allow_html=True)
        return

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

    st.markdown("</div></div>", unsafe_allow_html=True)
