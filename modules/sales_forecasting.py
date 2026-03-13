import os
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import streamlit as st

BUNDLE_PATH = "models/random_forest_bundle.pkl"
EXPORT_DIR = "data/exports"


def _ensure_export_dir():
    os.makedirs(EXPORT_DIR, exist_ok=True)


@st.cache_resource
def load_bundle():
    return joblib.load(BUNDLE_PATH)


def _get_model(bundle):
    # supports dict bundles or object bundles
    if isinstance(bundle, dict):
        for k in ("model", "pipeline", "estimator", "clf"):
            if k in bundle:
                return bundle[k]
    for k in ("model", "pipeline", "estimator", "clf"):
        if hasattr(bundle, k):
            return getattr(bundle, k)
    return bundle


def _get_feature_cols(bundle):
    if isinstance(bundle, dict):
        for k in ("feature_columns", "feature_cols", "columns", "X_columns"):
            if k in bundle and isinstance(bundle[k], (list, tuple)):
                return list(bundle[k])
    for k in ("feature_columns", "feature_cols", "columns", "X_columns"):
        if hasattr(bundle, k):
            v = getattr(bundle, k)
            if isinstance(v, (list, tuple)):
                return list(v)
    return None


def _month_to_yyyymm(ym: str) -> int:
    # "2026-03" -> 202603
    y, m = ym.split("-")
    return int(y) * 100 + int(m)


def _month_to_year_month(ym: str) -> tuple[int, int]:
    y, m = ym.split("-")
    return int(y), int(m)


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


def _build_row(feature_cols: list[str], region: str, vehicle: str, scenario: str, ym: str) -> pd.DataFrame:
    """
    Build a single-row DataFrame compatible with most sklearn pipelines.
    Key fix: month/date fields are provided as numeric if the model expects numeric.
    """
    year, month = _month_to_year_month(ym)
    yyyymm = _month_to_yyyymm(ym)

    row = {}
    for c in feature_cols:
        lc = c.lower()

        # region / vehicle / scenario
        if lc in ("region", "area"):
            row[c] = region
        elif lc in ("model", "vehicle_model", "vehicle"):
            row[c] = vehicle
        elif lc in ("scenario", "ev_scenario", "market_trend"):
            row[c] = scenario

        # date/month features (NUMERIC)
        elif lc in ("yyyymm", "yearmonth", "year_month"):
            row[c] = yyyymm
        elif lc in ("year",):
            row[c] = year
        elif lc in ("month", "mth"):
            row[c] = month
        elif lc in ("period",):
            row[c] = yyyymm
        elif lc in ("date",):
            # numeric safe fallback; many models use yyyymm or timestamp-like ints
            row[c] = yyyymm

        # unknown features: fill with 0 (numeric-safe)
        else:
            row[c] = 0

    return pd.DataFrame([row])


def _predict(model, X: pd.DataFrame) -> float:
    y = model.predict(X)
    return float(np.asarray(y).ravel()[0])


def _save_csv(df: pd.DataFrame, region: str, vehicle: str) -> str:
    _ensure_export_dir()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"forecast_{region}_{vehicle}_{ts}.csv".replace(" ", "_")
    path = os.path.join(EXPORT_DIR, name)
    df.to_csv(path, index=False)
    return path


def render():
    st.markdown("## Sales Forecasting")
    st.caption("Generate demand forecasts using the integrated model bundle and export results.")

    if not os.path.exists(BUNDLE_PATH):
        st.error(f"Model bundle not found: {BUNDLE_PATH}")
        st.info("Upload your model to: models/random_forest_bundle.pkl")
        return

    try:
        bundle = load_bundle()
        model = _get_model(bundle)
        feature_cols = _get_feature_cols(bundle)
    except Exception as e:
        st.error("Failed to load model bundle.")
        st.code(str(e))
        return

    # UI
    a, b, c = st.columns([1, 1, 1])
    with a:
        region = st.selectbox("Select Region", ["NCR", "Luzon", "Visayas", "Mindanao"], index=1)
    with b:
        vehicle = st.selectbox("Select Vehicle Model", ["Corolla Cross", "bZ4X", "Vios", "Fortuner"], index=3)
    with c:
        horizon = st.selectbox("Forecast Horizon", ["3 months", "6 months", "12 months"], index=2)

    scenario = st.selectbox("EV Market Trend (Scenario)", ["Baseline", "High EV Adoption", "Low EV Adoption"], index=1)
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
                    X = _build_row(feature_cols, region, vehicle, scenario, ym)
                else:
                    # If feature columns not stored in bundle, we can only try a minimal numeric input.
                    # This is a fallback; best is to store feature columns during training.
                    X = pd.DataFrame([[0]])

                pred = _predict(model, X)
                rows.append(
                    {
                        "month": ym,
                        "region": region,
                        "vehicle_model": vehicle,
                        "scenario": scenario,
                        "forecast_demand": round(pred, 2),
                    }
                )
            except Exception as e:
                errors.append((ym, str(e)))

        if errors:
            st.warning("Some predictions failed. This usually means feature mismatch vs training.")
            st.code("\n".join([f"{m}: {msg}" for m, msg in errors])[:2000])

        df = pd.DataFrame(rows)
        if df.empty:
            st.error("No forecast produced. Your model likely expects different feature columns.")
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

        saved_path = _save_csv(df, region, vehicle)
        st.success(f"Saved locally: {saved_path}")
