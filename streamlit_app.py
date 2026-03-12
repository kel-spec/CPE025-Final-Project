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

# Local hero images 
HOME_HERO = "assets/hero/home.jpg"
ABOUT_BG = "assets/hero/about.jpg"
FEATURES_BG = "assets/hero/features.jpg"
PROCEED_BG = "assets/hero/proceed.jpg"

# Local feature iamges
FEATURE_MEDIA = {
    "ev": "assets/features/ev.jpg",
    "sales": "assets/features/sales.jpg",
    "parts": "assets/features/parts.jpg",
}

PRIVACY_TEXT = """
Privacy Disclosure
We collect: first name, last name, username, email, selected EV type.
Purpose: account creation and profile display.
"""

def load_css():
    with open("assets/theme.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def _b64_file(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def src_for_image(path: str) -> str:
    b64 = _b64_file(path)
    if not b64:
        return ""  # will show gradient fallback
    ext = "jpg"
    if path.lower().endswith(".png"):
        ext = "png"
    return f"data:image/{ext};base64,{b64}"

def get_qp_page(default="home") -> str:
    qp = st.query_params
    p = qp.get("p", default)
    if isinstance(p, list):
        p = p[0] if p else default
    return p or default

def set_qp_page(page: str):
    st.query_params["p"] = page

def init_state():
    st.session_state.setdefault("authed", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("privacy_ack", False)
    st.session_state["page"] = get_qp_page("home")

def header_shell():
    user = st.session_state.get("user")
    uname = user["username"] if user else "Users"
    role = user["role"] if user else "guest"

    logo_b64 = _b64_file("assets/toyota_logo.png")
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="Toyota logo" />' if logo_b64 else ""

    st.markdown(
        f"""
        <div class="site-header">
          <div class="site-header-inner">
            <div class="brand-left">
              <div class="logo-box">{logo_html}</div>
              <div class="brand-text">TOYOTA</div>
              <div class="app-name">{APP_TITLE}</div>
            </div>
            <div class="header-right">Welcome, {uname} ({role})</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def top_nav():
    if st.session_state.get("authed"):
        nav = [
            ("home", "Home"),
            ("dashboard", "Dashboard"),
            ("ev", "EV Smart Routing"),
            ("sales", "Sales Forecasting"),
            ("parts", "Parts Procurement"),
        ]
    else:
        nav = [
            ("home", "Home"),
            ("auth", "Login / Sign Up"),
        ]

    current = st.session_state.get("page", "home")

    items = []
    for key, label in nav:
        cls = "nav-item active" if key == current else "nav-item"
        items.append(f'<a class="{cls}" href="?p={key}">{label}</a>')

    st.markdown(f"<div class='navline'>{''.join(items)}</div>", unsafe_allow_html=True)

def sidebar_panel():
    st.sidebar.markdown("## Menu")
    st.sidebar.caption("Account + shortcuts")

    if st.session_state.get("authed"):
        user = st.session_state.get("user") or {}
        username = user.get("username", "user")
        role = user.get("role", "user")
        vehicle_type = user.get("vehicle_type", "—")

        st.sidebar.markdown(
            f"""
            <div class="sidebar-card">
              <div class="sidebar-label">Signed in</div>
              <div class="sidebar-muted">User: {username}</div>
              <div class="sidebar-muted">Role: {role}</div>
              <div class="sidebar-muted">Vehicle: {vehicle_type}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.sidebar.markdown("### Quick actions")
        if st.sidebar.button("Dashboard", use_container_width=True):
            set_qp_page("dashboard"); st.rerun()
        if st.sidebar.button("Sales Forecasting", use_container_width=True):
            set_qp_page("sales"); st.rerun()
        if st.sidebar.button("EV Smart Routing", use_container_width=True):
            set_qp_page("ev"); st.rerun()
        if st.sidebar.button("Parts Procurement", use_container_width=True):
            set_qp_page("parts"); st.rerun()

        st.sidebar.markdown("### Status (mock)")
        st.sidebar.markdown(
            """
            <div class="sidebar-card">
              <div class="sidebar-label">System</div>
              <div class="sidebar-muted">Sales model: configured</div>
              <div class="sidebar-muted">Last update: —</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.sidebar.button("Log out", use_container_width=True):
            st.session_state["authed"] = False
            st.session_state["user"] = None
            set_qp_page("home")
            st.rerun()
    else:
        st.sidebar.markdown(
            """
            <div class="sidebar-card">
              <div class="sidebar-label">Guest</div>
              <div class="sidebar-muted">Log in to access modules and your profile.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.sidebar.button("Login / Sign Up", use_container_width=True):
            set_qp_page("auth"); st.rerun()

def goto_protected(target_page: str):
    if st.session_state.get("authed"):
        set_qp_page(target_page)
    else:
        set_qp_page("auth")
    st.rerun()

def hero_section(kicker: str, title: str, sub: str, bg_path: str):
    src = src_for_image(bg_path)
    st.markdown(
        f"""
        <div class="hero">
          <img src="{src}" alt="bg" />
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

def feature_card(img_path: str, title: str, sub: str):
    src = src_for_image(img_path)
    st.markdown(
        f"""
        <div class="card">
          <div class="card-media"><img src="{src}" alt="{title}" /></div>
          <div class="card-title">{title}</div>
          <div class="card-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def home_page():
    hero_section(
        "TOYOTA",
        "Decision Support System",
        "Route planning, sales forecasting, and parts procurement in one unified interface.",
        HOME_HERO,
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
        feature_card(FEATURE_MEDIA["ev"], "EV Smart Routing", "Map + ETA visualization")
        if st.button("Open EV Smart Routing", use_container_width=True, key="home_ev"):
            goto_protected("ev")

    with c2:
        feature_card(FEATURE_MEDIA["sales"], "Sales Forecasting", "Model-driven forecast charts")
        if st.button("Open Sales Forecasting", use_container_width=True, key="home_sales"):
            goto_protected("sales")

    with c3:
        feature_card(FEATURE_MEDIA["parts"], "Parts Procurement", "Stock vs demand monitoring")
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
            set_qp_page("auth"); st.rerun()
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
                    set_qp_page("dashboard")
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
    page = st.session_state.get("page", "home")
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

    sidebar_panel()
    header_shell()
    top_nav()

    page = st.session_state.get("page", "home")

    if page == "home":
        home_page()
        return

    if page == "auth":
        auth_page()
        return

    if not st.session_state.get("authed"):
        set_qp_page("auth")
        auth_page()
        return

    app_pages()

if __name__ == "__main__":
    main()
