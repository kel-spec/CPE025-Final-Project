import streamlit as st
from modules.auth import authenticate, create_user, ensure_default_admin
from modules.db import init_db
from modules.nav import PAGES, goto
from modules import dashboard, ev_routing, sales_forecasting, parts_procurement

APP_TITLE = "Toyota Decision Support System (Prototype)"

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

def auth_screen():
    st.title(APP_TITLE)
    st.caption("Sign in / Sign up baseline (User/Admin roles).")

    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])

    with tab1:
        st.markdown('<div class="dss-card">', unsafe_allow_html=True)
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
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="dss-card">', unsafe_allow_html=True)
        username = st.text_input("Create Username", key="su_user")
        password = st.text_input("Create Password", type="password", key="su_pass")
        role = st.selectbox("Role", ["user", "admin"], index=0)
        st.caption("Prototype: admin signup is allowed. Restrict later.")
        if st.button("Create Account", use_container_width=True):
            ok, msg = create_user(username, password, role)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

def top_nav():
    st.markdown("---")
    cols = st.columns([1, 1, 1, 1, 2])
    with cols[0]:
        if st.button("Quick Access", use_container_width=True):
            goto("dashboard")
    with cols[1]:
        if st.button("EV Smart Routing", use_container_width=True):
            goto("ev")
    with cols[2]:
        if st.button("Sales Forecasting", use_container_width=True):
            goto("sales")
    with cols[3]:
        if st.button("Parts Procurement", use_container_width=True):
            goto("parts")
    with cols[4]:
        st.write("")
        st.write("")
        st.button("Log out", on_click=logout, use_container_width=True)

def side_panel():
    with st.sidebar:
        st.header("Menu")
        st.caption(f"Signed in as: {st.session_state['user']['username']}")
        st.caption(f"Role: {st.session_state['user']['role']}")
        st.markdown("---")
        page = st.radio(
            "Navigate",
            list(PAGES.keys()),
            format_func=lambda k: PAGES[k],
            index=list(PAGES.keys()).index(st.session_state["page"]),
        )
        st.session_state["page"] = page

        st.markdown("---")
        if st.session_state["user"]["role"] == "admin":
            st.subheader("Admin (Mock)")
            st.button("User Management", use_container_width=True)
            st.button("System Settings", use_container_width=True)
        else:
            st.subheader("User Tools (Mock)")
            st.button("Saved Reports", use_container_width=True)
            st.button("Profile", use_container_width=True)

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
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    load_css()
    init_db()
    ensure_default_admin()
    init_state()

    if not st.session_state["authed"]:
        auth_screen()
        return

    top_nav()
    side_panel()
    render_page()

if __name__ == "__main__":
    main()
