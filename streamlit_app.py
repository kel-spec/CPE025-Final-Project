import base64
import os
import streamlit as st

from modules.auth import authenticate, create_user, ensure_default_admin
from modules.db import init_db
from modules import dashboard, ev_routing, sales_forecasting, parts_procurement

APP_TITLE = "Toyota Decision Support System"

EV_OPTIONS = [
    "Toyota bZ4X",
    "Nissan Leaf",
    "Tesla Model 3",
    "Tesla Model Y",
    "Hyundai Ioniq 5",
    "Kia EV6",
    "BYD Atto 3",
    "MG ZS EV",
    "Other (EV)",
]

# Backgrounds (replace later with local assets if needed)
HOME_HERO_IMG = "https://images.unsplash.com/photo-1617886322009-6f0bb0b1f3d3?auto=format&fit=crop&w=2400&q=80"
ABOUT_BG = "https://images.unsplash.com/photo-1611843467160-25afb8df1074?auto=format&fit=crop&w=2400&q=80"
FEATURES_BG = "https://images.unsplash.com/photo-1609520505218-7421b92a1f8a?auto=format&fit=crop&w=2400&q=80"
PROCEED_BG = "https://images.unsplash.com/photo-1619767886558-efdc259cde1a?auto=format&fit=crop&w=2400&q=80"

FEATURE_MEDIA = {
    "ev": "https://images.unsplash.com/photo-1524666041070-9d87656c25bb?auto=format&fit=crop&w=1400&q=80",
    "sales": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1400&q=80",
    "parts": "https://images.unsplash.com/photo-1586528116493-da8b8d8f99e9?auto=format&fit=crop&w=1400&q=80",
}

PRIVACY_TEXT = """
Privacy Disclosure
We collect: first name, last name, username, email, selected EV type.
Purpose: account creation and profile display.
"""

