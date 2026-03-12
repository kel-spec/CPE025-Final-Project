import streamlit as st

def render():
    st.markdown("## Dashboard")
    st.caption("Operational overview and quick access to modules.")

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Active Vehicles", "128", "+5")
    with k2:
        st.metric("Routes Computed (Today)", "42", "+8")
    with k3:
        st.metric("Forecast Accuracy (Model)", "92%", "+1%")
    with k4:
        st.metric("Parts Alerts", "3", "-1")

    st.divider()

    left, right = st.columns([2, 1], vertical_alignment="top")

    with left:
        st.markdown("### Sales Forecasting (Live)")
        st.write(
            "Use **Sales Forecasting** tab to generate vehicle-level forecasts using your trained model. "
            "This section confirms the feature is integrated and ready for demonstration."
        )

        st.markdown("### Quick Access")
        qa1, qa2, qa3 = st.columns(3)
        with qa1:
            st.markdown("**EV Smart Routing**")
            st.caption("Map + ETA visualization")
        with qa2:
            st.markdown("**Sales Forecasting**")
            st.caption("Forecast chart + table (working)")
        with qa3:
            st.markdown("**Parts Procurement**")
            st.caption("Stock vs demand monitoring")

        st.info("Use the tabs at the top to switch modules.", icon="ℹ️")

    with right:
        st.markdown("### System Status")
        st.write("**Data Sources:** mock + model bundle")
        st.write("**Forecasting Model:** Random Forest (loaded)")
        st.write("**Last Refresh:** current session")

        st.divider()
        st.markdown("### Recent Activity (Mock)")
        st.write("- Generated sales forecast (Corolla Cross)")
        st.write("- Viewed EV routing map")
        st.write("- Checked parts inventory alerts")
