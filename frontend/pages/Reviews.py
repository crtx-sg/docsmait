# frontend/pages/Reviews.py
import streamlit as st
import requests
import json
import time
from datetime import datetime
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers, BACKEND_URL

require_auth()

st.set_page_config(page_title="Reviews", page_icon="🔍", layout="wide")

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
</style>
""", unsafe_allow_html=True)

st.title("🔍 Reviews")

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

def get_project_reviews(project_id, status_filter=None, reviewer_filter=None):
    """Get reviews for a project"""
    try:
        params = {}
        if status_filter:
            params["status"] = status_filter
        if reviewer_filter:
            params["reviewer_id"] = reviewer_filter
        
        response = requests.get(
            f"{BACKEND_URL}/projects/{project_id}/reviews",
            params=params,
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching project reviews: {e}")
        return []

def get_user_review_queue(project_id=None):
    """Get review queue for current user"""
    try:
        params = {}
        if project_id:
            params["project_id"] = project_id
        
        response = requests.get(
            f"{BACKEND_URL}/reviews/queue",
            params=params,
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching review queue: {e}")
        return []

def get_submitted_reviews(project_id):
    """Get submitted reviews for a project"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/projects/{project_id}/reviews/submitted",
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching submitted reviews: {e}")
        return []

def get_review_analytics(project_id):
    """Get review analytics for a project"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/projects/{project_id}/reviews/analytics",
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception as e:
        st.error(f"Error fetching review analytics: {e}")
        return {}

def submit_review(document_id, revision_id, approved, comments):
    """Submit a review"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/documents/{document_id}/reviews",
            json={
                "document_id": document_id,
                "revision_id": revision_id,
                "approved": approved,
                "comments": comments
            },
            headers=get_auth_headers()
        )
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def get_project_members(project_id):
    """Get project members for filtering"""
    try:
        response = requests.get(f"{BACKEND_URL}/projects/{project_id}", headers=get_auth_headers())
        if response.status_code == 200:
            project_data = response.json()
            return project_data.get("members", [])
        return []
    except Exception as e:
        st.error(f"Error fetching project members: {e}")
        return []

