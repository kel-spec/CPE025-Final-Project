import base64
import os
import streamlit as st
import streamlit.components.v1 as components

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

HOME_HERO = "assets/hero/home.jpg"
ABOUT_BG = "assets/hero/about.jpg"
FEATURES_BG = "assets/hero/features.jpg"
PROCEED_BG = "assets/hero/proceed.jpg"

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
        return ""
    ext = "jpg"
    if path.lower().endswith(".png"):
        ext = "png"
    return f"data:image/{ext};base64,{b64}"


def init_state():
    st.session_state.setdefault("authed", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("privacy_ack", False)
    st.session_state.setdefault("guest_tab", "Home")


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


def sidebar_panel():
    st.sidebar.markdown("## Panel")
    st.sidebar.caption("Account • Status • Utilities")

    if st.session_state.get("authed"):
        user = st.session_state.get("user") or {}
        username = user.get("username", "user")
        role = user.get("role", "user")
        email = user.get("email", "—")
        vehicle_type = user.get("vehicle_type", "—")

        st.sidebar.markdown(
            f"""
            <div class="sidebar-card">
              <div class="sidebar-label">Account</div>
              <div class="sidebar-muted">User: {username}</div>
              <div class="sidebar-muted">Role: {role}</div>
              <div class="sidebar-muted">Email: {email}</div>
              <div class="sidebar-muted">Vehicle: {vehicle_type}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.sidebar.markdown(
            """
            <div class="sidebar-card" style="margin-top:10px;">
              <div class="sidebar-label">System health</div>
              <div class="sidebar-muted">DB: connected (local)</div>
              <div class="sidebar-muted">Sales model: available</div>
              <div class="sidebar-muted">Routing: mock</div>
              <div class="sidebar-muted">Procurement: mock</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.sidebar.markdown("### Session actions")
        if st.sidebar.button("Clear UI cache (refresh)", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.rerun()

        if st.sidebar.button("Log out", use_container_width=True):
            st.session_state["authed"] = False
            st.session_state["user"] = None
            st.session_state["guest_tab"] = "Home"
            st.rerun()
    else:
        st.sidebar.markdown(
            """
            <div class="sidebar-card">
              <div class="sidebar-label">Guest</div>
              <div class="sidebar-muted">Use Home / Login tabs in the main page.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.sidebar.button("Go to Login / Sign Up", use_container_width=True):
            st.session_state["guest_tab"] = "Login / Sign Up"
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


def footer_block():
    html = """
    <style>
      .site-footer{
        padding: 26px 18px 12px 18px;
        border-top: 1px solid rgba(255,255,255,0.10);
        background: rgba(10,12,16,0.96);
        color: rgba(255,255,255,0.90);
        font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
      }
      .footer-grid{
        display:grid;
        grid-template-columns: 1.2fr 1fr 1fr 1fr;
        gap: 18px;
        max-width: 1280px;
        margin: 0 auto;
      }
      .footer-brand{ font-weight: 900; letter-spacing: 0.4px; }
      .footer-note{
        margin-top: 10px;
        opacity: 0.75;
        font-size: 13px;
        line-height: 1.6;
      }
      .footer-col-title{
        font-weight: 900;
        letter-spacing: 0.6px;
        margin-bottom: 10px;
        opacity: 0.95;
        font-size: 13px;
      }
      .footer-link{
        display:block;
        opacity: 0.78;
        font-size: 13px;
        margin: 6px 0;
      }
      .footer-bottom{
        max-width: 1280px;
        margin: 18px auto 0 auto;
        display:flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
        opacity: 0.75;
        font-size: 12px;
      }
      .footer-social{ display:flex; gap: 10px; align-items:center; }
      .footer-pill{
        border: 1px solid rgba(255,255,255,0.14);
        background: rgba(255,255,255,0.04);
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 12px;
        opacity: 0.9;
      }
      body{ margin:0; background: rgba(10,12,16,0.96); }
    </style>

    <div class="site-footer">
      <div class="footer-grid">
        <div>
          <div class="footer-brand">© 2026 CPE025 Group — Technological Institute of the Philippines</div>
          <div class="footer-note">
            Toyota Decision Support System — a web-based decision support tool for EV routing,
            sales forecasting, and parts procurement analytics.
          </div>
        </div>

        <div>
          <div class="footer-col-title">PROJECT</div>
          <div class="footer-link">Overview</div>
          <div class="footer-link">System Modules</div>
          <div class="footer-link">Methodology</div>
          <div class="footer-link">Contact the Team</div>
        </div>

        <div>
          <div class="footer-col-title">POLICY</div>
          <div class="footer-link">Privacy Disclosure</div>
          <div class="footer-link">Terms of Use</div>
          <div class="footer-link">Cookie Notice</div>
          <div class="footer-link">Data Deletion Request</div>
        </div>

        <div>
          <div class="footer-col-title">SOCIALS</div>
          <div class="footer-link">Facebook: @CPE025Group</div>
          <div class="footer-link">Instagram: @CPE025Group</div>
          <div class="footer-link">Email: cpe025.group@sample.com</div>
          <div class="footer-link">GitHub: github.com/kel-spec/CPE025-Final-Project</div>
        </div>
      </div>

      <div class="footer-bottom">
        <div class="footer-social">
          <span class="footer-pill">in</span>
          <span class="footer-pill">ig</span>
          <span class="footer-pill">x</span>
          <span class="footer-pill">yt</span>
          <span class="footer-pill">fb</span>
        </div>
        <div>Demo footer text — replace with your real group details.</div>
      </div>
    </div>
    """
    components.html(html, height=330)

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
        "Sign in to access modules. Sales Forecasting is functional and demo-ready.",
        FEATURES_BG,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        feature_card(FEATURE_MEDIA["ev"], "EV Smart Routing", "Map + ETA visualization")
    with c2:
        feature_card(FEATURE_MEDIA["sales"], "Sales Forecasting", "Model-driven forecast charts")
    with c3:
        feature_card(FEATURE_MEDIA["parts"], "Parts Procurement", "Stock vs demand monitoring")

    hero_section(
        "PROCEED",
        "Login / Register",
        "Register your EV and access the system modules.",
        PROCEED_BG,
    )

    footer_block()


def auth_page():
    @st.dialog("Privacy Disclosure")
    def privacy_modal():
        st.markdown(PRIVACY_TEXT)
        st.divider()
        if st.button("I Understand", use_container_width=True):
            st.session_state["privacy_ack"] = True
            st.rerun()

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


def profile_tab():
    user = st.session_state.get("user") or {}
    st.subheader("Profile")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.write("**Username:**", user.get("username", "—"))
        st.write("**Email:**", user.get("email", "—"))
        st.write("**Role:**", user.get("role", "—"))
    with c2:
        st.write("**First Name:**", user.get("first_name", "—"))
        st.write("**Last Name:**", user.get("last_name", "—"))
        st.write("**Vehicle Type:**", user.get("vehicle_type", "—"))


def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    load_css()
    init_db()
    ensure_default_admin()
    init_state()

    sidebar_panel()
    header_shell()

    if not st.session_state.get("authed"):
        tabs = st.tabs(["Home", "Login / Sign Up"])
        if st.session_state.get("guest_tab") == "Login / Sign Up":
            with tabs[0]:
                home_page()
            with tabs[1]:
                auth_page()
        else:
            with tabs[0]:
                home_page()
            with tabs[1]:
                auth_page()
        return

    app_tabs = st.tabs(
        ["Dashboard", "EV Smart Routing", "Sales Forecasting", "Parts Procurement", "Profile"]
    )
    with app_tabs[0]:
        dashboard.render()
    with app_tabs[1]:
        ev_routing.render()
    with app_tabs[2]:
        sales_forecasting.render()
    with app_tabs[3]:
        parts_procurement.render()
    with app_tabs[4]:
        profile_tab()


if __name__ == "__main__":
    main()
