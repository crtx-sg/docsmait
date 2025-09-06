# Simplified Document Management - V2
import streamlit as st
import requests
import pandas as pd
import base64
import markdown
from datetime import datetime
from streamlit_ace import st_ace
from auth_utils import get_auth_headers, get_current_user, setup_authenticated_sidebar, BACKEND_URL
from config import DATAFRAME_HEIGHT, KB_REQUEST_TIMEOUT, MAX_CHAT_RESPONSES_PER_SESSION, MAX_CHAT_RESPONSE_LENGTH, KB_CHAT_REQUEST_TIMEOUT, PDF_GENERATION_TIMEOUT

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

def manage_chat_response_limits(chat_response_key, new_response):
    """
    Manage chat response storage limits to prevent excessive memory usage.
    
    Args:
        chat_response_key: The session state key for storing chat responses
        new_response: The new response entry to add
        
    Returns:
        None - modifies session state in place
    """
    # Initialize chat responses if not exists
    if chat_response_key not in st.session_state:
        st.session_state[chat_response_key] = []
    
    # Truncate response text if too long
    if 'response' in new_response and len(new_response['response']) > MAX_CHAT_RESPONSE_LENGTH:
        new_response['response'] = new_response['response'][:MAX_CHAT_RESPONSE_LENGTH] + "\n\n[Response truncated due to length limit]"
    
    # Add new response
    st.session_state[chat_response_key].append(new_response)
    
    # Enforce maximum number of responses per session
    if len(st.session_state[chat_response_key]) > MAX_CHAT_RESPONSES_PER_SESSION:
        # Remove oldest responses to maintain limit
        st.session_state[chat_response_key] = st.session_state[chat_response_key][-MAX_CHAT_RESPONSES_PER_SESSION:]

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

def get_document_reviewers_from_data(doc_data):
    """Get reviewers for a document from the document data itself"""
    try:
        # Check if reviewers are included in the document data
        if 'reviewers' in doc_data:
            reviewers = doc_data['reviewers']
            if isinstance(reviewers, list) and reviewers:
                # If reviewers is a list of user objects or names
                reviewer_names = []
                for reviewer in reviewers:
                    if isinstance(reviewer, dict):
                        reviewer_names.append(reviewer.get('username', reviewer.get('name', 'Unknown')))
                    else:
                        reviewer_names.append(str(reviewer))
                return ", ".join(reviewer_names)
            elif isinstance(reviewers, str) and reviewers.strip():
                return reviewers
        
        # Check if there are any reviewer-related fields
        reviewer_fields = ['current_reviewer', 'assigned_reviewers', 'current_reviewers', 'reviewer_usernames']
        for field in reviewer_fields:
            if field in doc_data and doc_data[field]:
                return str(doc_data[field])
        
        return "None"
    except Exception as e:
        return "None"

