# frontend/pages/Activity_Logs.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers, BACKEND_URL
from config import DATAFRAME_HEIGHT, DEFAULT_EXPORT_FORMAT

require_auth()

st.set_page_config(page_title="Activity Logs", page_icon="📋", layout="wide")

st.title("📋 Activity Logs")
setup_authenticated_sidebar()

# Helper functions
def get_activity_logs(view_type="user", **filters):
    """Get activity logs based on view type and filters"""
    try:
        if view_type == "user":
            endpoint = f"{BACKEND_URL}/activity-logs/my"
        elif view_type == "project":
            project_id = filters.get("project_id")
            if not project_id:
                return []
            endpoint = f"{BACKEND_URL}/activity-logs/project/{project_id}"
        else:  # all
            endpoint = f"{BACKEND_URL}/activity-logs/all"
        
        params = {}
        if filters.get("limit"):
            params["limit"] = filters["limit"]
        
        response = requests.get(endpoint, params=params, headers=get_auth_headers())
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'activities' in data:
                return data['activities']
            return data if isinstance(data, list) else []
        return []
    except Exception as e:
        st.error(f"Error fetching activity logs: {e}")
        return []

# Main interface
tab1, tab2 = st.tabs(["📋 Activity View", "ℹ️ Info"])

with tab1:
    st.subheader("Activity Logs")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        view_type = st.selectbox(
            "View Type",
            ["user", "all"],
            format_func=lambda x: {"user": "My Activities", "all": "All Activities"}[x]
        )
    
    with col2:
        limit = st.selectbox("Items per page", [25, 50, 100], index=1)
    
    # Fetch and display activities
    filters = {"limit": limit}
    activities = get_activity_logs(view_type, **filters)
    
    if activities:
        st.write(f"**Found {len(activities)} activities**")
        
        # Prepare data for st.dataframe
        grid_data = []
        for activity in activities:
            grid_row = {
                'timestamp': activity.get('timestamp', '')[:19],
                'user': activity.get('username', 'Unknown'),
                'action': activity.get('action', 'N/A'),
                'resource': activity.get('resource_type', 'N/A'),
                'description': activity.get('description', 'N/A')
            }
            grid_data.append(grid_row)
        
        # Create DataFrame for activity logs
        df_data = []
        for row in grid_data:
            df_row = {
                'Timestamp': row['timestamp'],
                'User': row['user'],
                'Action': row['action'],
                'Resource Type': row['resource'],
                'Description': row['description']
            }
            df_data.append(df_row)
        
        df = pd.DataFrame(df_data)
        
        # Display DataFrame
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=DATAFRAME_HEIGHT
        )
    else:
        st.info("No activities found.")

with tab2:
    st.subheader("About Activity Logs")
    st.success("✅ **Activity Logging is Enabled**")
    st.write("The system automatically logs all major user activities including:")
    st.write("• Document creation, updates, and reviews")
    st.write("• Project management activities")  
    st.write("• User authentication events")
    st.write("• Resource uploads and downloads")