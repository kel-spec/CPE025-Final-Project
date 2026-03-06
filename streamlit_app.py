import streamlit as st
from modules.auth import authenticate, create_user, ensure_default_admin
from modules.db import init_db
from modules import dashboard, ev_routing, sales_forecasting, parts_procurement

APP_TITLE = "Toyota Decision Support System"
PAGES = {
    "dashboard": "Quick Access",
    "ev": "EV Smart Routing",
    "sales": "Sales Forecasting",
    "parts": "Parts Procurement",
}

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

PRIVACY_TEXT = """
## Privacy Disclosure (Prototype)

We collect:
- First name, last name, username, email
- Selected electric vehicle type

Purpose:
- Account creation
- Displaying account info in the user profile page
- Basic personalization of the system

Storage:
- Saved in the project database for this prototype.

If you want your data deleted, contact the system administrator.
"""

def load_css():
    try:
        with open("assets/theme.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

    # Minimal auth-specific tweaks (less rounded, cleaner form)
    st.markdown(
        """
        <style>
        .block-container{max-width:1180px;}
        .auth-card{
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.10);
          border-radius: 8px;
          padding: 18px;
        }
        .auth-title{font-size:26px;font-weight:800;margin-bottom:6px;}
        .auth-sub{opacity:0.75;margin-bottom:14px;}
        .stTextInput input, .stSelectbox select{
          border-radius: 6px !important;
        }
        .stButton button{
          border-radius: 6px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def init_state():
    st.session_state.setdefault("authed", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "dashboard")
    st.session_state.setdefault("privacy_ack", False)

def logout():
    st.session_state["authed"] = False
    st.session_state["user"] = None
    st.session_state["page"] = "dashboard"
    st.rerun()

def top_shell():
    user = st.session_state.get("user")
    uname = user["username"] if user else "Users"
    role = user["role"] if user else ""

    st.markdown(
        f"""
        <div class="dss-topbar">
          <div class="dss-topbar-row">
            <div class="dss-brand">
              <div class="dss-brand-badge">T</div>
              <div>TOYOTA</div>
            </div>
            <div style="text-align:right">
              <div class="small-muted">Welcome, {uname}! {f"({role})" if role else ""}</div>
            </div>
          </div>
          <div class="dss-title">{APP_TITLE}</div>
          <div class="dss-sub">Decision Support System (Prototype)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def tabs_nav():
    cols = st.columns([4, 1])
    with cols[0]:
        current = st.session_state["page"]
        selection = st.radio(
            "Navigation",
            options=list(PAGES.keys()),
            index=list(PAGES.keys()).index(current),
            format_func=lambda k: PAGES[k],
            horizontal=True,
            label_visibility="collapsed",
        )
        st.session_state["page"] = selection
    with cols[1]:
        st.button("Log out", on_click=logout, use_container_width=True)

def auth_screen():
    @st.dialog("Privacy Disclosure")
    def privacy_modal():
        st.markdown(PRIVACY_TEXT)
        st.divider()
        col1, col2 = st.columns([1, 1])
        with col2:
            if st.button("I Understand", use_container_width=True):
                st.session_state["privacy_ack"] = True
                st.rerun()

    # Layout: left blank space, right form
    left, right, pad = st.columns([3, 2, 0.2], vertical_alignment="top")

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

            vehicle_type = st.selectbox(
                "Select Which type of Vehicle",
                EV_OPTIONS,
                index=0,
                key="su_vehicle",
            )

            if st.button("View Privacy Disclosure", use_container_width=True):
                privacy_modal()

            privacy_ok = st.checkbox(
                "I have read and understood the privacy disclosure.",
                value=st.session_state["privacy_ack"],
                disabled=not st.session_state["privacy_ack"],
                key="su_privacy",
            )

            if st.session_state["privacy_ack"]:
                st.caption("Privacy disclosure acknowledged.")
            else:
                st.caption("Open the disclosure and click “I Understand” to continue.")

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

def render_page():
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
        dashboard.render()

def main():
    st.set_page_config(page_title=f"{APP_TITLE} (Prototype)", layout="wide")
    load_css()
    init_db()
    ensure_default_admin()
    init_state()

    if not st.session_state["authed"]:
        auth_screen()
        return

    top_shell()
    tabs_nav()
    render_page()

if __name__ == "__main__":
    main()
