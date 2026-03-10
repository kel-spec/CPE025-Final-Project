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
    if st.session_state["menu_open"]:
        st.markdown(
            "<style>section[data-testid='stSidebar']{display:block !important;}</style>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<style>section[data-testid='stSidebar']{display:none !important;}</style>",
            unsafe_allow_html=True,
        )

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
    st.sidebar.title("Menu")
    st.sidebar.caption("Scroll shortcuts")
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

def footer_template():
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="border-top:1px solid rgba(255,255,255,0.10); padding-top:18px; padding-bottom:10px;">
          <div style="display:flex; flex-wrap:wrap; gap:40px; justify-content:space-between;">
            <div style="min-width:220px;">
              <div style="font-weight:900; letter-spacing:0.5px;">© 2026 YOUR GROUP / SCHOOL</div>
              <div style="opacity:0.75; margin-top:10px;">Replace this footer with your group details.</div>
            </div>

            <div style="min-width:220px;">
              <div style="font-weight:900; margin-bottom:10px;">PROJECT</div>
              <div style="opacity:0.85; line-height:1.9;">
                <div>About</div>
                <div>Modules</div>
                <div>Documentation</div>
                <div>Contact</div>
              </div>
            </div>

            <div style="min-width:220px;">
              <div style="font-weight:900; margin-bottom:10px;">POLICY</div>
              <div style="opacity:0.85; line-height:1.9;">
                <div>Privacy Policy</div>
                <div>Terms of Use</div>
                <div>Cookie Policy</div>
                <div>Data Deletion Request</div>
              </div>
            </div>

            <div style="min-width:220px;">
              <div style="font-weight:900; margin-bottom:10px;">SOCIALS</div>
              <div style="opacity:0.85; line-height:1.9;">
                <div>Facebook</div>
                <div>Instagram</div>
                <div>Email</div>
                <div>GitHub</div>
              </div>
            </div>
          </div>

          <div style="margin-top:18px; opacity:0.65; font-size:12px;">
            Template only. You will replace names/links with your own.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def goto_protected(target_page: str):
    if st.session_state["authed"]:
        st.session_state["page"] = target_page
    else:
        st.session_state["page"] = "auth"
    st.rerun()

def hero_section(section_id: str, kicker: str, title: str, sub: str):
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

def modules_showcase():
    # Title is already rendered by hero section, here we show the 3 feature cards.
    st.markdown("<div class='landing-root'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            "<div class='auth-card'><b>EV Smart Routing</b><div class='small-muted' style='margin-top:8px;'>Map + ETA (prototype)</div></div>",
            unsafe_allow_html=True,
        )
        if st.button("Open EV Smart Routing", use_container_width=True, key="mod_ev"):
            goto_protected("ev")

    with c2:
        st.markdown(
            "<div class='auth-card'><b>Sales Forecasting</b><div class='small-muted' style='margin-top:8px;'>Actual vs forecast (prototype)</div></div>",
            unsafe_allow_html=True,
        )
        if st.button("Open Sales Forecasting", use_container_width=True, key="mod_sales"):
            goto_protected("sales")

    with c3:
        st.markdown(
            "<div class='auth-card'><b>Parts Procurement</b><div class='small-muted' style='margin-top:8px;'>Stock vs demand (prototype)</div></div>",
            unsafe_allow_html=True,
        )
        if st.button("Open Parts Procurement", use_container_width=True, key="mod_parts"):
            goto_protected("parts")

    st.markdown("</div>", unsafe_allow_html=True)

def proceed_cta():
    # Button directly under the text, not isolated at the bottom.
    st.markdown("<div class='landing-root'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("PROCEED TO LOGIN / SIGN UP", use_container_width=True, key="proceed_btn"):
            st.session_state["page"] = "auth"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def home_page():
    sidebar_menu()

    hero_section(
        "home",
        "TOYOTA",
        "Decision Support System",
        "EV smart routing, sales forecasting, and parts procurement in one consistent prototype dashboard.",
    )

    hero_section(
        "about",
        "ABOUT",
        "What this prototype does",
        "A web-based decision support prototype demonstrating EV operations planning and analytics modules with a consistent UI.",
    )

    hero_section(
        "modules",
        "MODULES",
        "Core features",
        "Select a module below. If you're not logged in, you'll be redirected to Login / Sign Up.",
    )
    modules_showcase()

    hero_section(
        "proceed",
        "PROCEED",
        "Login / Register",
        "Register your EV and access the prototype modules.",
    )
    proceed_cta()

    footer_template()

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