def submit_for_review(document_id, reviewer_id, comment):
    """Submit document for review using V2 API"""
    try:
        url = f"{BACKEND_URL}/api/v2/documents/{document_id}/submit-for-review"
        params = {
            "reviewer_id": reviewer_id,
            "comment": comment
        }
        
        response = requests.post(url, params=params, headers=get_auth_headers())
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
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
        # Use the project details endpoint which includes full member data
        response = requests.get(
            f"{BACKEND_URL}/projects/{project_id}",
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            project_data = response.json()
            if "members" in project_data:
                members = project_data["members"]
                # Members already come in the correct format from backend
                return members
        
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
    """Display comment history as a dataframe - handles both V1 and V2 formats"""
    if not comments:
        st.info("No comments yet")
        return
    
    # Prepare data for dataframe
    comment_data = []
    for comment in comments:
        # Handle both V1 API format (timestamp, commenter) and V2 API format (date_time, user)
        timestamp = comment.get("timestamp") or comment.get("date_time", "")
        
        # Extract date and time separately
        if timestamp:
            try:
                # Handle both full timestamp and date-only formats
                if 'T' in timestamp:
                    date_part = timestamp.split('T')[0]
                    time_part = timestamp.split('T')[1][:8] if len(timestamp.split('T')) > 1 else "00:00:00"
                else:
                    date_part = timestamp[:10] if len(timestamp) >= 10 else timestamp
                    time_part = timestamp[11:19] if len(timestamp) > 11 else "00:00:00"
            except:
                date_part = timestamp[:10] if timestamp else "N/A"
                time_part = timestamp[11:19] if len(timestamp) > 11 else "00:00:00"
        else:
            date_part = "N/A"
            time_part = "00:00:00"
        
        # Handle different type formats between V1 and V2
        comment_type = comment.get("type", "Comment")
        if comment_type:
            comment_type = comment_type.replace('_', ' ').title()
        
        user = comment.get("commenter") or comment.get("user", "Unknown")
        text = comment.get("comment", "")
        
        comment_data.append({
            "Date": date_part,
            "Time": time_part,
            "Status": comment_type,
            "User": user,
            "Comment": text
        })
    
    # Create and display dataframe
    if comment_data:
        comment_df = pd.DataFrame(comment_data)
        st.dataframe(
            comment_df,
            use_container_width=True,
            hide_index=True,
            height=min(300, len(comment_data) * 35 + 50)  # Dynamic height based on number of comments
        )
    else:
        st.info("No comments yet")

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
            f"{BACKEND_URL}/api/v2/projects/{project_id}/documents/all",
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
    """Get document details using V2 API"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v2/documents/{document_id}", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching document: {e}")
        return None

def create_document(project_id, document_data):
    """Create a new document using V2 API with optional review workflow"""
    try:
        # Step 1: Create the basic document
        response = requests.post(
            f"{BACKEND_URL}/api/v2/documents",
            params={
                "name": document_data["name"],
                "document_type": document_data["document_type"],
                "content": document_data["content"],
                "project_id": project_id
            },
            headers=get_auth_headers()
        )
        
        if response.status_code != 200:
            return response.json(), response.status_code
            
        result = response.json()
        
        # Step 2: If status is request_review, submit for review
        if document_data.get("status") == "request_review" and document_data.get("reviewers"):
            document_id = result.get("document_id")
            if document_id:
                # Submit for review to the first reviewer
                reviewer_id = document_data["reviewers"][0]
                comment = document_data.get("comment", "Document submitted for review")
                
                review_result = submit_for_review(document_id, reviewer_id, comment)
                
                if not review_result.get("success"):
                    st.warning(f"Document created but review submission failed: {review_result.get('error')}")
        
        return result, response.status_code
        
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
tab1, tab2, tab3 = st.tabs(["➕ Create Document", "📋 My Documents", "📄 All Documents"])

with tab1:
    st.subheader("➕ Create New Document")
    st.caption("Create a new document in the project")
    
    # Document type and creation method selection
    col1, col2 = st.columns([1, 2])
    
    with col1:
        document_types = get_document_types()
        document_type = st.selectbox(
            "Document Type",
            options=[dt['value'] for dt in document_types],
            format_func=lambda x: next(dt['label'] for dt in document_types if dt['value'] == x),
            key="create_document_type"
        )
    
    with col2:
        creation_method = st.radio(
            "Creation Method",
            ["📝 Create from Scratch", "📄 Create from Template"],
            key="creation_method"
        )
    
    # Show document type description
    selected_doc_type = next((dt for dt in document_types if dt['value'] == document_type), None)
    if selected_doc_type:
        st.caption(f"📋 {selected_doc_type['label']}: {selected_doc_type['description']}")
    
    # Template/Document selection
    template_content = ""
    template_id = None
    
    if creation_method == "📝 Create from Scratch":
        if "template_content_create" in st.session_state:
            del st.session_state.template_content_create
    
    elif creation_method == "📄 Create from Template":
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
    
    # Document Name input (outside form for live updates)
    name = st.text_input("Document Name", placeholder="Enter document name", key="doc_name_input")
    
    st.subheader("📝 Document Content")
    
    # Initialize session state for mutually exclusive options
    if "create_preview_mode" not in st.session_state:
        st.session_state.create_preview_mode = True
    if "create_chat_mode" not in st.session_state:
        st.session_state.create_chat_mode = False
    
    # Add mutually exclusive options for preview or chat (outside form)
    col_option1, col_option2 = st.columns(2)
    with col_option1:
        preview_enabled = st.checkbox(
            "👁️ Enable Live Preview", 
            value=st.session_state.create_preview_mode, 
            help="Show HTML preview alongside markdown editor", 
            key="enable_preview_create"
        )
    with col_option2:
        chat_enabled = st.checkbox(
            "💬 Chat with Knowledge Base", 
            value=st.session_state.create_chat_mode, 
            help="Chat with AI using Knowledge Base context", 
            key="enable_chat_create"
        )
    
    # Update session state and handle mutual exclusivity
    if preview_enabled != st.session_state.create_preview_mode:
        st.session_state.create_preview_mode = preview_enabled
        if preview_enabled:
            st.session_state.create_chat_mode = False
            st.rerun()
    
    if chat_enabled != st.session_state.create_chat_mode:
        st.session_state.create_chat_mode = chat_enabled
        if chat_enabled:
            st.session_state.create_preview_mode = False
            st.rerun()
    
    # Ensure at least one option is always enabled
    if not st.session_state.create_preview_mode and not st.session_state.create_chat_mode:
        st.session_state.create_preview_mode = True
        st.rerun()
    
    # Use session state values for consistency
    preview_enabled = st.session_state.create_preview_mode
    chat_enabled = st.session_state.create_chat_mode
    
    # Content editor and preview (outside form for live updates)
    initial_content = ""
    editor_key = "create_document_content"
    
    if st.session_state.get("template_content_create"):
        initial_content = st.session_state.template_content_create
        if st.session_state.get("selected_template_id"):
            editor_key = f"create_document_content_{st.session_state.selected_template_id}"
    
    
    # Preserve existing content when toggling preview
    if editor_key in st.session_state and st.session_state[editor_key]:
        initial_content = st.session_state[editor_key]
    
    if preview_enabled:
        # Split view: Editor on left, Preview on right
        col_editor, col_preview = st.columns([1, 1])
        
        with col_editor:
            st.markdown("**Markdown Editor**")
            content = st_ace(
                value=initial_content,
                language='markdown',
                theme='github',
                key=editor_key,
                height=400,
                auto_update=True,  # Enable auto update for live preview
                wrap=True
            )
        
        with col_preview:
            col_preview_title, col_font_info = st.columns([2, 1])
            with col_preview_title:
                st.markdown("**HTML Preview**")
            with col_font_info:
                st.markdown("<div style='text-align: right;'><em>Font: Source Sans Pro, 14px, single-spacing</em></div>", unsafe_allow_html=True)
            if content and content.strip():
                try:
                    # Convert markdown to HTML
                    html_content = markdown.markdown(
                        content, 
                        extensions=['tables', 'fenced_code', 'codehilite', 'toc']
                    )
                    
                    # Display with single line spacing and font info
                    st.markdown(
                        f"""
                        <div style="
                            border: 1px solid #ddd; 
                            border-radius: 4px; 
                            padding: 16px; 
                            height: 400px; 
                            overflow-y: auto; 
                            background-color: #ffffff;
                            color: #262730;
                            font-family: 'Source Sans Pro', sans-serif;
                            font-size: 14px;
                            line-height: 1.2;
                        ">
                            <style>
                                .markdown-preview h1, .markdown-preview h2, .markdown-preview h3, 
                                .markdown-preview h4, .markdown-preview h5, .markdown-preview h6 {{
                                    color: #262730 !important;
                                    margin-top: 1rem;
                                    margin-bottom: 0.3rem;
                                    line-height: 1.2;
                                }}
                                .markdown-preview p {{
                                    color: #262730 !important;
                                    margin-bottom: 0.5rem;
                                    line-height: 1.2;
                                }}
                                .markdown-preview ul, .markdown-preview ol {{
                                    color: #262730 !important;
                                    margin-bottom: 0.5rem;
                                }}
                                .markdown-preview li {{
                                    color: #262730 !important;
                                    line-height: 1.2;
                                    margin-bottom: 0.2rem;
                                }}
                                .markdown-preview table {{
                                    border-collapse: collapse;
                                    width: 100%;
                                    margin-bottom: 0.5rem;
                                }}
                                .markdown-preview th, .markdown-preview td {{
                                    border: 1px solid #ddd;
                                    padding: 6px 8px;
                                    text-align: left;
                                    color: #262730 !important;
                                    line-height: 1.2;
                                }}
                                .markdown-preview th {{
                                    background-color: #f8f9fa;
                                }}
                                .markdown-preview code {{
                                    background-color: #f8f9fa;
                                    padding: 2px 4px;
                                    border-radius: 3px;
                                    color: #e91e63 !important;
                                    font-family: 'Monaco', 'Consolas', monospace;
                                    font-size: 13px;
                                }}
                                .markdown-preview pre {{
                                    background-color: #f8f9fa;
                                    padding: 8px;
                                    border-radius: 4px;
                                    border: 1px solid #e9ecef;
                                    overflow-x: auto;
                                    margin-bottom: 0.5rem;
                                    line-height: 1.2;
                                }}
                                .markdown-preview pre code {{
                                    background: none;
                                    padding: 0;
                                    color: #212529 !important;
                                    font-size: 13px;
                                }}
                                .markdown-preview a {{
                                    color: #1976d2 !important;
                                    text-decoration: underline;
                                }}
                                .markdown-preview blockquote {{
                                    border-left: 4px solid #1976d2;
                                    margin: 0 0 0.5rem 0;
                                    padding-left: 1rem;
                                    color: #555 !important;
                                    line-height: 1.2;
                                }}
                            </style>
                            <div class="markdown-preview">
                                {html_content}
                            </div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                except Exception as e:
                    st.error(f"Preview error: {str(e)}")
                    st.info("💡 Write some markdown content to see the preview")
            else:
                st.info("💡 Start typing markdown content to see the live preview")
    elif chat_enabled:
        # Split view: Editor on left, Chat on right
        col_editor, col_chat = st.columns([1, 1])
        
        with col_editor:
            st.markdown("**Markdown Editor**")
            content = st_ace(
                value=initial_content,
                language='markdown',
                theme='github',
                key=editor_key,
                height=400,
                auto_update=False,  # Disable auto update for chat mode
                wrap=True
            )
        
        with col_chat:
            st.markdown("**💬 Knowledge Base Chat**")
            
            # Chat Response Box (3/4 of editor height = 300px)
            chat_response_key = "create_doc_chat_responses"
            if chat_response_key not in st.session_state:
                st.session_state[chat_response_key] = []
            
            # Display chat responses in reverse chronological order (newest first)
            chat_responses = st.session_state[chat_response_key]
            chat_display = ""
            
            for i, response in enumerate(reversed(chat_responses)):
                timestamp = response.get('timestamp', 'Unknown time')
                query = response.get('query', 'No query')
                answer = response.get('response', 'No response')
                sources = response.get('sources', [])
                
                chat_display += f"""**Q ({timestamp}):** {query}

**A:** {answer}
"""
                if sources:
                    chat_display += f"\n**Sources:** {', '.join([s.get('filename', 'Unknown') for s in sources])}\n"
                
                chat_display += "\n" + "="*50 + "\n\n"
            
            # Add footer with usage and limits info
            if chat_display:
                current_count = len(chat_responses)
                chat_display += f"📊 **Chat Session:** {current_count}/{MAX_CHAT_RESPONSES_PER_SESSION} responses | Max response length: {MAX_CHAT_RESPONSE_LENGTH:,} chars"
            
            # Chat response display area
            st.text_area(
                "Chat History",
                value=chat_display if chat_display else "💡 Ask the Knowledge Base about your document...",
                height=300,
                disabled=True,
                key="create_chat_display",
                label_visibility="collapsed"
            )
            
            # Chat input area
            col_query, col_submit = st.columns([3, 1])
            with col_query:
                user_query = st.text_area(
                    "Ask the Knowledge Base",
                    height=80,
                    placeholder="Ask the Knowledge Base about your document...",
                    key="create_chat_query"
                )
            
            with col_submit:
                st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
                if st.button("🚀 Submit", key="submit_kb_query", type="primary"):
                    if user_query and user_query.strip():
                        # Get current document content for context (snapshot at query time)
                        document_context = st.session_state.get(editor_key, "")
                        
                        # Show loading spinner
                        with st.spinner("🤖 Querying Knowledge Base..."):
                            try:
                                # Create payload for the API
                                payload = {
                                    "query": user_query.strip(),
                                    "document_context": document_context if (document_context and document_context.strip()) else None,
                                    "collection_name": None,  # Use default
                                    "max_results": 5
                                }
                                
                                # Make API call to KB query with context endpoint
                                response = requests.post(
                                    f"{BACKEND_URL}/kb/query_with_context",
                                    json=payload,
                                    headers=get_auth_headers(),
                                    timeout=KB_CHAT_REQUEST_TIMEOUT
                                )
                                
                                if response.status_code == 200:
                                    result = response.json()
                                    
                                    # Add response to chat history
                                    chat_entry = {
                                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                                        'query': user_query.strip(),
                                        'response': result.get('response', 'No response received'),
                                        'sources': result.get('sources', []),
                                        'context_provided': result.get('document_context_provided', False),
                                        'kb_results': result.get('knowledge_base_results', 0)
                                    }
                                    
                                    manage_chat_response_limits(chat_response_key, chat_entry)
                                    
                                    # Clear the query input
                                    st.session_state.create_chat_query = ""
                                    
                                    # Success message
                                    st.success("✅ Response received!")
                                    st.rerun()
                                    
                                else:
                                    error_msg = response.json().get('detail', 'Failed to query Knowledge Base')
                                    st.error(f"❌ Error: {error_msg}")
                                    
                            except requests.exceptions.Timeout:
                                st.error("❌ Request timed out. Knowledge Base may be busy.")
                            except Exception as e:
                                st.error(f"❌ Failed to query Knowledge Base: {str(e)}")
                    else:
                        st.warning("⚠️ Please enter a query")
            
            # Clear chat history button
            if st.session_state[chat_response_key]:
                if st.button("🗑️ Clear Chat", key="clear_create_chat"):
                    st.session_state[chat_response_key] = []
                    st.rerun()
    else:
        # Full width editor (original behavior)
        content = st_ace(
            value=initial_content,
            language='markdown',
            theme='github',
            key=editor_key,
            height=400,
            auto_update=False,
            wrap=True
        )

    # Form for document creation settings
    with st.form("create_document_form"):
        # Find content from any create_document_content key in session state
        content = None
        
        # Try all possible editor keys for create document
        possible_keys = ["create_document_content"]
        if st.session_state.get("selected_template_id"):
            possible_keys.append(f"create_document_content_{st.session_state.selected_template_id}")
        
        # Look for content in any of these keys
        for key in possible_keys:
            if key in st.session_state and st.session_state[key]:
                content = st.session_state[key]
                break
        
        # If still no content, use initial_content
        if not content:
            content = initial_content
        
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
            
            # Filter out current user
            available_reviewers = [member for member in project_members if member["user_id"] != user_info["id"]]
            
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
        
        # Form submit button - disable during processing
        creating_document = st.session_state.get("creating_document", False)
        submitted = st.form_submit_button(
            "🚀 Create Document" if not creating_document else "⏳ Creating...", 
            type="primary",
            disabled=creating_document
        )
    
    # Note: Close Document button removed as per user request
    
    if submitted:
            # Set processing state to disable button
            st.session_state.creating_document = True
            
            # Get name from session state (since it's outside the form)
            name = st.session_state.get("doc_name_input", "")
            
            # Find content from any create_document_content key in session state (same logic as above)
            content = None
            
            # Try all possible editor keys for create document
            possible_keys = ["create_document_content"]
            if st.session_state.get("selected_template_id"):
                possible_keys.append(f"create_document_content_{st.session_state.selected_template_id}")
            
            # Look for content in any of these keys
            for key in possible_keys:
                if key in st.session_state and st.session_state[key]:
                    content = st.session_state[key]
                    break
            
            # If still no content, use initial_content
            if not content:
                content = initial_content
            
            
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
                # Reset processing state on validation error
                st.session_state.creating_document = False
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
                    "template_id": template_id if creation_method == "📄 Create from Template" else None
                }
                
                result, status_code = create_document(project_id, document_data)
                
                # Reset processing state after completion
                st.session_state.creating_document = False
                
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