# Main application
def main():
    # Project selection
    projects = get_user_projects()
    
    if not projects:
        st.warning("No projects found. Please create or join a project first.")
        return
    
    # Project dropdown
    project_options = {f"{proj['name']}": proj['id'] for proj in projects}
    selected_project_name = st.selectbox(
        "Select Project",
        options=list(project_options.keys()),
        key="project_selector"
    )
    
    if not selected_project_name:
        st.info("Please select a project to view reviews.")
        return
    
    selected_project_id = project_options[selected_project_name]
    
    # Get review analytics
    analytics = get_review_analytics(selected_project_id)
    
    # Display analytics cards
    if analytics:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📋 Pending Reviews", analytics.get("pending_reviews", 0))
        with col2:
            st.metric("✅ Approved", analytics.get("approved_reviews", 0))
        with col3:
            st.metric("📝 Need Revision", analytics.get("need_revision", 0))
        with col4:
            st.metric("📄 Total in Review", analytics.get("total_documents_in_review", 0))
        
        st.divider()
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📥 My Review Queue", "📋 All Project Reviews", "📤 Submitted Reviews"])
    
    with tab1:
        st.write("Documents assigned to you for review")
        
        # Get user's review queue for selected project
        review_queue = get_user_review_queue(selected_project_id)
        
        if not review_queue:
            st.info("🎉 No pending reviews! Your review queue is empty.")
        else:
            # Display review queue items
            for i, item in enumerate(review_queue):
                with st.expander(f"📄 {item['document_name']} - {item['document_type'].replace('_', ' ').title()}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Author:** {item['author']}")
                        st.write(f"**Submitted:** {item['submitted_at'][:19] if item['submitted_at'] else 'N/A'}")
                        if item.get('author_comment'):
                            st.write(f"**Author's Comment:** {item['author_comment']}")
                        
                        st.subheader("📄 Document Content")
                        st.markdown(item['content'])
                    
                    with col2:
                        st.subheader("✏️ Submit Review")
                        
                        # Review form
                        with st.form(f"review_form_{i}"):
                            review_decision = st.radio(
                                "Decision",
                                ["Approved", "Need Revision"],
                                key=f"decision_{i}"
                            )
                            
                            review_comments = st.text_area(
                                "Comments",
                                placeholder="Provide your review comments here...",
                                key=f"comments_{i}",
                                height=100
                            )
                            
                            submitted = st.form_submit_button("🚀 Submit Review", type="primary")
                            
                            if submitted:
                                if not review_comments.strip():
                                    st.error("Please provide comments for your review.")
                                else:
                                    approved = review_decision == "Approved"
                                    result, status_code = submit_review(
                                        item['document_id'],
                                        item['revision_id'],
                                        approved,
                                        review_comments
                                    )
                                    
                                    if status_code == 200 and result.get("success"):
                                        st.success("✅ Review submitted successfully!")
                                        time.sleep(2)
                                        st.rerun()
                                    else:
                                        error_msg = result.get("error", result.get("detail", "Unknown error"))
                                        st.error(f"❌ Failed to submit review: {error_msg}")
    
    with tab2:
        st.write("Overview of all reviews in the selected project")
        
        # Filters
        col1, col2 = st.columns(2)
        
        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Pending", "Approved", "Need Revision"],
                key="status_filter"
            )
        
        with col2:
            # Get project members for reviewer filter
            project_members = get_project_members(selected_project_id)
            reviewer_options = {"All": None}
            for member in project_members:
                reviewer_options[member["username"]] = member["user_id"]
            
            selected_reviewer = st.selectbox(
                "Filter by Reviewer",
                options=list(reviewer_options.keys()),
                key="reviewer_filter"
            )
        
        # Apply filters
        status_param = None
        if status_filter != "All":
            status_param = status_filter.lower().replace(" ", "_")
        
        reviewer_param = reviewer_options[selected_reviewer]
        
        # Get filtered reviews
        project_reviews = get_project_reviews(selected_project_id, status_param, reviewer_param)
        
        if not project_reviews:
            st.info("No reviews found matching the selected filters.")
        else:
            # Display reviews in a table format
            for review in project_reviews:
                with st.container():
                    st.markdown("---")
                    
                    col1, col2, col3 = st.columns([3, 2, 2])
                    
                    with col1:
                        st.subheader(f"📄 {review['document_name']}")
                        st.write(f"**Type:** {review['document_type'].replace('_', ' ').title()}")
                        st.write(f"**Author:** {review['author']}")
                        st.write(f"**Status:** {review['status'].replace('_', ' ').title()}")
                    
                    with col2:
                        st.write(f"**Created:** {review['created_at'][:19] if review['created_at'] else 'N/A'}")
                        st.write(f"**Updated:** {review['updated_at'][:19] if review['updated_at'] else 'N/A'}")
                        st.write(f"**Revision:** {review['current_revision']}")
                    
                    with col3:
                        st.write("**Reviewers:**")
                        for reviewer in review['reviewers']:
                            status_icon = "✅" if reviewer['review_submitted'] and reviewer['review_approved'] else "❌" if reviewer['review_submitted'] and not reviewer['review_approved'] else "⏳"
                            status_text = "Approved" if reviewer['review_submitted'] and reviewer['review_approved'] else "Need Revision" if reviewer['review_submitted'] and not reviewer['review_approved'] else "Pending"
                            st.write(f"{status_icon} {reviewer['username']} - {status_text}")
                    
                    # Show content preview
                    if st.button(f"👁️ View Content", key=f"view_{review['document_id']}"):
                        st.session_state[f"show_content_{review['document_id']}"] = True
                    
                    if st.session_state.get(f"show_content_{review['document_id']}", False):
                        st.markdown("**Document Content Preview:**")
                        st.markdown(review['content_preview'])
                        if st.button(f"🙈 Hide Content", key=f"hide_{review['document_id']}"):
                            st.session_state[f"show_content_{review['document_id']}"] = False
                            st.rerun()
    
    with tab3:
        st.write("History of all submitted reviews in the selected project")
        
        submitted_reviews = get_submitted_reviews(selected_project_id)
        
        if not submitted_reviews:
            st.info("No submitted reviews found for this project.")
        else:
            # Create a more detailed view of submitted reviews
            for review in submitted_reviews:
                with st.container():
                    st.markdown("---")
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        status_icon = "✅" if review['approved'] else "❌"
                        status_color = "green" if review['approved'] else "red"
                        
                        st.markdown(f"### {status_icon} {review['document_name']}")
                        st.write(f"**Type:** {review['document_type'].replace('_', ' ').title()}")
                        st.write(f"**Author:** {review['author']}")
                        st.write(f"**Reviewer:** {review['reviewer']}")
                        st.markdown(f"**Status:** :{status_color}[{review['status'].replace('_', ' ').title()}]")
                        
                        # Show review comments
                        if review['comments']:
                            with st.expander("💬 Review Comments", expanded=False):
                                st.write(review['comments'])
                    
                    with col2:
                        st.write(f"**Submitted:** {review['submitted_at'][:19] if review['submitted_at'] else 'N/A'}")
                        st.write(f"**Reviewed:** {review['reviewed_at'][:19] if review['reviewed_at'] else 'N/A'}")
                        
                        # Brief description
                        if review.get('brief_description'):
                            st.write("**Brief Description:**")
                            st.write(review['brief_description'])

if __name__ == "__main__":
    main()