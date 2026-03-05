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

def load_css():
    try:
        with open("assets/theme.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def init_state():
    st.session_state.setdefault("authed", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "dashboard")

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
    top_shell()

    st.markdown('<div class="dss-auth-wrap">', unsafe_allow_html=True)
    mode = st.radio(
        "Mode",
        ["Sign In", "Sign Up"],
        horizontal=True,
        label_visibility="collapsed",
    )

    st.markdown('<div class="dss-auth-head">Login</div>', unsafe_allow_html=True)
    st.markdown('<div class="dss-auth-body">', unsafe_allow_html=True)

    if mode == "Sign In":
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

    else:
        username = st.text_input("Create Username", key="su_user")
        password = st.text_input("Create Password", type="password", key="su_pass")
        role = st.selectbox("Role", ["user", "admin"], index=0)
        if st.button("Create Account", use_container_width=True):
            ok, msg = create_user(username, password, role)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    st.markdown("</div></div>", unsafe_allow_html=True)

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