with tab2:
    st.subheader("📝 My Documents") 
    st.caption("Documents you created")
    
    # Create sub-tabs for better organization
    author_tab1, author_tab2, author_tab3 = st.tabs(["📝 My Documents", "📋 My Reviews", "✅ Approved"])
    
    with author_tab1:
        documents = get_documents_for_author(project_id)
        
        if not documents:
            st.info("No documents found")
        else:
            # NEW LAYOUT: TOP SECTION (Document List + Editor) and BOTTOM SECTION (Full Width Content Editor)
            
            # ========== TOP SECTION ==========
            st.markdown("### 📋 Document Management")
            top_col1, top_col2 = st.columns([1, 1])
            
            with top_col1:
                st.markdown("**📄 My Documents List**")
                
                # Prepare data for st.dataframe
                grid_data = []
                for doc in documents:
                    # Get reviewer names
                    reviewers = ""
                    if doc.get('reviewers'):
                        if isinstance(doc['reviewers'], list) and doc['reviewers']:
                            # Handle both formats: list of strings or list of dicts
                            if isinstance(doc['reviewers'][0], dict):
                                reviewer_names = [r['username'] for r in doc['reviewers']]
                            else:
                                reviewer_names = doc['reviewers']
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
                    height=350,
                    key="my_docs_dataframe"
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
            
            with top_col2:
                st.markdown("**🔧 Document Editor & Actions**")
                
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
                        st.markdown(f"**{doc['name']}**")
                        st.caption(f"{doc['document_type'].replace('_', ' ').title()}")
                        # Handle both V1 (status) and V2 (document_state, review_state) formats
                        doc_state = doc.get('document_state', doc.get('status', 'unknown'))
                        review_state = doc.get('review_state')
                        st.markdown(f"**Status:** {format_status(doc_state, review_state)}", unsafe_allow_html=True)
                    
                    # Comment History - handle both V1 and V2 formats  
                    with st.expander("💬 Comment History", expanded=False):
                        comments = doc.get('comment_history', doc.get('review_comments', []))
                        display_comment_history(comments)
                    
                    # Author Actions - handle both V1 and V2 formats
                    doc_status = doc.get('document_state', doc.get('status', 'unknown'))
                    if doc_status in ['draft', 'needs_update', 'need_revision']:
                        st.markdown("**📝 Author Actions**")
                        
                        # Get project members for reviewer selection
                        members = get_project_members(project_id)
                        reviewer_options = [m for m in members if m.get('user_id') != user_info['id']]
                        
                        if reviewer_options:
                            selected_reviewer = st.selectbox(
                                "Select Reviewer:",
                                options=[(m['user_id'], m['username']) for m in reviewer_options],
                                format_func=lambda x: x[1]
                            )
                            
                            
                            author_comment = st.text_area("Comment for Reviewer:", height=80)
                            
                            col_submit, col_close = st.columns([1, 1])
                            with col_submit:
                                if st.button("📋 Submit for Review", type="primary"):
                                    if author_comment.strip():
                                        result = submit_for_review(doc['id'], selected_reviewer[0], author_comment)
                                        if result.get("success"):
                                            st.success(result["message"])
                                            # Refresh document data
                                            fresh_docs = get_documents_for_author(project_id)
                                            fresh_doc = next((d for d in fresh_docs if d['id'] == doc['id']), None)
                                            if fresh_doc:
                                                st.session_state.selected_doc = fresh_doc
                                            if "documents_cache" in st.session_state:
                                                del st.session_state.documents_cache
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to submit: {result.get('error', 'Unknown error')}")
                                    else:
                                        st.error("Please provide a comment for the reviewer")
                            
                            with col_close:
                                if st.button("❌ Close Document"):
                                    # Clear session state - including bottom editor keys
                                    keys_to_remove = []
                                    for key in st.session_state.keys():
                                        if (key.startswith('selected_doc') or 
                                            key.startswith('editor_my_') or 
                                            key.startswith('editor_bottom_') or 
                                            key.startswith('revision_comment_') or 
                                            key.startswith('create_revision_') or 
                                            key.startswith('preview_toggle_bottom_') or
                                            key.startswith('chat_toggle_bottom_') or
                                            key.startswith('edit_doc_chat_responses_') or
                                            key.startswith('edit_chat_query_') or
                                            key == 'my_docs_dataframe' or 
                                            key == 'selected_doc' or 
                                            key == 'mode'):
                                            keys_to_remove.append(key)
                                    
                                    for key in keys_to_remove:
                                        del st.session_state[key]
                                    st.rerun()
                        else:
                            st.info("No other project members available as reviewers")
                            if st.button("❌ Close Document"):
                                # Clear session state - including bottom editor keys
                                keys_to_remove = []
                                for key in st.session_state.keys():
                                    if (key.startswith('selected_doc') or 
                                        key.startswith('editor_my_') or 
                                        key.startswith('editor_bottom_') or 
                                        key.startswith('revision_comment_') or 
                                        key.startswith('create_revision_') or 
                                        key.startswith('preview_toggle_bottom_') or
                                        key == 'my_docs_dataframe' or 
                                        key == 'selected_doc' or 
                                        key == 'mode'):
                                        keys_to_remove.append(key)
                                
                                for key in keys_to_remove:
                                    del st.session_state[key]
                                st.rerun()
                    else:
                        st.info(f"Document is currently {doc_status.replace('_', ' ')}")
                        if st.button("❌ Close Document"):
                            # Clear session state - including bottom editor keys
                            keys_to_remove = []
                            for key in st.session_state.keys():
                                if (key.startswith('selected_doc') or 
                                    key.startswith('editor_my_') or 
                                    key.startswith('editor_bottom_') or 
                                    key.startswith('revision_comment_') or 
                                    key.startswith('create_revision_') or 
                                    key.startswith('preview_toggle_bottom_') or
                                    key.startswith('chat_toggle_bottom_') or
                                    key.startswith('edit_doc_chat_responses_') or
                                    key.startswith('edit_chat_query_') or
                                    key == 'my_docs_dataframe' or 
                                    key == 'selected_doc' or 
                                    key == 'mode'):
                                    keys_to_remove.append(key)
                            
                            for key in keys_to_remove:
                                del st.session_state[key]
                            st.rerun()
                else:
                    st.info("Select a document from the left panel to edit")
            
            # ========== BOTTOM SECTION ==========
            # Full-width Document Content Editor (similar to Create Document)
            if "selected_doc" in st.session_state and "mode" in st.session_state and st.session_state.mode == "author":
                doc = st.session_state.selected_doc
                
                # Horizontal separator
                st.markdown("---")
                
                # Document Content Section - Full Width
                st.subheader("📄 Document Content")
                
                # Add mutually exclusive options for preview or chat (full-width editing)
                preview_key_bottom = f"preview_toggle_bottom_{doc['id']}"
                chat_key_bottom = f"chat_toggle_bottom_{doc['id']}"
                
                # Get current values or use defaults
                current_preview_bottom = st.session_state.get(preview_key_bottom, True)
                current_chat_bottom = st.session_state.get(chat_key_bottom, False)
                
                col_option1_bottom, col_option2_bottom = st.columns(2)
                with col_option1_bottom:
                    preview_enabled_bottom = st.checkbox(
                        "👁️ Enable Live Preview", 
                        value=current_preview_bottom, 
                        help="Show HTML preview alongside markdown editor",
                        key=preview_key_bottom
                    )
                with col_option2_bottom:
                    chat_enabled_bottom = st.checkbox(
                        "💬 Chat with Knowledge Base", 
                        value=current_chat_bottom, 
                        help="Chat with AI using Knowledge Base context",
                        key=chat_key_bottom
                    )
                
                # Handle state changes after widget creation
                if preview_enabled_bottom != current_preview_bottom or chat_enabled_bottom != current_chat_bottom:
                    # User changed something, enforce mutual exclusion
                    if preview_enabled_bottom and chat_enabled_bottom:
                        # Both got enabled, disable the other based on what changed
                        if preview_enabled_bottom != current_preview_bottom:
                            # Preview was just enabled, disable chat
                            st.session_state[chat_key_bottom] = False
                        else:
                            # Chat was just enabled, disable preview  
                            st.session_state[preview_key_bottom] = False
                        st.rerun()
                    elif not preview_enabled_bottom and not chat_enabled_bottom:
                        # Both got disabled, enable preview by default
                        st.session_state[preview_key_bottom] = True
                        st.rerun()
                
                if preview_enabled_bottom:
                    # Split view: Editor on left, Preview on right (full width)
                    col_editor_bottom, col_preview_bottom = st.columns([1, 1])
                    
                    with col_editor_bottom:
                        st.markdown("**Markdown Editor**")
                        content = st_ace(
                            value=doc['content'],
                            language='markdown',
                            theme='github',
                            height=400,
                            auto_update=True,  # Enable live preview
                            wrap=True,
                            key=f"editor_bottom_{doc['id']}"
                        )
                    
                    with col_preview_bottom:
                        col_preview_title, col_font_info = st.columns([2, 1])
                        with col_preview_title:
                            st.markdown("**HTML Preview**")
                        with col_font_info:
                            st.markdown("<div style='text-align: right;'><em>Font: Source Sans Pro, 14px, single-spacing</em></div>", unsafe_allow_html=True)
                        if content and content.strip():
                            try:
                                # Convert markdown to HTML
                                html_content_bottom = markdown.markdown(
                                    content, 
                                    extensions=['tables', 'fenced_code', 'codehilite', 'toc']
                                )
                                
                                # Display with single line spacing and font info
                                st.markdown(
                                    f"""
                                    <div style="
                                        border: 1px solid #ddd; 
                                        border-radius: 4px; 
                                        padding: 16px; 
                                        height: 400px; 
                                        overflow-y: auto; 
                                        background-color: #ffffff;
                                        color: #262730;
                                        font-family: 'Source Sans Pro', sans-serif;
                                        font-size: 14px;
                                        line-height: 1.2;
                                    ">
                                        <style>
                                            .markdown-preview-bottom h1, .markdown-preview-bottom h2, .markdown-preview-bottom h3, 
                                            .markdown-preview-bottom h4, .markdown-preview-bottom h5, .markdown-preview-bottom h6 {{
                                                color: #262730 !important;
                                                margin-top: 1rem;
                                                margin-bottom: 0.3rem;
                                                line-height: 1.2;
                                            }}
                                            .markdown-preview-bottom p {{
                                                color: #262730 !important;
                                                margin-bottom: 0.5rem;
                                                line-height: 1.2;
                                            }}
                                            .markdown-preview-bottom ul, .markdown-preview-bottom ol {{
                                                color: #262730 !important;
                                                margin-bottom: 0.5rem;
                                            }}
                                            .markdown-preview-bottom li {{
                                                color: #262730 !important;
                                                line-height: 1.2;
                                                margin-bottom: 0.2rem;
                                            }}
                                            .markdown-preview-bottom table {{
                                                border-collapse: collapse;
                                                width: 100%;
                                                margin-bottom: 0.5rem;
                                            }}
                                            .markdown-preview-bottom th, .markdown-preview-bottom td {{
                                                border: 1px solid #ddd;
                                                padding: 6px 8px;
                                                text-align: left;
                                                color: #262730 !important;
                                                line-height: 1.2;
                                            }}
                                            .markdown-preview-bottom th {{
                                                background-color: #f8f9fa;
                                            }}
                                            .markdown-preview-bottom code {{
                                                background-color: #f8f9fa;
                                                padding: 2px 4px;
                                                border-radius: 3px;
                                                color: #e91e63 !important;
                                                font-family: 'Monaco', 'Consolas', monospace;
                                                font-size: 13px;
                                            }}
                                            .markdown-preview-bottom pre {{
                                                background-color: #f8f9fa;
                                                padding: 8px;
                                                border-radius: 4px;
                                                border: 1px solid #e9ecef;
                                                overflow-x: auto;
                                                margin-bottom: 0.5rem;
                                                line-height: 1.2;
                                            }}
                                            .markdown-preview-bottom pre code {{
                                                background: none;
                                                padding: 0;
                                                color: #212529 !important;
                                                font-size: 13px;
                                            }}
                                            .markdown-preview-bottom a {{
                                                color: #1976d2 !important;
                                                text-decoration: underline;
                                            }}
                                            .markdown-preview-bottom blockquote {{
                                                border-left: 4px solid #1976d2;
                                                margin: 0 0 0.5rem 0;
                                                padding-left: 1rem;
                                                color: #555 !important;
                                                line-height: 1.2;
                                            }}
                                        </style>
                                        <div class="markdown-preview-bottom">
                                            {html_content_bottom}
                                        </div>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )
                            except Exception as e:
                                st.error(f"Preview error: {str(e)}")
                                st.info("💡 Write some markdown content to see the preview")
                        else:
                            st.info("💡 Content will be displayed here as you edit")
                elif chat_enabled_bottom:
                    # Split view: Editor on left, Chat on right
                    col_editor_bottom, col_chat_bottom = st.columns([1, 1])
                    
                    with col_editor_bottom:
                        st.markdown("**Markdown Editor**")
                        content = st_ace(
                            value=doc['content'],
                            language='markdown',
                            theme='github',
                            height=400,
                            auto_update=False,  # Disable auto update for chat mode
                            key=f"editor_bottom_{doc['id']}"
                        )
                    
                    with col_chat_bottom:
                        st.markdown("**💬 Knowledge Base Chat**")
                        
                        # Chat Response Box for this document
                        chat_response_key = f"edit_doc_chat_responses_{doc['id']}"
                        if chat_response_key not in st.session_state:
                            st.session_state[chat_response_key] = []
                        
                        # Display chat responses in reverse chronological order (newest first)
                        chat_responses = st.session_state[chat_response_key]
                        chat_display = ""
                        
                        for i, response in enumerate(reversed(chat_responses)):
                            timestamp = response.get('timestamp', 'Unknown time')
                            query = response.get('query', 'No query')
                            answer = response.get('response', 'No response')
                            sources = response.get('sources', [])
                            
                            chat_display += f"""**Q ({timestamp}):** {query}

**A:** {answer}
"""
                            if sources:
                                chat_display += f"\n**Sources:** {', '.join([s.get('filename', 'Unknown') for s in sources])}\n"
                            
                            chat_display += "\n" + "="*50 + "\n\n"
                        
                        # Add footer with usage and limits info
                        if chat_display:
                            current_count = len(chat_responses)
                            chat_display += f"📊 **Chat Session:** {current_count}/{MAX_CHAT_RESPONSES_PER_SESSION} responses | Max response length: {MAX_CHAT_RESPONSE_LENGTH:,} chars"
                        
                        # Chat response display area
                        st.text_area(
                            "Chat History",
                            value=chat_display if chat_display else "💡 Ask the Knowledge Base about your document...",
                            height=300,
                            disabled=True,
                            key=f"edit_chat_display_{doc['id']}",
                            label_visibility="collapsed"
                        )
                        
                        # Chat input area
                        col_query_edit, col_submit_edit = st.columns([3, 1])
                        with col_query_edit:
                            user_query_edit = st.text_area(
                                "Ask the Knowledge Base",
                                height=80,
                                placeholder="Ask the Knowledge Base about your document...",
                                key=f"edit_chat_query_{doc['id']}"
                            )
                        
                        with col_submit_edit:
                            st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
                            if st.button("🚀 Submit", key=f"submit_kb_query_edit_{doc['id']}", type="primary"):
                                if user_query_edit and user_query_edit.strip():
                                    # Get current document content for context (snapshot at query time)
                                    document_context = st.session_state.get(f"editor_bottom_{doc['id']}", doc['content'])
                                    
                                    # Show loading spinner
                                    with st.spinner("🤖 Querying Knowledge Base..."):
                                        try:
                                            # Create payload for the API
                                            payload = {
                                                "query": user_query_edit.strip(),
                                                "document_context": document_context if (document_context and document_context.strip()) else None,
                                                "collection_name": None,  # Use default
                                                "max_results": 5
                                            }
                                            
                                            # Make API call to KB query with context endpoint
                                            response = requests.post(
                                                f"{BACKEND_URL}/kb/query_with_context",
                                                json=payload,
                                                headers=get_auth_headers(),
                                                timeout=KB_CHAT_REQUEST_TIMEOUT
                                            )
                                            
                                            if response.status_code == 200:
                                                result = response.json()
                                                
                                                # Add response to chat history
                                                chat_entry = {
                                                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                                                    'query': user_query_edit.strip(),
                                                    'response': result.get('response', 'No response received'),
                                                    'sources': result.get('sources', []),
                                                    'context_provided': result.get('document_context_provided', False),
                                                    'kb_results': result.get('knowledge_base_results', 0)
                                                }
                                                
                                                manage_chat_response_limits(chat_response_key, chat_entry)
                                                
                                                # Clear the query input
                                                st.session_state[f"edit_chat_query_{doc['id']}"] = ""
                                                
                                                # Success message
                                                st.success("✅ Response received!")
                                                st.rerun()
                                                
                                            else:
                                                error_msg = response.json().get('detail', 'Failed to query Knowledge Base')
                                                st.error(f"❌ Error: {error_msg}")
                                                
                                        except requests.exceptions.Timeout:
                                            st.error("❌ Request timed out. Knowledge Base may be busy.")
                                        except Exception as e:
                                            st.error(f"❌ Failed to query Knowledge Base: {str(e)}")
                                else:
                                    st.warning("⚠️ Please enter a query")
                        
                        # Clear chat history button
                        if st.session_state[chat_response_key]:
                            if st.button("🗑️ Clear Chat", key=f"clear_edit_chat_{doc['id']}"):
                                st.session_state[chat_response_key] = []
                                st.rerun()
                else:
                    # Full width editor without preview
                    content = st_ace(
                        value=doc['content'],
                        language='markdown',
                        theme='github',
                        height=400,
                        key=f"editor_bottom_{doc['id']}"
                    )
                
                # Save Draft functionality - moved to bottom section
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
                
                # Close Document Content button
                st.divider()
                if st.button("❌ Close Document Content", key=f"close_content_{doc['id']}", help="Close the document content editor and return to document list"):
                    # Clear session state - including bottom editor keys
                    keys_to_remove = []
                    for key in st.session_state.keys():
                        if (key.startswith('selected_doc') or 
                            key.startswith('editor_my_') or 
                            key.startswith('editor_bottom_') or 
                            key.startswith('revision_comment_') or 
                            key.startswith('create_revision_') or 
                            key.startswith('preview_toggle_bottom_') or
                            key.startswith('chat_toggle_bottom_') or
                            key.startswith('edit_doc_chat_responses_') or
                            key.startswith('edit_chat_query_') or
                            key == 'my_docs_dataframe' or 
                            key == 'selected_doc' or 
                            key == 'mode'):
                            keys_to_remove.append(key)
                    
                    for key in keys_to_remove:
                        del st.session_state[key]
                    st.rerun()
    
    with author_tab2:
        review_docs = get_documents_for_reviewer(project_id)
        
        if not review_docs:
            st.info("No documents to review")
        else:
            # ========== TOP SECTION ==========
            # Left-right panel layout for reviews (similar to My Documents)
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
                    height=350,
                    key="review_docs_dataframe"
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
                st.markdown("### Document Information")
                
                if "selected_review_doc" in st.session_state and st.session_state.mode == "reviewer":
                    doc = st.session_state.selected_review_doc
                    
                    # Document header
                    st.markdown(f"**{doc['name']}**")
                    st.caption(f"{doc['document_type'].replace('_', ' ').title()}")
                    doc_state = doc.get('document_state', doc.get('status', 'unknown'))
                    review_state = doc.get('review_state')
                    st.markdown(f"**Author:** {doc['author']} | **Status:** {format_status(doc_state, review_state)}", unsafe_allow_html=True)
                    
                    # Comment History
                    with st.expander("💬 Comment History", expanded=False):
                        display_comment_history(doc.get('comment_history', []))
                    
                    # Review Controls
                    st.markdown("**👨‍⚖️ Review Decision**")
                    
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
                                    
                                    # Send approved document content to Knowledge Base
                                    try:
                                        kb_content = f"""# Document: {doc['name']}
**Type**: {doc['document_type'].replace('_', ' ').title()}
**Author**: {doc['author']}
**Approval Date**: {datetime.now().strftime('%Y-%m-%d')}
**Reviewer**: {get_current_user()['username'] if get_current_user() else 'Unknown'}
**Review Comment**: {reviewer_comment}

## Document Content

{doc.get('content', 'No content available')}
"""
                                        
                                        metadata = {
                                            "document_id": doc['id'],
                                            "document_name": doc['name'],
                                            "document_type": doc['document_type'],
                                            "author": doc['author'],
                                            "approved_by": get_current_user()['username'] if get_current_user() else 'Unknown',
                                            "approval_date": datetime.now().isoformat(),
                                            "content_type": "approved_document"
                                        }
                                        
                                        kb_response = requests.post(
                                            f"{BACKEND_URL}/kb/add_text",
                                            params={
                                                "collection_name": "knowledge_base",  # Use default collection
                                                "text_content": kb_content,
                                                "filename": f"approved_document_{doc['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                                            },
                                            json=metadata,
                                            headers=get_auth_headers(),
                                            timeout=KB_REQUEST_TIMEOUT
                                        )
                                        
                                        if kb_response.status_code == 200:
                                            st.info("📚 Document also added to Knowledge Base")
                                        # Don't show error for KB failure to avoid disrupting the main approval flow
                                        
                                    except Exception:
                                        pass  # Silently handle KB integration failures
                                    
                                    del st.session_state.selected_review_doc
                                    st.rerun()
                                else:
                                    st.error(result.get("error", "Failed to submit review"))
                            else:
                                st.error("Please provide a comment with your approval")
                    
                    with col_r3:
                        if st.button("❌ Close", key="close_review_doc"):
                            # Clear all related session state including dataframe selection
                            keys_to_remove = []
                            for key in st.session_state.keys():
                                if (key.startswith('selected_review_doc') or 
                                    key.startswith('editor_review_') or 
                                    key.startswith('editor_review_bottom_') or
                                    key.startswith('preview_toggle_review_') or
                                    key == 'review_docs_dataframe'):
                                    keys_to_remove.append(key)
                            
                            for key in keys_to_remove:
                                del st.session_state[key]
                            
                            # Clear main review session state
                            if 'selected_review_doc' in st.session_state:
                                del st.session_state.selected_review_doc
                            if 'mode' in st.session_state:
                                del st.session_state.mode
                            
                            # Clear dataframe selection explicitly
                            if 'review_docs_dataframe' in st.session_state:
                                del st.session_state.review_docs_dataframe
                            
                            st.rerun()
                else:
                    st.info("Select a document from the review queue to start reviewing")
                    
            # ========== BOTTOM SECTION ==========
            # Full-width Document Content Viewer (similar to My Documents editor but read-only)
            if "selected_review_doc" in st.session_state and "mode" in st.session_state and st.session_state.mode == "reviewer":
                doc = st.session_state.selected_review_doc
                
                # Horizontal separator
                st.markdown("---")
                
                # Document Content Section - Full Width
                st.subheader("📄 Document Content")
                
                # Add mutually exclusive options for preview or chat (full-width viewing)
                preview_key_review = f"preview_toggle_review_{doc['id']}"
                chat_key_review = f"chat_toggle_review_{doc['id']}"
                
                # Get current values or use defaults
                current_preview_review = st.session_state.get(preview_key_review, True)
                current_chat_review = st.session_state.get(chat_key_review, False)
                
                col_option1_review, col_option2_review = st.columns(2)
                with col_option1_review:
                    preview_enabled_review = st.checkbox(
                        "👁️ Enable Live Preview", 
                        value=current_preview_review, 
                        help="Show HTML preview alongside markdown content",
                        key=preview_key_review
                    )
                with col_option2_review:
                    chat_enabled_review = st.checkbox(
                        "💬 Chat with Knowledge Base", 
                        value=current_chat_review, 
                        help="Chat with AI using Knowledge Base context",
                        key=chat_key_review
                    )
                
                # Handle state changes after widget creation
                if preview_enabled_review != current_preview_review or chat_enabled_review != current_chat_review:
                    # User changed something, enforce mutual exclusion
                    if preview_enabled_review and chat_enabled_review:
                        # Both got enabled, disable the other based on what changed
                        if preview_enabled_review != current_preview_review:
                            # Preview was just enabled, disable chat
                            st.session_state[chat_key_review] = False
                        else:
                            # Chat was just enabled, disable preview  
                            st.session_state[preview_key_review] = False
                        st.rerun()
                    elif not preview_enabled_review and not chat_enabled_review:
                        # Both got disabled, enable preview by default
                        st.session_state[preview_key_review] = True
                        st.rerun()
                
                if preview_enabled_review:
                    # Split view: Markdown source on left, HTML Preview on right (full width)
                    col_source_review, col_preview_review = st.columns([1, 1])
                    
                    with col_source_review:
                        st.markdown("**Markdown Source**")
                        # Read-only text area showing markdown source
                        st.text_area(
                            "Markdown Source",
                            value=doc['content'],
                            height=400,
                            disabled=True,  # Read-only for reviewers
                            key=f"editor_review_bottom_{doc['id']}",
                            label_visibility="collapsed"
                        )
                    
                    with col_preview_review:
                        col_preview_title, col_font_info = st.columns([2, 1])
                        with col_preview_title:
                            st.markdown("**HTML Preview**")
                        with col_font_info:
                            st.markdown("<div style='text-align: right;'><em>Font: Source Sans Pro, 14px, single-spacing</em></div>", unsafe_allow_html=True)
                        if doc['content'] and doc['content'].strip():
                            try:
                                # Convert markdown to HTML
                                html_content_review = markdown.markdown(
                                    doc['content'], 
                                    extensions=['tables', 'fenced_code', 'codehilite', 'toc']
                                )
                                
                                # Display with single line spacing and font info (same styling as My Documents)
                                st.markdown(
                                    f"""
                                    <div style="
                                        border: 1px solid #ddd; 
                                        border-radius: 4px; 
                                        padding: 16px; 
                                        height: 400px; 
                                        overflow-y: auto; 
                                        background-color: #ffffff;
                                        color: #262730;
                                        font-family: 'Source Sans Pro', sans-serif;
                                        font-size: 14px;
                                        line-height: 1.2;
                                    ">
                                        <style>
                                            .markdown-preview-review h1, .markdown-preview-review h2, .markdown-preview-review h3, 
                                            .markdown-preview-review h4, .markdown-preview-review h5, .markdown-preview-review h6 {{
                                                color: #262730 !important;
                                                margin-top: 1rem;
                                                margin-bottom: 0.3rem;
                                                line-height: 1.2;
                                            }}
                                            .markdown-preview-review p {{
                                                color: #262730 !important;
                                                margin-bottom: 0.5rem;
                                                line-height: 1.2;
                                            }}
                                            .markdown-preview-review ul, .markdown-preview-review ol {{
                                                color: #262730 !important;
                                                margin-bottom: 0.5rem;
                                            }}
                                            .markdown-preview-review li {{
                                                color: #262730 !important;
                                                line-height: 1.2;
                                                margin-bottom: 0.2rem;
                                            }}
                                            .markdown-preview-review table {{
                                                border-collapse: collapse;
                                                width: 100%;
                                                margin-bottom: 1rem;
                                            }}
                                            .markdown-preview-review th, .markdown-preview-review td {{
                                                border: 1px solid #ddd;
                                                padding: 8px;
                                                text-align: left;
                                            }}
                                            .markdown-preview-review th {{
                                                background-color: #f2f2f2;
                                                font-weight: bold;
                                            }}
                                        </style>
                                        <div class="markdown-preview-review">
                                            {html_content_review}
                                        </div>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )
                            except Exception as e:
                                st.error(f"Preview error: {str(e)}")
                                st.info("💡 Document content will be displayed here")
                        else:
                            st.info("💡 Document content will be displayed here")
                elif chat_enabled_review:
                    # Split view: Markdown source on left, Chat on right
                    col_source_review, col_chat_review = st.columns([1, 1])
                    
                    with col_source_review:
                        st.markdown("**Markdown Source**")
                        # Read-only text area showing markdown source
                        st.text_area(
                            "Markdown Source",
                            value=doc['content'],
                            height=400,
                            disabled=True,  # Read-only for reviewers
                            key=f"editor_review_bottom_{doc['id']}",
                            label_visibility="collapsed"
                        )
                    
                    with col_chat_review:
                        st.markdown("**💬 Knowledge Base Chat**")
                        
                        # Chat Response Box for this review document
                        chat_response_key = f"review_doc_chat_responses_{doc['id']}"
                        if chat_response_key not in st.session_state:
                            st.session_state[chat_response_key] = []
                        
                        # Display chat responses in reverse chronological order (newest first)
                        chat_responses = st.session_state[chat_response_key]
                        chat_display = ""
                        
                        for i, response in enumerate(reversed(chat_responses)):
                            timestamp = response.get('timestamp', 'Unknown time')
                            query = response.get('query', 'No query')
                            answer = response.get('response', 'No response')
                            sources = response.get('sources', [])
                            
                            chat_display += f"""**Q ({timestamp}):** {query}

**A:** {answer}
"""
                            if sources:
                                chat_display += f"\n**Sources:** {', '.join([s.get('filename', 'Unknown') for s in sources])}\n"
                            
                            chat_display += "\n" + "="*50 + "\n\n"
                        
                        # Add footer with usage and limits info
                        if chat_display:
                            current_count = len(chat_responses)
                            chat_display += f"📊 **Chat Session:** {current_count}/{MAX_CHAT_RESPONSES_PER_SESSION} responses | Max response length: {MAX_CHAT_RESPONSE_LENGTH:,} chars"
                        
                        # Chat response display area
                        st.text_area(
                            "Chat History",
                            value=chat_display if chat_display else "💡 Ask the Knowledge Base about this document...",
                            height=300,
                            disabled=True,
                            key=f"review_chat_display_{doc['id']}",
                            label_visibility="collapsed"
                        )
                        
                        # Chat input area
                        col_query_review, col_submit_review = st.columns([3, 1])
                        with col_query_review:
                            user_query_review = st.text_area(
                                "Ask the Knowledge Base",
                                height=80,
                                placeholder="Ask the Knowledge Base about this document...",
                                key=f"review_chat_query_{doc['id']}"
                            )
                        
                        with col_submit_review:
                            st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
                            if st.button("🚀 Submit", key=f"submit_kb_query_review_{doc['id']}", type="primary"):
                                if user_query_review and user_query_review.strip():
                                    # Get document content for context (read-only for reviewers)
                                    document_context = doc['content']
                                    
                                    # Show loading spinner
                                    with st.spinner("🤖 Querying Knowledge Base..."):
                                        try:
                                            # Create payload for the API
                                            payload = {
                                                "query": user_query_review.strip(),
                                                "document_context": document_context if (document_context and document_context.strip()) else None,
                                                "collection_name": None,  # Use default
                                                "max_results": 5
                                            }
                                            
                                            # Make API call to KB query with context endpoint
                                            response = requests.post(
                                                f"{BACKEND_URL}/kb/query_with_context",
                                                json=payload,
                                                headers=get_auth_headers(),
                                                timeout=KB_CHAT_REQUEST_TIMEOUT
                                            )
                                            
                                            if response.status_code == 200:
                                                result = response.json()
                                                
                                                # Add response to chat history
                                                chat_entry = {
                                                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                                                    'query': user_query_review.strip(),
                                                    'response': result.get('response', 'No response received'),
                                                    'sources': result.get('sources', []),
                                                    'context_provided': result.get('document_context_provided', False),
                                                    'kb_results': result.get('knowledge_base_results', 0)
                                                }
                                                
                                                manage_chat_response_limits(chat_response_key, chat_entry)
                                                
                                                # Clear the query input
                                                st.session_state[f"review_chat_query_{doc['id']}"] = ""
                                                
                                                # Success message
                                                st.success("✅ Response received!")
                                                st.rerun()
                                                
                                            else:
                                                error_msg = response.json().get('detail', 'Failed to query Knowledge Base')
                                                st.error(f"❌ Error: {error_msg}")
                                                
                                        except requests.exceptions.Timeout:
                                            st.error("❌ Request timed out. Knowledge Base may be busy.")
                                        except Exception as e:
                                            st.error(f"❌ Failed to query Knowledge Base: {str(e)}")
                                else:
                                    st.warning("⚠️ Please enter a query")
                        
                        # Clear chat history button
                        if st.session_state[chat_response_key]:
                            if st.button("🗑️ Clear Chat", key=f"clear_review_chat_{doc['id']}"):
                                st.session_state[chat_response_key] = []
                                st.rerun()
                else:
                    # Full width content display without preview
                    st.text_area(
                        "Document Content",
                        value=doc['content'],
                        height=400,
                        disabled=True,  # Read-only for reviewers
                        key=f"editor_review_full_{doc['id']}",
                        label_visibility="collapsed"
                    )
                
                # Close Document Content button
                st.divider()
                if st.button("❌ Close Document Content", key=f"close_review_content_{doc['id']}", help="Close the document content viewer and return to review list"):
                    # Clear session state - including review editor keys
                    keys_to_remove = []
                    for key in st.session_state.keys():
                        if (key.startswith('selected_review_doc') or 
                            key.startswith('editor_review_') or 
                            key.startswith('preview_toggle_review_') or
                            key == 'review_docs_dataframe' or 
                            key == 'mode'):
                            keys_to_remove.append(key)
                    
                    for key in keys_to_remove:
                        del st.session_state[key]
                    st.rerun()
    
    with author_tab3:
        approved_docs = get_approved_documents(project_id)
        
        if not approved_docs:
            st.info("No approved documents")
        else:
            # Left-right panel layout similar to My Documents
            approved_col1, approved_col2 = st.columns([2, 3])
            
            with approved_col1:
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
                    # Get reviewers for this document
                    reviewers = get_document_reviewers_from_data(row['full_doc_data'])
                    
                    approved_df_row = {
                        'Document Name': row['name'],
                        'Type': row['document_type'].replace('_', ' ').title(),
                        'Author': row['author'],
                        'Reviewers': reviewers,
                        'Created Date': row['full_doc_data'].get('created_at', '')[:10] if row['full_doc_data'].get('created_at') else 'N/A',
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
                    height=300,
                    key="approved_docs_dataframe"
                )
                
                st.caption("💡 Select a row to view the approved document")
                
                # Handle approved document selection
                if approved_selected_indices and len(approved_selected_indices.selection.rows) > 0:
                    selected_idx = approved_selected_indices.selection.rows[0]
                    full_doc = approved_grid_data[selected_idx]['full_doc_data']
                    # Only rerun if this is a different document
                    if (st.session_state.get('selected_approved_doc', {}).get('id') != full_doc.get('id') or 
                        st.session_state.get('approved_mode') != "view_only"):
                        st.session_state.selected_approved_doc = full_doc
                        st.session_state.approved_mode = "view_only"
                        st.rerun()
            
            with approved_col2:
                st.markdown("### Document PDF Viewer")
                
                if "selected_approved_doc" in st.session_state and st.session_state.approved_mode == "view_only":
                    doc = st.session_state.selected_approved_doc
                    
                    # Add refresh button to get latest document data
                    col_refresh1, col_refresh2 = st.columns([4, 1])
                    with col_refresh2:
                        if st.button("🔄 Refresh", key="refresh_approved_doc", help="Refresh document data"):
                            # Force refresh by getting latest document data
                            fresh_docs = get_approved_documents(project_id)
                            fresh_doc = next((d for d in fresh_docs if d['id'] == doc['id']), None)
                            if fresh_doc:
                                st.session_state.selected_approved_doc = fresh_doc
                                doc = fresh_doc
                            st.rerun()
                    
                    with col_refresh1:
                        # Document header
                        st.markdown(f"**{doc['name']}** | {doc['document_type'].replace('_', ' ').title()}")
                        # Handle both V1 (status) and V2 (document_state, review_state) formats
                        doc_state = doc.get('document_state', doc.get('status', 'approved'))
                        review_state = doc.get('review_state')
                        st.markdown(f"**Status:** {format_status(doc_state, review_state)}", unsafe_allow_html=True)
                    
                    # Generate and display PDF
                    try:
                        # Generate PDF from document content
                        pdf_response = requests.post(
                            f"{BACKEND_URL}/documents/{doc['id']}/generate-pdf",
                            headers=get_auth_headers(),
                            timeout=PDF_GENERATION_TIMEOUT
                        )
                        
                        if pdf_response.status_code == 200:
                            # Display PDF success message
                            st.success("✅ PDF generated successfully!")
                            
                            # Download button for PDF
                            st.download_button(
                                label="📥 Download PDF",
                                data=pdf_response.content,
                                file_name=f"{doc['name'].replace(' ', '_')}.pdf",
                                mime="application/pdf",
                                key=f"download_pdf_{doc['id']}",
                                use_container_width=True
                            )
                            
                            # Show PDF content inline using object tag (better browser compatibility)
                            with st.expander("📄 View PDF Content", expanded=True):
                                pdf_base64 = base64.b64encode(pdf_response.content).decode('utf-8')
                                pdf_display = f'''
                                <object data="data:application/pdf;base64,{pdf_base64}" type="application/pdf" width="100%" height="600px">
                                    <p>Your browser does not support PDFs. <a href="data:application/pdf;base64,{pdf_base64}" download="{doc['name']}.pdf">Download the PDF</a>.</p>
                                </object>
                                '''
                                st.markdown(pdf_display, unsafe_allow_html=True)
                        else:
                            st.error(f"Failed to generate PDF: {pdf_response.status_code}")
                            # Fallback to showing document content
                            st.subheader("📄 Document Content")
                            st.markdown(doc['content'])
                            
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
                        # Fallback to showing document content
                        st.subheader("📄 Document Content")
                        st.markdown(doc['content'])
                    
                    st.divider()
                    
                    # Comment History - handle both V1 and V2 formats
                    with st.expander("💬 View Comment History", expanded=False):
                        comments = doc.get('comment_history', doc.get('review_comments', []))
                        display_comment_history(comments)
                    
                    # Close button
                    if st.button("❌ Close PDF Viewer", key="close_approved_pdf_viewer", type="secondary"):
                        # Clear all related session state including dataframe selection
                        keys_to_remove = []
                        for key in st.session_state.keys():
                            if (key.startswith('selected_approved_doc') or 
                                key.startswith('editor_approved_') or 
                                key.startswith('approved_') or 
                                key == 'approved_docs_dataframe'):
                                keys_to_remove.append(key)
                        
                        for key in keys_to_remove:
                            del st.session_state[key]
                        
                        # Clear main approved session state
                        if 'selected_approved_doc' in st.session_state:
                            del st.session_state.selected_approved_doc
                        if 'approved_mode' in st.session_state:
                            del st.session_state.approved_mode
                        
                        # Clear dataframe selection explicitly
                        if 'approved_docs_dataframe' in st.session_state:
                            del st.session_state.approved_docs_dataframe
                        
                        st.rerun()
                else:
                    st.info("Select an approved document from the left panel to view as PDF")


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
                doc_status = doc.get('document_state', doc.get('status', 'unknown'))
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
                    'reviewers': get_document_reviewers_from_data(doc),
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
                    'Reviewers': row['reviewers']
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
                height=DATAFRAME_HEIGHT,
                key="all_docs_dataframe"
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
                
                # Document header
                st.markdown(f"**{doc['name']}** | {doc['document_type'].replace('_', ' ').title()}")
                doc_status = doc.get('document_state', doc.get('status', 'unknown'))
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
                
                # Document PDF Viewer (readonly in All Documents view)
                st.subheader("📄 Document PDF Viewer")
                try:
                    # Generate and display PDF
                    pdf_response = requests.post(
                        f"{BACKEND_URL}/documents/{doc['id']}/generate-pdf",
                        headers=get_auth_headers(),
                        timeout=PDF_GENERATION_TIMEOUT
                    )
                    
                    if pdf_response.status_code == 200:
                        # Display PDF content using streamlit's native PDF viewer
                        st.success("✅ PDF generated successfully!")
                        
                        # Provide download link for the PDF
                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_response.content,
                            file_name=f"{doc['name']}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        
                        # Show PDF content inline using Streamlit's method
                        with st.expander("📄 View PDF Content", expanded=True):
                            # Create a temporary display using base64 encoding with object tag
                            pdf_base64 = base64.b64encode(pdf_response.content).decode('utf-8')
                            pdf_display = f'''
                            <object data="data:application/pdf;base64,{pdf_base64}" type="application/pdf" width="100%" height="600px">
                                <p>Your browser does not support PDFs. <a href="data:application/pdf;base64,{pdf_base64}" download="{doc['name']}.pdf">Download the PDF</a>.</p>
                            </object>
                            '''
                            st.markdown(pdf_display, unsafe_allow_html=True)
                    else:
                        st.error(f"Failed to generate PDF: {pdf_response.status_code}")
                        # Fallback to show document content
                        st.subheader("📄 Document Content (Fallback)")
                        st_ace(
                            value=doc['content'],
                            language='markdown',
                            theme='github',
                            height=300,
                            key=f"editor_all_{doc['id']}",
                            readonly=True
                        )
                        
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")
                    # Fallback to show document content
                    st.subheader("📄 Document Content (Fallback)")
                    st_ace(
                        value=doc['content'],
                        language='markdown',
                        theme='github',
                        height=300,
                        key=f"editor_all_{doc['id']}",
                        readonly=True
                    )
                
                # Info message about readonly mode
                st.info("📋 **Note:** Documents in All Documents view are displayed in read-only mode. To edit, use the My Documents tab.")
                
                # Close button
                if st.button("❌ Close PDF Viewer", key="close_all_editor"):
                    # Clear all related session state including dataframe selection
                    keys_to_remove = []
                    for key in st.session_state.keys():
                        if (key.startswith('selected_all_doc') or 
                            key.startswith('editor_all_') or 
                            key == 'all_docs_dataframe'):
                            keys_to_remove.append(key)
                    
                    for key in keys_to_remove:
                        del st.session_state[key]
                    
                    # Also clear the main selection
                    if 'selected_all_doc' in st.session_state:
                        del st.session_state.selected_all_doc
                    
                    # Clear dataframe selection explicitly
                    if 'all_docs_dataframe' in st.session_state:
                        del st.session_state.all_docs_dataframe
                    
                    st.rerun()
            else:
                st.info("Select a document from the left panel to view or edit")

