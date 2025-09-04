# frontend/pages/_Projects.py
import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers, BACKEND_URL

require_auth()

st.set_page_config(page_title="Projects", page_icon="📋", layout="wide")

# Add CSS for smaller, more compact presentation
st.markdown("""
<style>
    .stSelectbox > div > div > div {
        font-size: 14px;
    }
    .stDataFrame {
        font-size: 13px;
    }
    .stMetric {
        font-size: 14px;
    }
    .stMetric > div {
        font-size: 12px;
    }
    .stTextInput > div > div > input {
        font-size: 14px;
    }
    .stTextArea > div > div > textarea {
        font-size: 14px;
    }
    h3 {
        font-size: 18px !important;
    }
    .element-container {
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("📋 Projects Management")

setup_authenticated_sidebar()

# Helper functions
def fetch_projects():
    """Fetch user's projects from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/projects", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch projects: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error fetching projects: {str(e)}")
        return []

def fetch_users():
    """Fetch all users for member selection"""
    try:
        response = requests.get(f"{BACKEND_URL}/users", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching users: {str(e)}")
        return []

def create_project(name, description):
    """Create a new project"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/projects",
            json={"name": name, "description": description},
            headers=get_auth_headers()
        )
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text
    except Exception as e:
        return False, str(e)

def get_project_details(project_id):
    """Get detailed project information"""
    try:
        response = requests.get(f"{BACKEND_URL}/projects/{project_id}", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching project details: {str(e)}")
        return None

def add_project_member(project_id, user_id, role="member"):
    """Add member to project"""
    try:
        print(f"🔍 DEBUG: Adding member by ID - project_id: {project_id}, user_id: {user_id}, role: {role}")
        response = requests.post(
            f"{BACKEND_URL}/projects/{project_id}/members",
            json={"user_id": user_id, "role": role},
            headers=get_auth_headers()
        )
        print(f"🔍 DEBUG: Member addition by ID response - status: {response.status_code}, body: {response.text[:200]}")
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text
    except Exception as e:
        return False, str(e)

def get_all_users():
    """Get all registered users"""
    try:
        response = requests.get(f"{BACKEND_URL}/users", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching users: {str(e)}")
        return []

def add_project_member_by_email(project_id, member_email, role="member"):
    """Add member to project by email address"""
    try:
        print(f"🔍 DEBUG: Adding member - project_id: {project_id}, email: {member_email}, role: {role}")
        response = requests.post(
            f"{BACKEND_URL}/projects/{project_id}/members/by-email",
            json={"email": member_email, "role": role},
            headers=get_auth_headers()
        )
        print(f"🔍 DEBUG: Member addition response - status: {response.status_code}, body: {response.text[:200]}")
        
        if response.status_code == 200:
            return True, response.json()
        else:
            # Handle error responses
            try:
                error_data = response.json()
                error_msg = error_data.get('error', error_data.get('detail', response.text))
            except:
                error_msg = response.text
            return False, error_msg
    except Exception as e:
        return False, str(e)

def add_multiple_project_members(project_id, member_emails, role="member"):
    """Add multiple members to project by email addresses"""
    results = []
    success_count = 0
    error_count = 0
    
    for email in member_emails:
        success, result = add_project_member_by_email(project_id, email, role)
        results.append({"email": email, "success": success, "result": result})
        if success:
            success_count += 1
        else:
            error_count += 1
    
    return results, success_count, error_count

def remove_project_member(project_id, user_id):
    """Remove member from project"""
    try:
        response = requests.delete(
            f"{BACKEND_URL}/projects/{project_id}/members/{user_id}",
            headers=get_auth_headers()
        )
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text
    except Exception as e:
        return False, str(e)

def add_project_resource(project_id, name, resource_type, content=None):
    """Add resource to project"""
    try:
        payload = {
            "name": name,
            "resource_type": resource_type
        }
        if content:
            payload["content"] = content
            
        response = requests.post(
            f"{BACKEND_URL}/projects/{project_id}/resources",
            json=payload,
            headers=get_auth_headers()
        )
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text
    except Exception as e:
        return False, str(e)

def update_project_resource(project_id, resource_id, name, resource_type, content=None):
    """Update project resource"""
    try:
        payload = {
            "name": name,
            "resource_type": resource_type,
            "content": content if content is not None else ""
        }
            
        response = requests.put(
            f"{BACKEND_URL}/projects/{project_id}/resources/{resource_id}",
            json=payload,
            headers=get_auth_headers()
        )
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text
    except Exception as e:
        return False, str(e)

def delete_project_resource(project_id, resource_id):
    """Delete project resource"""
    try:
        response = requests.delete(
            f"{BACKEND_URL}/projects/{project_id}/resources/{resource_id}",
            headers=get_auth_headers()
        )
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text
    except Exception as e:
        return False, str(e)

# Main interface
tab1, tab2, tab3 = st.tabs(["📊 My Projects", "➕ Create Project", "📁 Project Details"])

with tab1:
    
    # Fetch projects
    projects = fetch_projects()
    
    if projects:
        # Summary metrics
        total_projects = len(projects)
        created_projects = len([p for p in projects if p.get("is_creator", False)])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Projects", total_projects)
        with col2:
            st.metric("Projects Created", created_projects)
        with col3:
            st.metric("Projects Joined", total_projects - created_projects)
        
        # Projects table
        st.subheader("Projects")
        
        # Convert to DataFrame for better display
        df_data = []
        for project in projects:
            df_data.append({
                "Name": project["name"],
                "Description": project["description"][:80] + "..." if len(project["description"]) > 80 else project["description"],
                "Members": project["member_count"],
                "Created By": project["created_by_username"],
                "Created": project["created_at"][:10] if project["created_at"] else "Unknown",
                "Role": "Creator" if project.get("is_creator", False) else "Member",
                "Status": "✅ Active"
            })
        
        if df_data:
            df = pd.DataFrame(df_data)
            
            # Display with selection
            event = st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            # Action buttons for selected project
            if event.selection and event.selection.rows:
                selected_idx = event.selection.rows[0]
                selected_project = projects[selected_idx]
                
                col_action1, col_action2, col_action3 = st.columns(3)
                
                with col_action1:
                    if st.button("📦 Download Documents"):
                        st.session_state.download_project_id = selected_project["id"]
                        st.session_state.download_project_name = selected_project["name"]
                        st.session_state.show_download_progress = True
                        st.rerun()
                
                with col_action2:
                    if st.button("👥 Manage Members"):
                        st.session_state.manage_members_project = selected_project["id"]
                
                with col_action3:
                    if st.button("🗑️ Delete Project", type="secondary", disabled=not selected_project.get("is_creator", False)):
                        if not selected_project.get("is_creator", False):
                            st.info("Only project creators can delete projects")
                        else:
                            st.session_state.delete_project = selected_project["id"]
                
                # Handle member management
                if hasattr(st.session_state, 'manage_members_project'):
                    project_details = get_project_details(st.session_state.manage_members_project)
                    if project_details:
                        # Check if user has permission to manage members
                        can_manage = project_details.get("is_creator", False) or project_details.get("user_role", "") == "admin"
                        
                        if not can_manage:
                            st.info("ℹ️ You can view members but only project creators and admins can manage them.")
                        
                        st.write("**Current Members:**")
                        
                        member_display_data = []
                        for member in project_details["members"]:
                            status = "🔑 Creator" if member["user_id"] == project_details["created_by"] else f"👤 {member['role'].title()}"
                            member_display_data.append({
                                "Username": member["username"],
                                "Email": member["email"], 
                                "Status": status,
                                "Added": member["added_at"][:10] if member["added_at"] else "Unknown",
                                "User ID": member["user_id"]  # Hidden column for operations
                            })
                        
                        if member_display_data:
                            member_df = pd.DataFrame(member_display_data)
                            
                            # Display members with selection for removal
                            if can_manage:
                                member_event = st.dataframe(
                                    member_df.drop("User ID", axis=1),  # Hide User ID column
                                    use_container_width=True,
                                    hide_index=True,
                                    on_select="rerun",
                                    selection_mode="multi-row"
                                )
                                
                                # Remove selected members
                                if member_event.selection and member_event.selection.rows:
                                    selected_member_indices = member_event.selection.rows
                                    selected_members = [project_details["members"][i] for i in selected_member_indices]
                                    
                                    # Filter out creator from removal
                                    removable_members = [m for m in selected_members if m["user_id"] != project_details["created_by"]]
                                    
                                    if removable_members:
                                        st.write(f"**Selected for removal:** {len(removable_members)} member(s)")
                                        col_remove1, col_remove2 = st.columns([1, 3])
                                        
                                        with col_remove1:
                                            if st.button("🗑️ Remove Selected", type="secondary"):
                                                removed_count = 0
                                                for member in removable_members:
                                                    success, result = remove_project_member(
                                                        st.session_state.manage_members_project, 
                                                        member["user_id"]
                                                    )
                                                    if success:
                                                        removed_count += 1
                                                
                                                if removed_count > 0:
                                                    st.success(f"✅ Removed {removed_count} member(s) successfully!")
                                                    st.rerun()
                                                else:
                                                    st.error("Failed to remove members")
                                        
                                        with col_remove2:
                                            member_names = [m["username"] for m in removable_members]
                                            st.write(f"Members to remove: {', '.join(member_names)}")
                                    
                                    # Show warning if trying to remove creator
                                    if len(selected_members) > len(removable_members):
                                        st.warning("⚠️ Project creator cannot be removed from the project.")
                            else:
                                st.dataframe(
                                    member_df.drop("User ID", axis=1),
                                    use_container_width=True,
                                    hide_index=True
                                )
                        
                        # Add new members section (only for authorized users)
                        if can_manage:
                            st.write("**Add New Members:**")
                            
                            users = fetch_users()
                            if users:
                                # Filter out existing members
                                existing_member_ids = [m["user_id"] for m in project_details["members"]]
                                available_users = [u for u in users if u["id"] not in existing_member_ids]
                                
                                if available_users:
                                    # Multi-select widget for adding members
                                    col_select, col_role, col_add = st.columns([3, 1, 1])
                                    
                                    with col_select:
                                        selected_users = st.multiselect(
                                            "Select Users to Add",
                                            available_users,
                                            format_func=lambda x: f"{x['username']} ({x['email']})",
                                            help="Select multiple users to add to the project"
                                        )
                                    
                                    with col_role:
                                        default_role = st.selectbox(
                                            "Default Role", 
                                            ["member", "admin"],
                                            help="Role to assign to all selected users"
                                        )
                                    
                                    with col_add:
                                        st.write("")  # Spacer
                                        if st.button("➕ Add Selected", disabled=not selected_users):
                                            if selected_users:
                                                added_count = 0
                                                failed_users = []
                                                
                                                for user in selected_users:
                                                    success, result = add_project_member(
                                                        st.session_state.manage_members_project, 
                                                        user["id"], 
                                                        default_role
                                                    )
                                                    if success:
                                                        added_count += 1
                                                    else:
                                                        failed_users.append(f"{user['username']}: {result}")
                                                
                                                if added_count > 0:
                                                    st.success(f"✅ Added {added_count} member(s) successfully!")
                                                
                                                if failed_users:
                                                    st.error("❌ Failed to add some members:")
                                                    for error in failed_users:
                                                        st.write(f"- {error}")
                                                
                                                st.rerun()
                                    
                                    # Show preview of selected users
                                    if selected_users:
                                        st.write("**Preview:**")
                                        for user in selected_users:
                                            st.write(f"- {user['username']} ({user['email']}) → {default_role.title()}")
                                else:
                                    st.info("📝 All users are already members of this project")
                            else:
                                st.error("❌ No users available to add")
                        
                        # Close button
                        col_close1, col_close2, col_close3 = st.columns([1, 2, 1])
                        with col_close2:
                            if st.button("✅ Close Member Management", use_container_width=True):
                                del st.session_state.manage_members_project
                                st.rerun()
                
                # Handle project document download
                if hasattr(st.session_state, 'show_download_progress') and st.session_state.show_download_progress:
                    st.markdown("---")
                    st.markdown(f"### 📦 Project Document Export: {st.session_state.download_project_name}")
                    
                    # Export options
                    export_cols = st.columns([2, 1])
                    
                    with export_cols[0]:
                        st.markdown("**Export Contents:**")
                        include_documents = st.checkbox("📁 Approved Documents (PDF)", value=True, help="All approved documents from Documents module")
                        include_reviews = st.checkbox("🔍 Project Reviews (PDF)", value=True, help="All completed project reviews")
                        include_code_reviews = st.checkbox("💻 Code Reviews (PDF)", value=True, help="All approved code reviews")
                        include_design_record = st.checkbox("🔬 Complete Design Record (PDF)", value=True, help="Comprehensive design record report")
                        include_audit_report = st.checkbox("📊 Audit Report (PDF)", value=True, help="Latest audit report")
                        
                        # Additional options
                        st.markdown("**Export Options:**")
                        archive_format = st.selectbox("Archive Format", ["ZIP", "TAR.GZ"], index=0)
                        include_metadata = st.checkbox("📋 Include Export Metadata", value=True, help="Add README with export details")
                    
                    with export_cols[1]:
                        st.markdown("**Export Summary:**")
                        export_items = []
                        if include_documents: export_items.append("✅ Documents")
                        if include_reviews: export_items.append("✅ Project Reviews")
                        if include_code_reviews: export_items.append("✅ Code Reviews")
                        if include_design_record: export_items.append("✅ Design Record")
                        if include_audit_report: export_items.append("✅ Audit Report")
                        if include_metadata: export_items.append("✅ Metadata")
                        
                        for item in export_items:
                            st.write(item)
                        
                        if not any([include_documents, include_reviews, include_code_reviews, include_design_record, include_audit_report]):
                            st.warning("⚠️ Please select at least one item to export")
                    
                    # Export buttons
                    export_button_cols = st.columns([1, 1, 2])
                    
                    with export_button_cols[0]:
                        if st.button("📦 Start Export", type="primary", disabled=not any([include_documents, include_reviews, include_code_reviews, include_design_record, include_audit_report])):
                            # Start export process
                            with st.spinner("🔄 Preparing project documents for export..."):
                                try:
                                    export_config = {
                                        "project_id": st.session_state.download_project_id,
                                        "project_name": st.session_state.download_project_name,
                                        "include_documents": include_documents,
                                        "include_reviews": include_reviews,  
                                        "include_code_reviews": include_code_reviews,
                                        "include_design_record": include_design_record,
                                        "include_audit_report": include_audit_report,
                                        "archive_format": archive_format.lower(),
                                        "include_metadata": include_metadata,
                                        "export_timestamp": datetime.now().isoformat()
                                    }
                                    
                                    # Call backend export endpoint
                                    response = requests.post(
                                        f"{BACKEND_URL}/projects/{st.session_state.download_project_id}/export-documents",
                                        json=export_config,
                                        headers=get_auth_headers(),
                                        timeout=300  # 5 minute timeout for large exports
                                    )
                                    
                                    if response.status_code == 200:
                                        # Check if response is JSON (error) or binary (file download)
                                        content_type = response.headers.get('content-type', '')
                                        
                                        if 'application/json' in content_type:
                                            # JSON response with export statistics
                                            export_result = response.json()
                                            
                                            # Show success and download link
                                            st.success("✅ Project documents exported successfully!")
                                            
                                            # Display export statistics
                                            stats_cols = st.columns(4)
                                            with stats_cols[0]:
                                                st.metric("Documents", export_result.get("document_count", 0))
                                            with stats_cols[1]:
                                                st.metric("Reviews", export_result.get("review_count", 0))
                                            with stats_cols[2]:
                                                st.metric("Code Reviews", export_result.get("code_review_count", 0))
                                            with stats_cols[3]:
                                                st.metric("Archive Size", f"{export_result.get('file_size_mb', 0):.1f} MB")
                                        else:
                                            # Binary response - direct file download
                                            st.success("✅ Project export completed!")
                                            
                                            # Create download button with the received file content
                                            project_name_clean = "".join(c for c in st.session_state.download_project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                            filename = f"{project_name_clean.replace(' ', '_')}_documents_{timestamp}.{archive_format.lower()}"
                                            
                                            # Download the archive
                                            st.download_button(
                                                label=f"📥 Download {filename}",
                                                data=response.content,
                                                file_name=filename,
                                                mime="application/zip" if archive_format == "ZIP" else "application/gzip",
                                                type="primary",
                                                use_container_width=True
                                            )
                                            
                                            # Show basic stats
                                            file_size_mb = len(response.content) / (1024 * 1024)
                                            st.info(f"📊 Archive size: {file_size_mb:.2f} MB")
                                    
                                    elif response.status_code == 404:
                                        st.error("❌ Project not found or no documents available for export")
                                    elif response.status_code == 403:
                                        st.error("❌ Insufficient permissions to export project documents")
                                    else:
                                        st.error(f"❌ Export failed: {response.status_code} - {response.text}")
                                
                                except requests.exceptions.Timeout:
                                    st.error("⏰ Export timeout - project may be too large. Please try with fewer document types or contact administrator.")
                                except Exception as e:
                                    st.error(f"❌ Export error: {str(e)}")
                    
                    with export_button_cols[1]:
                        if st.button("❌ Cancel"):
                            del st.session_state.show_download_progress
                            if hasattr(st.session_state, 'download_project_id'):
                                del st.session_state.download_project_id
                            if hasattr(st.session_state, 'download_project_name'):
                                del st.session_state.download_project_name
                            st.rerun()
                    
                    with export_button_cols[2]:
                        st.info("💡 **Tip**: Large projects may take several minutes to export. The archive will include all selected documents organized in folders.")
                
                # Handle project deletion
                if hasattr(st.session_state, 'delete_project'):
                    st.warning(f"⚠️ Are you sure you want to delete project '{selected_project['name']}'?")
                    st.error("This action cannot be undone and will remove all project data including members and resources.")
                    
                    col_confirm1, col_confirm2 = st.columns(2)
                    
                    with col_confirm1:
                        if st.button("✅ Confirm Delete", type="primary"):
                            try:
                                response = requests.delete(
                                    f"{BACKEND_URL}/projects/{st.session_state.delete_project}",
                                    headers=get_auth_headers()
                                )
                                if response.status_code == 200:
                                    st.success("Project deleted successfully!")
                                    del st.session_state.delete_project
                                    st.rerun()
                                else:
                                    st.error(f"Failed to delete project: {response.text}")
                            except Exception as e:
                                st.error(f"Error deleting project: {str(e)}")
                    
                    with col_confirm2:
                        if st.button("❌ Cancel"):
                            del st.session_state.delete_project
                            st.rerun()
        else:
            st.info("No projects found.")
    else:
        st.info("You are not a member of any projects yet. Create one or ask to be added to an existing project.")

with tab2:
    
    with st.form("create_project_form"):
        col_form1, col_form2 = st.columns(2)
        
        with col_form1:
            project_name = st.text_input(
                "Project Name*", 
                placeholder="e.g., Marketing Campaign 2024",
                help="Enter a unique name for your project"
            )
            
            project_description = st.text_area(
                "Description",
                placeholder="Describe what this project is about, its goals, and scope...",
                help="Optional description for the project",
                height=120
            )
        
        with col_form2:
            st.write("")  # Empty column for spacing
        
        submitted = st.form_submit_button("🚀 Create Project", type="primary")
        
        if submitted:
            if not project_name:
                st.error("Project name is required!")
            else:
                success, result = create_project(project_name, project_description)
                if success:
                    st.success(f"✅ Project '{project_name}' created successfully!")
                    st.json(result)
                else:
                    st.error(f"❌ Failed to create project: {result}")

with tab3:
    
    # Project selector
    projects = fetch_projects()
    if projects:
        project_names = [(p["name"], p["id"]) for p in projects]
        
        # Use session state if coming from project overview
        default_idx = 0
        if hasattr(st.session_state, 'selected_project_id'):
            try:
                project_ids = [p[1] for p in project_names]
                default_idx = project_ids.index(st.session_state.selected_project_id)
            except ValueError:
                # Project ID not in list, will use default selection
                default_idx = 0
        
        selected_project = st.selectbox(
            "Select Project",
            project_names,
            format_func=lambda x: x[0],
            index=default_idx
        )
        
        if selected_project:
            project_id = selected_project[1]
            project_details = get_project_details(project_id)
            
            if project_details:
                # Project metadata
                col_meta1, col_meta2, col_meta3 = st.columns(3)
                
                with col_meta1:
                    st.metric("Members", len(project_details["members"]))
                    st.metric("Resources", len(project_details["resources"]))
                
                with col_meta2:
                    st.metric("Created", project_details["created_at"][:10] if project_details["created_at"] else "Unknown")
                    st.write(f"**Creator:** {project_details['created_by_username']}")
                
                with col_meta3:
                    st.write("**Description:**")
                    st.write(project_details["description"] or "No description provided")
                    st.write(f"**Your Role:** {project_details['user_role'].title()}")
                
                # Project members
                if project_details["members"]:
                    st.subheader(f"👥 Members ({len(project_details['members'])})")
                    
                    member_data = []
                    for member in project_details["members"]:
                        member_data.append({
                            "Username": member["username"],
                            "Email": member["email"],
                            "Role": member["role"].title(),
                            "Added": member["added_at"][:10] if member["added_at"] else "Unknown",
                            "Added By": member["added_by_username"]
                        })
                    
                    if member_data:
                        member_df = pd.DataFrame(member_data)
                        st.dataframe(member_df, use_container_width=True, hide_index=True)
                
                # Project resources
                
                # Always show resource management tabs
                # Group resources by type
                glossary_resources = [r for r in project_details["resources"] if r["resource_type"] == "glossary"]
                reference_resources = [r for r in project_details["resources"] if r["resource_type"] == "reference"]
                book_resources = [r for r in project_details["resources"] if r["resource_type"] == "book"]
                
                # Display resources in tabs
                res_tab1, res_tab2, res_tab3, res_tab4 = st.tabs(["➕ Add", "📖 Glossary", "📄 References", "📚 Books"])
                
                with res_tab1:
                    
                    # Submenu for Add options
                    add_sub1, add_sub2 = st.tabs(["📝 Add Resource", "👥 Add Team Member"])
                    
                    with add_sub1:
                        
                        with st.form("add_resource_form"):
                            resource_name = st.text_input("Resource Name*", placeholder="e.g., Marketing Terms")
                            resource_type = st.selectbox("Resource Type", ["glossary", "reference", "book"])
                            
                            if resource_type == "glossary":
                                resource_content = st.text_area("Glossary Content", 
                                                                placeholder="Term 1: Definition 1\nTerm 2: Definition 2\n...",
                                                                height=200)
                            else:
                                resource_content = st.text_area("Resource Description", 
                                                                placeholder="Description or notes about this resource...",
                                                                height=120)
                            
                            if st.form_submit_button("Add Resource"):
                                if not resource_name:
                                    st.error("Resource name is required!")
                                else:
                                    success, result = add_project_resource(project_id, resource_name, resource_type, resource_content)
                                    if success:
                                        st.success("Resource added successfully!")
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to add resource: {result}")
                    
                    with add_sub2:
                        
                        # Get all users
                        all_users = get_all_users()
                        
                        if not all_users:
                            st.warning("⚠️ No registered users found or unable to load users.")
                        else:
                            # Filter out users who are already members of this project
                            current_member_emails = {member["email"] for member in project_details.get("members", [])}
                            available_users = [user for user in all_users if user["email"] not in current_member_emails]
                            
                            print(f"🔍 DEBUG: All users: {[u['email'] for u in all_users]}")
                            print(f"🔍 DEBUG: Current member emails: {current_member_emails}")
                            print(f"🔍 DEBUG: Available users: {[u['email'] for u in available_users]}")
                            
                            if not available_users:
                                st.info("ℹ️ All registered users are already members of this project.")
                            else:
                                with st.form("add_member_form"):
                                    st.info("💡 **Note:** Select one or more users to add to this project.")
                                    
                                    # Create options for multiselect (show username and email)
                                    user_options = {f"{user['username']} ({user['email']})": user['email'] for user in available_users}
                                    
                                    selected_users = st.multiselect(
                                        "Select Users to Add*",
                                        options=list(user_options.keys()),
                                        help="Choose one or more users to add as team members"
                                    )
                                    
                                    member_role = st.selectbox("Role for Selected Users", ["member", "admin"], 
                                                             help="All selected users will be assigned this role")
                                    
                                    col1, col2 = st.columns([1, 2])
                                    with col1:
                                        if st.form_submit_button("Add Selected Members"):
                                            if not selected_users:
                                                st.error("Please select at least one user to add!")
                                            else:
                                                # Convert display names back to emails
                                                selected_emails = [user_options[user_display] for user_display in selected_users]
                                                
                                                with st.spinner(f"Adding {len(selected_emails)} member(s)..."):
                                                    results, success_count, error_count = add_multiple_project_members(project_id, selected_emails, member_role)
                                                
                                                # Show results
                                                if success_count > 0:
                                                    st.success(f"✅ Successfully added {success_count} member(s)!")
                                                    if success_count > 1:
                                                        st.balloons()
                                                
                                                if error_count > 0:
                                                    st.error(f"❌ Failed to add {error_count} member(s)")
                                                    
                                                    # Show detailed errors
                                                    with st.expander("View Details"):
                                                        for result in results:
                                                            if result["success"]:
                                                                st.success(f"✅ {result['email']}: Added successfully")
                                                            else:
                                                                st.error(f"❌ {result['email']}: {result['result']}")
                                                
                                                if success_count > 0:
                                                    st.rerun()
                                    
                                    with col2:
                                        st.caption("**Role Descriptions:**")
                                        st.caption("• **Member**: Can view and contribute to project")
                                        st.caption("• **Admin**: Can manage project settings and members")
                                        
                                        if len(available_users) > 0:
                                            st.caption(f"**Available Users:** {len(available_users)}")
                                        if len(current_member_emails) > 0:
                                            st.caption(f"**Current Members:** {len(current_member_emails)}")
                
                with res_tab2:
                    if glossary_resources:
                        # Create DataFrame for glossary resources
                        glos_grid_data = []
                        for resource in glossary_resources:
                            uploaded_date = resource.get('uploaded_at', resource.get('created_at', 'Unknown'))
                            if uploaded_date != 'Unknown':
                                uploaded_date = uploaded_date[:10]
                            
                            glos_grid_row = {
                                'Name': resource['name'],
                                'Added By': resource.get('uploaded_by_username', resource.get('uploaded_by', 'Unknown')),
                                'Date': uploaded_date,
                                'Content Preview': (resource["content"][:50] + "..." if resource["content"] and len(resource["content"]) > 50 else resource["content"] or "No content"),
                                'full_resource_data': resource
                            }
                            glos_grid_data.append(glos_grid_row)
                        
                        # Create DataFrame for display (without full data)
                        glos_df_data = []
                        for row in glos_grid_data:
                            glos_df_row = {
                                'Name': row['Name'],
                                'Added By': row['Added By'],
                                'Date': row['Date'],
                                'Content Preview': row['Content Preview']
                            }
                            glos_df_data.append(glos_df_row)
                        
                        glos_df = pd.DataFrame(glos_df_data)
                        
                        # Display DataFrame with selection
                        glos_selected_indices = st.dataframe(
                            glos_df,
                            use_container_width=True,
                            hide_index=True,
                            on_select="rerun",
                            selection_mode="single-row",
                            height=300
                        )
                        
                        st.caption("💡 Select a row to view/edit/delete glossary resource")
                        
                        # Handle selection
                        if glos_selected_indices and len(glos_selected_indices.selection.rows) > 0:
                            selected_idx = glos_selected_indices.selection.rows[0]
                            selected_resource = glos_grid_data[selected_idx]['full_resource_data']
                            
                            # Only update session state if different resource selected
                            if st.session_state.get('selected_glossary_id') != selected_resource.get('id'):
                                st.session_state.selected_glossary_id = selected_resource.get('id')
                                st.session_state.selected_glossary_data = selected_resource
                                st.rerun()
                        
                        # Show editable details for selected resource
                        if st.session_state.get('selected_glossary_data'):
                            resource = st.session_state.selected_glossary_data
                            st.markdown("---")
                            st.markdown("### 📝 Edit Selected Glossary Resource")
                            
                            # Check permissions once
                            can_edit = (project_details.get("is_creator", False) or 
                                      resource["uploaded_by"] == project_details.get("current_user_id"))
                            
                            if not can_edit:
                                st.warning("⚠️ You can only edit resources you created or if you're the project creator")
                            else:
                                # Edit form - only show if user can edit
                                with st.form("edit_glossary_form"):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        edited_name = st.text_input("Resource Name*", value=resource.get('name', ''))
                                        edited_type = st.selectbox("Type", ["glossary"], index=0, disabled=True)
                                    
                                    with col2:
                                        st.write("**Current Details:**")
                                        st.write(f"Added by: {resource.get('uploaded_by_username', 'Unknown')}")
                                        st.write(f"Date: {resource.get('uploaded_at', resource.get('created_at', 'Unknown'))[:10] if resource.get('uploaded_at', resource.get('created_at', 'Unknown')) != 'Unknown' else 'Unknown'}")
                                    
                                    edited_content = st.text_area("Glossary Content", 
                                                                value=resource.get('content', ''),
                                                                height=200,
                                                                placeholder="Term 1: Definition 1\nTerm 2: Definition 2\n...")
                                    
                                    # Single form submit button
                                    submitted = st.form_submit_button("💾 Save Changes", type="primary")
                                    
                                    if submitted:
                                        if not edited_name:
                                            st.error("Resource name is required!")
                                        else:
                                            # Update resource via API
                                            with st.spinner("Updating resource..."):
                                                success, result = update_project_resource(
                                                    project_id, resource.get('id'), 
                                                    edited_name, "glossary", edited_content
                                                )
                                            
                                            if success:
                                                st.success("✅ Glossary resource updated successfully!")
                                                # Clear selection to refresh data
                                                if 'selected_glossary_id' in st.session_state:
                                                    del st.session_state.selected_glossary_id
                                                if 'selected_glossary_data' in st.session_state:
                                                    del st.session_state.selected_glossary_data
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Failed to update: {result}")
                            
                            # Action buttons outside form (always shown if user can edit/delete)
                            if can_edit:
                                col_actions = st.columns([1, 1, 2])
                                
                                with col_actions[0]:
                                    if st.button("🗑️ Delete Resource", type="secondary", key="delete_glossary_btn"):
                                        # Check delete permission again  
                                        can_delete = (project_details.get("is_creator", False) or 
                                                    resource["uploaded_by"] == project_details.get("current_user_id"))
                                        
                                        if can_delete:
                                            with st.spinner("Deleting resource..."):
                                                success, result = delete_project_resource(project_id, resource["id"])
                                            
                                            if success:
                                                st.success("✅ Resource deleted!")
                                                # Clear selection
                                                if 'selected_glossary_id' in st.session_state:
                                                    del st.session_state.selected_glossary_id
                                                if 'selected_glossary_data' in st.session_state:
                                                    del st.session_state.selected_glossary_data
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Failed to delete: {result}")
                                        else:
                                            st.error("❌ You can only delete resources you created or if you're the project creator")
                                
                                with col_actions[1]:
                                    if st.button("❌ Cancel Edit", key="cancel_glossary_btn"):
                                        # Clear selection
                                        if 'selected_glossary_id' in st.session_state:
                                            del st.session_state.selected_glossary_id
                                        if 'selected_glossary_data' in st.session_state:
                                            del st.session_state.selected_glossary_data
                                        st.rerun()
                            else:
                                # Show cancel button for read-only users
                                if st.button("❌ Close", key="close_glossary_btn"):
                                    # Clear selection
                                    if 'selected_glossary_id' in st.session_state:
                                        del st.session_state.selected_glossary_id
                                    if 'selected_glossary_data' in st.session_state:
                                        del st.session_state.selected_glossary_data
                                    st.rerun()
                    else:
                        st.info("No glossary resources yet.")
                
                with res_tab3:
                    if reference_resources:
                        # Create DataFrame for reference resources
                        ref_grid_data = []
                        for resource in reference_resources:
                            uploaded_date = resource.get('uploaded_at', resource.get('created_at', 'Unknown'))
                            if uploaded_date != 'Unknown':
                                uploaded_date = uploaded_date[:10]
                            
                            ref_grid_row = {
                                'Name': resource['name'],
                                'Added By': resource.get('uploaded_by_username', resource.get('uploaded_by', 'Unknown')),
                                'Date': uploaded_date,
                                'Content Preview': (resource["content"][:50] + "..." if resource["content"] and len(resource["content"]) > 50 else resource["content"] or "No content"),
                                'full_resource_data': resource
                            }
                            ref_grid_data.append(ref_grid_row)
                        
                        # Create DataFrame for display (without full data)
                        ref_df_data = []
                        for row in ref_grid_data:
                            ref_df_row = {
                                'Name': row['Name'],
                                'Added By': row['Added By'],
                                'Date': row['Date'],
                                'Content Preview': row['Content Preview']
                            }
                            ref_df_data.append(ref_df_row)
                        
                        ref_df = pd.DataFrame(ref_df_data)
                        
                        # Display DataFrame with selection
                        ref_selected_indices = st.dataframe(
                            ref_df,
                            use_container_width=True,
                            hide_index=True,
                            on_select="rerun",
                            selection_mode="single-row",
                            height=300
                        )
                        
                        st.caption("💡 Select a row to view/edit/delete reference resource")
                        
                        # Handle selection
                        if ref_selected_indices and len(ref_selected_indices.selection.rows) > 0:
                            selected_idx = ref_selected_indices.selection.rows[0]
                            selected_resource = ref_grid_data[selected_idx]['full_resource_data']
                            
                            # Only update session state if different resource selected
                            if st.session_state.get('selected_reference_id') != selected_resource.get('id'):
                                st.session_state.selected_reference_id = selected_resource.get('id')
                                st.session_state.selected_reference_data = selected_resource
                                st.rerun()
                        
                        # Show editable details for selected resource
                        if st.session_state.get('selected_reference_data'):
                            resource = st.session_state.selected_reference_data
                            st.markdown("---")
                            st.markdown("### 📝 Edit Selected Reference Resource")
                            
                            # Check permissions once
                            can_edit = (project_details.get("is_creator", False) or 
                                      resource["uploaded_by"] == project_details.get("current_user_id"))
                            
                            if not can_edit:
                                st.warning("⚠️ You can only edit resources you created or if you're the project creator")
                            else:
                                # Edit form - only show if user can edit
                                with st.form("edit_reference_form"):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        edited_name = st.text_input("Resource Name*", value=resource.get('name', ''))
                                        edited_type = st.selectbox("Type", ["reference"], index=0, disabled=True)
                                    
                                    with col2:
                                        st.write("**Current Details:**")
                                        st.write(f"Added by: {resource.get('uploaded_by_username', 'Unknown')}")
                                        st.write(f"Date: {resource.get('uploaded_at', resource.get('created_at', 'Unknown'))[:10] if resource.get('uploaded_at', resource.get('created_at', 'Unknown')) != 'Unknown' else 'Unknown'}")
                                    
                                    edited_content = st.text_area("Reference Description", 
                                                                value=resource.get('content', ''),
                                                                height=200,
                                                                placeholder="Description or notes about this reference resource...")
                                    
                                    # Single form submit button
                                    submitted = st.form_submit_button("💾 Save Changes", type="primary")
                                    
                                    if submitted:
                                        if not edited_name:
                                            st.error("Resource name is required!")
                                        else:
                                            # Update resource via API
                                            with st.spinner("Updating resource..."):
                                                success, result = update_project_resource(
                                                    project_id, resource.get('id'), 
                                                    edited_name, "reference", edited_content
                                                )
                                            
                                            if success:
                                                st.success("✅ Reference resource updated successfully!")
                                                # Clear selection to refresh data
                                                if 'selected_reference_id' in st.session_state:
                                                    del st.session_state.selected_reference_id
                                                if 'selected_reference_data' in st.session_state:
                                                    del st.session_state.selected_reference_data
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Failed to update: {result}")
                            
                            # Action buttons outside form (always shown if user can edit/delete)
                            if can_edit:
                                col_actions = st.columns([1, 1, 2])
                                
                                with col_actions[0]:
                                    if st.button("🗑️ Delete Resource", type="secondary", key="delete_reference_btn"):
                                        # Check delete permission again  
                                        can_delete = (project_details.get("is_creator", False) or 
                                                    resource["uploaded_by"] == project_details.get("current_user_id"))
                                        
                                        if can_delete:
                                            with st.spinner("Deleting resource..."):
                                                success, result = delete_project_resource(project_id, resource["id"])
                                            
                                            if success:
                                                st.success("✅ Resource deleted!")
                                                # Clear selection
                                                if 'selected_reference_id' in st.session_state:
                                                    del st.session_state.selected_reference_id
                                                if 'selected_reference_data' in st.session_state:
                                                    del st.session_state.selected_reference_data
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Failed to delete: {result}")
                                        else:
                                            st.error("❌ You can only delete resources you created or if you're the project creator")
                                
                                with col_actions[1]:
                                    if st.button("❌ Cancel Edit", key="cancel_reference_btn"):
                                        # Clear selection
                                        if 'selected_reference_id' in st.session_state:
                                            del st.session_state.selected_reference_id
                                        if 'selected_reference_data' in st.session_state:
                                            del st.session_state.selected_reference_data
                                        st.rerun()
                            else:
                                # Show cancel button for read-only users
                                if st.button("❌ Close", key="close_reference_btn"):
                                    # Clear selection
                                    if 'selected_reference_id' in st.session_state:
                                        del st.session_state.selected_reference_id
                                    if 'selected_reference_data' in st.session_state:
                                        del st.session_state.selected_reference_data
                                    st.rerun()
                    else:
                        st.info("No reference resources yet.")
                
                with res_tab4:
                    if book_resources:
                        # Create DataFrame for book resources
                        book_grid_data = []
                        for resource in book_resources:
                            uploaded_date = resource.get('uploaded_at', resource.get('created_at', 'Unknown'))
                            if uploaded_date != 'Unknown':
                                uploaded_date = uploaded_date[:10]
                            
                            book_grid_row = {
                                'Name': resource['name'],
                                'Added By': resource.get('uploaded_by_username', resource.get('uploaded_by', 'Unknown')),
                                'Date': uploaded_date,
                                'Content Preview': (resource["content"][:50] + "..." if resource["content"] and len(resource["content"]) > 50 else resource["content"] or "No content"),
                                'full_resource_data': resource
                            }
                            book_grid_data.append(book_grid_row)
                        
                        # Create DataFrame for display (without full data)
                        book_df_data = []
                        for row in book_grid_data:
                            book_df_row = {
                                'Name': row['Name'],
                                'Added By': row['Added By'],
                                'Date': row['Date'],
                                'Content Preview': row['Content Preview']
                            }
                            book_df_data.append(book_df_row)
                        
                        book_df = pd.DataFrame(book_df_data)
                        
                        # Display DataFrame with selection
                        book_selected_indices = st.dataframe(
                            book_df,
                            use_container_width=True,
                            hide_index=True,
                            on_select="rerun",
                            selection_mode="single-row",
                            height=300
                        )
                        
                        st.caption("💡 Select a row to view/edit/delete book resource")
                        
                        # Handle selection
                        if book_selected_indices and len(book_selected_indices.selection.rows) > 0:
                            selected_idx = book_selected_indices.selection.rows[0]
                            selected_resource = book_grid_data[selected_idx]['full_resource_data']
                            
                            # Only update session state if different resource selected
                            if st.session_state.get('selected_book_id') != selected_resource.get('id'):
                                st.session_state.selected_book_id = selected_resource.get('id')
                                st.session_state.selected_book_data = selected_resource
                                st.rerun()
                        
                        # Show editable details for selected resource
                        if st.session_state.get('selected_book_data'):
                            resource = st.session_state.selected_book_data
                            st.markdown("---")
                            st.markdown("### 📝 Edit Selected Book Resource")
                            
                            # Check permissions once
                            can_edit = (project_details.get("is_creator", False) or 
                                      resource["uploaded_by"] == project_details.get("current_user_id"))
                            
                            if not can_edit:
                                st.warning("⚠️ You can only edit resources you created or if you're the project creator")
                            else:
                                # Edit form - only show if user can edit
                                with st.form("edit_book_form"):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        edited_name = st.text_input("Resource Name*", value=resource.get('name', ''))
                                        edited_type = st.selectbox("Type", ["book"], index=0, disabled=True)
                                    
                                    with col2:
                                        st.write("**Current Details:**")
                                        st.write(f"Added by: {resource.get('uploaded_by_username', 'Unknown')}")
                                        st.write(f"Date: {resource.get('uploaded_at', resource.get('created_at', 'Unknown'))[:10] if resource.get('uploaded_at', resource.get('created_at', 'Unknown')) != 'Unknown' else 'Unknown'}")
                                    
                                    edited_content = st.text_area("Book Description", 
                                                                value=resource.get('content', ''),
                                                                height=200,
                                                                placeholder="Description, notes, or summary about this book resource...")
                                    
                                    # Single form submit button
                                    submitted = st.form_submit_button("💾 Save Changes", type="primary")
                                    
                                    if submitted:
                                        if not edited_name:
                                            st.error("Resource name is required!")
                                        else:
                                            # Update resource via API
                                            with st.spinner("Updating resource..."):
                                                success, result = update_project_resource(
                                                    project_id, resource.get('id'), 
                                                    edited_name, "book", edited_content
                                                )
                                            
                                            if success:
                                                st.success("✅ Book resource updated successfully!")
                                                # Clear selection to refresh data
                                                if 'selected_book_id' in st.session_state:
                                                    del st.session_state.selected_book_id
                                                if 'selected_book_data' in st.session_state:
                                                    del st.session_state.selected_book_data
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Failed to update: {result}")
                            
                            # Action buttons outside form (always shown if user can edit/delete)
                            if can_edit:
                                col_actions = st.columns([1, 1, 2])
                                
                                with col_actions[0]:
                                    if st.button("🗑️ Delete Resource", type="secondary", key="delete_book_btn"):
                                        # Check delete permission again  
                                        can_delete = (project_details.get("is_creator", False) or 
                                                    resource["uploaded_by"] == project_details.get("current_user_id"))
                                        
                                        if can_delete:
                                            with st.spinner("Deleting resource..."):
                                                success, result = delete_project_resource(project_id, resource["id"])
                                            
                                            if success:
                                                st.success("✅ Resource deleted!")
                                                # Clear selection
                                                if 'selected_book_id' in st.session_state:
                                                    del st.session_state.selected_book_id
                                                if 'selected_book_data' in st.session_state:
                                                    del st.session_state.selected_book_data
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Failed to delete: {result}")
                                        else:
                                            st.error("❌ You can only delete resources you created or if you're the project creator")
                                
                                with col_actions[1]:
                                    if st.button("❌ Cancel Edit", key="cancel_book_btn"):
                                        # Clear selection
                                        if 'selected_book_id' in st.session_state:
                                            del st.session_state.selected_book_id
                                        if 'selected_book_data' in st.session_state:
                                            del st.session_state.selected_book_data
                                        st.rerun()
                            else:
                                # Show cancel button for read-only users
                                if st.button("❌ Close", key="close_book_btn"):
                                    # Clear selection
                                    if 'selected_book_id' in st.session_state:
                                        del st.session_state.selected_book_id
                                    if 'selected_book_data' in st.session_state:
                                        del st.session_state.selected_book_data
                                    st.rerun()
                    else:
                        st.info("No book resources yet.")
    else:
        st.info("No projects available. Create a project first.")


# Clean up session state
if hasattr(st.session_state, 'selected_project_id'):
    del st.session_state.selected_project_id

# Clean up resource selection states when leaving the page
cleanup_states = [
    'selected_glossary_id', 'selected_glossary_data',
    'selected_reference_id', 'selected_reference_data', 
    'selected_book_id', 'selected_book_data'
]
for state in cleanup_states:
    if hasattr(st.session_state, state):
        del st.session_state[state]