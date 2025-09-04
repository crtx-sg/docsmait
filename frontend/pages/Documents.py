# Simplified Document Management - V2
import streamlit as st
import requests
import pandas as pd
from streamlit_ace import st_ace
from auth_utils import get_auth_headers, get_current_user, setup_authenticated_sidebar, BACKEND_URL
from config import DATAFRAME_HEIGHT

st.set_page_config(page_title="📄 Documents", page_icon="📄", layout="wide")

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
    .revision-item {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .revision-current {
        border-left: 4px solid #198754;
        background-color: #d1e7dd;
    }
    .revision-old {
        border-left: 4px solid #6c757d;
    }
    .revision-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    .revision-meta {
        font-size: 0.9rem;
        color: #6c757d;
    }
</style>
""", unsafe_allow_html=True)

def get_documents_for_author(project_id):
    """Get all documents for current author using V2 API"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v2/projects/{project_id}/documents/author",
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            data = response.json()["documents"]
            return data
        else:
            return []
    except Exception as e:
        st.error(f"Error fetching documents: {e}")
        return []

def get_documents_for_reviewer(project_id):
    """Get documents assigned to current reviewer"""
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

def get_approved_documents(project_id):
    """Get all approved documents"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v2/projects/{project_id}/documents/approved",
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()["documents"]
        return []
    except Exception as e:
        st.error(f"Error fetching approved documents: {e}")
        return []

def submit_for_review(document_id, reviewer_id, comment):
    """Submit document for review using V2 API"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v2/documents/{document_id}/submit-for-review",
            params={
                "reviewer_id": reviewer_id,
                "comment": comment
            },
            headers=get_auth_headers()
        )
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

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

def get_document_revisions(document_id):
    """Get revision history for a document using V2 API"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v2/documents/{document_id}/revisions",
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()["revisions"]
        return []
    except Exception as e:
        st.error(f"Error fetching revisions: {e}")
        return []

def create_document_revision(document_id, content, comment=""):
    """Create a new revision for a document using V2 API"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v2/documents/{document_id}/revisions",
            params={
                "content": content,
                "comment": comment
            },
            headers=get_auth_headers()
        )
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_document_content(document_id, content, create_revision=True, comment=""):
    """Update document content with optional revision creation using V2 API"""
    try:
        response = requests.put(
            f"{BACKEND_URL}/api/v2/documents/{document_id}/content",
            params={
                "content": content,
                "create_revision": create_revision,
                "comment": comment
            },
            headers=get_auth_headers()
        )
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_project_members(project_id):
    """Get project members for reviewer selection"""
    try:
        
        # Get project details which should include members
        response = requests.get(
            f"{BACKEND_URL}/projects/{project_id}",
            headers=get_auth_headers()
        )
        
        
        if response.status_code == 200:
            project_data = response.json()
            if "members" in project_data:
                return project_data["members"]
        
        # Fallback: Get from the projects list (like in All Documents tab)
        projects = get_user_projects()
        selected_project = next((p for p in projects if p["id"] == project_id), None)
        
        if selected_project and selected_project.get("members"):
            return selected_project["members"]
        
        return []
    except Exception as e:
        st.error(f"Error fetching project members: {e}")
        return []

def format_status(document_state, review_state=None):
    """Format status with color - handles both V1 and V2 formats"""
    # Handle V2 format
    if review_state is not None:
        if document_state == "draft":
            return f'<span class="status-draft">📝 Draft</span>'
        elif document_state == "review_request" and review_state == "under_review":
            return f'<span class="status-review-request">📋 Under Review</span>'
        elif document_state == "needs_update":
            return f'<span class="status-needs-update">⚠️ Needs Update</span>'
        elif document_state == "approved":
            return f'<span class="status-approved">✅ Approved</span>'
    
    # Handle V1 format (backwards compatibility)
    status = document_state  # In V1, this is the status field
    if status == "draft":
        return f'<span class="status-draft">📝 Draft</span>'
    elif status == "request_review":
        return f'<span class="status-review-request">📋 Request Review</span>'
    elif status == "need_revision":
        return f'<span class="status-needs-update">⚠️ Need Revision</span>'
    elif status == "approved":
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

