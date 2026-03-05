import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

def render():
    st.markdown(
        """
        <div class="dss-section">
          <div class="dss-section-head">Sales Forecasting</div>
          <div class="dss-section-body">
        """,
        unsafe_allow_html=True,
    )

    top = st.columns([1, 1, 2])
    with top[0]:
        region = st.selectbox("Select Region", ["NCR", "Luzon", "Visayas", "Mindanao"])
    with top[1]:
        model = st.selectbox("Select Model", ["Corolla Cross", "Vios", "Hilux", "RAV4", "bZ4X (EV)"])

    rng = np.random.default_rng(42)
    months = pd.date_range("2025-01-01", periods=12, freq="MS").strftime("%b")
    actual = np.clip(np.cumsum(rng.normal(0, 20, 12)) + 250, 120, None).round()
    forecast = (actual + rng.normal(0, 25, 12)).round()

    st.markdown('<div class="dss-card">', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=months, y=actual, name="Actual"))
    fig.add_trace(go.Bar(x=months, y=forecast, name="Forecast"))
    fig.update_layout(
        height=420,
        barmode="group",
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=f"Sales Forecast Chart — {region} / {model}"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Next Month Forecast (Mock)", int(max(forecast[-1], 0)))
    c2.metric("MAPE (Mock)", "8.4%")
    c3.metric("Data Points", "12")

    st.markdown("</div></div>", unsafe_allow_html=True)
