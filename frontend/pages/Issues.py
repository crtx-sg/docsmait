# frontend/pages/Issues.py
import streamlit as st
import requests
from datetime import datetime, date
import pandas as pd
from typing import List, Dict, Any, Optional
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers
from config import BACKEND_URL

require_auth()

st.set_page_config(page_title="Issues Management", page_icon="🐛", layout="wide")

# Add CSS for styling
st.markdown("""
<style>
    .element-container {
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
    .priority-high {
        background-color: #ffe6e6 !important;
        border-left: 4px solid #ff4444 !important;
    }
    .priority-medium {
        background-color: #fff3e6 !important;
        border-left: 4px solid #ff9944 !important;
    }
    .priority-low {
        background-color: #e6f7ff !important;
        border-left: 4px solid #4499ff !important;
    }
</style>
""", unsafe_allow_html=True)

setup_authenticated_sidebar()

st.title("🐛 Issues Management")

# Helper functions
def get_user_projects() -> List[Dict]:
    """Fetch user's projects"""
    try:
        response = requests.get(f"{BACKEND_URL}/projects", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching projects: {str(e)}")
        return []

def get_project_members(project_id: str) -> List[Dict]:
    """Fetch project members for assignee selection"""
    try:
        response = requests.get(f"{BACKEND_URL}/projects/{project_id}", headers=get_auth_headers())
        if response.status_code == 200:
            project_data = response.json()
            return project_data.get("members", [])
        return []
    except Exception as e:
        st.error(f"Error fetching project members: {str(e)}")
        return []

def get_project_issues(project_id: str, status_filter: Optional[str] = None, 
                      priority_filter: Optional[str] = None, 
                      type_filter: Optional[str] = None) -> List[Dict]:
    """Fetch issues for a project"""
    try:
        params = {}
        if status_filter:
            params["status"] = status_filter
        if priority_filter:
            params["priority"] = priority_filter
        if type_filter:
            params["issue_type"] = type_filter
            
        response = requests.get(
            f"{BACKEND_URL}/projects/{project_id}/issues",
            headers=get_auth_headers(),
            params=params
        )
        if response.status_code == 200:
            return response.json().get("issues", [])
        return []
    except Exception as e:
        st.error(f"Error fetching issues: {str(e)}")
        return []

def create_issue(issue_data: Dict) -> bool:
    """Create a new issue"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/projects/{issue_data['project_id']}/issues",
            headers=get_auth_headers(),
            json=issue_data
        )
        if response.status_code == 200:
            st.success("Issue created successfully!")
            return True
        else:
            error_data = response.json()
            st.error(f"Error creating issue: {error_data.get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error creating issue: {str(e)}")
        return False

def update_issue(issue_id: str, update_data: Dict) -> bool:
    """Update an issue"""
    try:
        response = requests.put(
            f"{BACKEND_URL}/issues/{issue_id}",
            headers=get_auth_headers(),
            json=update_data
        )
        if response.status_code == 200:
            st.success("Issue updated successfully!")
            return True
        else:
            error_data = response.json()
            st.error(f"Error updating issue: {error_data.get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error updating issue: {str(e)}")
        return False

def delete_issue(issue_id: str) -> bool:
    """Delete an issue"""
    try:
        response = requests.delete(
            f"{BACKEND_URL}/issues/{issue_id}",
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            st.success("Issue deleted successfully!")
            return True
        else:
            error_data = response.json()
            st.error(f"Error deleting issue: {error_data.get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error deleting issue: {str(e)}")
        return False

def get_issue_comments(issue_id: str) -> List[Dict]:
    """Get comments for an issue"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/issues/{issue_id}/comments",
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json().get("comments", [])
        return []
    except Exception as e:
        st.error(f"Error fetching comments: {str(e)}")
        return []

def add_issue_comment(issue_id: str, comment_text: str) -> bool:
    """Add a comment to an issue"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/issues/{issue_id}/comments",
            headers=get_auth_headers(),
            json={"comment_text": comment_text}
        )
        if response.status_code == 200:
            st.success("Comment added successfully!")
            return True
        else:
            error_data = response.json()
            st.error(f"Error adding comment: {error_data.get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error adding comment: {str(e)}")
        return False

# Main UI
projects = get_user_projects()

if not projects:
    st.warning("No projects found. Please create or join a project to manage issues.")
    st.stop()

# Project selection
project_options = {project["name"]: project["id"] for project in projects}
selected_project_name = st.selectbox("Select Project", list(project_options.keys()))
selected_project_id = project_options[selected_project_name] if selected_project_name else None

if not selected_project_id:
    st.warning("Please select a project")
    st.stop()

# Tab layout
tab_create, tab_manage, tab_export = st.tabs(["➕ Create Issue", "⚙️ Manage Issues", "📤 Export Issues"])

# Create Issue Tab
with tab_create:
    st.header("Create New Issue")
    
    # Initialize form state
    if "form_submitted_successfully" not in st.session_state:
        st.session_state.form_submitted_successfully = False
    if "clear_form" not in st.session_state:
        st.session_state.clear_form = False
    
    # Show success message if form was submitted successfully
    if st.session_state.form_submitted_successfully:
        st.success("✅ Issue created successfully! Form cleared for next issue.")
        st.session_state.form_submitted_successfully = False
    
    with st.form("create_issue_form", clear_on_submit=True):
        # Main issue details
        issue_title = st.text_input("Title*", 
            placeholder="Brief description of the issue", 
            value="" if st.session_state.clear_form else None)
        issue_description = st.text_area("Description*", 
            placeholder="Detailed description of the issue...", 
            height=150,
            value="" if st.session_state.clear_form else None)
        
        # Two column layout for metadata
        col1, col2 = st.columns(2)
        
        with col1:
            issue_type = st.selectbox("Type*", ["Bug", "Feature", "Enhancement", "Task", "Documentation"])
            priority = st.selectbox("Priority*", ["High", "Medium", "Low"])
            severity = st.selectbox("Severity*", ["Critical", "Major", "Minor"])
            version = st.text_input("Version", 
                placeholder="e.g., 1.0.0",
                value="" if st.session_state.clear_form else None)
            
        with col2:
            component = st.text_input("Component", 
                placeholder="e.g., Frontend, Backend",
                value="" if st.session_state.clear_form else None)
            due_date = st.date_input("Due Date", value=None)
            story_points = st.text_input("Story Points", 
                placeholder="e.g., 1, 2, 3, 5, 8",
                value="" if st.session_state.clear_form else None)
            
            # Labels (multi-select simulation)
            labels_input = st.text_input("Labels", 
                placeholder="Enter comma-separated labels",
                value="" if st.session_state.clear_form else None)
            labels = [label.strip() for label in labels_input.split(",") if label.strip()] if labels_input else []
        
        # Assignees section
        project_members = get_project_members(selected_project_id)
        if project_members:
            assignee_options = {f"{member['username']} ({member['email']})": member['user_id'] for member in project_members}
            assignee_names = st.multiselect("Assignees", list(assignee_options.keys()))
            assignees = [assignee_options[name] for name in assignee_names]
        else:
            assignees = []
            st.info("No project members found for assignment")
        
        # Initial comment
        initial_comment = st.text_area("Initial Comment", 
            placeholder="Optional initial comment...", 
            height=100,
            value="" if st.session_state.clear_form else None)
        
        # Form buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            cancel_clicked = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        with col2:
            submitted = st.form_submit_button("✅ Create Issue", type="primary", use_container_width=True)
        
        # Handle Cancel button
        if cancel_clicked:
            st.session_state.clear_form = True
            st.info("Form cleared and ready for new input.")
            st.rerun()
        
        # Handle Create Issue button
        if submitted:
            if not issue_title or not issue_description:
                st.error("Title and Description are required")
            else:
                issue_data = {
                    "project_id": selected_project_id,
                    "title": issue_title,
                    "description": issue_description,
                    "issue_type": issue_type,
                    "priority": priority,
                    "severity": severity,
                    "version": version,
                    "labels": labels,
                    "component": component,
                    "due_date": due_date.isoformat() if due_date else None,
                    "story_points": story_points,
                    "assignees": assignees,
                    "comment": initial_comment
                }
                
                if create_issue(issue_data):
                    st.session_state.form_submitted_successfully = True
                    st.session_state.clear_form = True
                    st.rerun()
    
    # Reset clear_form flag after rerun
    if st.session_state.clear_form:
        st.session_state.clear_form = False

# Manage Issues Tab
with tab_manage:
    st.header("Manage Issues")
    
    # Filters
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1, 1, 1, 1])
    
    with filter_col1:
        status_filter = st.selectbox("Filter by Status", ["All", "open", "in_progress", "closed", "resolved"], key="status_filter")
        status_filter = None if status_filter == "All" else status_filter
    
    with filter_col2:
        priority_filter = st.selectbox("Filter by Priority", ["All", "High", "Medium", "Low"], key="priority_filter")
        priority_filter = None if priority_filter == "All" else priority_filter
    
    with filter_col3:
        type_filter = st.selectbox("Filter by Type", ["All", "Bug", "Feature", "Enhancement", "Task", "Documentation"], key="type_filter")
        type_filter = None if type_filter == "All" else type_filter
    
    with filter_col4:
        if st.button("🔄 Refresh", key="refresh_issues"):
            st.rerun()
    
    # Get issues with filters
    issues = get_project_issues(selected_project_id, status_filter, priority_filter, type_filter)
    
    if issues:
        # Convert to DataFrame for display
        df_data = []
        for issue in issues:
            df_data.append({
                "ID": issue.get("issue_number", issue["id"][:8]),  # Use issue_number if available
                "Title": issue["title"],
                "Type": issue["issue_type"],
                "Priority": issue["priority"],
                "Severity": issue["severity"],
                "Status": issue["status"],
                "Assignees": ", ".join(issue.get("assignee_usernames", [])),
                "Comments": issue.get("comment_count", 0),
                "Created": datetime.fromisoformat(issue["created_at"]).strftime("%Y-%m-%d"),
                "Creator": issue["creator_username"]
            })
        
        df = pd.DataFrame(df_data)
        
        # Display issues dataframe
        st.markdown("### Issues List")
        selected_issue_indices = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            height=min(400, len(df) * 35 + 50)
        )
        
        # Handle issue selection - similar to Design Record pattern
        if selected_issue_indices and len(selected_issue_indices["selection"]["rows"]) > 0:
            selected_row = selected_issue_indices["selection"]["rows"][0]
            selected_issue = issues[selected_row]
            
            # Store selected issue in session state
            if st.session_state.get('selected_issue_id') != selected_issue['id']:
                st.session_state.selected_issue_id = selected_issue['id']
                st.session_state.selected_issue_data = selected_issue
                st.rerun()
        
        # Show editable form for selected issue (similar to Design Record)
        if st.session_state.get('selected_issue_data'):
            selected_issue = st.session_state.selected_issue_data
            st.markdown("---")
            st.markdown("### 📝 Edit Selected Issue")
            
            with st.form("edit_issue_form"):
                # Main issue details
                edited_title = st.text_input("Title*", value=selected_issue.get('title', ''))
                edited_description = st.text_area("Description*", value=selected_issue.get('description', ''), height=150)
                
                # Two column layout for metadata
                col1, col2 = st.columns(2)
                
                with col1:
                    edited_type = st.selectbox("Type*", 
                        ["Bug", "Feature", "Enhancement", "Task", "Documentation"],
                        index=["Bug", "Feature", "Enhancement", "Task", "Documentation"].index(selected_issue.get('issue_type', 'Bug'))
                    )
                    edited_priority = st.selectbox("Priority*", 
                        ["High", "Medium", "Low"],
                        index=["High", "Medium", "Low"].index(selected_issue.get('priority', 'Medium'))
                    )
                    edited_severity = st.selectbox("Severity*", 
                        ["Critical", "Major", "Minor"],
                        index=["Critical", "Major", "Minor"].index(selected_issue.get('severity', 'Major'))
                    )
                    edited_status = st.selectbox("Status*", 
                        ["open", "in_progress", "closed", "resolved"],
                        index=["open", "in_progress", "closed", "resolved"].index(selected_issue.get('status', 'open'))
                    )
                
                with col2:
                    edited_version = st.text_input("Version", value=selected_issue.get('version', ''))
                    edited_component = st.text_input("Component", value=selected_issue.get('component', ''))
                    
                    # Handle due date
                    current_due_date = None
                    if selected_issue.get('due_date'):
                        try:
                            current_due_date = datetime.fromisoformat(selected_issue['due_date']).date()
                        except:
                            pass
                    edited_due_date = st.date_input("Due Date", value=current_due_date)
                    
                    edited_story_points = st.text_input("Story Points", value=selected_issue.get('story_points', ''))
                
                # Labels
                current_labels = ', '.join(selected_issue.get('labels', []))
                edited_labels_input = st.text_input("Labels", value=current_labels, placeholder="Enter comma-separated labels")
                edited_labels = [label.strip() for label in edited_labels_input.split(",") if label.strip()] if edited_labels_input else []
                
                # Assignees
                project_members = get_project_members(selected_project_id)
                if project_members:
                    assignee_options = {f"{member['username']} ({member['email']})": member['user_id'] for member in project_members}
                    
                    # Pre-select current assignees
                    current_assignees = selected_issue.get('assignees', [])
                    current_assignee_names = []
                    for name, user_id in assignee_options.items():
                        if user_id in current_assignees:
                            current_assignee_names.append(name)
                    
                    edited_assignee_names = st.multiselect("Assignees", list(assignee_options.keys()), default=current_assignee_names)
                    edited_assignees = [assignee_options[name] for name in edited_assignee_names]
                else:
                    edited_assignees = []
                    st.info("No project members found for assignment")
                
                # Form buttons
                col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                
                with col2:
                    update_submitted = st.form_submit_button("✅ Update Issue", type="primary", use_container_width=True)
                
                with col3:
                    delete_submitted = st.form_submit_button("🗑️ Delete Issue", type="secondary", use_container_width=True)
                
                if update_submitted:
                    if not edited_title or not edited_description:
                        st.error("Title and Description are required")
                    else:
                        update_data = {
                            "title": edited_title,
                            "description": edited_description,
                            "issue_type": edited_type,
                            "priority": edited_priority,
                            "severity": edited_severity,
                            "status": edited_status,
                            "version": edited_version,
                            "component": edited_component,
                            "labels": edited_labels,
                            "due_date": edited_due_date.isoformat() if edited_due_date else None,
                            "story_points": edited_story_points,
                            "assignees": edited_assignees
                        }
                        
                        if update_issue(selected_issue['id'], update_data):
                            # Clear selection and refresh
                            if 'selected_issue_id' in st.session_state:
                                del st.session_state.selected_issue_id
                            if 'selected_issue_data' in st.session_state:
                                del st.session_state.selected_issue_data
                            st.rerun()
                
                if delete_submitted:
                    if delete_issue(selected_issue['id']):
                        # Clear selection and refresh
                        if 'selected_issue_id' in st.session_state:
                            del st.session_state.selected_issue_id
                        if 'selected_issue_data' in st.session_state:
                            del st.session_state.selected_issue_data
                        st.rerun()
            
            # Comments section with dataframe
            st.markdown("### 💬 Comments")
            comments = get_issue_comments(selected_issue['id'])
            
            if comments:
                # Convert comments to DataFrame
                comments_data = []
                for comment in comments:
                    comments_data.append({
                        "Username": comment['username'],
                        "Comment": comment['comment_text'][:100] + "..." if len(comment['comment_text']) > 100 else comment['comment_text'],
                        "Date": datetime.fromisoformat(comment['created_at']).strftime('%Y-%m-%d %H:%M'),
                        "Full Comment": comment['comment_text']  # Keep full text for selection
                    })
                
                comments_df = pd.DataFrame(comments_data)
                
                # Display comments dataframe
                selected_comment_indices = st.dataframe(
                    comments_df[["Username", "Comment", "Date"]],  # Hide full comment column
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    height=min(300, len(comments_df) * 35 + 50)
                )
                
                # Show full comment when selected
                if selected_comment_indices and len(selected_comment_indices["selection"]["rows"]) > 0:
                    selected_comment_row = selected_comment_indices["selection"]["rows"][0]
                    full_comment = comments_data[selected_comment_row]["Full Comment"]
                    st.markdown("**Full Comment:**")
                    st.info(full_comment)
            else:
                st.info("No comments yet")
            
            # Add comment form
            with st.form(f"add_comment_{selected_issue['id']}"):
                new_comment = st.text_area("Add Comment", placeholder="Enter your comment...")
                col1, col2, col3 = st.columns([1, 1, 2])
                with col2:
                    if st.form_submit_button("Add Comment", use_container_width=True):
                        if new_comment.strip():
                            if add_issue_comment(selected_issue['id'], new_comment):
                                st.rerun()
                        else:
                            st.error("Comment cannot be empty")
    else:
        st.info("No issues found for the selected filters")

# Export Issues Tab
with tab_export:
    st.header("Export Issues")
    
    # Export options
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        export_format = st.selectbox("Export Format", ["CSV", "Markdown Table"])
        
    with export_col2:
        # Include filters for export
        include_closed = st.checkbox("Include Closed Issues", value=True)
    
    # Get all issues for export
    export_status_filter = None if include_closed else "open"
    all_issues = get_project_issues(selected_project_id, export_status_filter)
    
    if all_issues:
        st.markdown(f"**{len(all_issues)} issues** will be exported from project: **{selected_project_name}**")
        
        # Show preview
        preview_df_data = []
        for issue in all_issues[:5]:  # Show first 5 as preview
            preview_df_data.append({
                "ID": issue.get("issue_number", issue["id"][:8]),
                "Title": issue["title"][:50] + "..." if len(issue["title"]) > 50 else issue["title"],
                "Type": issue["issue_type"],
                "Priority": issue["priority"],
                "Status": issue["status"],
                "Assignees": ", ".join(issue.get("assignee_usernames", [])),
                "Created": datetime.fromisoformat(issue["created_at"]).strftime("%Y-%m-%d")
            })
        
        if preview_df_data:
            st.markdown("**Preview (first 5 issues):**")
            preview_df = pd.DataFrame(preview_df_data)
            st.dataframe(preview_df, use_container_width=True, hide_index=True)
        
        # Export functionality
        if st.button("🔽 Export Issues", type="primary"):
            if export_format == "CSV":
                # Prepare CSV data
                csv_data = []
                for issue in all_issues:
                    csv_data.append({
                        "ID": issue.get("issue_number", issue["id"]),
                        "UUID": issue["id"],
                        "Title": issue["title"],
                        "Description": issue["description"],
                        "Type": issue["issue_type"],
                        "Priority": issue["priority"],
                        "Severity": issue["severity"],
                        "Status": issue["status"],
                        "Version": issue.get("version", ""),
                        "Component": issue.get("component", ""),
                        "Labels": ", ".join(issue.get("labels", [])),
                        "Story Points": issue.get("story_points", ""),
                        "Assignees": ", ".join(issue.get("assignee_usernames", [])),
                        "Creator": issue["creator_username"],
                        "Created Date": datetime.fromisoformat(issue["created_at"]).strftime("%Y-%m-%d %H:%M"),
                        "Updated Date": datetime.fromisoformat(issue["updated_at"]).strftime("%Y-%m-%d %H:%M"),
                        "Due Date": issue.get("due_date", ""),
                        "Comment Count": issue.get("comment_count", 0)
                    })
                
                csv_df = pd.DataFrame(csv_data)
                csv_string = csv_df.to_csv(index=False)
                
                # Provide download
                st.download_button(
                    label="📁 Download CSV",
                    data=csv_string,
                    file_name=f"{selected_project_name}_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            elif export_format == "Markdown Table":
                # Generate markdown table
                markdown_content = f"# Issues Export - {selected_project_name}\n\n"
                markdown_content += f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                markdown_content += f"**Total Issues:** {len(all_issues)}\n\n"
                
                markdown_content += "| ID | Title | Type | Priority | Severity | Status | Assignees | Creator | Created Date |\n"
                markdown_content += "|---|---|---|---|---|---|---|---|---|\n"
                
                for issue in all_issues:
                    # Escape pipe characters in content
                    title = issue["title"].replace("|", "\\|")[:50]
                    if len(issue["title"]) > 50:
                        title += "..."
                    
                    assignees = ", ".join(issue.get("assignee_usernames", [])).replace("|", "\\|")
                    creator = issue["creator_username"].replace("|", "\\|")
                    created_date = datetime.fromisoformat(issue["created_at"]).strftime("%Y-%m-%d")
                    
                    issue_id_display = issue.get('issue_number', issue['id'][:8])
                    markdown_content += f"| {issue_id_display} | {title} | {issue['issue_type']} | {issue['priority']} | {issue['severity']} | {issue['status']} | {assignees} | {creator} | {created_date} |\n"
                
                # Add detailed sections
                markdown_content += "\n\n## Detailed Issue Information\n\n"
                
                for issue in all_issues:
                    markdown_content += f"### {issue['title']}\n\n"
                    markdown_content += f"**ID:** {issue.get('issue_number', issue['id'][:8])}\n\n"
                    if issue.get('issue_number'):
                        markdown_content += f"**UUID:** {issue['id']}\n\n"
                    markdown_content += f"**Type:** {issue['issue_type']} | **Priority:** {issue['priority']} | **Severity:** {issue['severity']} | **Status:** {issue['status']}\n\n"
                    
                    if issue.get('version'):
                        markdown_content += f"**Version:** {issue['version']}\n\n"
                    
                    if issue.get('component'):
                        markdown_content += f"**Component:** {issue['component']}\n\n"
                    
                    if issue.get('labels'):
                        markdown_content += f"**Labels:** {', '.join(issue['labels'])}\n\n"
                    
                    if issue.get('story_points'):
                        markdown_content += f"**Story Points:** {issue['story_points']}\n\n"
                    
                    assignees = ', '.join(issue.get('assignee_usernames', []))
                    if assignees:
                        markdown_content += f"**Assignees:** {assignees}\n\n"
                    
                    markdown_content += f"**Creator:** {issue['creator_username']}\n\n"
                    markdown_content += f"**Created:** {datetime.fromisoformat(issue['created_at']).strftime('%Y-%m-%d %H:%M')}\n\n"
                    markdown_content += f"**Updated:** {datetime.fromisoformat(issue['updated_at']).strftime('%Y-%m-%d %H:%M')}\n\n"
                    
                    if issue.get('due_date'):
                        markdown_content += f"**Due Date:** {issue['due_date']}\n\n"
                    
                    markdown_content += f"**Description:**\n{issue['description']}\n\n"
                    markdown_content += "---\n\n"
                
                # Provide download
                st.download_button(
                    label="📁 Download Markdown",
                    data=markdown_content,
                    file_name=f"{selected_project_name}_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
    else:
        st.info("No issues found to export for the selected criteria")