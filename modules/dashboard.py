import base64
import os
import streamlit as st

def _b64(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def _img_src(path: str) -> str:
    b64 = _b64(path)
    if not b64:
        return ""
    ext = "jpg"
    if path.lower().endswith(".png"):
        ext = "png"
    return f"data:image/{ext};base64,{b64}"

def _preview(title: str, pills: list[str], img_path: str, note: str):
    img = _img_src(img_path)
    pills_html = "".join([f'<div class="pill">{p}</div>' for p in pills])
    st.markdown(
        f"""
        <div class="preview">
          <div class="preview-head">{title}</div>
          <div class="preview-body">
            <div class="preview-kpi">{pills_html}</div>
            <div class="preview-mini">{f'<img src="{img}" alt="{title}"/>' if img else ''}</div>
            <div style="margin-top:10px; opacity:0.72; font-size:13px;">{note}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render():
    st.markdown("## Dashboard")
    st.caption("Operational overview and module previews.")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Active Vehicles", "128", "+5")
    with k2:
        st.metric("Routes Computed (Today)", "42", "+8")
    with k3:
        st.metric("Sales Forecasting", "Ready", "Model loaded")
    with k4:
        st.metric("Parts Alerts", "3", "-1")

    st.divider()
    st.markdown("### Module previews")

    c1, c2, c3 = st.columns(3)

    with c1:
        _preview(
            "EV Smart Routing",
            ["Map", "ETA list", "Stations (mock)"],
            "assets/previews/ev_preview.jpg",
            "Preview of routing UI. Use EV Smart Routing tab for full view.",
        )

    with c2:
        _preview(
            "Sales Forecasting",
            ["Random Forest", "Multi-month", "Vehicle-level"],
            "assets/previews/sales_preview.jpg",
            "Forecast is working. Use Sales Forecasting tab to generate charts.",
        )

    with c3:
        _preview(
            "Parts Procurement",
            ["Stock vs demand", "Suppliers (mock)", "Alerts (mock)"],
            "assets/previews/parts_preview.jpg",
            "Preview of procurement dashboard. Use Parts Procurement tab for details.",
        )

    st.divider()
    st.markdown("### Notes")
    st.write(
        "- Sales Forecasting is functional and demo-ready.\n"
        "- Other modules remain UI placeholders and will be refined next."
    )
