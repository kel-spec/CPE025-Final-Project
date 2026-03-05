import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

def render():
    st.header("Sales Forecasting")
    st.caption("Prototype: actual vs forecast chart with dropdown placeholders.")

    top = st.columns([1, 1, 2])
    with top[0]:
        region = st.selectbox("Select Region", ["NCR", "Luzon", "Visayas", "Mindanao"])
    with top[1]:
        model = st.selectbox("Select Model", ["Corolla Cross", "Vios", "Hilux", "RAV4", "bZ4X (EV)"])

    # mock data
    rng = np.random.default_rng(42)
    months = pd.date_range("2025-01-01", periods=12, freq="MS").strftime("%b")
    actual = np.clip(np.cumsum(rng.normal(0, 20, 12)) + 250, 120, None).round()
    forecast = (actual + rng.normal(0, 25, 12)).round()

    fig = go.Figure()
    fig.add_trace(go.Bar(x=months, y=actual, name="Actual"))
    fig.add_trace(go.Bar(x=months, y=forecast, name="Forecast"))
    fig.add_trace(go.Scatter(x=months, y=(actual * 0.95 + forecast * 0.05), mode="lines+markers", name="Trend"))

    fig.update_layout(
        height=420,
        barmode="group",
        margin=dict(l=10, r=10, t=35, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=f"Sales Forecast Chart — {region} / {model}"
    )
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Next Month Forecast (Mock)", int(max(forecast[-1], 0)))
    c2.metric("MAPE (Mock)", "8.4%")
    c3.metric("Data Points", "12")

    st.markdown('<div class="small-muted">Replace mock arrays with your trained model output later.</div>', unsafe_allow_html=True)
