# frontend/app.py
# This is the main entrypoint for the Streamlit app.
import streamlit as st
from auth_utils import is_logged_in, get_current_user, setup_authenticated_sidebar
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Configure page
st.set_page_config(
    page_title="Docsmait - Home",
    page_icon="🏠",
    layout="wide"
)

st.markdown("# Welcome to Docsm<u>ai</u>t 🚀", unsafe_allow_html=True)
st.write("Your AI-powered document and compliance management system.")

if is_logged_in():
    # Setup authenticated sidebar
    setup_authenticated_sidebar()
    
    current_user = get_current_user()
    if current_user:
        # Welcome Header
        st.markdown(f"### Welcome back, {current_user['username']}! 👋")
        from datetime import datetime
        last_login = datetime.now().strftime("%Y-%m-%d %H:%M")
        if current_user['is_admin']:
            st.markdown(f"🔑 **Admin Privileges** | Last login: {last_login}")
        else:
            st.markdown(f"👤 **User Role** | Last login: {last_login}")
        # === PERSONAL ACTIVITY DASHBOARD ===
        st.markdown("## 📊 Personal Activity Dashboard")
        
        # User metrics row - dynamic data
        user_metrics = st.columns([1, 1, 1, 1, 1])
        with user_metrics[0]:
            st.metric("Active Projects", "—")
        with user_metrics[1]:
            st.metric("Pending Tasks", "—")
        with user_metrics[2]:
            st.metric("This Month", "—")
        with user_metrics[3]:
            st.metric("Reviews Due", "—")
        with user_metrics[4]:
            st.metric("Notifications", "—")
        
        # Activity and notifications row
        activity_cols = st.columns([2, 1])
        
        with activity_cols[0]:
            st.markdown("#### 🕒 Recent Activity")
            st.info("No recent activity to display")
        
        with activity_cols[1]:
            st.markdown("#### 🔔 Notifications")
            st.info("No notifications")
        
        # === PROJECT HEALTH OVERVIEW ===
        st.markdown("## 🏆 Project Health Overview")
        
        # Project health metrics
        health_metrics = st.columns([1, 1, 1, 1])
        with health_metrics[0]:
            st.metric("Compliance Score", "—", help="Average compliance across all projects")
        with health_metrics[1]:
            st.metric("Test Coverage", "—", help="Average test coverage")
        with health_metrics[2]:
            st.metric("Risk Mitigation", "—", help="Percentage of risks with mitigation")
        with health_metrics[3]:
            st.metric("On-Time Delivery", "—", help="Projects meeting deadlines")
        
        # Charts row
        charts_cols = st.columns([1, 1, 1])
        
        with charts_cols[0]:
            st.markdown("**Project Status Distribution**")
            st.info("No data available")
        
        with charts_cols[1]:
            st.markdown("**Risk Distribution**")
            st.info("No data available")
        
        with charts_cols[2]:
            st.markdown("**Monthly Trends**")
            st.info("No data available")
        
        # === KEY PROJECT METRICS ===
        st.markdown("## 📋 Key Project Metrics")
        
        metrics_tabs = st.tabs(["📋 Requirements", "⚠️ Risk & Safety", "🧪 Quality & Testing", "📊 Compliance"])
        
        with metrics_tabs[0]:
            req_cols = st.columns([1, 1, 1])
            with req_cols[0]:
                st.metric("Total Requirements", "—")
                st.metric("Approval Rate", "—")
            with req_cols[1]:
                st.metric("Traceability Coverage", "—")
                st.metric("Avg. Review Time", "—")
            with req_cols[2]:
                st.markdown("**Requirements by Type**")
                st.info("No data available")
        
        with metrics_tabs[1]:
            risk_cols = st.columns([1, 1, 1])
            with risk_cols[0]:
                st.metric("Total Hazards", "—")
                st.metric("Mitigation Rate", "—")
            with risk_cols[1]:
                st.metric("SIL/ASIL Achieved", "—")
                st.metric("Critical Risks", "—")
            with risk_cols[2]:
                st.markdown("**Safety Integrity Levels**")
                st.info("No data available")
        
        with metrics_tabs[2]:
            test_cols = st.columns([1, 1, 1])
            with test_cols[0]:
                st.metric("Test Execution Rate", "—")
                st.metric("Pass Rate", "—")
            with test_cols[1]:
                st.metric("Defect Density", "—")
                st.metric("Automation Rate", "—")
            with test_cols[2]:
                st.markdown("**Test Types Distribution**")
                st.info("No data available")
        
        with metrics_tabs[3]:
            comp_cols = st.columns([1, 1, 1])
            with comp_cols[0]:
                st.metric("ISO 13485", "—")
                st.metric("ISO 14971", "—")
            with comp_cols[1]:
                st.metric("IEC 62304", "—")
                st.metric("FDA 21 CFR 820", "—")
            with comp_cols[2]:
                st.markdown("**Compliance Trends**")
                st.info("No data available")
        
        # === RECENT PROJECT UPDATES ===
        st.markdown("## 🔄 Recent Project Updates")
        
        update_cols = st.columns([1, 1])
        
        with update_cols[0]:
            st.markdown("#### 📋 Latest Requirements")
            st.info("No recent requirements")
            
            st.markdown("#### ⚠️ Critical Risks")
            st.info("No critical risks")
        
        with update_cols[1]:
            st.markdown("#### 🏆 Completed Milestones")
            st.info("No completed milestones")
            
            st.markdown("#### 📅 Upcoming Deadlines")
            st.info("No upcoming deadlines")
        
        # === SYSTEM-WIDE ANALYTICS ===
        st.markdown("## 📈 System Analytics & Alerts")
        
        system_cols = st.columns([2, 1])
        
        with system_cols[0]:
            st.markdown("#### 📊 Performance KPIs")
            st.info("No performance metrics available")
        
        with system_cols[1]:
            st.markdown("#### 🚨 System Alerts")
            st.info("No system alerts")
        
        # Footer stats
        footer_cols = st.columns([1, 1, 1, 1, 1])
        with footer_cols[0]:
            st.metric("Total Users", "—")
        with footer_cols[1]:
            st.metric("Active Sessions", "—")
        with footer_cols[2]:
            st.metric("Documents", "—")
        with footer_cols[3]:
            st.metric("System Uptime", "—")
        with footer_cols[4]:
            st.metric("Storage Used", "—")
            
    else:
        st.warning("Session expired. Please login again.")
        if st.button("Go to Login"):
            st.switch_page("pages/Auth.py")
else:
    # Hide sidebar completely and show login prompt
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {display: none !important;}
        .css-1d391kg {display: none;}
        .css-1f4c4qu {display: none;}
        ul[data-testid="stSidebarNavItems"] {display: none !important;}
        section[data-testid="stSidebarNav"] {display: none !important;}
        div[data-testid="stSidebarNav"] {display: none !important;}
        .css-1y4p8pa {display: none !important;}
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.info("Please login or sign up to access all features.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔐 Login / Sign Up", type="primary"):
            st.switch_page("pages/Auth.py")
    with col2:
        st.write("First user gets admin privileges!")

