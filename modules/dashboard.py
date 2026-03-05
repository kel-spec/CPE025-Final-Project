import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from modules.nav import goto

def _mini_line(title: str, seed: int = 1):
    rng = np.random.default_rng(seed)
    y = np.clip(np.cumsum(rng.normal(0, 1, 20)) + 20, 5, None)
    x = list(range(1, len(y) + 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=title))
    fig.update_layout(
        height=220, margin=dict(l=10, r=10, t=35, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, title=title
    )
    st.plotly_chart(fig, use_container_width=True)

def render():
    st.title("Toyota Decision Support System")
    st.caption(f"Welcome, {st.session_state['user']['username']} ({st.session_state['user']['role']})")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Vehicles", "128", "+5")
    c2.metric("Routes Computed (Today)", "42", "+8")
    c3.metric("Forecast Accuracy (Mock)", "92%", "+1%")
    c4.metric("Parts Alerts", "3", "-1")

    st.markdown("### Quick Access")
    qa1, qa2, qa3 = st.columns(3)
    with qa1:
        st.markdown('<div class="dss-card">', unsafe_allow_html=True)
        st.write("EV Smart Routing")
        st.caption("Prototype map + ETA list")
        if st.button("Open EV Routing", use_container_width=True):
            goto("ev")
        st.markdown("</div>", unsafe_allow_html=True)

    with qa2:
        st.markdown('<div class="dss-card">', unsafe_allow_html=True)
        st.write("Sales Forecasting")
        st.caption("Prototype actual vs forecast")
        if st.button("Open Sales Forecasting", use_container_width=True):
            goto("sales")
        st.markdown("</div>", unsafe_allow_html=True)

    with qa3:
        st.markdown('<div class="dss-card">', unsafe_allow_html=True)
        st.write("Parts Procurement")
        st.caption("Prototype stock vs demand")
        if st.button("Open Parts Procurement", use_container_width=True):
            goto("parts")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    t1, t2 = st.columns(2)
    with t1:
        _mini_line("Sales Trend (Mock)", seed=10)
    with t2:
        _mini_line("Parts Demand (Mock)", seed=20)

    st.markdown('<div class="small-muted">This is a baseline UI + navigation skeleton. Replace mock data with your datasets/models later.</div>', unsafe_allow_html=True)
