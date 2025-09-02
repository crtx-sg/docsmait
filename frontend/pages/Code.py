# frontend/pages/Code.py
import streamlit as st
import requests
from datetime import datetime, date
import pandas as pd
from typing import List, Dict, Any
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers
from config import BACKEND_URL

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
</style>
""", unsafe_allow_html=True)

st.title("💻 Code Review Management")

setup_authenticated_sidebar()

def get_projects():
    """Get all projects for dropdown"""
    try:
        headers = get_auth_headers()
        response = requests.get(f"{BACKEND_URL}/projects", headers=headers)
        if response.status_code == 200:
            projects = response.json()
            return projects
        else:
            st.error(f"Failed to fetch projects: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"Error fetching projects: {e}")
        return []

def get_users():
    """Get all users for team selection"""
    try:
        response = requests.get(f"{BACKEND_URL}/users", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_repositories(project_id=None):
    """Get repositories with optional filtering"""
    try:
        params = {}
        if project_id:
            params["project_id"] = project_id
        
        response = requests.get(f"{BACKEND_URL}/repositories", headers=get_auth_headers(), params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_pull_requests(repository_id=None, status=None):
    """Get pull requests with optional filtering"""
    try:
        params = {}
        if repository_id:
            params["repository_id"] = repository_id
        if status:
            params["status"] = status
        
        response = requests.get(f"{BACKEND_URL}/pull-requests", headers=get_auth_headers(), params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_pr_files(pr_id):
    """Get files changed in a pull request"""
    try:
        response = requests.get(f"{BACKEND_URL}/pull-requests/{pr_id}/files", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_code_reviews(pr_id=None):
    """Get code reviews for a PR"""
    try:
        params = {}
        if pr_id:
            params["pr_id"] = pr_id
        
        response = requests.get(f"{BACKEND_URL}/code-reviews", headers=get_auth_headers(), params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# Main tab navigation
tab1, tab2, tab3, tab4 = st.tabs(["Code Dashboard", "Repositories", "Pull Requests", "Reviews"])

with tab1:
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        projects = get_projects()
        project_options = ["All Projects"] + [p["name"] for p in projects]
        selected_project = st.selectbox("Filter by Project", project_options)
        project_id = None
        if selected_project != "All Projects":
            project_id = next((p["id"] for p in projects if p["name"] == selected_project), None)
    
    with col2:
        status_filter = st.selectbox("Filter by PR Status", ["All", "draft", "open", "review_requested", "changes_requested", "approved", "merged", "closed"])
        status = None if status_filter == "All" else status_filter
    
    # Get and display repositories and PRs
    repositories = get_repositories(project_id)
    
    if repositories:
        # Summary metrics
        total_repos = len(repositories)
        total_prs = sum(repo["pull_requests_count"] for repo in repositories)
        open_prs = sum(repo["open_prs_count"] for repo in repositories)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Repositories", total_repos)
        with col2:
            st.metric("Total Pull Requests", total_prs)
        with col3:
            st.metric("Open PRs", open_prs)
        with col4:
            merge_rate = round((total_prs - open_prs) / max(total_prs, 1) * 100, 1)
            st.metric("Merge Rate", f"{merge_rate}%")
        
        # Recent Pull Requests
        st.subheader("Recent Pull Requests")
        all_prs = get_pull_requests(status=status)
        
        if all_prs:
            pr_data = []
            for pr in all_prs[:10]:  # Show last 10 PRs
                pr_data.append({
                    "PR #": f"#{pr['pr_number']}",
                    "Title": pr['title'][:50] + "..." if len(pr['title']) > 50 else pr['title'],
                    "Repository": pr['repository_name'],
                    "Author": pr['author_username'],
                    "Status": pr['status'].replace('_', ' ').title(),
                    "Files": pr['files_changed_count'],
                    "Reviews": f"{pr['reviews_count'] - pr['pending_reviews_count']}/{pr['reviews_count']}",
                    "Created": pr['created_at'][:10]
                })
            
            df = pd.DataFrame(pr_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No pull requests found.")
    else:
        st.info("No repositories found. Create your first repository in the 'Repositories' tab.")

with tab2:
    
    action = st.radio("Select Action", ["Create New Repository", "View/Edit Existing"])
    
    if action == "Create New Repository":
        
        with st.form("create_repository_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Repository Name*", placeholder="my-awesome-repo")
                description = st.text_area("Description", placeholder="Repository description...")
                git_url = st.text_input("Git URL (Optional)", placeholder="https://github.com/user/repo.git")
                
            with col2:
                projects = get_projects()
                if projects:
                    project_names = [p["name"] for p in projects]
                    selected_project_name = st.selectbox("Project*", project_names)
                    selected_project_id = next((p["id"] for p in projects if p["name"] == selected_project_name), None)
                else:
                    st.error("No projects available. Please create a project first in the Projects page.")
                    st.info("Go to Projects → Create Project to add a new project")
                    selected_project_id = None
                
                git_provider = st.selectbox("Git Provider", ["github", "gitlab", "bitbucket", "azure", "other"])
                default_branch = st.text_input("Default Branch", value="main")
                is_private = st.checkbox("Private Repository", value=True)
            
            submitted = st.form_submit_button("Create Repository", type="primary")
            
            if submitted:
                if not all([name, selected_project_id]):
                    st.error("Please fill in all required fields marked with *")
                else:
                    try:
                        repo_data = {
                            "name": name,
                            "description": description,
                            "git_url": git_url or None,
                            "git_provider": git_provider,
                            "default_branch": default_branch,
                            "is_private": is_private,
                            "project_id": selected_project_id
                        }
                        
                        response = requests.post(f"{BACKEND_URL}/repositories", json=repo_data, headers=get_auth_headers())
                        
                        if response.status_code == 200:
                            repo_result = response.json()
                            st.success(f"✅ Repository created successfully! Repository: {repo_result['name']}")
                            st.balloons()
                            st.rerun()
                        else:
                            error_msg = response.text
                            try:
                                error_json = response.json()
                                if "detail" in error_json:
                                    error_msg = error_json["detail"]
                            except:
                                pass
                            st.error(f"❌ Failed to create repository: {error_msg}")
                    except Exception as e:
                        st.error(f"❌ Connection error: {e}")
    
    else:  # View/Edit Existing
        
        repositories = get_repositories()
        if repositories:
            repo_options = [f"{repo['name']} ({repo['project_name']})" for repo in repositories]
            selected_repo_str = st.selectbox("Select Repository", repo_options)
            selected_repo = repositories[repo_options.index(selected_repo_str)]
            
            # Display repository details
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Name:** {selected_repo['name']}")
                st.markdown(f"**Project:** {selected_repo['project_name']}")
                st.markdown(f"**Git Provider:** {selected_repo['git_provider'] or 'Not specified'}")
                st.markdown(f"**Default Branch:** {selected_repo['default_branch']}")
            
            with col2:
                st.markdown(f"**Created By:** {selected_repo['created_by_username']}")
                st.markdown(f"**Created:** {selected_repo['created_at'][:10]}")
                st.markdown(f"**Pull Requests:** {selected_repo['pull_requests_count']} (Open: {selected_repo['open_prs_count']})")
                st.markdown(f"**Private:** {'Yes' if selected_repo['is_private'] else 'No'}")
            
            st.markdown(f"**Description:** {selected_repo['description'] or 'No description'}")
            if selected_repo['git_url']:
                st.markdown(f"**Git URL:** {selected_repo['git_url']}")
        else:
            st.info("No repositories found.")

with tab3:
    
    # Select repository for PRs
    repositories = get_repositories()
    if repositories:
        repo_options = [f"{repo['name']} ({repo['project_name']})" for repo in repositories]
        selected_repo_str = st.selectbox("Select Repository for Pull Requests", repo_options, key="pr_repo")
        selected_repo = repositories[repo_options.index(selected_repo_str)]
        
        pr_tab1, pr_tab2 = st.tabs(["View Pull Requests", "Create Pull Request"])
        
        with pr_tab1:
            pull_requests = get_pull_requests(selected_repo["id"])
            
            if pull_requests:
                st.markdown(f"### Pull Requests for {selected_repo['name']}")
                
                for pr in pull_requests:
                    status_color = {
                        "draft": "🟡", "open": "🟢", "review_requested": "🔵",
                        "changes_requested": "🟠", "approved": "✅", "merged": "🟪", "closed": "⚪"
                    }
                    
                    with st.expander(f"#{pr['pr_number']}: {pr['title']} ({status_color.get(pr['status'], '⚪')} {pr['status'].replace('_', ' ').title()})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Author:** {pr['author_username']}")
                            st.markdown(f"**Source → Target:** {pr['source_branch']} → {pr['target_branch']}")
                            st.markdown(f"**Status:** {pr['status'].replace('_', ' ').title()}")
                            st.markdown(f"**Merge Status:** {pr['merge_status'].title()}")
                        
                        with col2:
                            st.markdown(f"**Created:** {pr['created_at'][:10]}")
                            st.markdown(f"**Files Changed:** {pr['files_changed_count']}")
                            st.markdown(f"**Changes:** +{pr['additions']} -{pr['deletions']}")
                            st.markdown(f"**Reviews:** {pr['reviews_count']} ({pr['pending_reviews_count']} pending)")
                        
                        st.markdown(f"**Description:** {pr['description'] or 'No description provided'}")
                        
                        # Show files changed
                        if st.button(f"View Files Changed", key=f"files_{pr['id']}"):
                            files = get_pr_files(pr['id'])
                            if files:
                                st.markdown("**Files Changed:**")
                                for file in files:
                                    status_icon = {"added": "🆕", "modified": "📝", "deleted": "🗑️", "renamed": "📛"}
                                    st.markdown(f"- {status_icon.get(file['file_status'], '📄')} `{file['file_path']}` (+{file['additions']} -{file['deletions']})")
                            else:
                                st.info("No files found for this PR")
                        
                        # Show reviews
                        reviews = get_code_reviews(pr['id'])
                        if reviews:
                            st.markdown("**Reviews:**")
                            for review in reviews:
                                status_icon = {"pending": "⏳", "approved": "✅", "changes_requested": "🔄", "commented": "💬"}
                                st.markdown(f"- {status_icon.get(review['status'], '💭')} **{review['reviewer_username']}**: {review['status'].replace('_', ' ').title()}")
                                if review['summary_comment']:
                                    st.markdown(f"  _{review['summary_comment']}_")
            else:
                st.info("No pull requests found for this repository.")
        
        with pr_tab2:
            st.markdown("### Create New Pull Request")
            
            with st.form("create_pr_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    pr_title = st.text_input("Title*", placeholder="Add new feature X")
                    source_branch = st.text_input("Source Branch*", placeholder="feature/new-feature")
                    external_id = st.text_input("External PR ID (Optional)", placeholder="123")
                
                with col2:
                    target_branch = st.text_input("Target Branch*", value=selected_repo['default_branch'])
                    external_url = st.text_input("External URL (Optional)", placeholder="https://github.com/user/repo/pull/123")
                
                description = st.text_area("Description", height=100, placeholder="Describe what this PR does...")
                
                submitted = st.form_submit_button("Create Pull Request", type="primary")
                
                if submitted:
                    if not all([pr_title, source_branch, target_branch]):
                        st.error("Please fill in all required fields marked with *")
                    else:
                        try:
                            pr_data = {
                                "repository_id": selected_repo["id"],
                                "title": pr_title,
                                "description": description,
                                "source_branch": source_branch,
                                "target_branch": target_branch,
                                "external_id": external_id or None,
                                "external_url": external_url or None
                            }
                            
                            response = requests.post(f"{BACKEND_URL}/pull-requests", json=pr_data, headers=get_auth_headers())
                            
                            if response.status_code == 200:
                                pr_result = response.json()
                                st.success(f"✅ Pull Request created successfully! PR #{pr_result['pr_number']}")
                                st.balloons()
                                st.rerun()
                            else:
                                error_msg = response.text
                                try:
                                    error_json = response.json()
                                    if "detail" in error_json:
                                        error_msg = error_json["detail"]
                                except:
                                    pass
                                st.error(f"❌ Failed to create pull request: {error_msg}")
                        except Exception as e:
                            st.error(f"❌ Connection error: {e}")
    else:
        st.info("No repositories available. Create a repository first.")

with tab4:
    
    # Select PR for reviews
    repositories = get_repositories()
    if repositories:
        repo_options = [f"{repo['name']} ({repo['project_name']})" for repo in repositories]
        selected_repo_str = st.selectbox("Select Repository for Reviews", repo_options, key="review_repo")
        selected_repo = repositories[repo_options.index(selected_repo_str)]
        
        pull_requests = get_pull_requests(selected_repo["id"])
        
        if pull_requests:
            pr_options = [f"#{pr['pr_number']}: {pr['title']}" for pr in pull_requests]
            selected_pr_str = st.selectbox("Select Pull Request", pr_options, key="review_pr")
            selected_pr = pull_requests[pr_options.index(selected_pr_str)]
            
            review_tab1, review_tab2 = st.tabs(["View Reviews", "Create Review"])
            
            with review_tab1:
                reviews = get_code_reviews(selected_pr["id"])
                
                if reviews:
                    st.markdown(f"### Reviews for PR #{selected_pr['pr_number']}")
                    
                    for review in reviews:
                        status_color = {"pending": "⏳", "approved": "✅", "changes_requested": "🔄", "commented": "💬"}
                        
                        with st.expander(f"{status_color.get(review['status'], '💭')} {review['reviewer_username']} - {review['status'].replace('_', ' ').title()}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**Reviewer:** {review['reviewer_username']}")
                                st.markdown(f"**Status:** {review['status'].replace('_', ' ').title()}")
                            
                            with col2:
                                st.markdown(f"**Created:** {review['created_at'][:10]}")
                                if review['submitted_at']:
                                    st.markdown(f"**Submitted:** {review['submitted_at'][:10]}")
                                st.markdown(f"**Comments:** {review['comments_count']}")
                            
                            if review['summary_comment']:
                                st.markdown(f"**Summary Comment:** {review['summary_comment']}")
                else:
                    st.info("No reviews found for this pull request.")
            
            with review_tab2:
                st.markdown("### Create Code Review")
                
                with st.form("create_review_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        users = get_users()
                        if users:
                            reviewer_names = [f"{u['username']} ({u['email']})" for u in users]
                            selected_reviewers = st.multiselect("Select Reviewers*", reviewer_names)
                            reviewer_ids = [users[reviewer_names.index(name)]["id"] for name in selected_reviewers]
                        else:
                            st.error("No users available for review assignment.")
                            reviewer_ids = []
                    
                    with col2:
                        review_status = st.selectbox("Review Status", ["pending", "approved", "changes_requested", "commented"])
                    
                    summary_comment = st.text_area("Summary Comment", height=100, placeholder="Overall feedback on this PR...")
                    
                    submitted = st.form_submit_button("Create Review", type="primary")
                    
                    if submitted:
                        if not reviewer_ids:
                            st.error("Please select at least one reviewer")
                        else:
                            try:
                                review_data = {
                                    "pull_request_id": selected_pr["id"],
                                    "reviewer_ids": reviewer_ids,
                                    "summary_comment": summary_comment or None,
                                    "status": review_status
                                }
                                
                                response = requests.post(f"{BACKEND_URL}/code-reviews", json=review_data, headers=get_auth_headers())
                                
                                if response.status_code == 200:
                                    reviews_result = response.json()
                                    st.success(f"✅ Code review(s) created successfully! {len(reviews_result)} reviewer(s) assigned.")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    error_msg = response.text
                                    try:
                                        error_json = response.json()
                                        if "detail" in error_json:
                                            error_msg = error_json["detail"]
                                    except:
                                        pass
                                    st.error(f"❌ Failed to create review: {error_msg}")
                            except Exception as e:
                                st.error(f"❌ Connection error: {e}")
        else:
            st.info("No pull requests available. Create a pull request first.")
    else:
        st.info("No repositories available. Create a repository first.")