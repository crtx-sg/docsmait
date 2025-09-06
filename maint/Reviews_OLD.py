# frontend/pages/Reviews.py
import streamlit as st
import requests
import json
import time
from datetime import datetime
from streamlit_ace import st_ace
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers, BACKEND_URL

require_auth()

def generate_unique_key(prefix: str, *args) -> str:
    """Generate a unique key by combining prefix with arguments and current timestamp"""
    key_parts = [str(prefix)] + [str(arg) for arg in args if arg is not None]
    base_key = "_".join(key_parts)
    # Add timestamp to ensure uniqueness across re-runs
    unique_suffix = str(int(time.time() * 1000))[-6:]  # Last 6 digits of timestamp
    return f"{base_key}_{unique_suffix}"

st.set_page_config(page_title="Reviews", page_icon="🔍", layout="wide")

# Add CSS for compact layout
st.markdown("""
<style>
    .element-container {
        margin-bottom: 0.3rem;
    }
    .stExpander {
        margin-bottom: 0.3rem;
    }
    .stExpander > div > div > div {
        padding-top: 0.25rem;
        padding-bottom: 0.25rem;
        line-height: 1.2;
    }
    .stExpander .stMarkdown p {
        margin-bottom: 0.2rem;
        line-height: 1.2;
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
    .stMarkdown {
        margin-bottom: 0.25rem;
    }
    .stSubheader {
        margin-top: 0.5rem;
        margin-bottom: 0.25rem;
    }
    .block-container {
        padding-top: 0.5rem;
    }
    h1, h2, h3 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.25rem !important;
    }
    .stSelectbox {
        margin-bottom: 0.5rem;
    }
    .stColumns {
        gap: 0.5rem;
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
    
    # Create main 2:3 split layout
    main_col1, main_col2 = st.columns([2, 3])
    
    with main_col1:
        st.markdown("### Review Management")
        
        # Create tabs for different views in the left panel
        tab1, tab2, tab3 = st.tabs(["📥 My Queue", "📋 All Reviews", "📤 Submitted"])
    
        with tab1:
            # Get user's review queue for selected project
            review_queue = get_user_review_queue(selected_project_id)
            
            # Sort by most recent first (submitted_at or created_at)
            if review_queue:
                review_queue.sort(key=lambda x: x.get('submitted_at') or x.get('created_at') or '', reverse=True)
            
            if not review_queue:
                st.info("🎉 No pending reviews!")
            else:
                st.caption(f"🔍 DEBUG: Review queue has {len(review_queue)} items")
                if review_queue:
                    st.caption(f"🔍 DEBUG: First item keys: {list(review_queue[0].keys())}")
                    if 'review_comments' in review_queue[0]:
                        st.caption(f"🔍 DEBUG: First item has review_comments: {len(review_queue[0]['review_comments'])} comments")
                    else:
                        st.caption("🔍 DEBUG: First item has NO review_comments field")
                # Display review queue items using expander format like Documents/Templates
                for i, item in enumerate(review_queue):
                    with st.expander(f"📄 {item['document_name']} - {item['status'].replace('_', ' ').title() if item.get('status') else 'Request Review'}"):
                        st.write(f"**Document Type:** {item['document_type'].replace('_', ' ').title()}")
                        st.write(f"**Document Status:** {item['status'].replace('_', ' ').title() if item.get('status') else 'Request Review'}")
                        st.write(f"**Author:** {item['author']}")
                        st.write(f"**Submitted:** {item['submitted_at'][:10] if item['submitted_at'] else 'N/A'}")
                        if item.get('author_comment'):
                            st.write(f"**Comment:** {item['author_comment'][:60]}..." if len(str(item['author_comment'])) > 60 else f"**Comment:** {item['author_comment']}")
                        
                        # Action button
                        if st.button("👀 Review", key=f"review_{item['document_id']}_{i}", use_container_width=True):
                            st.session_state.selected_review_item = item
                            st.session_state.review_mode = "submit_review"
                            st.rerun()
    
        with tab2:
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.selectbox(
                    "Status",
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
                    "Reviewer",
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
                st.info("No reviews found.")
            else:
                # Display reviews using expander format like Documents/Templates
                for review in project_reviews:
                    # Show reviewer status summary
                    reviewer_status = []
                    for reviewer in review['reviewers']:
                        icon = "✅" if reviewer['review_submitted'] and reviewer['review_approved'] else "❌" if reviewer['review_submitted'] and not reviewer['review_approved'] else "⏳"
                        reviewer_status.append(f"{icon} {reviewer['username']}")
                    
                    with st.expander(f"📄 {review['document_name']} (Rev {review['current_revision']}) - {review['status'].replace('_', ' ').title()}"):
                        st.write(f"**Document Type:** {review['document_type'].replace('_', ' ').title()}")
                        st.write(f"**Document Status:** {review['status'].replace('_', ' ').title()}")
                        st.write(f"**Author:** {review['author']}")
                        if review.get('created_at'):
                            st.write(f"**Submitted:** {review['created_at'][:10]}")
                        if review.get('updated_at'):
                            st.write(f"**Updated:** {review['updated_at'][:10]}")
                        
                        if reviewer_status:
                            st.write(f"**Reviewers:** {', '.join(reviewer_status)}")
                        
                        # Action button
                        if st.button("📄 View Details", key=generate_unique_key("view_all", review['document_id'], review.get('current_revision')), use_container_width=True):
                            st.session_state.selected_review_item = review
                            st.session_state.review_mode = "view_details"
                            st.rerun()
    
        with tab3:
            submitted_reviews = get_submitted_reviews(selected_project_id)
            
            if not submitted_reviews:
                st.info("No submitted reviews found.")
            else:
                # Display submitted reviews using expander format like Documents/Templates
                for review in submitted_reviews:
                    status_icon = "✅" if review['approved'] else "❌"
                    with st.expander(f"{status_icon} {review['document_name']} - {review['status'].replace('_', ' ').title()}"):
                        st.write(f"**Document Type:** {review['document_type'].replace('_', ' ').title()}")
                        st.write(f"**Document Status:** {review['status'].replace('_', ' ').title()}")
                        st.write(f"**Author:** {review['author']}")
                        st.write(f"**Reviewer:** {review['reviewer']}")
                        if review.get('reviewed_at'):
                            st.write(f"**Reviewed:** {review['reviewed_at'][:10]}")
                        if review.get('comments'):
                            st.write(f"**Comments:** {review['comments'][:60]}..." if len(str(review['comments'])) > 60 else f"**Comments:** {review['comments']}")
                        
                        # Action button
                        if st.button("📄 View Review", key=generate_unique_key("view_submitted", review.get('review_id', review['document_id']), review.get('reviewer_id')), use_container_width=True):
                            st.session_state.selected_review_item = review
                            st.session_state.review_mode = "view_submitted"
                            st.rerun()
    
    with main_col2:
        st.markdown("### Document Viewer")
        
        
        # Right panel content based on selected review
        if st.session_state.get("selected_review_item") and st.session_state.get("review_mode"):
            item = st.session_state.selected_review_item
            mode = st.session_state.review_mode
            
            if mode == "submit_review":
                # Show complete comment history if available
                st.caption(f"🔍 DEBUG: Submit Review - Item has review_comments: {len(item.get('review_comments', []))} comments")
                if item.get('review_comments'):
                    st.subheader("💬 Comment History")
                    st.caption(f"🔍 DEBUG: About to display {len(item['review_comments'])} comments")
                    for i, comment in enumerate(item['review_comments']):
                        st.caption(f"🔍 DEBUG: Comment {i+1}: {comment}")  # Debug each comment
                        # Format timestamp
                        timestamp = comment.get('timestamp', '')
                        date_str = timestamp[:10] if timestamp and len(timestamp) >= 10 else 'N/A'
                        time_str = timestamp[11:16] if timestamp and len(timestamp) >= 16 else ''
                        datetime_str = f"{date_str} {time_str}".strip()
                        
                        # Format: [date/time, person name, author/reviewer, comments]
                        person_name = comment.get('commenter', 'Unknown')
                        role = comment.get('type', 'unknown').title()
                        comment_text = comment.get('comment', '')
                        
                        # Get status from comment type and approval
                        if comment.get('type') == 'author':
                            status = "Author Comment"
                        elif comment.get('approved') == True:
                            status = "Approved"
                        elif comment.get('approved') == False:
                            status = "Need Revision"
                        else:
                            status = "Reviewer Comment"
                        
                        formatted_comment = f"[{datetime_str}, {status}, {comment_text}]"
                        
                        # Determine styling based on comment type
                        if comment.get('type') == 'author':
                            # Author comments (from revisions)
                            st.info(f"📝 {formatted_comment}")
                        else:
                            # Reviewer comments
                            status_icon = "✅" if comment.get('approved') else "❌"
                            if comment.get('approved'):
                                st.success(f"{status_icon} {formatted_comment}")
                            else:
                                st.error(f"❌ {formatted_comment}")
                
                # Show document header after comment history
                st.subheader(f"📄 {item['document_name']}")
                st.caption(f"{item['document_type'].replace('_', ' ').title()} • by {item['author']}")
                st.caption(f"Submitted: {item['submitted_at'][:19] if item['submitted_at'] else 'N/A'}")
                
                st.subheader("📄 Document Content")
                # Debug: Check content availability
                content = item.get('content', '')
                if not content:
                    st.warning(f"⚠️ Document content is empty or not available. Item keys: {list(item.keys())}")
                    st.warning(f"Content value: '{content}' (length: {len(content) if content else 0})")
                else:
                    st.caption(f"📊 Content length: {len(content)} characters")
                
                st_ace(
                    value=content,
                    language='markdown',
                    theme='github',
                    key=generate_unique_key("content_viewer", item['document_id'], item.get('revision_id')),
                    height=400,
                    auto_update=False,
                    wrap=True,
                    readonly=True
                )
                
                st.subheader("✏️ Submit Review")
                
                # Review form
                with st.form(generate_unique_key("review_form", item['document_id'], item.get('revision_id'))):
                    review_decision = st.radio(
                        "Decision",
                        ["Approved", "Need Revision"],
                        key=generate_unique_key("decision", item['document_id'], item.get('revision_id'))
                    )
                    
                    review_comments = st.text_area(
                        "Comments",
                        placeholder="Provide your review comments here...",
                        key=generate_unique_key("comments", item['document_id'], item.get('revision_id')),
                        height=100
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("🚀 Submit Review", type="primary", use_container_width=True)
                    with col2:
                        if st.form_submit_button("❌ Cancel", use_container_width=True):
                            del st.session_state.selected_review_item
                            del st.session_state.review_mode
                            st.rerun()
                    
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
                                del st.session_state.selected_review_item
                                del st.session_state.review_mode
                                time.sleep(2)
                                st.rerun()
                            else:
                                error_msg = result.get("error", result.get("detail", "Unknown error"))
                                st.error(f"❌ Failed to submit review: {error_msg}")
                                
            elif mode == "view_only":
                # Show complete comment history if available
                st.caption(f"🔍 DEBUG: View Only - Item has review_comments: {len(item.get('review_comments', []))} comments")
                if item.get('review_comments'):
                    st.subheader("💬 Comment History")
                    st.caption(f"🔍 DEBUG: About to display {len(item['review_comments'])} comments")
                    for i, comment in enumerate(item['review_comments']):
                        st.caption(f"🔍 DEBUG: Comment {i+1}: {comment}")  # Debug each comment
                        # Format timestamp
                        timestamp = comment.get('timestamp', '')
                        date_str = timestamp[:10] if timestamp and len(timestamp) >= 10 else 'N/A'
                        time_str = timestamp[11:16] if timestamp and len(timestamp) >= 16 else ''
                        datetime_str = f"{date_str} {time_str}".strip()
                        
                        # Format: [date/time, person name, author/reviewer, comments]
                        person_name = comment.get('commenter', 'Unknown')
                        role = comment.get('type', 'unknown').title()
                        comment_text = comment.get('comment', '')
                        
                        # Get status from comment type and approval
                        if comment.get('type') == 'author':
                            status = "Author Comment"
                        elif comment.get('approved') == True:
                            status = "Approved"
                        elif comment.get('approved') == False:
                            status = "Need Revision"
                        else:
                            status = "Reviewer Comment"
                        
                        formatted_comment = f"[{datetime_str}, {status}, {comment_text}]"
                        
                        # Determine styling based on comment type
                        if comment.get('type') == 'author':
                            # Author comments (from revisions)
                            st.info(f"📝 {formatted_comment}")
                        else:
                            # Reviewer comments
                            status_icon = "✅" if comment.get('approved') else "❌"
                            if comment.get('approved'):
                                st.success(f"{status_icon} {formatted_comment}")
                            else:
                                st.error(f"❌ {formatted_comment}")
                
                # Show document header after comment history
                st.subheader(f"📄 {item['document_name']}")
                st.caption(f"{item['document_type'].replace('_', ' ').title()} • by {item['author']}")
                st.caption(f"Submitted: {item['submitted_at'][:19] if item['submitted_at'] else 'N/A'}")
                
                st.subheader("📄 Document Content")
                st_ace(
                    value=item['content'],
                    language='markdown',
                    theme='github',
                    key=generate_unique_key("content_viewer_only", item['document_id'], item.get('revision_id')),
                    height=400,
                    auto_update=False,
                    wrap=True,
                    readonly=True
                )
                
                if st.button("❌ Close", key=generate_unique_key("close_view_only", item['document_id'], item.get('revision_id')), use_container_width=True):
                    del st.session_state.selected_review_item
                    del st.session_state.review_mode
                    st.rerun()
                    
            elif mode == "view_details":
                # Show review details for all project reviews
                st.subheader(f"📄 {item['document_name']}")
                st.caption(f"{item['document_type'].replace('_', ' ').title()} • by {item['author']}")
                st.caption(f"Status: {item['status'].replace('_', ' ').title()} • Revision: {item['current_revision']}")
                
                st.subheader("👥 Reviewers Status")
                for reviewer in item['reviewers']:
                    status_icon = "✅" if reviewer['review_submitted'] and reviewer['review_approved'] else "❌" if reviewer['review_submitted'] and not reviewer['review_approved'] else "⏳"
                    status_text = "Approved" if reviewer['review_submitted'] and reviewer['review_approved'] else "Need Revision" if reviewer['review_submitted'] and not reviewer['review_approved'] else "Pending"
                    st.write(f"{status_icon} **{reviewer['username']}:** {status_text}")
                
                st.subheader("📄 Document Content")
                if item.get('content_preview'):
                    st_ace(
                        value=item['content_preview'],
                        language='markdown',
                        theme='github',
                        key=generate_unique_key("content_viewer_details", item['document_id'], item.get('current_revision')),
                        height=400,
                        auto_update=False,
                        wrap=True,
                        readonly=True
                    )
                else:
                    st.info("Content preview not available")
                
                if st.button("❌ Close", key=generate_unique_key("close_view_details", item['document_id'], item.get('current_revision')), use_container_width=True):
                    del st.session_state.selected_review_item
                    del st.session_state.review_mode
                    st.rerun()
                    
            elif mode == "view_submitted":
                # Show submitted review details
                status_icon = "✅" if item['approved'] else "❌"
                st.subheader(f"📄 {item['document_name']}")
                st.caption(f"{item['document_type'].replace('_', ' ').title()} • by {item['author']}")
                
                status_color = "green" if item['approved'] else "red"
                st.markdown(f"**Review Status:** :{status_color}[{status_icon} {item['status'].replace('_', ' ').title()}]")
                st.write(f"**Reviewer:** {item['reviewer']}")
                st.write(f"**Reviewed:** {item['reviewed_at'][:19] if item['reviewed_at'] else 'N/A'}")
                
                st.subheader("💬 Review Comments")
                if item['comments']:
                    st.markdown(item['comments'])
                else:
                    st.info("No comments provided")
                
                st.subheader("📄 Document Content")
                if item.get('brief_description'):
                    st_ace(
                        value=item['brief_description'],
                        language='markdown',
                        theme='github',
                        key=generate_unique_key("content_viewer_submitted", item.get('review_id', item['document_id']), item.get('reviewer_id')),
                        height=400,
                        auto_update=False,
                        wrap=True,
                        readonly=True
                    )
                else:
                    st.info("Content preview not available")
                
                if st.button("❌ Close", key=generate_unique_key("close_view_submitted", item.get('review_id', item['document_id']), item.get('reviewer_id')), use_container_width=True):
                    del st.session_state.selected_review_item
                    del st.session_state.review_mode
                    st.rerun()
        else:
            st.info("Select a document from the left panel to view details or submit a review.")

if __name__ == "__main__":
    main()