# Reviews Page - Focused on Review Functionality
import streamlit as st
import requests
import pandas as pd
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
        
        # Prepare data for st.dataframe
        grid_data = []
        for doc in review_docs:
            # Get latest comment for display
            comments = doc.get('comment_history', [])
            latest_comment = ""
            if comments:
                comment = comments[0]  # V2 API returns sorted by most recent first
                if comment.get('type') == 'Review Request':
                    latest_comment = comment['comment'][:100] + ('...' if len(comment['comment']) > 100 else '')
            
            grid_row = {
                'id': doc.get('id', doc.get('document_id')),
                'name': doc.get('name', doc.get('document_name', 'Unknown Document')),
                'document_type': doc['document_type'],
                'author': doc['author'],
                'status': doc.get('document_state', 'review_request'),
                'submitted': doc.get('updated_at', doc.get('submitted_at', 'N/A'))[:10] if doc.get('updated_at', doc.get('submitted_at', 'N/A')) != 'N/A' else 'N/A',
                'author_message': latest_comment,
                'full_doc_data': doc  # Store full doc data for selection
            }
            grid_data.append(grid_row)
        
        # Create DataFrame
        df_data = []
        for row in grid_data:
            df_row = {
                'Document Name': row['name'],
                'Type': row['document_type'].replace('_', ' ').title(),
                'Author': row['author'],
                'Status': row['status'].replace('_', ' ').title(),
                'Submitted': row['submitted'],
                'Author Message': row['author_message'][:50] + "..." if len(row['author_message']) > 50 else row['author_message']
            }
            df_data.append(df_row)
        
        df = pd.DataFrame(df_data)
        
        # Display with selection capability
        selected_indices = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            height=300
        )
        
        st.caption("💡 Select a row to review the document")
        
        # Handle selection
        if selected_indices and len(selected_indices.selection.rows) > 0:
            selected_idx = selected_indices.selection.rows[0]
            full_doc = grid_data[selected_idx]['full_doc_data']
            # Only rerun if this is a different document
            if st.session_state.get('selected_review_doc', {}).get('id') != full_doc.get('id'):
                st.session_state.selected_review_doc = full_doc
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
            # Show document in readonly markdown editor
            st_ace(
                value=content,
                language='markdown',
                theme='github',
                height=400,
                key=f"review_editor_{doc.get('id', doc.get('document_id'))}",
                read_only=True,
                wrap=True,
                font_size=14
            )
        else:
            st.info("No content available")
        
        # Review Controls
        st.subheader("👨‍⚖️ Review Decision")
        
        # Review form
        col_comment, col_actions = st.columns([2, 1])
        
        with col_comment:
            reviewer_comment = st.text_area("Your Review Comment:", height=100, placeholder="Provide your review feedback...")
        
        with col_actions:
            # Document Next State dropdown
            st.write("**Document Next State:**")
            next_state = st.selectbox(
                "Choose outcome:",
                options=[
                    ("needs_update", "⚠️ Needs Update"),
                    ("approved", "✅ Approved")
                ],
                format_func=lambda x: x[1],
                key=f"next_state_{doc.get('id', doc.get('document_id'))}"
            )
            
            st.write("")  # Add some spacing
            
            # Action buttons
            col_submit, col_close = st.columns(2)
            
            with col_submit:
                if st.button("📋 Submit Review", type="primary"):
                    if reviewer_comment.strip():
                        doc_id = doc.get('id', doc.get('document_id'))
                        result = submit_review(doc_id, reviewer_comment, next_state[0])
                        if result.get("success"):
                            st.success(result["message"])
                            del st.session_state.selected_review_doc
                            st.rerun()
                        else:
                            st.error(result.get("error", "Failed to submit review"))
                    else:
                        st.error("Please provide a review comment")
            
            with col_close:
                if st.button("❌ Close", key="close_review_editor"):
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