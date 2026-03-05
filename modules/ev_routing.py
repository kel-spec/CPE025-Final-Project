import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium

def render():
    st.markdown(
        """
        <div class="dss-section">
          <div class="dss-section-head">EV Smart Routing</div>
          <div class="dss-section-body">
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 2], gap="large")

    with left:
        st.markdown('<div class="dss-card">', unsafe_allow_html=True)
        st.subheader("Inputs")
        battery = st.slider("Battery (%)", 0, 100, 55)
        origin = st.text_input("Origin", "Toyota QC")
        destination = st.text_input("Destination", "BGC Taguig")
        optimize_for = st.selectbox("Optimize for", ["Fastest", "Shortest", "Least Charging Stops"])

        st.markdown("---")
        st.subheader("ETAs (Mock)")
        df = pd.DataFrame({
            "Stop": ["Charger A", "Charger B", "Destination"],
            "Distance (km)": [5, 10, 18],
            "ETA (min)": [12, 25, 44],
        })
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"Battery: {battery}% | Optimize: {optimize_for}")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="dss-card">', unsafe_allow_html=True)
        st.subheader("Map (Mock)")
        center = (14.5995, 120.9842)
        m = folium.Map(location=center, zoom_start=12, tiles="CartoDB positron")

        rng = np.random.default_rng(7)
        pts = [(center[0] + float(rng.normal(0, 0.02)), center[1] + float(rng.normal(0, 0.02))) for _ in range(7)]

        folium.Marker(pts[0], tooltip=f"Origin: {origin}", icon=folium.Icon(color="blue")).add_to(m)
        folium.Marker(pts[-1], tooltip=f"Destination: {destination}", icon=folium.Icon(color="red")).add_to(m)

        for i, p in enumerate(pts[1:-1], start=1):
            folium.CircleMarker(p, radius=6, tooltip=f"Charger {i}", color="#2B4B6A", fill=True).add_to(m)

        folium.PolyLine(pts, color="#2B4B6A", weight=5, opacity=0.9).add_to(m)
        st_folium(m, height=520, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)
