# frontend/pages/Code.py
import streamlit as st
import requests
from datetime import datetime, date
import pandas as pd
from typing import List, Dict, Any
from streamlit_ace import st_ace
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers
from config import BACKEND_URL

# Review status constants (matching Document Reviews)
REVIEW_STATUS_OPTIONS = ["draft", "review_request", "needs_update", "approved"]

require_auth()

st.set_page_config(page_title="Code Review Management", page_icon="💻", layout="wide")

# Add CSS for compact layout
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
    .success-metric {
        background-color: #f8f9fa;
        border: 1px solid #28a745;
        border-radius: 0.25rem;
        padding: 0.5rem;
        margin: 0.5rem 0;
        color: #000000;
    }
    .warning-metric {
        background-color: #f8f9fa;
        border: 1px solid #ffc107;
        border-radius: 0.25rem;
        padding: 0.5rem;
        margin: 0.5rem 0;
        color: #000000;
    }
    .danger-metric {
        background-color: #f8f9fa;
        border: 1px solid #dc3545;
        border-radius: 0.25rem;
        padding: 0.5rem;
        margin: 0.5rem 0;
        color: #000000;
    }
</style>
""", unsafe_allow_html=True)

st.title("💻 Code Review Management")

setup_authenticated_sidebar()

# === API FUNCTIONS ===

def get_projects():
    """Get all projects for dropdown"""
    try:
        headers = get_auth_headers()
        response = requests.get(f"{BACKEND_URL}/projects", headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_users():
    """Get all registered users for reviewer selection"""
    try:
        headers = get_auth_headers()
        response = requests.get(f"{BACKEND_URL}/users", headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_repositories():
    """Get all repositories"""
    try:
        response = requests.get(f"{BACKEND_URL}/repositories", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching repositories: {str(e)}")
        return []

def create_repository(repo_data):
    """Create a new repository"""
    try:
        response = requests.post(f"{BACKEND_URL}/repositories", json=repo_data, headers=get_auth_headers())
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error creating repository: {str(e)}")
        return False

def delete_repository(repo_id):
    """Delete a repository"""
    try:
        response = requests.delete(f"{BACKEND_URL}/repositories/{repo_id}", headers=get_auth_headers())
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error deleting repository: {str(e)}")
        return False

def validate_git_url(git_url):
    """Validate Git repository URL"""
    try:
        data = {"git_url": git_url}
        response = requests.post(f"{BACKEND_URL}/repositories/validate-url", data=data, headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return {"valid": False, "message": "Validation failed"}
    except Exception as e:
        return {"valid": False, "message": f"Error: {str(e)}"}

def get_pull_requests(repository_id=None):
    """Get pull requests"""
    try:
        params = {"repository_id": repository_id} if repository_id else {}
        response = requests.get(f"{BACKEND_URL}/pull-requests", params=params, headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching pull requests: {str(e)}")
        return []

def create_pull_request(pr_data):
    """Create a pull request"""
    try:
        response = requests.post(f"{BACKEND_URL}/pull-requests", json=pr_data, headers=get_auth_headers())
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Error creating pull request: {str(e)}")
        return False, None

def get_code_reviews(pr_id=None):
    """Get code reviews"""
    try:
        params = {"pr_id": pr_id} if pr_id else {}
        response = requests.get(f"{BACKEND_URL}/code-reviews", params=params, headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching reviews: {str(e)}")
        return []

def create_code_review(review_data):
    """Create a code review"""
    try:
        response = requests.post(f"{BACKEND_URL}/code-reviews", json=review_data, headers=get_auth_headers())
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Error creating review: {str(e)}")
        return False, None

def update_code_review(review_id, review_data):
    """Update a code review"""
    try:
        response = requests.put(f"{BACKEND_URL}/code-reviews/{review_id}", json=review_data, headers=get_auth_headers())
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Error updating review: {str(e)}")
        return False, None

def get_pr_files(pr_id):
    """Get pull request files"""
    try:
        response = requests.get(f"{BACKEND_URL}/pull-requests/{pr_id}/files", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching PR files: {str(e)}")
        return []

def trigger_automated_review(pr_id):
    """Trigger automated AI code review"""
    try:
        response = requests.post(f"{BACKEND_URL}/pull-requests/{pr_id}/automated-review", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to trigger automated review: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error triggering automated review: {str(e)}")
        return None

def get_pr_analysis(pr_id):
    """Get AI analysis for a pull request"""
    try:
        response = requests.get(f"{BACKEND_URL}/pull-requests/{pr_id}/analysis", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching analysis: {str(e)}")
        return None

# === UI HELPER FUNCTIONS ===

def display_repositories_dataframe(repositories):
    """Display repositories as an interactive dataframe"""
    if not repositories:
        st.info("No repositories found.")
        return None, None
    
    # Create DataFrame
    repo_data = []
    for repo in repositories:
        repo_data.append({
            "ID": repo["id"],
            "Name": repo["name"],
            "Project": repo.get("project_name", "N/A"),
            "Git URL": repo.get("git_url", "N/A"),
            "Default Branch": repo.get("default_branch", "main"),
            "Created": repo.get("created_at", "N/A")[:10] if repo.get("created_at") else "N/A"
        })
    
    df = pd.DataFrame(repo_data)
    
    # Display with selection
    selected_indices = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="repositories_dataframe"
    )
    
    selected_repo = None
    if selected_indices and len(selected_indices.selection.rows) > 0:
        selected_idx = selected_indices.selection.rows[0]
        selected_repo = repositories[selected_idx]
    
    return selected_repo, selected_indices

def display_pull_requests_dataframe(pull_requests):
    """Display pull requests as an interactive dataframe"""
    if not pull_requests:
        st.info("No pull requests found.")
        return None, None
    
    # Create DataFrame
    pr_data = []
    for pr in pull_requests:
        pr_data.append({
            "ID": pr["id"],
            "PR #": pr["pr_number"],
            "Title": pr["title"],
            "Author": pr.get("author_name", "N/A"),
            "Status": pr["status"],
            "Source → Target": f"{pr.get('source_branch', 'N/A')} → {pr.get('target_branch', 'N/A')}",
            "Files": pr.get("files_changed_count", 0),
            "Changes": f"+{pr.get('additions', 0)} -{pr.get('deletions', 0)}",
            "Created": pr.get("created_at", "N/A")[:10] if pr.get("created_at") else "N/A"
        })
    
    df = pd.DataFrame(pr_data)
    
    # Display with selection
    selected_indices = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="pull_requests_dataframe"
    )
    
    selected_pr = None
    if selected_indices and len(selected_indices.selection.rows) > 0:
        selected_idx = selected_indices.selection.rows[0]
        selected_pr = pull_requests[selected_idx]
    
    return selected_pr, selected_indices

def display_reviews_dataframe(reviews):
    """Display reviews as an interactive dataframe"""
    if not reviews:
        st.info("No reviews found.")
        return None, None
    
    # Create DataFrame
    review_data = []
    for review in reviews:
        review_data.append({
            "ID": review["id"],
            "Reviewer": review.get("reviewer_name", "N/A"),
            "Status": review["status"],
            "Summary": review.get("summary_comment", "")[:50] + "..." if len(review.get("summary_comment", "")) > 50 else review.get("summary_comment", ""),
            "Created": review.get("created_at", "N/A")[:10] if review.get("created_at") else "N/A"
        })
    
    df = pd.DataFrame(review_data)
    
    # Display with selection
    selected_indices = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="reviews_dataframe"
    )
    
    selected_review = None
    if selected_indices and len(selected_indices.selection.rows) > 0:
        selected_idx = selected_indices.selection.rows[0]
        selected_review = reviews[selected_idx]
    
    return selected_review, selected_indices

def display_success_metrics(analysis_results):
    """Display success metrics for AI reviews"""
    if not analysis_results:
        return
    
    summary = analysis_results.get('summary', {})
    
    st.markdown("### 📊 Code Quality Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        security_count = summary.get('security_issues_count', 0)
        security_class = "success-metric" if security_count == 0 else "danger-metric" if security_count > 3 else "warning-metric"
        st.markdown(f'<div class="{security_class}"><strong>Security Issues</strong><br/>{security_count}</div>', unsafe_allow_html=True)
    
    with col2:
        performance_count = summary.get('performance_issues_count', 0)
        performance_class = "success-metric" if performance_count <= 2 else "warning-metric"
        st.markdown(f'<div class="{performance_class}"><strong>Performance Issues</strong><br/>{performance_count}</div>', unsafe_allow_html=True)
    
    with col3:
        quality_count = summary.get('code_quality_issues_count', 0)
        quality_class = "success-metric" if quality_count <= 5 else "warning-metric"
        st.markdown(f'<div class="{quality_class}"><strong>Quality Issues</strong><br/>{quality_count}</div>', unsafe_allow_html=True)
    
    with col4:
        suggestions_count = summary.get('suggestions_count', 0)
        suggestions_class = "success-metric" if suggestions_count > 0 else "warning-metric"
        st.markdown(f'<div class="{suggestions_class}"><strong>AI Suggestions</strong><br/>{suggestions_count}</div>', unsafe_allow_html=True)
    
    # Overall score
    total_issues = security_count + performance_count + quality_count
    if total_issues == 0:
        score = "Excellent (100%)"
        score_class = "success-metric"
    elif total_issues <= 3:
        score = "Good (80-90%)"
        score_class = "success-metric"
    elif total_issues <= 8:
        score = "Needs Improvement (60-80%)"
        score_class = "warning-metric"
    else:
        score = "Poor (<60%)"
        score_class = "danger-metric"
    
    st.markdown(f'<div class="{score_class}"><strong>Overall Code Quality Score:</strong> {score}</div>', unsafe_allow_html=True)

# === MAIN UI STRUCTURE ===

# Create main tabs for the new structure
main_tab1, main_tab2 = st.tabs(["🏢 Repository Management", "🔄 Pull Request Management"])

with main_tab1:
    st.header("Repository Management")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Repositories")
        repositories = get_repositories()
        selected_repo, repo_indices = display_repositories_dataframe(repositories)
    
    with col2:
        st.subheader("Actions")
        
        if st.button("➕ Create Repository", type="primary", use_container_width=True):
            st.session_state["show_create_repo"] = True
        
        if selected_repo:
            st.markdown(f"**Selected:** {selected_repo['name']}")
            
            if selected_repo.get("git_url"):
                if st.button("🔍 Test Connection", use_container_width=True):
                    with st.spinner("Testing Git connection..."):
                        validation = validate_git_url(selected_repo["git_url"])
                        if validation.get("valid"):
                            st.success("✅ Repository is accessible")
                        else:
                            st.error(f"❌ {validation.get('message')}")
            
            if st.button("🗑️ Delete Repository", use_container_width=True, type="secondary"):
                if st.session_state.get("confirm_delete") != selected_repo["id"]:
                    st.session_state["confirm_delete"] = selected_repo["id"]
                    st.rerun()
                else:
                    with st.spinner("Deleting repository..."):
                        if delete_repository(selected_repo["id"]):
                            st.success("Repository deleted successfully!")
                            st.session_state["confirm_delete"] = None
                            st.rerun()
                        else:
                            st.error("Failed to delete repository")
            
            if st.session_state.get("confirm_delete") == selected_repo["id"]:
                st.warning("Click 'Delete Repository' again to confirm")
    
    # Create Repository Form
    if st.session_state.get("show_create_repo"):
        st.markdown("---")
        st.subheader("Create New Repository")
        
        with st.form("create_repository_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Repository Name*", placeholder="my-awesome-repo")
                description = st.text_area("Description", placeholder="Repository description...")
                git_url = st.text_input("Git URL (Optional)", placeholder="https://github.com/user/repo.git")
            
            with col2:
                projects = get_projects()
                project_options = ["None"] + [p["name"] for p in projects] if projects else ["None"]
                selected_project = st.selectbox("Project", options=project_options)
                
                default_branch = st.text_input("Default Branch", value="main")
                
                # URL validation
                if git_url and st.form_submit_button("🔍 Validate URL"):
                    validation = validate_git_url(git_url)
                    if validation.get("valid"):
                        st.success(f"✅ {validation.get('message', 'Repository is accessible')}")
                    else:
                        st.error(f"❌ {validation.get('message', 'Repository validation failed')}")
            
            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submitted = st.form_submit_button("Create Repository", type="primary", use_container_width=True)
            with col_cancel:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state["show_create_repo"] = False
                    st.rerun()
            
            if submitted and name:
                project_id = None
                if selected_project != "None" and projects:
                    project_id = next((p["id"] for p in projects if p["name"] == selected_project), None)
                
                repo_data = {
                    "name": name,
                    "description": description,
                    "git_url": git_url if git_url else None,
                    "project_id": project_id,
                    "default_branch": default_branch
                }
                
                if create_repository(repo_data):
                    st.success("Repository created successfully!")
                    st.session_state["show_create_repo"] = False
                    st.rerun()
                else:
                    st.error("Failed to create repository")

with main_tab2:
    st.header("Pull Request Management")
    
    # Sub-navigation for Pull Requests
    pr_tab1, pr_tab2 = st.tabs(["📋 Manage Pull Requests", "➕ Create Pull Request"])
    
    with pr_tab1:
        # Repository filter
        repositories = get_repositories()
        if repositories:
            repo_options = ["All Repositories"] + [repo["name"] for repo in repositories]
            selected_repo_name = st.selectbox("Filter by Repository", options=repo_options)
            
            selected_repo_id = None
            if selected_repo_name != "All Repositories":
                selected_repo_id = next((repo["id"] for repo in repositories if repo["name"] == selected_repo_name), None)
        else:
            st.warning("No repositories found. Please create a repository first.")
            st.stop()
        
        # Get and display pull requests
        pull_requests = get_pull_requests(selected_repo_id)
        selected_pr, pr_indices = display_pull_requests_dataframe(pull_requests)
        
        if selected_pr:
            st.markdown("---")
            st.subheader(f"Pull Request Details: #{selected_pr['pr_number']} - {selected_pr['title']}")
            
            # Sub-tabs for PR details
            detail_tab1, detail_tab2, detail_tab3 = st.tabs(["👥 Reviews Management", "📄 Code Changes", "🤖 AI-Powered Reviews"])
            
            with detail_tab1:
                st.subheader("Reviews Management")
                
                # Display existing reviews
                reviews = get_code_reviews(selected_pr["id"])
                selected_review, review_indices = display_reviews_dataframe(reviews)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("➕ Create New Review", type="primary"):
                        st.session_state["show_create_review"] = True
                
                with col2:
                    if selected_review and st.button("✏️ Modify Review"):
                        st.session_state["show_edit_review"] = selected_review["id"]
                
                # Create Review Form
                if st.session_state.get("show_create_review"):
                    st.markdown("**Create New Review**")
                    with st.form("create_review_form"):
                        # Get users for reviewer selection
                        users = get_users()
                        if users:
                            user_options = [f"{user['username']} ({user['email']})" for user in users]
                            selected_reviewers = st.multiselect(
                                "Select Reviewers*", 
                                options=user_options,
                                help="Select one or more users to review this pull request"
                            )
                        else:
                            st.warning("No users found. Please ensure users are registered.")
                            selected_reviewers = []
                        
                        summary_comment = st.text_area("Review Summary", placeholder="Overall review comments...")
                        status = st.selectbox("Review Status", options=REVIEW_STATUS_OPTIONS)
                        
                        col_submit, col_cancel = st.columns(2)
                        with col_submit:
                            if st.form_submit_button("Create Review", type="primary"):
                                if selected_reviewers:
                                    # Extract user IDs from selected reviewers
                                    reviewer_ids = []
                                    for reviewer_option in selected_reviewers:
                                        # Extract username from "username (email)" format
                                        username = reviewer_option.split(' (')[0]
                                        user_id = next((user['id'] for user in users if user['username'] == username), None)
                                        if user_id:
                                            reviewer_ids.append(user_id)
                                    
                                    if reviewer_ids:
                                        review_data = {
                                            "pull_request_id": selected_pr["id"],
                                            "reviewer_ids": reviewer_ids,
                                            "summary_comment": summary_comment,
                                            "status": status
                                        }
                                        success, result = create_code_review(review_data)
                                        if success:
                                            st.success("Review created successfully!")
                                            st.session_state["show_create_review"] = False
                                            st.rerun()
                                    else:
                                        st.error("Failed to find selected reviewers")
                                else:
                                    st.error("Please select at least one reviewer")
                        
                        with col_cancel:
                            if st.form_submit_button("Cancel"):
                                st.session_state["show_create_review"] = False
                                st.rerun()
                
                # Edit Review Form
                if st.session_state.get("show_edit_review") and selected_review:
                    st.markdown("**Modify Review**")
                    with st.form("edit_review_form"):
                        summary_comment = st.text_area("Review Summary", value=selected_review.get("summary_comment", ""))
                        current_status = selected_review.get("status", "draft")
                        # Handle legacy status mapping
                        if current_status not in REVIEW_STATUS_OPTIONS:
                            legacy_mapping = {"pending": "draft", "changes_requested": "needs_update", "commented": "review_request", "approved": "approved"}
                            current_status = legacy_mapping.get(current_status, "draft")
                        
                        status = st.selectbox("Review Status", 
                                            options=REVIEW_STATUS_OPTIONS,
                                            index=REVIEW_STATUS_OPTIONS.index(current_status))
                        
                        col_submit, col_cancel = st.columns(2)
                        with col_submit:
                            if st.form_submit_button("Update Review", type="primary"):
                                review_data = {
                                    "summary_comment": summary_comment,
                                    "status": status
                                }
                                success, result = update_code_review(selected_review["id"], review_data)
                                if success:
                                    st.success("Review updated successfully!")
                                    st.session_state["show_edit_review"] = None
                                    st.rerun()
                        
                        with col_cancel:
                            if st.form_submit_button("Cancel"):
                                st.session_state["show_edit_review"] = None
                                st.rerun()
            
            with detail_tab2:
                st.subheader("Code Changes")
                
                # Display files changed
                pr_files = get_pr_files(selected_pr["id"])
                
                if pr_files:
                    # Create DataFrame for files
                    file_data = []
                    for file in pr_files:
                        file_data.append({
                            "File Path": file["file_path"],
                            "Status": file["file_status"],
                            "Changes": f"+{file.get('additions', 0)} -{file.get('deletions', 0)}",
                            "Total Changes": file.get("changes", 0)
                        })
                    
                    files_df = pd.DataFrame(file_data)
                    st.dataframe(files_df, use_container_width=True, hide_index=True)
                    
                    # Show overall stats
                    total_additions = sum(f.get("additions", 0) for f in pr_files)
                    total_deletions = sum(f.get("deletions", 0) for f in pr_files)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Files Changed", len(pr_files))
                    with col2:
                        st.metric("Total Additions", total_additions, delta=f"+{total_additions}")
                    with col3:
                        st.metric("Total Deletions", total_deletions, delta=f"-{total_deletions}")
                else:
                    st.info("No files changed in this pull request.")
            
            with detail_tab3:
                st.subheader("AI-Powered Automated Reviews")
                
                col_ai1, col_ai2 = st.columns([2, 1])
                
                with col_ai2:
                    if st.button("🚀 Run AI Analysis", type="primary", use_container_width=True):
                        with st.spinner("🤖 AI is analyzing the code changes..."):
                            analysis_result = trigger_automated_review(selected_pr["id"])
                            if analysis_result:
                                st.success("✅ Automated review completed!")
                                st.session_state[f"analysis_{selected_pr['id']}"] = analysis_result
                                st.rerun()
                    
                    if st.button("📊 View Analysis", use_container_width=True):
                        analysis = get_pr_analysis(selected_pr["id"])
                        if analysis:
                            st.session_state[f"show_analysis_{selected_pr['id']}"] = analysis
                        else:
                            st.warning("No analysis available. Run AI analysis first.")
                
                with col_ai1:
                    # Display AI analysis results
                    analysis = st.session_state.get(f"show_analysis_{selected_pr['id']}")
                    if analysis and not analysis.get('error'):
                        # Success metrics
                        display_success_metrics(analysis)
                        
                        # Detailed analysis sections
                        if analysis.get('security_issues'):
                            with st.expander("🔒 Security Issues", expanded=True):
                                for i, issue in enumerate(analysis['security_issues'][:3]):
                                    st.error(f"**{issue.get('description')}**")
                                    if issue.get('match'):
                                        st.code(issue.get('match'), language='python')
                        
                        if analysis.get('suggestions'):
                            with st.expander("💡 AI Suggestions", expanded=True):
                                for i, suggestion in enumerate(analysis['suggestions'][:3]):
                                    st.info(f"**{suggestion.get('description')}**")
                                    if suggestion.get('rationale'):
                                        st.caption(f"*Rationale: {suggestion['rationale']}*")
                        
                        if analysis.get('performance_issues'):
                            with st.expander("⚡ Performance Recommendations", expanded=False):
                                for issue in analysis['performance_issues'][:3]:
                                    st.warning(f"**{issue.get('description')}**")
                                    if issue.get('match'):
                                        st.code(issue.get('match'), language='python')
                    else:
                        st.info("💡 Click 'View Analysis' to see AI-powered code analysis results")
    
    with pr_tab2:
        st.subheader("Create New Pull Request")
        
        repositories = get_repositories()
        if not repositories:
            st.warning("No repositories found. Please create a repository first.")
        else:
            with st.form("create_pr_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    repo_names = [repo["name"] for repo in repositories]
                    selected_repo_name = st.selectbox("Repository*", options=repo_names)
                    title = st.text_input("Pull Request Title*", placeholder="Add new feature...")
                    source_branch = st.text_input("Source Branch*", value="feature-branch", placeholder="feature-branch")
                
                with col2:
                    target_branch = st.text_input("Target Branch*", value="main", placeholder="main")
                    description = st.text_area("Description", placeholder="Describe the changes...")
                
                if st.form_submit_button("Create Pull Request", type="primary", use_container_width=True):
                    if title and source_branch and target_branch:
                        selected_repo_id = next((repo["id"] for repo in repositories if repo["name"] == selected_repo_name), None)
                        
                        pr_data = {
                            "repository_id": selected_repo_id,
                            "title": title,
                            "description": description,
                            "source_branch": source_branch,
                            "target_branch": target_branch
                        }
                        
                        success, result = create_pull_request(pr_data)
                        if success:
                            st.success("Pull request created successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to create pull request")
                    else:
                        st.error("Please fill in all required fields")