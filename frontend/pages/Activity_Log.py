# frontend/pages/Activity_Log.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers, BACKEND_URL

require_auth()

st.set_page_config(page_title="Activity Log", page_icon="📋", layout="wide")

# Add CSS for compact layout
st.markdown("""
<style>
    .element-container {
        margin-bottom: 0.5rem;
    }
    .stExpander {
        margin-bottom: 0.5rem;
    }
    .stSelectbox > div > div > div {
        font-size: 14px;
    }
    .stTextInput > div > div > input {
        font-size: 14px;
    }
    .stTextArea > div > div > textarea {
        font-size: 14px;
    }
    .stMetric {
        font-size: 14px;
    }
    .stButton > button {
        font-size: 14px;
        padding: 0.25rem 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .activity-item {
        padding: 10px;
        margin: 5px 0;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        background: #f9f9f9;
    }
    .activity-meta {
        font-size: 12px;
        color: #666;
        margin-bottom: 5px;
    }
    .activity-description {
        font-size: 14px;
        color: #333;
    }
    .activity-user {
        font-weight: bold;
        color: #1f77b4;
    }
    .activity-action {
        font-weight: bold;
        color: #2ca02c;
    }
    .activity-resource {
        font-weight: bold;
        color: #ff7f0e;
    }
</style>
""", unsafe_allow_html=True)

st.title("📋 Activity Log")

setup_authenticated_sidebar()