def load_css():
    with open("assets/theme.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def init_state():
    st.session_state.setdefault("authed", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "home")  # home | auth | dashboard | ev | sales | parts
    st.session_state.setdefault("privacy_ack", False)

def _b64_image(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def header_shell():
    user = st.session_state.get("user")
    uname = user["username"] if user else "Users"
    role = user["role"] if user else "guest"

    logo_b64 = _b64_image("assets/toyota_logo.png")
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="Toyota logo" />' if logo_b64 else ""

    st.markdown(
        f"""
        <div class="site-header">
          <div class="site-header-inner">
            <div class="brand-left">
              <div class="logo-box">{logo_html}</div>
              <div class="brand-text">TOYOTA</div>
            </div>
            <div class="header-right">Welcome, {uname} ({role})</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def top_nav():
    if st.session_state["authed"]:
        nav = {
            "home": "Home",
            "dashboard": "Dashboard",
            "ev": "EV Smart Routing",
            "sales": "Sales Forecasting",
            "parts": "Parts Procurement",
        }
    else:
        nav = {
            "home": "Home",
            "auth": "Login / Sign Up",
        }

    cols = st.columns([7, 1])

    with cols[0]:
        st.markdown('<div class="topnav">', unsafe_allow_html=True)
        current = st.session_state["page"]
        if current not in nav:
            current = "home"
            st.session_state["page"] = "home"

        choice = st.radio(
            "Navigation",
            options=list(nav.keys()),
            index=list(nav.keys()).index(current),
            format_func=lambda k: nav[k],
            horizontal=True,
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.session_state["page"] = choice

    with cols[1]:
        if st.session_state["authed"]:
            if st.button("Log out", use_container_width=True):
                st.session_state["authed"] = False
                st.session_state["user"] = None
                st.session_state["page"] = "home"
                st.rerun()

def goto_protected(target_page: str):
    if st.session_state["authed"]:
        st.session_state["page"] = target_page
    else:
        st.session_state["page"] = "auth"
    st.rerun()

def hero_section(kicker: str, title: str, sub: str, bg_url: str):
    st.markdown(
        f"""
        <div class="hero">
          <img src="{bg_url}" alt="bg" />
          <div class="hero-content">
            <div class="hero-inner">
              <div class="hero-kicker">{kicker}</div>
              <div class="hero-title">{title}</div>
              <div class="hero-sub">{sub}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def home_page():
    hero_section(
        "TOYOTA",
        "Decision Support System",
        "Route planning, sales forecasting, and parts procurement in one unified interface.",
        HOME_HERO_IMG,
    )

    hero_section(
        "ABOUT",
        "What this system does",
        "A decision support web app for EV operations: routing assistance, forecasting, and procurement insights.",
        ABOUT_BG,
    )

    hero_section(
        "FEATURES",
        "Core features",
        "Open a module below. If you're not logged in, you'll be redirected to Login / Sign Up.",
        FEATURES_BG,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div class="card">
              <div class="card-media"><img src="{FEATURE_MEDIA['ev']}" alt="ev" /></div>
              <div class="card-title">EV Smart Routing</div>
              <div class="card-sub">Map + ETA visualization</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open EV Smart Routing", use_container_width=True, key="home_ev"):
            goto_protected("ev")

    with c2:
        st.markdown(
            f"""
            <div class="card">
              <div class="card-media"><img src="{FEATURE_MEDIA['sales']}" alt="sales" /></div>
              <div class="card-title">Sales Forecasting</div>
              <div class="card-sub">Model-driven forecast charts</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Sales Forecasting", use_container_width=True, key="home_sales"):
            goto_protected("sales")

    with c3:
        st.markdown(
            f"""
            <div class="card">
              <div class="card-media"><img src="{FEATURE_MEDIA['parts']}" alt="parts" /></div>
              <div class="card-title">Parts Procurement</div>
              <div class="card-sub">Stock vs demand monitoring</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Parts Procurement", use_container_width=True, key="home_parts"):
            goto_protected("parts")

    hero_section(
        "PROCEED",
        "Login / Register",
        "Register your EV and access the system modules.",
        PROCEED_BG,
    )

    mid = st.columns([1, 2, 1])[1]
    with mid:
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("PROCEED TO LOGIN / SIGN UP", use_container_width=True, key="proceed_login"):
            st.session_state["page"] = "auth"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

def auth_page():
    @st.dialog("Privacy Disclosure")
    def privacy_modal():
        st.markdown(PRIVACY_TEXT)
        st.divider()
        if st.button("I Understand", use_container_width=True):
            st.session_state["privacy_ack"] = True
            st.rerun()

    left, right = st.columns([3, 2], vertical_alignment="top")
    with right:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown('<div class="auth-title">Login</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-sub">Sign in or register your electric vehicle.</div>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])

        with tab1:
            username = st.text_input("Username", key="li_user")
            password = st.text_input("Password", type="password", key="li_pass")
            if st.button("Sign In", use_container_width=True):
                ok, user = authenticate(username, password)
                if ok:
                    st.session_state["authed"] = True
                    st.session_state["user"] = user
                    st.session_state["page"] = "dashboard"
                    st.rerun()
                else:
                    st.error("Invalid username/password.")

        with tab2:
            first_name = st.text_input("First Name", key="su_first")
            last_name = st.text_input("Last Name", key="su_last")
            username = st.text_input("Username", key="su_user")
            email = st.text_input("Email", key="su_email")
            password = st.text_input("Password", type="password", key="su_pass")
            confirm = st.text_input("Confirm Password", type="password", key="su_pass2")
            vehicle_type = st.selectbox("Select Which type of Vehicle", EV_OPTIONS, key="su_vehicle")

            if st.button("View Privacy Disclosure", use_container_width=True):
                privacy_modal()

            st.checkbox(
                "I have read and understood the privacy disclosure.",
                value=st.session_state["privacy_ack"],
                disabled=not st.session_state["privacy_ack"],
                key="su_privacy",
            )

            if st.button("Sign Up", use_container_width=True):
                if password != confirm:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = create_user(
                        first_name=first_name,
                        last_name=last_name,
                        username=username,
                        email=email,
                        password=password,
                        vehicle_type=vehicle_type,
                        privacy_accepted=st.session_state["privacy_ack"],
                    )
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

        st.markdown("</div>", unsafe_allow_html=True)

def app_pages():
    page = st.session_state["page"]
    if page == "dashboard":
        dashboard.render()
    elif page == "ev":
        ev_routing.render()
    elif page == "sales":
        sales_forecasting.render()
    elif page == "parts":
        parts_procurement.render()
    else:
        home_page()

def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    load_css()
    init_db()
    ensure_default_admin()
    init_state()

    header_shell()
    top_nav()

    if st.session_state["page"] == "home":
        home_page()
        return

    if st.session_state["page"] == "auth":
        auth_page()
        return

    if not st.session_state["authed"]:
        st.session_state["page"] = "auth"
        auth_page()
        return

    app_pages()

if __name__ == "__main__":
    main()
