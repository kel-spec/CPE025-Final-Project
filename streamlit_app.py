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

# Replace these later with local assets for 100% reliability.
# These are stable "images.unsplash.com" URLs (not the random "source.unsplash.com").
HERO_IMAGES = {
    "home": "https://images.unsplash.com/photo-1619767886558-efdc259cde1a?auto=format&fit=crop&w=2400&q=80",
    "about": "https://images.unsplash.com/photo-1611843467160-25afb8df1074?auto=format&fit=crop&w=2400&q=80",
    "modules": "https://images.unsplash.com/photo-1609520505218-7421b92a1f8a?auto=format&fit=crop&w=2400&q=80",
    "proceed": "https://images.unsplash.com/photo-1617886322009-6f0bb0b1f3d3?auto=format&fit=crop&w=2400&q=80",
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
    st.session_state.setdefault("page", "home")     # home | auth | dashboard | ev | sales | parts
    st.session_state.setdefault("privacy_ack", False)
    st.session_state.setdefault("menu_open", False)

def set_sidebar_visibility():
    # Toggle sidebar open/closed using CSS (same button)
    if st.session_state["menu_open"]:
        css = """
        <style>
        section[data-testid="stSidebar"]{ display:block !important; }
        </style>
        """
    else:
        css = """
        <style>
        section[data-testid="stSidebar"]{ display:none !important; }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)

def top_shell():
    user = st.session_state.get("user")
    uname = user["username"] if user else "Users"
    role = user["role"] if user else "guest"

    st.markdown(
        f"""
        <div class="dss-topbar">
          <div class="dss-topbar-row">
            <div class="dss-brand">
              <div class="dss-brand-badge">T</div>
              <div>TOYOTA</div>
            </div>
            <div style="text-align:right">
              <div class="small-muted">Welcome, {uname}! ({role})</div>
            </div>
          </div>
          <div class="dss-title">{APP_TITLE}</div>
          <div class="dss-sub">Decision Support System (Prototype)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def top_nav():
    # Text nav (Home / Login) when logged out.
    # When logged in, shows app pages too.
    if st.session_state["authed"]:
        nav = {
            "home": "Home",
            "dashboard": "Quick Access",
            "ev": "EV Smart Routing",
            "sales": "Sales Forecasting",
            "parts": "Parts Procurement",
        }
    else:
        nav = {
            "home": "Home",
            "auth": "Login / Sign Up",
        }

    cols = st.columns([6, 1, 1])

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
        st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
        if st.button("≡ Menu", use_container_width=True):
            st.session_state["menu_open"] = not st.session_state["menu_open"]
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with cols[2]:
        if st.session_state["authed"]:
            if st.button("Log out", use_container_width=True):
                st.session_state["authed"] = False
                st.session_state["user"] = None
                st.session_state["page"] = "home"
                st.session_state["menu_open"] = False
                st.rerun()

def sidebar_menu():
    # Sidebar content only (visibility toggled by CSS)
    st.sidebar.title("Menu")
    st.sidebar.caption("Scroll shortcuts")

    # These only work on Home page (anchors).
    if st.sidebar.button("Home", use_container_width=True):
        st.session_state["page"] = "home"
        st.rerun()
    st.sidebar.markdown("[About](#about)")
    st.sidebar.markdown("[Modules](#modules)")
    st.sidebar.markdown("[Proceed](#proceed)")

    st.sidebar.divider()
    if st.sidebar.button("Close", use_container_width=True):
        st.session_state["menu_open"] = False
        st.rerun()

def hero_section(section_id: str, kicker: str, title: str, sub: str, show_cta: bool = False):
    img = HERO_IMAGES.get(section_id, "")
    st.markdown(f'<a id="{section_id}"></a>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="hero">
          <img src="{img}" alt="{section_id}" />
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

    if show_cta:
        st.markdown('<div class="landing-root">', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("PROCEED TO LOGIN / SIGN UP", use_container_width=True):
                st.session_state["page"] = "auth"
                st.rerun()
        with c2:
            if st.session_state["authed"]:
                if st.button("GO TO QUICK ACCESS", use_container_width=True):
                    st.session_state["page"] = "dashboard"
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

def home_page():
    sidebar_menu()

    hero_section(
        "home",
        "TOYOTA",
        "Decision Support System",
        "EV smart routing, sales forecasting, and parts procurement in one consistent prototype dashboard.",
        show_cta=False,
    )

    hero_section(
        "about",
        "ABOUT",
        "What this prototype does",
        "A web-based decision support prototype demonstrating EV operations planning and analytics modules with a consistent UI.",
        show_cta=False,
    )

    hero_section(
        "modules",
        "MODULES",
        "Core features",
        "EV Smart Routing, Sales Forecasting, and Parts Procurement. Data/models are mock for now.",
        show_cta=False,
    )

    hero_section(
        "proceed",
        "PROCEED",
        "Login / Register",
        "Register your EV and access the prototype modules.",
        show_cta=True,
    )

def auth_page():
    @st.dialog("Privacy Disclosure")
    def privacy_modal():
        st.markdown(PRIVACY_TEXT)
        st.divider()
        col1, col2 = st.columns([1, 1])
        with col2:
            if st.button("I Understand", use_container_width=True):
                st.session_state["privacy_ack"] = True
                st.rerun()

    sidebar_menu()

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
                    st.session_state["menu_open"] = False
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
    sidebar_menu()
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
    st.set_page_config(page_title=f"{APP_TITLE} (Prototype)", layout="wide")
    load_css()
    init_db()
    ensure_default_admin()
    init_state()

    set_sidebar_visibility()

    top_shell()
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
