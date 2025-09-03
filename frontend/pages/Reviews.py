# Reviews Page - Focused on Review Functionality
import streamlit as st
import requests
from streamlit_ace import st_ace
from auth_utils import get_auth_headers, get_current_user, setup_authenticated_sidebar, BACKEND_URL

st.set_page_config(page_title="📋 Reviews", page_icon="📋", layout="wide")

# Custom CSS for single line spacing and clean layout
st.markdown("""
<style>
    .stSubheader {
        margin-top: 0.5rem;
        margin-bottom: 0.25rem;
        font-size: 1.1rem;
        font-weight: 600;
    }
    .block-container {
        padding-top: 0.5rem;
    }
    .stMarkdown {
        margin-bottom: 0.25rem;
        line-height: 1.3;
    }
    .stColumns {
        gap: 0.5rem;
    }
    .comment-item {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin-bottom: 0.25rem;
        border-left: 3px solid #007bff;
        color: #212529 !important;
    }
    .comment-item strong {
        color: #495057 !important;
    }
    .status-draft { color: #6c757d; }
    .status-review-request { color: #fd7e14; }
    .status-needs-update { color: #dc3545; }
    .status-approved { color: #198754; }
    .review-under-review { color: #0d6efd; }
</style>
""", unsafe_allow_html=True)

def get_documents_for_reviewer(project_id):
    """Get documents assigned to current reviewer using V2 API"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v2/projects/{project_id}/documents/reviewer",
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            data = response.json()["documents"]
            return data
        else:
            return []
    except Exception as e:
        st.error(f"Error fetching review documents: {e}")
        return []

def submit_review(document_id, reviewer_comment, review_decision):
    """Submit review decision using V2 API"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v2/documents/{document_id}/submit-review",
            params={
                "reviewer_comment": reviewer_comment,
                "review_decision": review_decision
            },
            headers=get_auth_headers()
        )
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def format_status_v2(document_state, review_state=None):
    """Format status with color for V2 API data"""
    if document_state == "draft":
        return f'<span class="status-draft">📝 Draft</span>'
    elif document_state == "review_request" and review_state == "under_review":
        return f'<span class="review-under-review">📋 Under Review</span>'
    elif document_state == "needs_update":
        return f'<span class="status-needs-update">⚠️ Needs Update</span>'
    elif document_state == "approved":
        return f'<span class="status-approved">✅ Approved</span>'
    return document_state.replace('_', ' ').title() if document_state else "Unknown"

def display_comment_history(comments):
    """Display comment history in clean format - handles both V1 and V2 formats"""
    if not comments:
        st.info("No comments yet")
        return
    
    for comment in comments:
        # Handle both V1 API format (timestamp, commenter) and V2 API format (date_time, user)
        timestamp = comment.get("timestamp") or comment.get("date_time", "")
        date_time = timestamp[:16] if timestamp else "N/A"
        
        # Handle different type formats between V1 and V2
        comment_type = comment.get("type", "Comment")
        if comment_type:
            comment_type = comment_type.replace('_', ' ').title()
        
        user = comment.get("commenter") or comment.get("user", "Unknown")
        text = comment.get("comment", "")
        
        st.markdown(f"""
        <div class="comment-item">
            <strong>{date_time}</strong> | <strong>{comment_type}</strong> | {user}<br>
            {text}
        </div>
        """, unsafe_allow_html=True)

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

# Main interface
st.title("📋 Reviews - Document Review Workflow")

# Get user info and project
user_info = get_current_user()
if not user_info:
    st.error("Please log in to access reviews")
    st.stop()


# Setup authenticated sidebar
setup_authenticated_sidebar()

# Project selection
projects = get_user_projects()
if not projects:
    st.warning("⚠️ You are not a member of any projects. Please join or create a project to review documents.")
    st.stop()

st.subheader("📋 Select Project")
project_options = {p["name"]: p["id"] for p in projects}
selected_project_name = st.selectbox(
    "Project",
    options=list(project_options.keys()),
    key="selected_project_reviews"
)

if not selected_project_name:
    st.info("Please select a project to view reviews.")
    st.stop()

project_id = project_options[selected_project_name]

