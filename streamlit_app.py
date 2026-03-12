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

# Home page imagery (replace later with your own local images for 100% reliability)
HOME_HERO_IMG = "https://images.unsplash.com/photo-1617886322009-6f0bb0b1f3d3?auto=format&fit=crop&w=2400&q=80"
FEATURE_MEDIA = {
    "ev": "https://images.unsplash.com/photo-1524666041070-9d87656c25bb?auto=format&fit=crop&w=1400&q=80",
    "sales": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1400&q=80",
    "parts": "https://images.unsplash.com/photo-1586528116493-da8b8d8f99e9?auto=format&fit=crop&w=1400&q=80",
}

PRIVACY_TEXT = """
Privacy Disclosure (Prototype Text Placeholder)
We collect: first name, last name, username, email, selected EV type.
Purpose: account creation and profile display.
"""

def load_css():
    with open("assets/theme.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def init_state():
    st.session_state.setdefault("authed", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "home")     # home | auth | dashboard | ev | sales | parts
    st.session_state.setdefault("privacy_ack", False)

def b64_image(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def header_shell():
    # Logo: use assets/toyota_logo.png if you add it; otherwise fallback badge only
    logo_b64 = b64_image("assets/toyota_logo.png")
    logo_html = ""
    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="Toyota logo" />'
    else:
        # fallback: empty box (still shows badge via CSS)
        logo_html = ""

    user = st.session_state.get("user")
    uname = user["username"] if user else "Users"
    role = user["role"] if user else "guest"

    st.markdown(
        f"""
        <div class="site-header">
          <div class="site-header-inner">
            <div class="brand-left">
              <div class="logo-box">{logo_html}</div>
              <div class="brand-text">TOYOTA</div>
            </div>

            <div class="topnav" style="flex:1;"></div>

            <div class="header-right">
              Welcome, {uname} ({role})
            </div>
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

    # render the nav bar right under the header in the white area style
    st.markdown('<div class="site-header" style="padding-top:0; padding-bottom:10px;">', unsafe_allow_html=True)
    st.markdown('<div class="site-header-inner" style="padding-top:0;">', unsafe_allow_html=True)

    left, mid, right = st.columns([1, 6, 1])
    with mid:
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

    with right:
        if st.session_state["authed"]:
            if st.button("Log out", use_container_width=True):
                st.session_state["authed"] = False
                st.session_state["user"] = None
                st.session_state["page"] = "home"
                st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)

def goto_protected(target_page: str):
    if st.session_state["authed"]:
        st.session_state["page"] = target_page
    else:
        st.session_state["page"] = "auth"
    st.rerun()

def home_page():
    # HERO
    st.markdown(
        f"""
        <div class="hero-wrap">
          <img class="hero-bg" src="{HOME_HERO_IMG}" alt="Hero" />
          <div class="hero-content">
            <div class="hero-kicker">ALL-NEW TOYOTA EV OPERATIONS</div>
            <div class="hero-title">Decision Support System</div>
            <div class="hero-sub">
              Route planning, sales forecasting, and parts procurement in one unified interface.
              Built for operational decisions and reporting.
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # CTA buttons in Streamlit (styled by CSS)
    cta1, cta2, cta3 = st.columns([1, 1, 2])
    with cta1:
        st.markdown('<div class="btn-solid">', unsafe_allow_html=True)
        if st.button("LEARN MORE", use_container_width=True):
            # scroll target not reliable; keep it simple: go to features anchor by rerendering below
            pass
        st.markdown("</div>", unsafe_allow_html=True)
    with cta2:
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("LOGIN / SIGN UP", use_container_width=True):
            st.session_state["page"] = "auth"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # FEATURES SECTION
    st.markdown("<div class='card-grid'></div>", unsafe_allow_html=True)
    st.markdown("### Core Features")

    f1, f2, f3 = st.columns(3)

    with f1:
        st.markdown(
            f"""
            <div class="card">
              <div class="card-media"><img src="{FEATURE_MEDIA['ev']}" alt="EV Routing" /></div>
              <div class="card-title">EV Smart Routing</div>
              <div class="card-sub">Map + ETA visualization (prototype UI)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open EV Smart Routing", use_container_width=True, key="home_ev"):
            goto_protected("ev")

    with f2:
        st.markdown(
            f"""
            <div class="card">
              <div class="card-media"><img src="{FEATURE_MEDIA['sales']}" alt="Sales Forecasting" /></div>
              <div class="card-title">Sales Forecasting</div>
              <div class="card-sub">Model-driven forecast charts</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Sales Forecasting", use_container_width=True, key="home_sales"):
            goto_protected("sales")

    with f3:
        st.markdown(
            f"""
            <div class="card">
              <div class="card-media"><img src="{FEATURE_MEDIA['parts']}" alt="Parts" /></div>
              <div class="card-title">Parts Procurement</div>
              <div class="card-sub">Stock vs demand monitoring</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Parts Procurement", use_container_width=True, key="home_parts"):
            goto_protected("parts")

def auth_page():
    @st.dialog("Privacy Disclosure")
    def privacy_modal():
        st.markdown(PRIVACY_TEXT)
        st.divider()
        c1, c2 = st.columns([1, 1])
        with c2:
            if st.button("I Understand", use_container_width=True):
                st.session_state["privacy_ack"] = True
                st.rerun()

    left, right = st.columns([3, 2], vertical_alignment="top")
    with right:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown('<div class="auth-title">Login</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-sub">Sign in or register your electric vehicle.</div>', unsafe_allow_html=True)

        tabs = st.tabs(["Sign In", "Sign Up"])

        with tabs[0]:
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

        with tabs[1]:
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