# Helper functions
def get_user_projects():
    """Get all projects where user is a member"""
    try:
        response = requests.get(f"{BACKEND_URL}/projects", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching projects: {e}")
        return []

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
        if filters.get("offset"):
            params["offset"] = filters["offset"]
        if filters.get("start_date"):
            params["start_date"] = filters["start_date"]
        if filters.get("end_date"):
            params["end_date"] = filters["end_date"]
        if filters.get("action_filter"):
            params["action_filter"] = filters["action_filter"]
        if filters.get("resource_type_filter"):
            params["resource_type_filter"] = filters["resource_type_filter"]
        if filters.get("search_query"):
            params["search_query"] = filters["search_query"]
        
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

def get_activity_stats(**filters):
    """Get activity statistics"""
    try:
        params = {}
        if filters.get("start_date"):
            params["start_date"] = filters["start_date"]
        if filters.get("end_date"):
            params["end_date"] = filters["end_date"]
        
        response = requests.get(f"{BACKEND_URL}/activity-logs/stats", params=params, headers=get_auth_headers())
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'stats' in data:
                return data['stats']
            return data if isinstance(data, dict) else {}
        return {}
    except Exception as e:
        st.error(f"Error fetching activity statistics: {e}")
        return {}

def format_timestamp(timestamp_str):
    """Format timestamp for display"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str

def get_action_icon(action):
    """Get icon for action type"""
    icons = {
        "create": "✅",
        "update": "✏️",
        "delete": "❌",
        "view": "👀",
        "upload": "⬆️",
        "download": "⬇️",
        "approve": "✅",
        "reject": "❌",
        "submit_for_review": "📝",
        "complete_review": "✅",
        "join_project": "👥",
        "leave_project": "👋",
        "add_member": "➕",
        "remove_member": "➖",
        "login": "🔐",
        "logout": "🚪",
        "export": "📤",
        "import": "📥"
    }
    return icons.get(action, "📋")

# Main interface
tab1, tab2, tab3 = st.tabs(["📋 Activity View", "📊 Statistics", "ℹ️ Info"])

with tab1:
    st.subheader("Activity Logs")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        view_type = st.selectbox(
            "View Type",
            ["user", "project", "all"],
            format_func=lambda x: {"user": "My Activities", "project": "Project Activities", "all": "All Activities"}[x]
        )
    
    with col2:
        if view_type == "project":
            projects = get_user_projects()
            if projects:
                project_options = {p["id"]: p["name"] for p in projects}
                selected_project_id = st.selectbox("Select Project", options=list(project_options.keys()), format_func=lambda x: project_options[x])
            else:
                st.warning("No projects found")
                selected_project_id = None
        else:
            selected_project_id = None
    
    with col3:
        date_range = st.selectbox(
            "Date Range",
            ["Last 7 days", "Last 30 days", "Last 90 days", "Custom"],
            index=1
        )
    
    with col4:
        limit = st.selectbox("Items per page", [25, 50, 100, 200], index=1)
    
    # Custom date range
    start_date = None
    end_date = None
    if date_range == "Custom":
        col_start, col_end = st.columns(2)
        with col_start:
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
        with col_end:
            end_date = st.date_input("End Date", value=datetime.now())
    else:
        days_back = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}[date_range]
        start_date = datetime.now() - timedelta(days=days_back)
        end_date = datetime.now()
    
    # Additional filters
    with st.expander("🔍 Advanced Filters"):
        col1, col2, col3 = st.columns(3)
        with col1:
            action_filter = st.selectbox(
                "Action Type",
                ["", "create", "update", "delete", "view", "upload", "download", 
                 "approve", "reject", "submit_for_review", "complete_review", 
                 "login", "logout", "export", "import"],
                format_func=lambda x: "All Actions" if x == "" else x.replace("_", " ").title()
            )
        
        with col2:
            resource_filter = st.selectbox(
                "Resource Type",
                ["", "user", "project", "document", "template", "review", 
                 "code_review", "audit", "system"],
                format_func=lambda x: "All Resources" if x == "" else x.replace("_", " ").title()
            )
        
        with col3:
            search_query = st.text_input("Search in descriptions", placeholder="Search...")
    
    # Fetch and display activities
    filters = {
        "limit": limit,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "action_filter": action_filter if action_filter else None,
        "resource_type_filter": resource_filter if resource_filter else None,
        "search_query": search_query if search_query else None,
        "project_id": selected_project_id if view_type == "project" else None
    }
    
    activities = get_activity_logs(view_type, **filters)
    
    if activities:
        st.write(f"**Found {len(activities)} activities**")
        
        for activity in activities:
            with st.container():
                st.markdown(f"""
                <div class="activity-item">
                    <div class="activity-meta">
                        {get_action_icon(activity['action'])} 
                        <span class="activity-user">{activity.get('username', 'Unknown User')}</span> • 
                        {format_timestamp(activity['timestamp'])} • 
                        <span class="activity-action">{activity['action'].replace('_', ' ').title()}</span> • 
                        <span class="activity-resource">{activity['resource_type'].replace('_', ' ').title()}</span>
                        {f" • Project: {activity.get('project_name', 'N/A')}" if activity.get('project_name') else ""}
                    </div>
                    <div class="activity-description">
                        {activity['description']}
                        {f" ({activity.get('resource_name', '')})" if activity.get('resource_name') else ""}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No activities found for the selected filters.")

with tab2:
    st.subheader("Activity Statistics")
    
    # Date range for stats
    col1, col2 = st.columns(2)
    with col1:
        stats_start_date = st.date_input("Start Date (Stats)", value=datetime.now() - timedelta(days=30), key="stats_start")
    with col2:
        stats_end_date = st.date_input("End Date (Stats)", value=datetime.now(), key="stats_end")
    
    if st.button("📊 Generate Statistics"):
        stats = get_activity_stats(
            start_date=stats_start_date.isoformat(),
            end_date=stats_end_date.isoformat()
        )
        
        if stats:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Activities", stats.get('total_activities', 0))
            
            with col2:
                if stats.get('date_range'):
                    st.write(f"**Period:** {stats['date_range']['start_date'][:10]} to {stats['date_range']['end_date'][:10]}")
            
            with col3:
                st.write("")
            
            # Action breakdown
            if stats.get('action_breakdown'):
                st.subheader("Activity Breakdown by Action")
                action_data = stats['action_breakdown']
                df_actions = pd.DataFrame(list(action_data.items()), columns=['Action', 'Count'])
                df_actions['Action'] = df_actions['Action'].str.replace('_', ' ').str.title()
                st.bar_chart(df_actions.set_index('Action'))
            
            # Resource breakdown  
            if stats.get('resource_breakdown'):
                st.subheader("Activity Breakdown by Resource Type")
                resource_data = stats['resource_breakdown']
                df_resources = pd.DataFrame(list(resource_data.items()), columns=['Resource Type', 'Count'])
                df_resources['Resource Type'] = df_resources['Resource Type'].str.replace('_', ' ').str.title()
                st.bar_chart(df_resources.set_index('Resource Type'))
            
            # Most active users
            if stats.get('most_active_users'):
                st.subheader("Most Active Users")
                users_df = pd.DataFrame(stats['most_active_users'])
                if not users_df.empty:
                    st.dataframe(
                        users_df[['username', 'activity_count']].rename(columns={
                            'username': 'Username',
                            'activity_count': 'Activity Count'
                        }),
                        use_container_width=True
                    )
        else:
            st.warning("No statistics available for the selected date range.")

with tab3:
    st.subheader("About Activity Log")
    
    st.success("✅ **Activity Logging is Enabled**")
    st.write("The system automatically logs all major user activities including:")
    st.write("• Document creation, updates, and reviews")
    st.write("• Project management activities")  
    st.write("• User authentication events")
    st.write("• Resource uploads and downloads")
    
    st.subheader("Features")
    st.write("• **Multi-view Support**: View your own activities, project activities, or system-wide activities (admin)")
    st.write("• **Advanced Filtering**: Filter by date range, action type, resource type, with search functionality")
    st.write("• **Statistics Dashboard**: Activity statistics with breakdowns and charts")
    st.write("• **Real-time Updates**: Activities are logged immediately as they occur")
    
    st.subheader("Data Retention")
    st.write("Activity logs are retained for compliance and audit purposes.")
    st.write("• Default retention period: 365 days")
    st.write("• Logs are automatically cleaned up after the retention period")
    
    st.subheader("Privacy & Security")
    st.write("• User activities are logged with timestamps and IP addresses")
    st.write("• Sensitive information like passwords are never logged")
    st.write("• Access to activity logs is role-based and audited")