# Main layout: Left panel for review queue, Right panel for review editor
col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("📋 Review Queue")
    st.caption("Documents assigned to you for review")
    
    review_docs = get_documents_for_reviewer(project_id)
    
    if not review_docs:
        st.info("🎉 No documents to review!")
    else:
        st.caption(f"📄 {len(review_docs)} document(s) pending review")
        
        for doc in review_docs:
            doc_name = doc.get('name', doc.get('document_name', 'Unknown Document'))
            with st.expander(f"📄 {doc_name}", expanded=False):
                st.markdown(f"**Type:** {doc['document_type'].replace('_', ' ').title()}")
                st.markdown(f"**Author:** {doc['author']}")
                # Use V2 status format
                doc_state = doc.get('document_state', 'review_request')
                review_state = doc.get('review_state', 'under_review')
                st.markdown(f"**Status:** {format_status_v2(doc_state, review_state)}", unsafe_allow_html=True)
                st.markdown(f"**Submitted:** {doc.get('updated_at', doc.get('submitted_at', 'N/A'))[:10]}")
                
                # Show latest comment from comment history
                comments = doc.get('comment_history', [])
                if comments:
                    latest_comment = comments[0]  # V2 API returns sorted by most recent first
                    if latest_comment.get('type') == 'Review Request':
                        st.markdown(f"**Author's Message:** _{latest_comment['comment'][:100]}{'...' if len(latest_comment['comment']) > 100 else ''}_")
                
                doc_id = doc.get('id', doc.get('document_id'))
                if st.button("👀 Review", key=f"review_{doc_id}"):
                    st.session_state.selected_review_doc = doc
                    st.rerun()

with col2:
    st.subheader("📄 Review Editor")
    
    if "selected_review_doc" in st.session_state:
        doc = st.session_state.selected_review_doc
        
        # Document header with clean layout
        doc_name = doc.get('name', doc.get('document_name', 'Unknown Document'))
        st.markdown(f"**{doc_name}** | {doc['document_type'].replace('_', ' ').title()}")
        
        # Use V2 status format
        doc_state = doc.get('document_state', 'review_request')
        review_state = doc.get('review_state', 'under_review')
        st.markdown(f"**Author:** {doc['author']} | **Status:** {format_status_v2(doc_state, review_state)}", unsafe_allow_html=True)
        
        # Comment History (always displayed first)
        st.subheader("💬 Comment History")
        comments = doc.get('comment_history', doc.get('review_comments', []))
        display_comment_history(comments)
        
        # Document Content (read-only for reviewers)
        st.subheader("📄 Document Content")
        content = doc.get('content', '')
        if content:
            st.markdown(content)
        else:
            st.info("No content available")
        
        # Review Controls
        st.subheader("👨‍⚖️ Review Decision")
        
        reviewer_comment = st.text_area("Your Review Comment:", height=100, placeholder="Provide your review feedback...")
        
        # Action buttons
        col_r1, col_r2, col_r3 = st.columns([1, 1, 1])
        
        with col_r1:
            if st.button("⚠️ Needs Update", type="secondary", help="Request author to make changes"):
                if reviewer_comment.strip():
                    doc_id = doc.get('id', doc.get('document_id'))
                    result = submit_review(doc_id, reviewer_comment, "needs_update")
                    if result.get("success"):
                        st.success(result["message"])
                        del st.session_state.selected_review_doc
                        st.rerun()
                    else:
                        st.error(result.get("error", "Failed to submit review"))
                else:
                    st.error("Please provide a comment explaining what needs to be updated")
        
        with col_r2:
            if st.button("✅ Approved", type="primary", help="Approve the document"):
                if reviewer_comment.strip():
                    doc_id = doc.get('id', doc.get('document_id'))
                    result = submit_review(doc_id, reviewer_comment, "approved")
                    if result.get("success"):
                        st.success(result["message"])
                        del st.session_state.selected_review_doc
                        st.rerun()
                    else:
                        st.error(result.get("error", "Failed to submit review"))
                else:
                    st.error("Please provide a comment with your approval")
        
        with col_r3:
            if st.button("❌ Close"):
                del st.session_state.selected_review_doc
                st.rerun()
        
        # Help text
        st.caption("💡 **Tips:** Review the document content and comment history above. Provide clear, actionable feedback in your comment before making a decision.")
    
    else:
        st.info("Select a document from the review queue to start reviewing")
        
        # Show some helpful information
        st.markdown("""
        ### 📋 Review Process
        
        1. **Select** a document from the review queue
        2. **Read** the document content and comment history
        3. **Provide** constructive feedback in your comment
        4. **Choose** your decision:
           - ⚠️ **Needs Update**: Document requires changes
           - ✅ **Approved**: Document is ready for use
        
        Your review decision will be recorded in the comment history and the author will be notified.
        """)

# Quick refresh button
if st.button("🔄 Refresh Review Queue"):
    if "selected_review_doc" in st.session_state:
        del st.session_state.selected_review_doc
    st.rerun()