def get_document_types():
    """Get available document types"""
    fallback_types = [
        {"value": "planning_documents", "label": "Planning Documents", "description": "Project Plans, Quality Plans, Risk Assessments"},
        {"value": "process_documents", "label": "Process Documents", "description": "Procedures, Work Instructions, Process Maps"},
        {"value": "specifications", "label": "Specifications", "description": "Requirements, Technical Specifications, Design Documents"},
        {"value": "records", "label": "Records", "description": "Test Reports, Audit Reports, Meeting Minutes"},
        {"value": "templates", "label": "Templates", "description": "Forms, Checklists, Report Templates"},
        {"value": "policies", "label": "Policies", "description": "Quality Policy, Environmental Policy, Safety Policy"},
        {"value": "manuals", "label": "Manuals", "description": "User Manuals, Operation Manuals, Maintenance Guides"}
    ]
    
    try:
        response = requests.get(f"{BACKEND_URL}/templates/document-types", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return fallback_types
    except Exception as e:
        return fallback_types

def get_templates(document_type=None, status=None):
    """Get available templates for document creation"""
    try:
        params = {}
        if status:
            params["status"] = status
        if document_type:
            params["document_type"] = document_type
        
        response = requests.get(f"{BACKEND_URL}/templates", params=params, headers=get_auth_headers())
        if response.status_code == 200:
            templates = response.json()
            if not status:
                return [t for t in templates if t.get("status") in ["active", "approved"]]
            return templates
        return []
    except Exception as e:
        st.error(f"Error fetching templates: {e}")
        return []

def get_project_documents(project_id, status=None, document_type=None, created_by=None):
    """Get documents for a project"""
    try:
        params = {}
        if status:
            params["status"] = status
        if document_type:
            params["document_type"] = document_type
        if created_by:
            params["created_by"] = created_by
        
        response = requests.get(
            f"{BACKEND_URL}/projects/{project_id}/documents",
            params=params,
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching documents: {e}")
        return []

def get_document_by_id(document_id):
    """Get document details"""
    try:
        response = requests.get(f"{BACKEND_URL}/documents/{document_id}", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching document: {e}")
        return None

def create_document(project_id, document_data):
    """Create a new document"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/projects/{project_id}/documents",
            json=document_data,
            headers=get_auth_headers()
        )
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 500


# Main interface
st.title("📄 Documents - Simplified Workflow")

# Get user info and project
user_info = get_current_user()
if not user_info:
    st.error("Please log in to access documents")
    st.stop()


# Setup authenticated sidebar
setup_authenticated_sidebar()

# Project selection
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

projects = get_user_projects()
if not projects:
    st.warning("⚠️ You are not a member of any projects. Please join or create a project to manage documents.")
    st.stop()

st.subheader("📋 Select Project")
project_options = {p["name"]: p["id"] for p in projects}
selected_project_name = st.selectbox(
    "Project",
    options=list(project_options.keys()),
    key="selected_project_v2"
)

if not selected_project_name:
    st.info("Please select a project to view documents.")
    st.stop()

project_id = project_options[selected_project_name]

# Check if user came from Reviews menu
show_reviews_notice = False
if st.session_state.get("show_reviews_tab"):
    # Clear the flag and show notice
    del st.session_state.show_reviews_tab
    show_reviews_notice = True

if show_reviews_notice:
    st.info("📋 **Looking for Reviews?** You can find document reviews in the **'My Documents' → 'Reviews'** tab below, or use the **'All Documents'** tab to review any project document.")

# Tabs for different operations
tab1, tab2, tab3, tab4 = st.tabs(["📋 My Documents", "➕ Create Document", "📄 All Documents", "📚 Revision History"])

with tab1:
    st.subheader("📝 My Documents")
    st.caption("Documents you created")
    
    # Create sub-tabs for better organization
    author_tab1, author_tab2, author_tab3 = st.tabs(["📝 My Documents", "📋 Reviews", "✅ Approved"])
    
    with author_tab1:
        documents = get_documents_for_author(project_id)
        
        if not documents:
            st.info("No documents found")
        else:
            # Left-right panel layout
            my_col1, my_col2 = st.columns([2, 3])
            
            with my_col1:
                st.markdown("### My Documents List")
                
                # Prepare data for st.dataframe
                grid_data = []
                for doc in documents:
                    # Get reviewer names
                    reviewers = ""
                    if doc.get('reviewers'):
                        reviewer_names = [r['username'] for r in doc['reviewers']]
                        reviewers = ', '.join(reviewer_names)
                    
                    grid_row = {
                        'id': doc['id'],
                        'name': doc['name'],
                        'document_type': doc['document_type'],
                        'status': doc.get('document_state', doc.get('status', 'unknown')),
                        'reviewers': reviewers,
                        'updated_at': doc['updated_at'][:10] if doc['updated_at'] else 'N/A',
                        'full_doc_data': doc  # Store full doc data for editing
                    }
                    grid_data.append(grid_row)
                
                # Create DataFrame for documents - show only requested columns  
                df_data = []
                for row in grid_data:
                    df_row = {
                        'Document Name': row['name'],
                        'Status': row['status'].replace('_', ' ').title(),
                        'Reviewers': row['reviewers']
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
                    height=400
                )
                
                st.caption("💡 Select a row to edit the document")
                
                # Handle document selection for editing
                if selected_indices and len(selected_indices.selection.rows) > 0:
                    selected_idx = selected_indices.selection.rows[0]
                    full_doc = grid_data[selected_idx]['full_doc_data']
                    # Only rerun if this is a different document
                    if (st.session_state.get('selected_doc', {}).get('id') != full_doc.get('id') or 
                        st.session_state.get('mode') != "author"):
                        st.session_state.selected_doc = full_doc
                        st.session_state.mode = "author"
                        st.rerun()
            
            with my_col2:
                st.markdown("### Document Editor")
                
                if "selected_doc" in st.session_state and "mode" in st.session_state and st.session_state.mode == "author":
                    doc = st.session_state.selected_doc
                    
                    # Add refresh button to get latest document data
                    col_refresh1, col_refresh2 = st.columns([4, 1])
                    with col_refresh2:
                        if st.button("🔄 Refresh", key="refresh_doc", help="Refresh document data"):
                            # Force refresh by getting latest document data
                            fresh_docs = get_documents_for_author(project_id)
                            fresh_doc = next((d for d in fresh_docs if d['id'] == doc['id']), None)
                            if fresh_doc:
                                st.session_state.selected_doc = fresh_doc
                                doc = fresh_doc
                            st.rerun()
                    
                    with col_refresh1:
                        # Document header
                        st.markdown(f"**{doc['name']}** | {doc['document_type'].replace('_', ' ').title()}")
                        # Handle both V1 (status) and V2 (document_state, review_state) formats
                        doc_state = doc.get('document_state', doc.get('status', 'unknown'))
                        review_state = doc.get('review_state')
                        st.markdown(f"**Status:** {format_status(doc_state, review_state)}", unsafe_allow_html=True)
                    
                    # Comment History - handle both V1 and V2 formats
                    st.subheader("💬 Comment History")
                    comments = doc.get('comment_history', doc.get('review_comments', []))
                    display_comment_history(comments)
                    
                    st.divider()
                    
                    # Document Content Editor
                    st.subheader("📄 Document Content")
                    content = st_ace(
                        value=doc['content'],
                        language='markdown',
                        theme='github',
                        height=300,
                        key=f"editor_my_{doc['id']}"
                    )
                    
                    # Save Draft functionality
                    if content != doc['content']:
                        st.info("📝 Content has been modified")
                        save_col1, save_col2 = st.columns([3, 1])
                        
                        with save_col1:
                            revision_comment = st.text_input(
                                "Revision Comment (optional):",
                                placeholder="Describe the changes made...",
                                key=f"revision_comment_{doc['id']}"
                            )
                        
                        with save_col2:
                            create_revision_option = st.checkbox(
                                "Create Revision",
                                value=True,
                                help="Create a new revision to track changes",
                                key=f"create_revision_{doc['id']}"
                            )
                        
                        # Save buttons
                        save_button_col1, save_button_col2 = st.columns([1, 1])
                        
                        with save_button_col1:
                            if st.button("💾 Save Draft", key=f"save_draft_{doc['id']}", type="primary"):
                                result = update_document_content(
                                    doc['id'], 
                                    content, 
                                    create_revision=create_revision_option,
                                    comment=revision_comment
                                )
                                
                                if result.get("success"):
                                    st.success(result["message"])
                                    # Refresh document data
                                    fresh_docs = get_documents_for_author(project_id)
                                    fresh_doc = next((d for d in fresh_docs if d['id'] == doc['id']), None)
                                    if fresh_doc:
                                        st.session_state.selected_doc = fresh_doc
                                    st.rerun()
                                else:
                                    st.error(f"Failed to save: {result.get('error', 'Unknown error')}")
                        
                        with save_button_col2:
                            if st.button("🔄 Revert Changes", key=f"revert_{doc['id']}"):
                                # Force refresh to revert changes
                                fresh_docs = get_documents_for_author(project_id)
                                fresh_doc = next((d for d in fresh_docs if d['id'] == doc['id']), None)
                                if fresh_doc:
                                    st.session_state.selected_doc = fresh_doc
                                st.rerun()
                    
                    # Author Actions - handle both V1 and V2 formats
                    doc_status = doc.get('document_state', doc.get('status', 'unknown'))
                    if doc_status in ['draft', 'needs_update', 'need_revision']:
                        st.subheader("📝 Author Actions")
                        
                        col_a, col_b = st.columns([2, 1])
                        with col_a:
                            # Get project members for reviewer selection
                            members = get_project_members(project_id)
                            reviewer_options = [m for m in members if m['user_id'] != user_info['id']]
                            
                            if reviewer_options:
                                selected_reviewer = st.selectbox(
                                    "Select Reviewer:",
                                    options=[(m['user_id'], m['username']) for m in reviewer_options],
                                    format_func=lambda x: x[1]
                                )
                                
                                author_comment = st.text_area("Comment for Reviewer:", height=100)
                                
                                if st.button("📋 Submit for Review", type="primary"):
                                    if author_comment.strip():
                                        st.info(f"Submitting document '{doc['name']}' to reviewer ID {selected_reviewer[0]} with comment: {author_comment[:50]}...")
                                        result = submit_for_review(doc['id'], selected_reviewer[0], author_comment)
                                        if result.get("success"):
                                            st.success(result["message"])
                                            # Refresh document data to show updated comment history
                                            fresh_docs = get_documents_for_author(project_id)
                                            fresh_doc = next((d for d in fresh_docs if d['id'] == doc['id']), None)
                                            if fresh_doc:
                                                st.session_state.selected_doc = fresh_doc
                                            # Clear any cached data to force refresh
                                            if "documents_cache" in st.session_state:
                                                del st.session_state.documents_cache
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to submit: {result.get('error', 'Unknown error')}")
                                    else:
                                        st.error("Please provide a comment for the reviewer")
                            else:
                                st.info("No other project members available as reviewers")
                        
                        with col_b:
                            if st.button("❌ Close", key="close_editable_doc"):
                                if 'selected_doc' in st.session_state:
                                    del st.session_state.selected_doc
                                if 'mode' in st.session_state:
                                    del st.session_state.mode
                                st.rerun()
                    else:
                        st.info(f"Document is currently {doc_status.replace('_', ' ')}")
                        if st.button("❌ Close", key="close_readonly_doc"):
                            if 'selected_doc' in st.session_state:
                                del st.session_state.selected_doc
                            if 'mode' in st.session_state:
                                del st.session_state.mode
                            st.rerun()
                else:
                    st.info("Select a document from the left panel to edit")
    
    with author_tab2:
        review_docs = get_documents_for_reviewer(project_id)
        
        if not review_docs:
            st.info("No documents to review")
        else:
            # Left-right panel layout for reviews
            review_col1, review_col2 = st.columns([2, 3])
            
            with review_col1:
                st.markdown("### Review Queue")
                st.caption(f"📄 {len(review_docs)} document(s) pending review")
                
                # Prepare review queue data for st.dataframe
                review_grid_data = []
                for doc in review_docs:
                    # Get latest comment from author
                    author_message = ""
                    if doc.get('comment_history'):
                        latest_comment = doc['comment_history'][0]
                        if latest_comment['type'] == 'Review Request':
                            author_message = latest_comment['comment'][:100] + ('...' if len(latest_comment['comment']) > 100 else '')
                    
                    review_row = {
                        'id': doc['id'],
                        'name': doc['name'],
                        'document_type': doc['document_type'],
                        'author': doc['author'],
                        'status': doc.get('document_state', doc.get('status', 'unknown')),
                        'submitted': doc['updated_at'][:10] if doc['updated_at'] else 'N/A',
                        'author_message': author_message,
                        'full_doc_data': doc  # Store full doc data for reviewing
                    }
                    review_grid_data.append(review_row)
                
                # Create DataFrame for review queue
                review_df_data = []
                for row in review_grid_data:
                    review_df_row = {
                        'Document Name': row['name'],
                        'Type': row['document_type'].replace('_', ' ').title(),
                        'Author': row['author'],
                        'Status': row['status'].replace('_', ' ').title(),
                        'Submitted': row['submitted'],
                        'Message': row['author_message'][:50] + "..." if len(row['author_message']) > 50 else row['author_message']
                    }
                    review_df_data.append(review_df_row)
                
                review_df = pd.DataFrame(review_df_data)
                
                # Display with selection capability
                review_selected_indices = st.dataframe(
                    review_df,
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun", 
                    selection_mode="single-row",
                    height=350
                )
                
                st.caption("💡 Select a row to review the document")
                
                # Handle review queue selection
                if review_selected_indices and len(review_selected_indices.selection.rows) > 0:
                    selected_idx = review_selected_indices.selection.rows[0]
                    full_doc = review_grid_data[selected_idx]['full_doc_data']
                    # Only rerun if this is a different document
                    if (st.session_state.get('selected_review_doc', {}).get('id') != full_doc.get('id') or 
                        st.session_state.get('mode') != "reviewer"):
                        st.session_state.selected_review_doc = full_doc
                        st.session_state.mode = "reviewer"
                        st.rerun()
            
            with review_col2:
                st.markdown("### Review Editor")
                
                if "selected_review_doc" in st.session_state and st.session_state.mode == "reviewer":
                    doc = st.session_state.selected_review_doc
                    
                    # Document header
                    st.markdown(f"**{doc['name']}** | {doc['document_type'].replace('_', ' ').title()}")
                    doc_state = doc.get('document_state', doc.get('status', 'unknown'))
                    review_state = doc.get('review_state')
                    st.markdown(f"**Author:** {doc['author']} | **Status:** {format_status(doc_state, review_state)}", unsafe_allow_html=True)
                    
                    # Comment History
                    st.subheader("💬 Comment History")
                    display_comment_history(doc.get('comment_history', []))
                    
                    st.divider()
                    
                    # Document Content (read-only for reviewers)
                    st.subheader("📄 Document Content")
                    st.markdown(doc['content'])
                    
                    # Review Controls
                    st.subheader("👨‍⚖️ Review Decision")
                    
                    reviewer_comment = st.text_area("Your Review Comment:", height=100, placeholder="Provide your review feedback...")
                    
                    col_r1, col_r2, col_r3 = st.columns([1, 1, 1])
                    
                    with col_r1:
                        if st.button("⚠️ Needs Update", type="secondary"):
                            if reviewer_comment.strip():
                                result = submit_review(doc['id'], reviewer_comment, "needs_update")
                                if result.get("success"):
                                    st.success(result["message"])
                                    del st.session_state.selected_review_doc
                                    st.rerun()
                                else:
                                    st.error(result.get("error", "Failed to submit review"))
                            else:
                                st.error("Please provide a comment explaining what needs to be updated")
                    
                    with col_r2:
                        if st.button("✅ Approved", type="primary"):
                            if reviewer_comment.strip():
                                result = submit_review(doc['id'], reviewer_comment, "approved")
                                if result.get("success"):
                                    st.success(result["message"])
                                    del st.session_state.selected_review_doc
                                    st.rerun()
                                else:
                                    st.error(result.get("error", "Failed to submit review"))
                            else:
                                st.error("Please provide a comment with your approval")
                    
                    with col_r3:
                        if st.button("❌ Close", key="close_review_doc"):
                            del st.session_state.selected_review_doc
                            st.rerun()
                else:
                    st.info("Select a document from the review queue to start reviewing")
    
    with author_tab3:
        approved_docs = get_approved_documents(project_id)
        
        if not approved_docs:
            st.info("No approved documents")
        else:
            st.markdown("### Approved Documents")
            
            # Prepare data for st.dataframe
            approved_grid_data = []
            for doc in approved_docs:
                approved_row = {
                    'name': doc['name'],
                    'document_type': doc['document_type'],
                    'author': doc['author'],
                    'status': 'approved',
                    'approved_date': doc['updated_at'][:10] if doc['updated_at'] else 'N/A',
                    'full_doc_data': doc
                }
                approved_grid_data.append(approved_row)
            
            # Create DataFrame for approved documents
            approved_df_data = []
            for row in approved_grid_data:
                approved_df_row = {
                    'Document Name': row['name'],
                    'Type': row['document_type'].replace('_', ' ').title(),
                    'Author': row['author'],
                    'Status': row['status'].title(),
                    'Approved Date': row['approved_date']
                }
                approved_df_data.append(approved_df_row)
            
            approved_df = pd.DataFrame(approved_df_data)
            
            # Display with selection capability
            approved_selected_indices = st.dataframe(
                approved_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                height=300
            )
            
            st.caption("💡 Select a row to view the approved document")
            
            # Handle approved document selection
            if approved_selected_indices and len(approved_selected_indices.selection.rows) > 0:
                selected_idx = approved_selected_indices.selection.rows[0]
                full_doc = approved_grid_data[selected_idx]['full_doc_data']
                # Only rerun if this is a different document
                if (st.session_state.get('selected_doc', {}).get('id') != full_doc.get('id') or 
                    st.session_state.get('mode') != "view_only"):
                    st.session_state.selected_doc = full_doc
                    st.session_state.mode = "view_only"
                    st.rerun()

with tab2:
    st.subheader("➕ Create Document")
    
    # Document type and creation method selection
    col1, col2 = st.columns([1, 2])
    
    with col1:
        document_types = get_document_types()
        document_type = st.selectbox(
            "Document Type",
            options=[dt['value'] for dt in document_types],
            format_func=lambda x: next((dt['label'] for dt in document_types if dt['value'] == x), x),
            key="create_document_type"
        )
    
    with col2:
        creation_method = st.radio(
            "Creation Method",
            ["Blank Document", "Using Template", "From Previous Version"],
            horizontal=True,
            key="creation_method"
        )
    
    # Show document type description
    selected_doc_type = next((dt for dt in document_types if dt['value'] == document_type), None)
    if selected_doc_type:
        st.caption(f"📋 {selected_doc_type['label']}: {selected_doc_type['description']}")
    
    # Template/Document selection
    template_content = ""
    template_id = None
    
    if creation_method == "Blank Document":
        if "template_content_create" in st.session_state:
            del st.session_state.template_content_create
    
    elif creation_method == "Using Template":
        templates = get_templates(document_type)
        if templates:
            template_options = {t["name"]: t["id"] for t in templates}
            selected_template_name = st.selectbox(
                "Select Template",
                options=list(template_options.keys()),
                key="selected_template"
            )
            if selected_template_name:
                template_id = template_options[selected_template_name]
                selected_template = next(t for t in templates if t["id"] == template_id)
                template_content = selected_template["content"]
                st.session_state.template_content_create = template_content
                st.session_state.selected_template_id = template_id
                st.info(f"Template: {selected_template['name']} - {selected_template['description']}")
        else:
            st.warning("No templates available for this document type.")
    
    elif creation_method == "From Previous Version":
        all_docs = get_project_documents(project_id)
        if all_docs:
            doc_options = {f"{d['name']}": d["id"] for d in all_docs}
            selected_doc_name = st.selectbox(
                "Select Document to Copy",
                options=list(doc_options.keys()),
                key="selected_copy_doc"
            )
            if selected_doc_name:
                copy_doc_id = doc_options[selected_doc_name]
                copy_doc = get_document_by_id(copy_doc_id)
                if copy_doc:
                    template_content = copy_doc["content"]
                    st.session_state.template_content_create = template_content
                    st.info(f"Copying content from: {copy_doc['name']}")
        else:
            st.warning("No documents available to copy from.")
    
    with st.form("create_document_form"):
        name = st.text_input("Document Name", placeholder="Enter document name")
        
        st.subheader("📝 Document Content")
        
        initial_content = ""
        editor_key = "create_document_content"
        
        if st.session_state.get("template_content_create"):
            initial_content = st.session_state.template_content_create
            if st.session_state.get("selected_template_id"):
                editor_key = f"create_document_content_{st.session_state.selected_template_id}"
        
        content = st_ace(
            value=initial_content,
            language='markdown',
            theme='github',
            key=editor_key,
            height=300,
            auto_update=False,
            wrap=True
        )
        
        # Document status and workflow
        col_status, col_comment = st.columns([1, 2])
        with col_status:
            status = st.selectbox(
                "Document Status",
                ["draft", "request_review"],
                format_func=lambda x: x.replace('_', ' ').title(),
                key="document_status"
            )
        
        with col_comment:
            comment = ""
            if status != "draft":
                comment = st.text_input(
                    "Comment (required for non-draft)",
                    placeholder="Brief description...",
                    key="document_comment"
                )
        
        # Reviewer selection for request_review status
        reviewers = []
        if status == "request_review":
            project_members = get_project_members(project_id)
            st.write(f"🔍 DEBUG: Found {len(project_members)} project members")
            st.write(f"🔍 DEBUG: Current user ID: {user_info['id']}")
            for member in project_members:
                st.write(f"🔍 DEBUG: Member: {member}")
            
            # Filter out current user
            available_reviewers = [member for member in project_members if member["user_id"] != user_info["id"]]
            st.write(f"🔍 DEBUG: Available reviewers after filtering: {len(available_reviewers)}")
            
            if available_reviewers:
                reviewer_options = st.multiselect(
                    "👥 Select Reviewers",
                    options=[member["user_id"] for member in available_reviewers],
                    format_func=lambda x: next((member["username"] for member in available_reviewers if member["user_id"] == x), "Unknown"),
                    key="document_reviewers",
                    help="Choose team members to review this document"
                )
                reviewers = reviewer_options
            else:
                st.error("⚠️ No project members available for review (excluding yourself).")
                st.write(f"🔍 DEBUG: Total project members: {len(project_members)}, Current user filtered out: {user_info.get('username', 'Unknown')}")
        
        submitted = st.form_submit_button("🚀 Create Document", type="primary")
        
        if submitted:
            # Validation
            errors = []
            
            if not name or not name.strip():
                errors.append("Document name is required")
            
            if not content or not content.strip():
                errors.append("Document content is required")
            
            if status == "request_review" and not reviewers:
                errors.append("Please select at least one reviewer for review request")
            
            if status != "draft" and not comment.strip():
                errors.append("Comment is required for non-draft documents")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                document_data = {
                    "name": name,
                    "document_type": document_type,
                    "content": content,
                    "status": status,
                    "comment": comment if comment else None,
                    "reviewers": reviewers if reviewers else None,
                    "template_id": template_id if creation_method == "Using Template" else None
                }
                
                result, status_code = create_document(project_id, document_data)
                
                if status_code == 200:
                    st.success(f"Document '{name}' created successfully!")
                    # Clear form data
                    if "template_content_create" in st.session_state:
                        del st.session_state.template_content_create
                    if "selected_template_id" in st.session_state:
                        del st.session_state.selected_template_id
                    st.rerun()
                else:
                    st.error(f"Failed to create document: {result.get('error', 'Unknown error')}")

with tab3:
    st.subheader("📄 All Documents")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "draft", "request_review", "approved"],
            key="status_filter"
        )
    
    with col2:
        document_types = get_document_types()
        doc_type_options = ["All"] + [dt["value"] for dt in document_types]
        doc_type_labels = ["All"] + [dt["label"] for dt in document_types]
        doc_type_filter = st.selectbox(
            "Filter by Document Type",
            options=doc_type_options,
            format_func=lambda x: doc_type_labels[doc_type_options.index(x)] if x in doc_type_options else x,
            key="doc_type_filter"
        )
    
    with col3:
        projects = get_user_projects()
        selected_project = next(p for p in projects if p["id"] == project_id)
        author_filter = st.selectbox(
            "Filter by Author",
            ["All"] + [member["username"] for member in selected_project.get("members", [])],
            key="author_filter"
        )
    
    with col4:
        if st.button("🔄 Refresh", key="refresh_documents"):
            st.rerun()
    
    # Get documents with filters
    status = None if status_filter == "All" else status_filter
    document_type = None if doc_type_filter == "All" else doc_type_filter
    created_by = None
    if author_filter != "All":
        for member in selected_project.get("members", []):
            if member["username"] == author_filter:
                created_by = member["user_id"]
                break
    
    documents = get_project_documents(project_id, status, document_type, created_by)
    
    if not documents:
        st.info("No documents found with the current filters")
    else:
        st.markdown(f"**Found {len(documents)} documents**")
        
        # Split into two columns - document list on left, editor on right
        main_col1, main_col2 = st.columns([2, 3])
        
        with main_col1:
            st.markdown("### Documents List")
            
            # Prepare data for st.dataframe
            all_docs_grid_data = []
            for doc in documents:
                doc_status = doc.get('status', doc.get('document_state', 'unknown'))
                # Try multiple possible author field names
                author = (doc.get('created_by_username') or 
                         doc.get('author') or 
                         doc.get('created_by') or 
                         'Unknown')
                
                all_docs_row = {
                    'name': doc['name'],
                    'document_type': doc['document_type'],
                    'status': doc_status,
                    'author': author,
                    'created_at': doc['created_at'][:10] if doc['created_at'] else 'N/A',
                    'updated_at': doc['updated_at'][:10] if doc['updated_at'] else 'N/A',
                    'full_doc_data': doc
                }
                all_docs_grid_data.append(all_docs_row)
            
            # Create DataFrame for all documents
            all_docs_df_data = []
            for row in all_docs_grid_data:
                all_docs_df_row = {
                    'Document Name': row['name'],
                    'Type': row['document_type'].replace('_', ' ').title(),
                    'Status': row['status'].replace('_', ' ').title(),
                    'Author': row['author'],
                    'Updated': row['updated_at']
                }
                all_docs_df_data.append(all_docs_df_row)
            
            all_docs_df = pd.DataFrame(all_docs_df_data)
            
            # Display with selection capability
            all_docs_selected_indices = st.dataframe(
                all_docs_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                height=DATAFRAME_HEIGHT
            )
            
            st.caption("💡 Select a row to edit the document")
            
            # Handle all documents selection
            if all_docs_selected_indices and len(all_docs_selected_indices.selection.rows) > 0:
                selected_idx = all_docs_selected_indices.selection.rows[0]
                doc = all_docs_grid_data[selected_idx]['full_doc_data']
                # Only rerun if this is a different document
                if st.session_state.get('selected_all_doc', {}).get('id') != doc.get('id'):
                    # Get the full document data with comments from V2 API
                    full_docs = get_documents_for_author(project_id)
                    full_doc = next((d for d in full_docs if d['id'] == doc['id']), None)
                    if full_doc:
                        st.session_state.selected_all_doc = full_doc
                    else:
                        st.session_state.selected_all_doc = doc
                    st.rerun()
        
        with main_col2:
            st.markdown("### Document Editor")
            
            if "selected_all_doc" in st.session_state:
                doc = st.session_state.selected_all_doc
                mode = "author"  # Default mode for all documents tab
                
                # Document header
                st.markdown(f"**{doc['name']}** | {doc['document_type'].replace('_', ' ').title()}")
                doc_status = doc.get('status', doc.get('document_state', 'unknown'))
                # Try multiple possible author field names
                author = (doc.get('created_by_username') or 
                         doc.get('author') or 
                         doc.get('created_by') or 
                         'Unknown')
                st.markdown(f"**Author:** {author} | **Status:** {doc_status.replace('_', ' ').title()}")
                
                # Comment History - handle both V1 and V2 formats
                st.subheader("💬 Comment History")
                comments = doc.get('comment_history', doc.get('review_comments', []))
                if comments and len(comments) > 0:
                    display_comment_history(comments)
                else:
                    st.info("No comments yet")
                
                st.divider()
                
                # Document Content
                st.subheader("📄 Document Content")
                if mode == "view_only":
                    st.markdown(doc['content'])
                else:
                    # Show editor for edit mode
                    content = st_ace(
                        value=doc['content'],
                        language='markdown',
                        theme='github',
                        height=300,
                        key=f"editor_all_{doc['id']}"
                    )
                
                # Close button
                if st.button("❌ Close", key="close_all_editor"):
                    del st.session_state.selected_all_doc
                    st.rerun()
            else:
                st.info("Select a document from the left panel to view or edit")

with tab4:
    st.subheader("📚 Revision History")
    st.caption("View and compare document revisions")
    
    # Document selection for revision history
    all_docs = get_documents_for_author(project_id)
    approved_docs = get_approved_documents(project_id)
    
    # Combine and deduplicate documents
    combined_docs = {}
    for doc in all_docs + approved_docs:
        combined_docs[doc['id']] = doc
    
    available_docs = list(combined_docs.values())
    
    if not available_docs:
        st.info("No documents available for revision history")
    else:
        # Document selector
        col_doc, col_refresh = st.columns([4, 1])
        
        with col_doc:
            doc_options = {f"{doc['name']} ({doc.get('document_state', doc.get('status', 'unknown')).replace('_', ' ').title()})": doc['id'] 
                          for doc in available_docs}
            
            selected_doc_display = st.selectbox(
                "Select Document:",
                options=list(doc_options.keys()),
                key="revision_history_doc_selector"
            )
        
        with col_refresh:
            if st.button("🔄 Refresh", key="refresh_revisions"):
                st.rerun()
        
        if selected_doc_display:
            selected_doc_id = doc_options[selected_doc_display]
            selected_doc = combined_docs[selected_doc_id]
            
            # Get revision history
            revisions = get_document_revisions(selected_doc_id)
            
            if not revisions:
                st.info("No revision history available for this document")
            else:
                st.markdown(f"**Document:** {selected_doc['name']}")
                st.markdown(f"**Total Revisions:** {len(revisions)}")
                
                # Create columns for revision list and content viewer
                rev_col1, rev_col2 = st.columns([1, 2])
                
                with rev_col1:
                    st.subheader("📋 Revisions")
                    
                    # Prepare data for DataFrame
                    revision_grid_data = []
                    for revision in revisions:
                        created_at = revision.get('created_at', '')
                        date_str = created_at[:10] if created_at else 'N/A'
                        current_indicator = "🔴 Current" if revision['is_current'] else ""
                        
                        revision_row = {
                            'Revision': f"Rev {revision['revision_number']}",
                            'Date': date_str,
                            'Author': revision['created_by'],
                            'Status': revision['status'].replace('_', ' ').title(),
                            'Current': current_indicator,
                            'Comment': revision.get('comment', '')[:50] + '...' if revision.get('comment') and len(revision.get('comment', '')) > 50 else revision.get('comment', ''),
                            'full_revision_data': revision
                        }
                        revision_grid_data.append(revision_row)
                    
                    revision_df_data = []
                    for row in revision_grid_data:
                        revision_df_row = {
                            'Revision': row['Revision'],
                            'Date': row['Date'],
                            'Author': row['Author'],
                            'Status': row['Status'],
                            'Current': row['Current']
                        }
                        revision_df_data.append(revision_df_row)
                    
                    revision_df = pd.DataFrame(revision_df_data)
                    
                    # Display with selection capability
                    revision_selected_indices = st.dataframe(
                        revision_df,
                        use_container_width=True,
                        hide_index=True,
                        on_select="rerun",
                        selection_mode="single-row",
                        height=400
                    )
                    
                    st.caption("💡 Select a row to view revision details")
                    
                    # Handle revision selection
                    if revision_selected_indices and len(revision_selected_indices.selection.rows) > 0:
                        selected_idx = revision_selected_indices.selection.rows[0]
                        revision = revision_grid_data[selected_idx]['full_revision_data']
                        # Only update if different revision selected
                        if st.session_state.get('selected_revision_id') != revision.get('revision_id'):
                            st.session_state.selected_revision_id = revision.get('revision_id')
                            st.session_state.selected_revision = revision
                            st.rerun()
                
                with rev_col2:
                    st.subheader("📄 Revision Content")
                    
                    if "selected_revision" in st.session_state:
                        revision = st.session_state.selected_revision
                        
                        # Revision header
                        current_text = " (Current Version)" if revision['is_current'] else ""
                        st.markdown(f"**Revision {revision['revision_number']}{current_text}**")
                        
                        revision_info_col1, revision_info_col2 = st.columns(2)
                        with revision_info_col1:
                            created_at = revision.get('created_at', '')
                            date_str = created_at[:10] if created_at else 'N/A'
                            st.markdown(f"**Date:** {date_str}")
                            st.markdown(f"**Author:** {revision['created_by']}")
                        
                        with revision_info_col2:
                            st.markdown(f"**Status:** {revision['status'].replace('_', ' ').title()}")
                            if revision.get('comment'):
                                st.markdown(f"**Comment:** {revision['comment']}")
                        
                        st.divider()
                        
                        # Content display
                        if revision['content']:
                            # Show content in markdown format
                            st.markdown("**Content:**")
                            with st.container():
                                st.markdown(revision['content'])
                        else:
                            st.info("No content available for this revision")
                        
                        # Action buttons for current user if they own the document
                        if selected_doc.get('author') == user_info.get('username') or selected_doc.get('created_by') == user_info.get('id'):
                            st.divider()
                            st.subheader("🔧 Revision Actions")
                            
                            if not revision['is_current']:
                                # Option to restore this revision
                                if st.button("🔄 Restore This Revision", 
                                           key=f"restore_rev_{revision['revision_id']}", 
                                           help="Create a new revision with this content"):
                                    restore_comment = st.text_input(
                                        "Restoration Comment:",
                                        value=f"Restored from revision {revision['revision_number']}",
                                        key=f"restore_comment_{revision['revision_id']}"
                                    )
                                    
                                    if st.button("✅ Confirm Restore", key=f"confirm_restore_{revision['revision_id']}"):
                                        result = create_document_revision(
                                            selected_doc_id, 
                                            revision['content'], 
                                            restore_comment
                                        )
                                        
                                        if result.get("success"):
                                            st.success(f"Revision restored successfully as revision {result.get('revision_number')}")
                                            # Clear the selected revision and refresh
                                            if "selected_revision" in st.session_state:
                                                del st.session_state.selected_revision
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to restore revision: {result.get('error', 'Unknown error')}")
                            else:
                                st.info("This is the current revision")
                        
                        # Close button
                        if st.button("❌ Close Revision View", key="close_revision_view"):
                            if "selected_revision" in st.session_state:
                                del st.session_state.selected_revision
                            st.rerun()
                    else:
                        st.info("Select a revision from the left panel to view its content")
                        
                        # Show instructions
                        st.markdown("""
                        ### 📚 How to Use Revision History
                        
                        1. **View Revisions**: Click on any revision in the left panel to see its content
                        2. **Current Revision**: The current revision is highlighted in green
                        3. **Compare Changes**: View different revisions to see how the document evolved
                        4. **Restore Revision**: Document authors can restore any previous revision
                        
                        📝 **Note**: Revisions are automatically created when significant changes are made to documents.
                        """)

