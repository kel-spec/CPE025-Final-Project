PAGES = {
    "dashboard": "Dashboard",
    "ev": "EV Smart Routing",
    "sales": "Sales Forecasting",
    "parts": "Parts Procurement",
}

def goto(page_key: str):
    import streamlit as st
    if page_key in PAGES:
        st.session_state["page"] = page_key
