import os
import sqlite3
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import streamlit as st


# ===== Paths =====
BUNDLE_PATH = "models/random_forest_bundle.pkl"  # put your .pkl here
DB_PATH = "data/app.db"
EXPORT_DIR = "data/exports"


def _ensure_export_dir() -> None:
    os.makedirs(EXPORT_DIR, exist_ok=True)


@st.cache_resource
def _load_bundle():
    """
    Flexible loader:
    - If your bundle is a dict, we will try common keys.
    - If your bundle is directly a model/pipeline, we use it as-is.
    """
    return joblib.load(BUNDLE_PATH)


def _safe_users_count() -> int | None:
    """Used only to tag the export with local DB context. Safe if DB/table missing."""
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


def _infer_feature_columns(bundle) -> list[str] | None:
    if isinstance(bundle, dict):
        for k in ["feature_columns", "feature_cols", "columns", "X_columns"]:
            if k in bundle and isinstance(bundle[k], (list, tuple)):
                return list(bundle[k])
    return None


def _get_model(bundle):
    if isinstance(bundle, dict):
        for k in ["model", "estimator", "pipeline", "clf"]:
            if k in bundle:
                return bundle[k]
    return bundle  # bundle might itself be a model/pipeline


def _build_input_row(feature_cols: list[str], region: str, model_name: str, ev_scenario: str) -> pd.DataFrame:
    """
    Builds a 1-row dataframe for prediction. This is necessarily generic.
    If your trained model expects different columns, update mapping here to match your training features.
    """
    row = {c: 0 for c in feature_cols}

    # Common mappings (safe defaults):
    for c in feature_cols:
        lc = c.lower()
        if lc in ["region", "area"]:
            row[c] = region
        elif lc in ["model", "vehicle_model", "vehicle"]:
            row[c] = model_name
        elif lc in ["scenario", "ev_scenario", "market_trend"]:
            row[c] = ev_scenario

    return pd.DataFrame([row])


def _predict_value(model, X: pd.DataFrame) -> float:
    """
    Works for sklearn models/pipelines with .predict.
    """
    y = model.predict(X)
    # ensure scalar float
    return float(np.array(y).ravel()[0])


def _make_horizon(start_month: str, periods: int) -> list[str]:
    """
    start_month: "YYYY-MM"
    returns list of "YYYY-MM" months
    """
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


def render():
    st.markdown("## Sales Forecasting")
    st.caption("Generate demand forecasts using the integrated model bundle and export results.")

    # ---------- Load model ----------
    if not os.path.exists(BUNDLE_PATH):
        st.error(f"Model bundle not found: {BUNDLE_PATH}. Upload it into /models/ and redeploy.")
        return

    try:
        bundle = _load_bundle()
        model = _get_model(bundle)
        feature_cols = _infer_feature_columns(bundle)
    except Exception as e:
        st.error("Failed to load model bundle.")
        st.code(str(e))
        return

    # ---------- Inputs ----------
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
        help="This is a scenario label. If your model was trained with an EV adoption feature, map it in code.",
    )

    start_month = st.text_input("Start Month (YYYY-MM)", value=datetime.now().strftime("%Y-%m"))

    periods = {"3 months": 3, "6 months": 6, "12 months": 12}[horizon]

    st.divider()

    # ---------- Generate forecast ----------
    if st.button("Generate Forecast", use_container_width=True):
        months = _make_horizon(start_month, periods)

        rows = []
        errors = []

        for i, mo in enumerate(months):
            try:
                if feature_cols:
                    X = _build_input_row(feature_cols, region=region, model_name=vehicle, ev_scenario=scenario)
                    # Try to set month/time column if it exists
                    for c in feature_cols:
                        if c.lower() in ["month", "period", "date", "year_month"]:
                            X.loc[0, c] = mo

                    pred = _predict_value(model, X)
                else:
                    # Fallback: model expects numeric array/pipeline without columns.
                    # This keeps the demo running but you should align this with training features.
                    pred = float(_predict_value(model, pd.DataFrame([[0]])))
                rows.append({"month": mo, "region": region, "vehicle_model": vehicle, "scenario": scenario, "forecast_demand": round(pred, 2)})
            except Exception as e:
                errors.append((mo, str(e)))

        if errors:
            st.warning("Some months failed to predict. Showing what succeeded; fix feature mapping if needed.")
            st.code("\n".join([f"{mo}: {msg}" for mo, msg in errors])[:2000])

        df = pd.DataFrame(rows)

        if df.empty:
            st.error("No forecast rows generated. Your model likely expects different features/columns.")
            return

        # ---------- Display output dataset ----------
        st.markdown("### Forecast Output Dataset")
        st.dataframe(df, use_container_width=True)

        # Simple chart
        st.line_chart(df.set_index("month")["forecast_demand"])

        # ---------- Download CSV ----------
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV",
            data=csv_bytes,
            file_name=f"forecast_{region}_{vehicle}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv".replace(" ", "_"),
            mime="text/csv",
            use_container_width=True,
        )

        # ---------- Save locally to data/exports ----------
        saved_path = _save_forecast(df, region=region, vehicle=vehicle)
        st.success(f"Saved locally: {saved_path}")

        # ---------- Proof tag (optional) ----------
        n_users = _safe_users_count()
        if n_users is not None:
            st.caption(f"Local DB check: users in database = {n_users}")
