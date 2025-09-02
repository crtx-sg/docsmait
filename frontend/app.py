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
        
        # User metrics row
        user_metrics = st.columns([1, 1, 1, 1, 1])
        with user_metrics[0]:
            st.metric("Active Projects", "8", "↑ 2")
        with user_metrics[1]:
            st.metric("Pending Tasks", "14", "↓ 3")
        with user_metrics[2]:
            st.metric("This Month", "47 items", "↑ 15")
        with user_metrics[3]:
            st.metric("Reviews Due", "3", "⚠️")
        with user_metrics[4]:
            st.metric("Notifications", "12", "🔔")
        
        # Activity and notifications row
        activity_cols = st.columns([2, 1])
        
        with activity_cols[0]:
            st.markdown("#### 🕒 Recent Activity")
            recent_activities = [
                {"time": "2 hours ago", "action": "Updated REQ-045", "project": "CardioDevice Pro", "type": "requirement"},
                {"time": "4 hours ago", "action": "Approved HAZ-012", "project": "InsulinPump V2", "type": "risk"},
                {"time": "1 day ago", "action": "Created DES-034", "project": "BloodGlucose Monitor", "type": "design"}
            ]
            
            for activity in recent_activities:
                icon = {"requirement": "📋", "risk": "⚠️", "test": "🧪", "design": "🏗️", "fmea": "🛠️", "compliance": "📑"}.get(activity['type'], "📄")
                st.markdown(f"{icon} **{activity['action']}** in *{activity['project']}* - {activity['time']}")
        
        with activity_cols[1]:
            st.markdown("#### 🔔 Notifications")
            notifications = [
                {"type": "warning", "msg": "Review due: FMEA-007", "time": "Today"},
                {"type": "info", "msg": "New requirement REQ-050", "time": "1h ago"},
                {"type": "success", "msg": "Test TC-034 passed", "time": "4h ago"}
            ]
            
            for notif in notifications:
                if notif['type'] == 'warning':
                    st.warning(f"⚠️ {notif['msg']} - {notif['time']}")
                elif notif['type'] == 'error':
                    st.error(f"🚨 {notif['msg']} - {notif['time']}")
                elif notif['type'] == 'success':
                    st.success(f"✅ {notif['msg']} - {notif['time']}")
                else:
                    st.info(f"ℹ️ {notif['msg']} - {notif['time']}")
        
        # === PROJECT HEALTH OVERVIEW ===
        st.markdown("## 🏆 Project Health Overview")
        
        # Project health metrics
        health_metrics = st.columns([1, 1, 1, 1])
        with health_metrics[0]:
            st.metric("Compliance Score", "94%", "↑ 2%", help="Average compliance across all projects")
        with health_metrics[1]:
            st.metric("Test Coverage", "87%", "↑ 5%", help="Average test coverage")
        with health_metrics[2]:
            st.metric("Risk Mitigation", "92%", "↑ 3%", help="Percentage of risks with mitigation")
        with health_metrics[3]:
            st.metric("On-Time Delivery", "89%", "↓ 1%", help="Projects meeting deadlines")
        
        # Charts row
        charts_cols = st.columns([1, 1, 1])
        
        with charts_cols[0]:
            st.markdown("**Project Status Distribution**")
            project_data = pd.DataFrame({
                'Status': ['Active', 'Under Review', 'Completed', 'On Hold'],
                'Count': [12, 4, 23, 2]
            })
            st.bar_chart(project_data.set_index('Status'))
        
        with charts_cols[1]:
            st.markdown("**Risk Distribution**")
            risk_data = pd.DataFrame({
                'Risk Level': ['High', 'Medium', 'Low'],
                'Count': [8, 24, 43]
            })
            st.bar_chart(risk_data.set_index('Risk Level'))
        
        with charts_cols[2]:
            st.markdown("**Monthly Trends**")
            trend_data = pd.DataFrame({
                'Month': ['Oct', 'Nov', 'Dec', 'Jan'],
                'Requirements': [45, 52, 61, 47],
                'Tests': [32, 38, 44, 51],
                'Risks': [18, 22, 19, 15]
            })
            st.line_chart(trend_data.set_index('Month'))
        
        # === KEY PROJECT METRICS ===
        st.markdown("## 📋 Key Project Metrics")
        
        metrics_tabs = st.tabs(["📋 Requirements", "⚠️ Risk & Safety", "🧪 Quality & Testing", "📊 Compliance"])
        
        with metrics_tabs[0]:
            req_cols = st.columns([1, 1, 1])
            with req_cols[0]:
                st.metric("Total Requirements", "487", "↑ 23 this month")
                st.metric("Approval Rate", "92%", "↑ 3%")
            with req_cols[1]:
                st.metric("Traceability Coverage", "89%", "↑ 7%")
                st.metric("Avg. Review Time", "2.4 days", "↓ 0.3")
            with req_cols[2]:
                st.markdown("**Requirements by Type**")
                req_type_data = pd.DataFrame({
                    'Type': ['Functional', 'Safety', 'Performance', 'Usability', 'Security'],
                    'Count': [186, 124, 89, 56, 32]
                })
                st.bar_chart(req_type_data.set_index('Type'))
        
        with metrics_tabs[1]:
            risk_cols = st.columns([1, 1, 1])
            with risk_cols[0]:
                st.metric("Total Hazards", "156", "↑ 12 this month")
                st.metric("Mitigation Rate", "94%", "↑ 2%")
            with risk_cols[1]:
                st.metric("SIL/ASIL Achieved", "98%", "→ 0%")
                st.metric("Critical Risks", "3", "↓ 2")
            with risk_cols[2]:
                st.markdown("**Safety Integrity Levels**")
                sil_data = pd.DataFrame({
                    'Level': ['ASIL D', 'ASIL C', 'ASIL B', 'ASIL A', 'SIL 3', 'SIL 2'],
                    'Projects': [2, 4, 6, 8, 3, 5]
                })
                st.bar_chart(sil_data.set_index('Level'))
        
        with metrics_tabs[2]:
            test_cols = st.columns([1, 1, 1])
            with test_cols[0]:
                st.metric("Test Execution Rate", "87%", "↑ 5%")
                st.metric("Pass Rate", "94%", "↑ 1%")
            with test_cols[1]:
                st.metric("Defect Density", "0.8/KLOC", "↓ 0.2")
                st.metric("Automation Rate", "76%", "↑ 8%")
            with test_cols[2]:
                st.markdown("**Test Types Distribution**")
                test_data = pd.DataFrame({
                    'Type': ['Unit', 'Integration', 'System', 'Clinical', 'Usability'],
                    'Executed': [234, 156, 89, 23, 34]
                })
                st.bar_chart(test_data.set_index('Type'))
        
        with metrics_tabs[3]:
            comp_cols = st.columns([1, 1, 1])
            with comp_cols[0]:
                st.metric("ISO 13485", "96%", "↑ 2%")
                st.metric("ISO 14971", "94%", "↑ 1%")
            with comp_cols[1]:
                st.metric("IEC 62304", "92%", "↑ 3%")
                st.metric("FDA 21 CFR 820", "89%", "↑ 4%")
            with comp_cols[2]:
                st.markdown("**Compliance Trends**")
                compliance_data = pd.DataFrame({
                    'Month': ['Oct', 'Nov', 'Dec', 'Jan'],
                    'ISO 13485': [91, 93, 94, 96],
                    'ISO 14971': [89, 91, 92, 94],
                    'IEC 62304': [86, 88, 90, 92]
                })
                st.line_chart(compliance_data.set_index('Month'))
        
        # === RECENT PROJECT UPDATES ===
        st.markdown("## 🔄 Recent Project Updates")
        
        update_cols = st.columns([1, 1])
        
        with update_cols[0]:
            st.markdown("#### 📋 Latest Requirements")
            recent_reqs = [
                {"id": "REQ-050", "title": "ECG Signal Processing", "project": "CardioDevice Pro", "status": "Under Review"},
                {"id": "REQ-049", "title": "Battery Life Monitoring", "project": "InsulinPump V2", "status": "Approved"},
                {"id": "REQ-048", "title": "Data Encryption", "project": "BloodGlucose Monitor", "status": "Draft"},
                {"id": "REQ-047", "title": "User Authentication", "project": "PatientPortal", "status": "Implemented"}
            ]
            
            for req in recent_reqs:
                status_color = {"Draft": "🟡", "Under Review": "🟠", "Approved": "🟢", "Implemented": "🔵"}.get(req['status'], "⚪")
                st.markdown(f"{status_color} **{req['id']}**: {req['title']} - *{req['project']}*")
            
            st.markdown("#### ⚠️ Critical Risks")
            critical_risks = [
                {"id": "HAZ-015", "title": "Signal interference", "project": "CardioDevice Pro", "level": "High"},
                {"id": "HAZ-016", "title": "Battery failure", "project": "InsulinPump V2", "level": "Medium"},
                {"id": "HAZ-017", "title": "Data corruption", "project": "PatientPortal", "level": "High"}
            ]
            
            for risk in critical_risks:
                level_color = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}.get(risk['level'], "⚪")
                st.markdown(f"{level_color} **{risk['id']}**: {risk['title']} - *{risk['project']}*")
        
        with update_cols[1]:
            st.markdown("#### 🏆 Completed Milestones")
            milestones = [
                {"title": "Design Review Phase 2", "project": "CardioDevice Pro", "date": "Jan 14"},
                {"title": "Clinical Trial Approval", "project": "InsulinPump V2", "date": "Jan 12"},
                {"title": "FDA Pre-Submission", "project": "BloodGlucose Monitor", "date": "Jan 10"},
                {"title": "Risk Management Plan", "project": "PatientPortal", "date": "Jan 08"}
            ]
            
            for milestone in milestones:
                st.success(f"✅ **{milestone['title']}** - *{milestone['project']}* ({milestone['date']})")
            
            st.markdown("#### 📅 Upcoming Deadlines")
            deadlines = [
                {"title": "Design Verification", "project": "CardioDevice Pro", "date": "Jan 20", "days": 5},
                {"title": "Clinical Protocol", "project": "InsulinPump V2", "date": "Jan 25", "days": 10},
                {"title": "510(k) Submission", "project": "BloodGlucose Monitor", "date": "Feb 01", "days": 17},
                {"title": "Post-Market Report", "project": "PatientPortal", "date": "Feb 15", "days": 31}
            ]
            
            for deadline in deadlines:
                urgency = "🔴" if deadline['days'] <= 7 else "🟠" if deadline['days'] <= 14 else "🟢"
                st.markdown(f"{urgency} **{deadline['title']}** - *{deadline['project']}* ({deadline['days']} days)")
        
        # === SYSTEM-WIDE ANALYTICS ===
        st.markdown("## 📈 System Analytics & Alerts")
        
        system_cols = st.columns([2, 1])
        
        with system_cols[0]:
            st.markdown("#### 📊 Performance KPIs")
            kpi_data = pd.DataFrame({
                'Metric': ['Avg Project Duration', 'Review Cycle Time', 'Defect Resolution', 'User Adoption'],
                'Current': [8.2, 3.1, 2.4, 94],
                'Target': [7.5, 2.8, 2.0, 95],
                'Trend': ['↑ 0.3 months', '↓ 0.4 days', '↓ 0.8 days', '↑ 2%']
            })
            
            for _, row in kpi_data.iterrows():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                col1.write(f"**{row['Metric']}**")
                col2.metric("Current", f"{row['Current']}")
                col3.write(f"Target: {row['Target']}")
                col4.write(row['Trend'])
        
        with system_cols[1]:
            st.markdown("#### 🚨 System Alerts")
            alerts = [
                {"type": "info", "msg": "ISO 13485:2023 update available"},
                {"type": "warning", "msg": "Database backup delayed"},
                {"type": "success", "msg": "All systems operational"},
                {"type": "info", "msg": "New user onboarding: 3 pending"}
            ]
            
            for alert in alerts:
                if alert['type'] == 'warning':
                    st.warning(f"⚠️ {alert['msg']}")
                elif alert['type'] == 'success':
                    st.success(f"✅ {alert['msg']}")
                else:
                    st.info(f"ℹ️ {alert['msg']}")
        
        # Footer stats
        footer_cols = st.columns([1, 1, 1, 1, 1])
        with footer_cols[0]:
            st.metric("Total Users", "47", "↑ 3 this week")
        with footer_cols[1]:
            st.metric("Active Sessions", "23", "Real-time")
        with footer_cols[2]:
            st.metric("Documents", "1,247", "↑ 89 this month")
        with footer_cols[3]:
            st.metric("System Uptime", "99.8%", "Last 30 days")
        with footer_cols[4]:
            st.metric("Storage Used", "2.3 GB", "of 10 GB")
            
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

