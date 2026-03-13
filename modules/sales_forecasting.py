import os
import sqlite3
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import streamlit as st

BUNDLE_PATH = "models/random_forest_bundle.pkl"
DB_PATH = "data/app.db"
EXPORT_DIR = "data/exports"


def _ensure_export_dir() -> None:
    os.makedirs(EXPORT_DIR, exist_ok=True)


@st.cache_resource
def _load_bundle():
    return joblib.load(BUNDLE_PATH)


def _infer_feature_columns(bundle) -> list[str] | None:
    if isinstance(bundle, dict):
        for k in ["feature_columns", "feature_cols", "columns", "X_columns"]:
            if k in bundle and isinstance(bundle[k], (list, tuple)):
                return list(bundle[k])
    # if it's a custom class, it may have attribute
    for attr in ["feature_columns", "feature_cols", "columns", "X_columns"]:
        if hasattr(bundle, attr):
            val = getattr(bundle, attr)
            if isinstance(val, (list, tuple)):
                return list(val)
    return None


def _get_model(bundle):
    if isinstance(bundle, dict):
        for k in ["model", "estimator", "pipeline", "clf"]:
            if k in bundle:
                return bundle[k]
    for attr in ["model", "estimator", "pipeline", "clf"]:
        if hasattr(bundle, attr):
            return getattr(bundle, attr)
    return bundle


def _build_input_row(feature_cols: list[str], region: str, model_name: str, ev_scenario: str, ym: str) -> pd.DataFrame:
    row = {c: 0 for c in feature_cols}

    for c in feature_cols:
        lc = c.lower()
        if lc in ["region", "area"]:
            row[c] = region
        elif lc in ["model", "vehicle_model", "vehicle"]:
            row[c] = model_name
        elif lc in ["scenario", "ev_scenario", "market_trend"]:
            row[c] = ev_scenario
        elif lc in ["month", "period", "date", "year_month"]:
            row[c] = ym

    return pd.DataFrame([row])


def _predict_value(model, X: pd.DataFrame) -> float:
    y = model.predict(X)
    return float(np.array(y).ravel()[0])


def _make_horizon(start_month: str, periods: int) -> list[str]:
    dt = datetime.strptime(start_month + "-01", "%Y-%m-%d")
    months = []
    y, m = dt.year, dt.month
    for _ in range(periods):
        months.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            m = 1
            y += 1
    return months


def _save_forecast(df: pd.DataFrame, region: str, vehicle: str) -> str:
    _ensure_export_dir()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"forecast_{region}_{vehicle}_{ts}.csv".replace(" ", "_").replace("/", "-")
    path = os.path.join(EXPORT_DIR, filename)
    df.to_csv(path, index=False)
    return path


def _safe_users_count() -> int | None:
    if not os.path.exists(DB_PATH):
        return None
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        n = int(cur.fetchone()[0])
        con.close()
        return n
    except Exception:
        try:
            con.close()
        except Exception:
            pass
        return None


def render():
    st.markdown("## Sales Forecasting")
    st.caption("Generate demand forecasts using the integrated model bundle and export results.")

    if not os.path.exists(BUNDLE_PATH):
        st.error(f"Model bundle not found: {BUNDLE_PATH}")
        st.info("Put the file here: models/random_forest_bundle.pkl")
        return

    try:
        bundle = _load_bundle()
        model = _get_model(bundle)
        feature_cols = _infer_feature_columns(bundle)
    except Exception as e:
        st.error("Failed to load model bundle.")
        st.code(str(e))
        return

    top1, top2, top3 = st.columns([1, 1, 1])
    with top1:
        region = st.selectbox("Select Region", ["NCR", "Luzon", "Visayas", "Mindanao"], index=0)
    with top2:
        vehicle = st.selectbox("Select Vehicle Model", ["Corolla Cross", "bZ4X", "Vios", "Fortuner"], index=0)
    with top3:
        horizon = st.selectbox("Forecast Horizon", ["3 months", "6 months", "12 months"], index=1)

    scenario = st.selectbox(
        "EV Market Trend (Scenario)",
        ["Baseline", "High EV Adoption", "Low EV Adoption"],
        index=0,
    )

    start_month = st.text_input("Start Month (YYYY-MM)", value=datetime.now().strftime("%Y-%m"))
    periods = {"3 months": 3, "6 months": 6, "12 months": 12}[horizon]

    st.divider()

    if st.button("Generate Forecast", use_container_width=True):
        months = _make_horizon(start_month, periods)

        rows = []
        errors = []

        for ym in months:
            try:
                if feature_cols:
                    X = _build_input_row(feature_cols, region, vehicle, scenario, ym)
                    pred = _predict_value(model, X)
                else:
                    # fallback: model without columns (keeps demo alive)
                    pred = _predict_value(model, pd.DataFrame([[0]]))

                rows.append(
                    {
                        "month": ym,
                        "region": region,
                        "vehicle_model": vehicle,
                        "scenario": scenario,
                        "forecast_demand": round(float(pred), 2),
                    }
                )
            except Exception as e:
                errors.append((ym, str(e)))

        if errors:
            st.warning("Some predictions failed. This usually means feature mismatch vs training.")
            st.code("\n".join([f"{m}: {msg}" for m, msg in errors])[:2000])

        df = pd.DataFrame(rows)
        if df.empty:
            st.error("No output produced. Align your feature columns with the model training pipeline.")
            return

        st.markdown("### Forecast Output Dataset")
        st.dataframe(df, use_container_width=True)
        st.line_chart(df.set_index("month")["forecast_demand"])

        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV",
            data=csv_bytes,
            file_name=f"forecast_{region}_{vehicle}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv".replace(" ", "_"),
            mime="text/csv",
            use_container_width=True,
        )

        saved_path = _save_forecast(df, region, vehicle)
        st.success(f"Saved locally: {saved_path}")

        n_users = _safe_users_count()
        if n_users is not None:
            st.caption(f"Local DB check: users in database = {n_users}")
