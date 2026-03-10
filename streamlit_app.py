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

# Static section images (replace later with your own hosted EV images)
SECTION_BG = {
    "home": "https://source.unsplash.com/2400x1400/?electric,car",
    "about": "https://source.unsplash.com/2400x1400/?ev,charging",
    "modules": "https://source.unsplash.com/2400x1400/?electric,vehicle",
    "proceed": "https://source.unsplash.com/2400x1400/?charging,station,night",
}

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
    with open("assets/theme.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def init_state():
    st.session_state.setdefault("authed", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "dashboard")
    st.session_state.setdefault("privacy_ack", False)
    st.session_state.setdefault("route", "landing")  # landing | auth | app
    st.session_state.setdefault("menu_open", False)

def logout():
    st.session_state["authed"] = False
    st.session_state["user"] = None
    st.session_state["page"] = "dashboard"
    st.session_state["route"] = "landing"
    st.session_state["menu_open"] = False
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

def landing_topbar():
    # Fixed top bar (visual)
    st.markdown(
        """
        <div class="l-topbar">
          <div class="l-topbar-inner">
            <div class="l-logo">
              <div class="l-mark">T</div>
              <div>TOYOTA</div>
            </div>
            <div class="l-hamburger-slot"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Clickable hamburger rendered by Streamlit, positioned BELOW the fixed bar
    # so it is not blocked by the fixed div overlay.
    st.markdown('<div class="hamburger-spacer"></div>', unsafe_allow_html=True)
    colA, colB = st.columns([6, 1])
    with colB:
        if st.button("☰", use_container_width=True, key="menu_btn"):
            st.session_state["menu_open"] = True
            st.rerun()

def drawer_menu():
    if not st.session_state["menu_open"]:
        return

    st.markdown('<div class="drawer-backdrop"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="drawer">
          <h3>Menu</h3>
          <a href="#home">Home</a>
          <a href="#about">About</a>
          <a href="#modules">Modules</a>
          <a href="#proceed">Proceed</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # close button rendered in Streamlit for state change
    if st.button("Close Menu", use_container_width=True, key="close_menu"):
        st.session_state["menu_open"] = False
        st.rerun()

def section(section_id: str, kicker: str, title: str, sub: str, right_panel: str | None = None, proceed_btn: bool = False):
    bg = SECTION_BG[section_id]
    st.markdown(f'<a id="{section_id}"></a>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="l-section" style="background-image:url('{bg}')">
          <div class="l-content">
            <div>
              <div class="l-kicker">{kicker}</div>
              <div class="l-title">{title}</div>
              <div class="l-sub">{sub}</div>
            </div>
            <div class="l-panel">
              {right_panel or ""}
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if proceed_btn:
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Proceed to Login / Sign Up", use_container_width=True):
                st.session_state["route"] = "auth"
                st.session_state["menu_open"] = False
                st.rerun()
        with c2:
            if st.button("Open Dashboard (if logged in)", use_container_width=True):
                if st.session_state["authed"]:
                    st.session_state["route"] = "app"
                else:
                    st.session_state["route"] = "auth"
                st.session_state["menu_open"] = False
                st.rerun()

def landing_page():
    landing_topbar()
    drawer_menu()

    st.markdown('<div class="landing">', unsafe_allow_html=True)

    section(
        "home",
        "TOYOTA",
        "Decision Support System",
        "EV smart routing, sales forecasting, and parts procurement in one consistent prototype dashboard.",
        right_panel="<b>Explore</b><br><span style='opacity:0.75'>Use the menu to navigate sections.</span>"
    )

    section(
        "about",
        "ABOUT",
        "What this prototype does",
        "A web-based decision support prototype that demonstrates EV operations planning and analytics modules with a consistent UI.",
        right_panel="<b>Goal</b><br><span style='opacity:0.75'>Support operational decisions using dashboards and forecasts.</span>"
    )

    section(
        "modules",
        "MODULES",
        "Core features",
        "Routing support, forecasting visuals, and inventory/procurement insights. Data and models are mock for now.",
        right_panel="""
        <b>Included</b><br>
        <span style='opacity:0.75'>• EV Smart Routing</span><br>
        <span style='opacity:0.75'>• Sales Forecasting</span><br>
        <span style='opacity:0.75'>• Parts Procurement</span>
        """
    )

    section(
        "proceed",
        "PROCEED",
        "Login / Register",
        "Register your EV and access the prototype modules.",
        right_panel="<b>Next</b><br><span style='opacity:0.75'>Proceed to authentication.</span>",
        proceed_btn=True
    )

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

    top = st.columns([1, 6])
    with top[0]:
        if st.button("← Back", use_container_width=True):
            st.session_state["route"] = "landing"
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

    if st.session_state["route"] == "landing":
        landing_page()
        return

    if st.session_state["route"] == "auth" and not st.session_state["authed"]:
        auth_screen()
        return

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
