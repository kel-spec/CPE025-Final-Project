import streamlit as st
import numpy as np
import plotly.graph_objects as go

def render():
    st.markdown(
        """
        <div class="dss-section">
          <div class="dss-section-head">Parts Procurement</div>
          <div class="dss-section-body">
        """,
        unsafe_allow_html=True,
    )

    top = st.columns([1, 1, 2])
    with top[0]:
        part = st.selectbox("Select Part", ["Brake Pads", "Oil Filter", "Battery Pack", "Tire", "Air Filter"])
    with top[1]:
        supplier = st.selectbox("Select Supplier", ["Supplier A", "Supplier B", "Supplier C"])

    rng = np.random.default_rng(9)
    weeks = [f"W{i}" for i in range(1, 13)]
    stock = np.clip(np.cumsum(rng.normal(0, 15, 12)) + 260, 80, None).round()
    demand = np.clip(stock + rng.normal(0, 30, 12), 60, None).round()

    st.markdown('<div class="dss-card">', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=weeks, y=stock, name="Stock Levels"))
    fig.add_trace(go.Bar(x=weeks, y=demand, name="Demand Forecast"))
    fig.update_layout(
        height=420,
        barmode="group",
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=f"Parts Inventory Analysis — {part} / {supplier}"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    alert = (demand[-1] > stock[-1])
    if alert:
        st.warning("Procurement Alert (Mock): forecast demand exceeds stock for the latest period.")
    else:
        st.success("Procurement Status (Mock): stock covers forecast demand for the latest period.")

    a1, a2, a3 = st.columns(3)
    a1.button("Generate PO Draft", use_container_width=True)
    a2.button("View Lead Times", use_container_width=True)
    a3.button("Export Report", use_container_width=True)

    st.markdown("</div></div>", unsafe_allow_html=True)
