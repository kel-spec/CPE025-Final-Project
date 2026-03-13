# =========================
# Pickle compatibility shim
# =========================
class TrainedModelBundle:
    """
    Compatibility class for loading old pickles that reference
    __main__.TrainedModelBundle from the training script/notebook.
    Only used so joblib/pickle can resolve the symbol.
    """
    pass


import base64
import os
import sqlite3
import streamlit as st

from modules.auth import authenticate, create_user, ensure_default_admin
from modules.db import init_db
from modules import dashboard, ev_routing, sales_forecasting, parts_procurement

APP_TITLE = "Toyota Decision Support System"

DB_PATH = "data/app.db"
EXPORT_DIR = "data/exports"

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


def _exports_count() -> int:
    if not os.path.isdir(EXPORT_DIR):
        return 0
    try:
        return len([f for f in os.listdir(EXPORT_DIR) if f.lower().endswith(".csv")])
    except Exception:
        return 0


def _db_exists() -> bool:
    return os.path.exists(DB_PATH)


def _admin_db_details():
    info = {
        "abs_path": os.path.abspath(DB_PATH),
        "exists": os.path.exists(DB_PATH),
        "size_bytes": None,
        "users_count": None,
        "latest_users": [],
        "error": None,
    }
    if not info["exists"]:
        return info

    try:
        info["size_bytes"] = os.path.getsize(DB_PATH)
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        info["users_count"] = int(cur.fetchone()[0])

        try:
            cur.execute(
                """
                SELECT username, email, role
                FROM users
                ORDER BY id DESC
                LIMIT 5
                """
            )
            info["latest_users"] = cur.fetchall()
        except Exception:
            info["latest_users"] = []

        con.close()
    except Exception as e:
        info["error"] = str(e)
        try:
            con.close()
        except Exception:
            pass

    return info


def sidebar_panel():
    st.sidebar.markdown("## Panel")
    st.sidebar.caption("Session • Account")

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

        st.sidebar.markdown(
            f"""
            <div class="sidebar-card" style="margin-top:10px;">
              <div class="sidebar-label">Storage</div>
              <div class="sidebar-muted">Local DB: {"Yes" if _db_exists() else "No"}</div>
              <div class="sidebar-muted">Forecast exports: {_exports_count()} CSV</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.sidebar.markdown("### Utilities")
        if st.sidebar.button("Clear UI cache", use_container_width=True):
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
        "Sign in to access modules. Sales Forecasting is functional and exportable.",
        FEATURES_BG,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        feature_card(FEATURE_MEDIA["ev"], "EV Smart Routing", "Map + ETA visualization")
    with c2:
        feature_card(FEATURE_MEDIA["sales"], "Sales Forecasting", "Forecast chart + dataset output + CSV export")
    with c3:
        feature_card(FEATURE_MEDIA["parts"], "Parts Procurement", "Stock vs demand monitoring")

    hero_section(
        "PROCEED",
        "Login / Register",
        "Register your EV and access the system modules.",
        PROCEED_BG,
    )


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
    role = user.get("role", "user")

    st.subheader("Profile")

    c1, c2 = st.columns([1, 1])
    with c1:
        st.write("**Username:**", user.get("username", "—"))
        st.write("**Email:**", user.get("email", "—"))
        st.write("**Role:**", role)
    with c2:
        st.write("**First Name:**", user.get("first_name", "—"))
        st.write("**Last Name:**", user.get("last_name", "—"))
        st.write("**Vehicle Type:**", user.get("vehicle_type", "—"))

    st.divider()

    with st.expander("Storage status", expanded=False):
        st.write("**Local database exists:**", "Yes" if _db_exists() else "No")
        st.write("**Forecast exports saved:**", f"{_exports_count()} CSV file(s)")
        st.caption("Confirms storage without exposing other users.")

    if role == "admin":
        with st.expander("System proof (Admin only)", expanded=False):
            info = _admin_db_details()
            st.write("**DB absolute path:**", info["abs_path"])
            st.write("**DB exists:**", "Yes" if info["exists"] else "No")
            if info["size_bytes"] is not None:
                st.write("**DB size (bytes):**", info["size_bytes"])
            if info["users_count"] is not None:
                st.write("**Users in DB:**", info["users_count"])
            if info["error"]:
                st.error(info["error"])


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

    app_tabs = st.tabs(["Dashboard", "EV Smart Routing", "Sales Forecasting", "Parts Procurement", "Profile"])
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
