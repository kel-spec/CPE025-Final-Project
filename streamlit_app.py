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

# Static hero images (Unsplash “source” URLs; replace later with your own hosted images)
HERO_IMAGES = [
    "https://source.unsplash.com/2400x1400/?electric,car",
    "https://source.unsplash.com/2400x1400/?ev,car",
    "https://source.unsplash.com/2400x1400/?tesla,car",
    "https://source.unsplash.com/2400x1400/?charging,station",
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

    # Minimal auth card styling (cleaner, less round)
    st.markdown(
        """
        <style>
        .block-container{max-width:1180px;}

        .auth-card{
          background: rgba(10,12,16,0.72);
          border: 1px solid rgba(255,255,255,0.10);
          border-radius: 10px;
          padding: 18px;
          backdrop-filter: blur(8px);
        }
        .auth-title{font-size:26px;font-weight:800;margin-bottom:6px;}
        .auth-sub{opacity:0.75;margin-bottom:14px;}

        .stTextInput input, .stSelectbox select{ border-radius: 6px !important; }
        .stButton button{ border-radius: 6px !important; }

        /* Landing */
        .landing-wrap{ padding-top: 14px; }
        .hero{
          border-radius: 16px;
          border: 1px solid rgba(255,255,255,0.10);
          overflow: hidden;
          min-height: 520px;
          position: relative;
          background-size: cover;
          background-position: center;
        }
        .hero::before{
          content:"";
          position:absolute; inset:0;
          background: linear-gradient(90deg, rgba(10,12,16,0.88) 0%, rgba(10,12,16,0.55) 55%, rgba(10,12,16,0.25) 100%);
        }
        .hero-inner{
          position: relative;
          padding: 26px;
          display:grid;
          grid-template-columns: 1.1fr 0.9fr;
          gap: 18px;
        }
        .hero-brand{
          font-weight: 800;
          letter-spacing: 0.4px;
          opacity: 0.9;
        }
        .hero-title{
          font-size: 44px;
          font-weight: 900;
          line-height: 1.05;
          margin-top: 12px;
        }
        .hero-sub{
          margin-top: 10px;
          opacity: 0.78;
          max-width: 52ch;
        }
        .hero-cta{ margin-top: 18px; display:flex; gap:10px; flex-wrap:wrap; }
        .section{
          margin-top: 18px;
          border: 1px solid rgba(255,255,255,0.10);
          border-radius: 16px;
          background: rgba(255,255,255,0.03);
          overflow: hidden;
        }
        .section-h{
          padding: 12px 16px;
          background: rgba(43,75,106,0.40);
          border-bottom: 1px solid rgba(255,255,255,0.08);
          font-weight: 900;
        }
        .section-b{ padding: 16px; }
        .mini-card{
          border: 1px solid rgba(255,255,255,0.10);
          border-radius: 14px;
          background: rgba(255,255,255,0.03);
          padding: 14px;
          height: 100%;
        }

        /* Anchor offset so headings aren’t hidden */
        .anchor{ position: relative; top: -10px; }

        </style>
        """,
        unsafe_allow_html=True,
    )

def init_state():
    st.session_state.setdefault("authed", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "dashboard")
    st.session_state.setdefault("privacy_ack", False)
    st.session_state.setdefault("route", "landing")  # landing | auth | app
    st.session_state.setdefault("hero_idx", 0)

def logout():
    st.session_state["authed"] = False
    st.session_state["user"] = None
    st.session_state["page"] = "dashboard"
    st.session_state["route"] = "landing"
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
        st.markdown('<div class="dss-nav">', unsafe_allow_html=True)
        current = st.session_state["page"]
        selection = st.radio(
            "Navigation",
            options=list(PAGES.keys()),
            index=list(PAGES.keys()).index(current),
            format_func=lambda k: PAGES[k],
            horizontal=True,
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.session_state["page"] = selection
    with cols[1]:
        st.button("Log out", on_click=logout, use_container_width=True)

def landing_sidebar():
    with st.sidebar:
        with st.expander("Menu", expanded=True):
            st.markdown(
                """
                - [Home](#home)
                - [About](#about)
                - [Modules](#modules)
                - [Proceed](#proceed)
                """,
                unsafe_allow_html=True,
            )
        st.divider()
        st.caption("Prototype landing page. Replace images later with your own EV assets.")

def landing_page():
    landing_sidebar()

    # rotate hero image (manual)
    c1, c2, c3 = st.columns([1, 1, 4])
    with c1:
        if st.button("◀", use_container_width=True):
            st.session_state["hero_idx"] = (st.session_state["hero_idx"] - 1) % len(HERO_IMAGES)
            st.rerun()
    with c2:
        if st.button("▶", use_container_width=True):
            st.session_state["hero_idx"] = (st.session_state["hero_idx"] + 1) % len(HERO_IMAGES)
            st.rerun()

    hero_url = HERO_IMAGES[st.session_state["hero_idx"]]

    st.markdown('<div class="landing-wrap">', unsafe_allow_html=True)

    st.markdown('<div class="anchor" id="home"></div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="hero" style="background-image:url('{hero_url}')">
          <div class="hero-inner">
            <div>
              <div class="hero-brand">TOYOTA</div>
              <div class="hero-title">Decision Support System</div>
              <div class="hero-sub">
                EV smart routing, sales forecasting, and parts procurement in one unified dashboard.
              </div>
              <div class="hero-cta">
                <span style="opacity:0.75;">Scroll to learn more or proceed now.</span>
              </div>
            </div>
            <div class="auth-card">
              <div class="auth-title">Proceed</div>
              <div class="auth-sub">Login or register your electric vehicle.</div>
        """,
        unsafe_allow_html=True,
    )

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Go to Login / Sign Up", use_container_width=True):
            st.session_state["route"] = "auth"
            st.rerun()
    with b2:
        if st.button("Open Dashboard (Demo)", use_container_width=True):
            # Only works if already authed; otherwise goes to auth
            if st.session_state["authed"]:
                st.session_state["route"] = "app"
            else:
                st.session_state["route"] = "auth"
            st.rerun()

    st.markdown(
        """
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="anchor" id="about"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="section">
          <div class="section-h">About</div>
          <div class="section-b">
            This prototype demonstrates a decision support web application for EV operations:
            routing support, forecasting, and procurement insights in a consistent interface.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="anchor" id="modules"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="section">
          <div class="section-h">Modules</div>
          <div class="section-b">
        """,
        unsafe_allow_html=True,
    )
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown('<div class="mini-card"><b>EV Smart Routing</b><br><span style="opacity:0.75">Map + ETA (prototype)</span></div>', unsafe_allow_html=True)
    with m2:
        st.markdown('<div class="mini-card"><b>Sales Forecasting</b><br><span style="opacity:0.75">Actual vs forecast (prototype)</span></div>', unsafe_allow_html=True)
    with m3:
        st.markdown('<div class="mini-card"><b>Parts Procurement</b><br><span style="opacity:0.75">Stock vs demand (prototype)</span></div>', unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown('<div class="anchor" id="proceed"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="section">
          <div class="section-h">Proceed</div>
          <div class="section-b">
        """,
        unsafe_allow_html=True,
    )
    if st.button("Proceed to Login / Sign Up", use_container_width=True):
        st.session_state["route"] = "auth"
        st.rerun()
    st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

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

    # back to landing
    top = st.columns([1, 4])
    with top[0]:
        if st.button("← Back", use_container_width=True):
            st.session_state["route"] = "landing"
            st.rerun()

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
                    st.session_state["route"] = "app"
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

            st.checkbox(
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

    # Routing
    if st.session_state["route"] == "landing":
        landing_page()
        return

    if st.session_state["route"] == "auth" and not st.session_state["authed"]:
        auth_screen()
        return

    # App (logged in)
    if not st.session_state["authed"]:
        st.session_state["route"] = "auth"
        auth_screen()
        return

    st.session_state["route"] = "app"
    top_shell()
    tabs_nav()
    render_page()

if __name__ == "__main__":
    main()
