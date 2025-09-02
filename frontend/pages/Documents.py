# frontend/pages/Documents.py
import streamlit as st
import requests
import json
import time
from datetime import datetime
from streamlit_ace import st_ace
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers, BACKEND_URL

require_auth()

st.set_page_config(page_title="Documents", page_icon="📁", layout="wide")

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

st.title("📁 Documents")

setup_authenticated_sidebar()

# Display persistent success message if present
if hasattr(st.session_state, 'document_success_message') and hasattr(st.session_state, 'show_doc_success_until'):
    if time.time() < st.session_state.show_doc_success_until:
        st.success(f"✅ {st.session_state.document_success_message}")
    else:
        # Clear the message after timeout
        delattr(st.session_state, 'document_success_message')
        delattr(st.session_state, 'show_doc_success_until')

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

def get_project_members(project_id):
    """Get project members for reviewer selection"""
    try:
        response = requests.get(f"{BACKEND_URL}/projects/{project_id}", headers=get_auth_headers())
        if response.status_code == 200:
            project_data = response.json()
            return project_data.get("members", [])
        return []
    except Exception as e:
        st.error(f"Error fetching project members: {e}")
        return []

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

def map_document_category_to_specific_type(doc_category):
    """Map document category to a specific document type for AI prompts"""
    category_mappings = {
        "planning_documents": "project_plans",
        "process_documents": "procedures", 
        "specifications": "requirements",
        "records": "test_reports",
        "templates": "forms",
        "policies": "quality_policy",
        "manuals": "user_manuals"
    }
    return category_mappings.get(doc_category, doc_category)

def get_ai_prompt_for_document_type(document_type):
    """Get the AI prompt template for a specific document type"""
    try:
        # Convert category to specific document type if needed
        specific_doc_type = map_document_category_to_specific_type(document_type)
        
        response = requests.get(
            f"{BACKEND_URL}/ai/config/prompts/{specific_doc_type}",
            headers=get_auth_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("prompt", "")
        else:
            # If specific type not found, try with original category name
            response = requests.get(
                f"{BACKEND_URL}/ai/config/prompts/{document_type}",
                headers=get_auth_headers(),
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("prompt", "")
            return ""
    except Exception as e:
        st.error(f"Error fetching AI prompt: {str(e)}")
        return ""

def display_debug_log(debug_log):
    """Display debug log information in an organized way"""
    if not debug_log:
        return
    
    st.subheader("🔍 Debug Log")
    
    # Create tabs for different phases
    debug_tabs = st.tabs([
        "⚙️ Settings", "🏥 Health", "📝 Prompts", "📊 Content", 
        "🌐 API", "📨 Response", "❌ Errors"
    ])
    
    with debug_tabs[0]:  # Settings
        if "1_settings" in debug_log:
            settings = debug_log["1_settings"]
            st.json(settings)
    
    with debug_tabs[1]:  # Health Check
        if "2_health_check" in debug_log:
            health = debug_log["2_health_check"]
            col1, col2 = st.columns(2)
            with col1:
                if health.get("healthy"):
                    st.success(f"✅ Service Healthy")
                else:
                    st.error(f"❌ Service Unhealthy")
            with col2:
                st.metric("Health Check Time", f"{health.get('check_time_ms', 0):.1f}ms")
    
    with debug_tabs[2]:  # Prompt Information
        if "3_prompt_preparation" in debug_log:
            prompt_info = debug_log["3_prompt_preparation"]
            st.write(f"**Document Type:** {prompt_info.get('document_type')}")
            st.write(f"**Prompt Source:** {prompt_info.get('prompt_source')}")
            st.text_area("Original Prompt:", prompt_info.get('original_prompt', ''), height=100)
            st.text_area("User Input:", prompt_info.get('user_input', ''), height=60)
            st.metric("Fetch Time", f"{prompt_info.get('fetch_time_ms', 0):.1f}ms")
        
        if "5_final_prompts" in debug_log:
            final_prompts = debug_log["5_final_prompts"]
            st.text_area("System Prompt:", final_prompts.get('system_prompt', ''), height=100)
            st.text_area("User Prompt (Preview):", final_prompts.get('user_prompt', ''), height=80)
            st.write(f"**Model:** {final_prompts.get('model_to_use')}")
    
    with debug_tabs[3]:  # Content Processing
        if "4_content_processing" in debug_log:
            content = debug_log["4_content_processing"]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Original Length", f"{content.get('original_length', 0):,} chars")
            with col2:
                st.metric("Truncated Length", f"{content.get('truncated_length', 0):,} chars")
            with col3:
                if content.get('was_truncated'):
                    st.error("Content Truncated")
                else:
                    st.success("Content Not Truncated")
            st.metric("Processing Time", f"{content.get('processing_time_ms', 0):.1f}ms")
    
    with debug_tabs[4]:  # API Information
        if "6_api_request" in debug_log:
            api_req = debug_log["6_api_request"]
            st.write(f"**URL:** {api_req.get('url')}")
            st.metric("Payload Size", f"{api_req.get('payload_size_bytes', 0):,} bytes")
            st.metric("Timeout", f"{api_req.get('timeout')} seconds")
            st.metric("Max Response Length", api_req.get('num_predict'))
        
        if "8_api_response" in debug_log:
            api_resp = debug_log["8_api_response"]
            col1, col2, col3 = st.columns(3)
            with col1:
                status_code = api_resp.get('status_code')
                if status_code == 200:
                    st.success(f"Status: {status_code}")
                else:
                    st.error(f"Status: {status_code}")
            with col2:
                st.metric("API Call Time", f"{api_resp.get('api_call_time_ms', 0):.1f}ms")
            with col3:
                st.metric("Total Time", f"{api_resp.get('total_processing_time_ms', 0):.1f}ms")
    
    with debug_tabs[5]:  # Response Processing
        if "9_response_data" in debug_log:
            resp_data = debug_log["9_response_data"]
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Response Length", f"{resp_data.get('response_length', 0):,} chars")
            with col2:
                st.write(f"**Response Keys:** {resp_data.get('raw_response_keys', [])}")
            
            if resp_data.get('response_preview'):
                st.text_area("Response Preview:", resp_data['response_preview'], height=100)
        
        if "10_response_processing" in debug_log:
            resp_proc = debug_log["10_response_processing"]
            col1, col2 = st.columns(2)
            with col1:
                if resp_proc.get('response_truncated'):
                    st.warning("Response was truncated due to length limit")
                else:
                    st.success("Response was not truncated")
            with col2:
                st.metric("Final Length", f"{resp_proc.get('final_response_length', 0):,} chars")
    
    with debug_tabs[6]:  # Error Information
        error_found = False
        
        if "11_api_error" in debug_log:
            error_found = True
            api_error = debug_log["11_api_error"]
            st.error(f"**API Error:** {api_error.get('error_message')}")
            st.write(f"**Status Code:** {api_error.get('status_code')}")
            if api_error.get('error_data'):
                st.json(api_error['error_data'])
            if api_error.get('response_text'):
                st.text_area("Response Text:", api_error['response_text'], height=100)
        
        if "12_timeout_error" in debug_log:
            error_found = True
            timeout_error = debug_log["12_timeout_error"]
            st.error(f"**Timeout Error:** {timeout_error.get('error_type')}")
            st.write(f"**Timeout:** {timeout_error.get('timeout_seconds')} seconds")
            st.write(f"**Processing Time:** {timeout_error.get('processing_time_ms'):.1f}ms")
        
        if "13_connection_error" in debug_log:
            error_found = True
            conn_error = debug_log["13_connection_error"]
            st.error(f"**Connection Error:** {conn_error.get('error_type')}")
            st.write(f"**Base URL:** {conn_error.get('base_url')}")
            st.text_area("Error Details:", conn_error.get('error_details', ''), height=80)
        
        if "14_unexpected_error" in debug_log:
            error_found = True
            unexp_error = debug_log["14_unexpected_error"]
            st.error(f"**Unexpected Error:** {unexp_error.get('error_type')}")
            st.text_area("Error Message:", unexp_error.get('error_message', ''), height=80)
            st.write(f"**Processing Time:** {unexp_error.get('processing_time_ms'):.1f}ms")
        
        if not error_found:
            st.success("✅ No errors detected in the AI processing pipeline")

def get_ai_assistance(document_type, document_content, user_input, custom_prompt=None, model=None, debug_mode=False):
    """Get AI assistance for document editing"""
    try:
        request_data = {
            "document_type": document_type,
            "document_content": document_content,
            "user_input": user_input,
            "debug_mode": debug_mode
        }
        
        if custom_prompt:
            request_data["custom_prompt"] = custom_prompt
        if model:
            request_data["model"] = model
        
        response = requests.post(
            f"{BACKEND_URL}/ai/assist",
            json=request_data,
            headers=get_auth_headers(),
            timeout=180  # 3 minutes timeout for AI requests
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
            return {
                "success": False,
                "error_message": error_data.get("detail", f"HTTP {response.status_code}")
            }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error_message": "AI request timed out. Please try again with shorter content or simpler requirements."
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Error getting AI assistance: {str(e)}"
        }

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
            # Filter to show both active and approved templates for document creation
            templates = response.json()
            if not status:  # If no status specified, show active and approved templates
                return [t for t in templates if t.get("status") in ["active", "approved"]]
            return templates
        return []
    except Exception as e:
        st.error(f"Error fetching templates: {e}")
        return []

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

def update_document(document_id, document_data):
    """Update document"""
    try:
        response = requests.put(
            f"{BACKEND_URL}/documents/{document_id}",
            json=document_data,
            headers=get_auth_headers()
        )
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def delete_document(document_id):
    """Delete document"""
    try:
        response = requests.delete(f"{BACKEND_URL}/documents/{document_id}", headers=get_auth_headers())
        
        # Handle different response formats
        try:
            response_data = response.json()
        except:
            # If response is not JSON (e.g., HTTPException), create error structure
            response_data = {"error": f"HTTP {response.status_code}: {response.text}"}
        
        return response_data, response.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def export_document_pdf(document_id):
    """Export document to PDF"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/documents/{document_id}/export",
            json={"format": "pdf", "include_metadata": True},
            headers=get_auth_headers()
        )
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def get_document_revisions(document_id):
    """Get document revision history"""
    try:
        response = requests.get(f"{BACKEND_URL}/documents/{document_id}/revisions", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching revisions: {e}")
        return []

# Main interface
projects = get_user_projects()
if not projects:
    st.warning("⚠️ You are not a member of any projects. Please join or create a project to manage documents.")
    st.stop()

# Project selection
st.subheader("📋 Select Project")
project_options = {p["name"]: p["id"] for p in projects}
selected_project_name = st.selectbox(
    "Project",
    options=list(project_options.keys()),
    key="selected_project"
)

if not selected_project_name:
    st.info("Please select a project to view documents.")
    st.stop()

selected_project_id = project_options[selected_project_name]
selected_project = next(p for p in projects if p["id"] == selected_project_id)

# Tabs for different operations
tab1, tab2, tab3 = st.tabs(["📋 Documents List", "➕ Create Document", "📚 Revision History"])

with tab1:
    
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
        # Find user ID by username
        for member in selected_project.get("members", []):
            if member["username"] == author_filter:
                created_by = member["user_id"]
                break
    
    documents = get_project_documents(selected_project_id, status, document_type, created_by)
    
    if documents:
        for doc in documents:
            with st.expander(f"📄 {doc['name']} (Rev {doc['current_revision']}) - {doc['status'].title()}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Document Type:** {doc['document_type'].replace('_', ' ').title()}")
                    st.write(f"**Status:** {doc['status'].title()}")
                    st.write(f"**Created by:** {doc['created_by_username']}")
                    st.write(f"**Created:** {doc['created_at'][:10]}")
                    st.write(f"**Last Updated:** {doc['updated_at'][:10]}")
                    
                    if doc['reviewers']:
                        reviewer_names = [r['username'] for r in doc['reviewers']]
                        st.write(f"**Reviewers:** {', '.join(reviewer_names)}")
                    
                    if doc['reviewed_at']:
                        st.write(f"**Last Reviewed:** {doc['reviewed_at'][:10]}")
                        if doc['reviewed_by_username']:
                            st.write(f"**Reviewed by:** {doc['reviewed_by_username']}")
                
                with col2:
                    # Action buttons
                    if st.button(f"👁️ View", key=f"view_{doc['id']}"):
                        st.session_state.view_document_id = doc['id']
                        st.rerun()
                    
                    if st.button(f"✏️ Edit", key=f"edit_{doc['id']}"):
                        st.session_state.edit_document_id = doc['id']
                        st.rerun()
                    
                    if st.button(f"📋 Export PDF", key=f"export_{doc['id']}"):
                        result, status_code = export_document_pdf(doc['id'])
                        if status_code == 200:
                            st.success(result['message'])
                        else:
                            st.error(f"Export failed: {result.get('error', 'Unknown error')}")
                    
                    # Handle delete with confirmation using session state
                    delete_confirm_key = f"confirm_delete_doc_{doc['id']}"
                    
                    if delete_confirm_key not in st.session_state:
                        # Show delete button
                        if st.button(f"🗑️ Delete", key=f"delete_{doc['id']}"):
                            st.session_state[delete_confirm_key] = True
                            st.rerun()
                    else:
                        # Show confirmation buttons
                        st.warning(f"⚠️ Are you sure you want to delete '{doc['name']}'?")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button(f"✅ Yes, Delete", key=f"confirm_yes_doc_{doc['id']}"):
                                result, status_code = delete_document(doc['id'])
                                if status_code in [200, 204] or (isinstance(result, dict) and result.get('success')):
                                    st.success("✅ **Document Deleted Successfully!**")
                                    st.success(f"Document **'{doc['name']}'** has been permanently removed.")
                                    # Clear confirmation state
                                    del st.session_state[delete_confirm_key]
                                    st.rerun()
                                else:
                                    st.error("❌ **Document Deletion Failed**")
                                    error_msg = result.get('error', f'HTTP {status_code}') if isinstance(result, dict) else f'HTTP {status_code}'
                                    st.error(f"**Error:** {error_msg}")
                                    del st.session_state[delete_confirm_key]
                        
                        with col2:
                            if st.button(f"❌ Cancel", key=f"confirm_no_doc_{doc['id']}"):
                                # Clear confirmation state
                                del st.session_state[delete_confirm_key]
                                st.rerun()
    else:
        st.info("No documents found. Create your first document using the 'Create Document' tab.")

with tab2:
    
    # Document type and creation method selection in same row
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
    
    # Show document type description (compact)
    selected_doc_type = next((dt for dt in document_types if dt['value'] == document_type), None)
    if selected_doc_type:
        st.caption(f"📋 {selected_doc_type['label']}: {selected_doc_type['description']}")
    
    # AI Assistant for Blank Document (outside form)
    if creation_method == "Blank Document":
        col_header, col_ai = st.columns([2, 1])
        with col_header:
            st.subheader("📝 AI Assistant")
        with col_ai:
            if st.button("🤖 AI Assist", help="Generate content with AI", key="create_ai_assist"):
                st.session_state.show_ai_assist_create = True
        
        # AI Assistant expander
        if st.session_state.get("show_ai_assist_create", False):
            with st.expander("🤖 AI Assistant", expanded=True):
                user_input = st.text_area(
                    "Describe what you need:",
                    placeholder="e.g., Create a project plan for a software development project with 5 team members...",
                    key="create_ai_input",
                    height=60
                )
                
                col_gen, col_close = st.columns([1, 1])
                with col_gen:
                    if st.button("🚀 Generate", key="create_submit_ai", type="primary"):
                        if user_input.strip():
                            with st.spinner("Generating..."):
                                mapped_doc_type = map_document_category_to_specific_type(document_type)
                                ai_response = get_ai_assistance(
                                    document_type=mapped_doc_type,
                                    document_content="",
                                    user_input=user_input,
                                    debug_mode=False
                                )
                                if ai_response.get("success"):
                                    st.session_state.ai_generated_content_create = ai_response["response"]
                                    st.session_state.show_ai_assist_create = False
                                    st.success("✅ Content generated!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {ai_response.get('error_message', 'Error occurred')}")
                        else:
                            st.warning("Please describe what you need.")
                
                with col_close:
                    if st.button("❌ Close", key="create_close_ai"):
                        st.session_state.show_ai_assist_create = False
                        st.rerun()
    
    # Template/Document selection (outside form so it updates immediately)
    template_content = ""
    template_id = None
    
    # Clear template content when switching to blank document
    if creation_method == "Blank Document":
        if "template_content_create" in st.session_state:
            del st.session_state.template_content_create
        if "selected_template_info" in st.session_state:
            del st.session_state.selected_template_info
    
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
                # Store in session state so it persists for the editor
                st.session_state.template_content_create = template_content
                st.session_state.selected_template_id = template_id
                # Store template info in session state too
                st.session_state.selected_template_info = f"Template: {selected_template['name']} - {selected_template['description']}"
                st.info(st.session_state.selected_template_info)
        else:
            st.warning("No templates available for this document type.")
    
    elif creation_method == "From Previous Version":
        # Get documents for copying
        all_docs = get_project_documents(selected_project_id)
        if all_docs:
            doc_options = {f"{d['name']} (Rev {d['current_revision']})": d["id"] for d in all_docs}
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
                    # Store in session state so it persists for the editor
                    st.session_state.template_content_create = template_content
                    st.info(f"Copying content from: {copy_doc['name']}")
        else:
            st.warning("No documents available to copy from.")
    
    with st.form("create_document_form"):
        # Basic information (more compact)
        name = st.text_input("Document Name", placeholder="Enter document name")
        
        # Document content editor
        st.subheader("📝 Document Content")
        
        # Get content from various sources
        initial_content = ""
        editor_key = "create_document_content"
        
        if st.session_state.get("ai_generated_content_create"):
            initial_content = st.session_state.ai_generated_content_create
            del st.session_state.ai_generated_content_create
        elif st.session_state.get("template_content_create"):
            initial_content = st.session_state.template_content_create
            # Use template ID in key to force re-initialization when template changes
            if st.session_state.get("selected_template_id"):
                editor_key = f"create_document_content_{st.session_state.selected_template_id}"
        
        content = st_ace(
            value=initial_content,
            language='markdown',
            theme='github',
            key=editor_key,
            height=300,
            auto_update=False,
            placeholder="Enter your document content in Markdown format...",
            wrap=False,
            font_size=14
        )
        
        # Document status (more compact)
        col_status, col_comment = st.columns([1, 2])
        with col_status:
            status = st.selectbox(
                "Document Status",
                ["draft", "request_review", "approved"],
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
        
        # Reviewer selection (inline)
        reviewers = []
        if status == "request_review":
            project_members = get_project_members(selected_project_id)
            if project_members:
                reviewer_options = st.multiselect(
                    "👥 Select Reviewers",
                    options=[member["user_id"] for member in project_members],
                    format_func=lambda x: next((member["username"] for member in project_members if member["user_id"] == x), "Unknown"),
                    key="document_reviewers",
                    help="Choose team members to review this document"
                )
                reviewers = reviewer_options
            else:
                st.warning("⚠️ No project members available for review.")
        
        # Submit button
        if st.form_submit_button("🚀 Create Document"):
            # Validation
            errors = []
            
            if not name or not name.strip():
                errors.append("Document name is required")
            
            if not content or not content.strip():
                errors.append("Document content is required")
            
            if status == "request_review" and not reviewers:
                errors.append("Please select at least one reviewer when requesting review")
            
            if status != "draft" and (not comment or not comment.strip()):
                errors.append("Comment is required when status is not draft")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Get template_id from session state if available
                template_id_to_use = st.session_state.get("selected_template_id", None)
                document_data = {
                    "name": name.strip(),
                    "document_type": document_type,
                    "content": content.strip(),
                    "status": status,
                    "template_id": template_id_to_use,
                    "comment": comment.strip()
                }
                
                # Add reviewers if requesting review
                if status == "request_review":
                    document_data["reviewers"] = reviewers
                
                with st.spinner("Creating document..."):
                    result, status_code = create_document(selected_project_id, document_data)
                
                if status_code == 200:
                    # Store success message in session state to persist after rerun
                    st.session_state.document_success_message = f"Document **'{name}'** was created successfully!"
                    st.session_state.show_doc_success_until = time.time() + 5  # Show for 5 seconds
                    # Clear template content from session state
                    if "template_content_create" in st.session_state:
                        del st.session_state.template_content_create
                    
                    st.success(f"✅ **Document Created Successfully!**")
                    st.success(f"Document **'{name}'** has been created in {selected_project_name}.")
                    st.balloons()
                    
                    # Add a small delay to let user see the message before rerun
                    st.info("🔄 Refreshing page to clear form...")
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error("❌ **Document Creation Failed**")
                    # Handle both 'error' and 'detail' keys from different response formats
                    error_msg = result.get('error') or result.get('detail', 'Unknown error occurred')
                    st.error(f"**Error:** {error_msg}")
                    
                    # Show specific guidance based on error type
                    if "already exists" in error_msg.lower():
                        st.info("💡 **Tip:** Choose a different document name or check existing documents in this project.")

with tab3:
    
    if documents:
        # Document selection for revision history
        doc_options = {f"{d['name']} (Rev {d['current_revision']})": d["id"] for d in documents}
        selected_doc_name = st.selectbox(
            "Select Document",
            options=list(doc_options.keys()),
            key="revision_history_doc"
        )
        
        if selected_doc_name:
            doc_id = doc_options[selected_doc_name]
            revisions = get_document_revisions(doc_id)
            
            if revisions:
                st.subheader(f"Revision History for {selected_doc_name}")
                
                for revision in revisions:
                    with st.expander(f"📝 Revision {revision['revision_number']} - {revision['status'].title()} ({revision['created_at'][:10]})"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**Status:** {revision['status'].title()}")
                            st.write(f"**Created by:** {revision['created_by_username']}")
                            st.write(f"**Date:** {revision['created_at']}")
                            
                            if revision['comment']:
                                st.write(f"**Comment:** {revision['comment']}")
                            
                            if revision['reviewers']:
                                reviewer_info = []
                                for reviewer in revision['reviewers']:
                                    status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(reviewer['status'], "❓")
                                    reviewer_info.append(f"{status_emoji} {reviewer['username']}")
                                st.write(f"**Reviewers:** {', '.join(reviewer_info)}")
                        
                        with col2:
                            if st.button(f"👀 View Content", key=f"view_rev_{revision['id']}"):
                                st.session_state.view_revision_id = revision['id']
                                st.session_state.view_revision_content = revision['content']
                                st.rerun()
            else:
                st.info("No revision history available for this document.")
    else:
        st.info("No documents available. Create a document first to view revision history.")

# Handle document viewing
if 'view_document_id' in st.session_state:
    document = get_document_by_id(st.session_state.view_document_id)
    if document:
        st.subheader(f"👀 Viewing: {document['name']}")
        
        # Document metadata
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Status:** {document['status'].title()}")
            st.write(f"**Document Type:** {document['document_type'].replace('_', ' ').title()}")
            st.write(f"**Revision:** {document['current_revision']}")
        with col2:
            st.write(f"**Created by:** {document['created_by_username']}")
            st.write(f"**Created:** {document['created_at'][:10]}")
            st.write(f"**Last Updated:** {document['updated_at'][:10]}")
        
        # Document content
        st.subheader("📄 Content")
        st.markdown(document['content'])
        
        if st.button("❌ Close View"):
            del st.session_state.view_document_id
            st.rerun()

# Handle document editing
if 'edit_document_id' in st.session_state:
    document = get_document_by_id(st.session_state.edit_document_id)
    if document:
        st.subheader(f"✏️ Editing: {document['name']}")
        
        # Document info (compact)
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.caption(f"📋 {document['document_type']} • Rev {document['current_revision']} • {document['status'].title()}")
        with col_info2:
            st.caption(f"👤 {document['created_by_username']} • {document['created_at'][:10]}")
            
        # Skip AI Assistant in edit mode for cleaner layout
        if False:  # Disabled AI Assistant for editing
            with st.expander("🤖 AI Assistant", expanded=True):
                st.write("Get AI assistance to improve your document content.")
                
                # Get appropriate prompt for current document type
                current_doc_type = document['document_type']
                ai_prompt = get_ai_prompt_for_document_type(current_doc_type)
                if ai_prompt:
                    with st.expander("💡 View AI Prompt Template", expanded=False):
                        st.write(f"**Document Type:** {current_doc_type.replace('_', ' ').title()}")
                        st.markdown("**AI Prompt:**")
                        prompt_display = ai_prompt.replace('[configurable_item]', '**[Your Requirements]**')
                        st.markdown(f"_{prompt_display}_")
                        st.info("💡 Your requirements below will replace **[Your Requirements]** in the prompt above.")
                
                user_input = st.text_area(
                    "Your specific requirements:",
                    placeholder="e.g., Add more detail to the risk management section, improve clarity of procedures, enhance technical specifications...",
                    key="edit_ai_input",
                    height=80,
                    help="This will replace [configurable_item] in the AI prompt above"
                )
                
                col_ai1, col_ai2, col_ai3 = st.columns(3)
                with col_ai1:
                    use_custom_prompt = st.checkbox("Use custom prompt", key="edit_use_custom")
                with col_ai2:
                    debug_mode = st.checkbox("Debug mode", key="edit_debug_mode", help="Show detailed AI processing logs")
                with col_ai3:
                    if st.button("❌ Close AI Assist", key="edit_close_ai"):
                        st.session_state.show_ai_assist_edit = False
                        st.rerun()
                
                custom_prompt = None
                if use_custom_prompt:
                    custom_prompt = st.text_area(
                        "Custom prompt:",
                        placeholder="Enter your custom AI prompt here...",
                        key="edit_custom_prompt",
                        height=80
                    )
                
                col_submit, col_loading = st.columns([1, 3])
                
                with col_submit:
                    if st.button("🚀 Generate Improvements", key="edit_submit_ai", type="primary"):
                        if user_input.strip():
                            with st.spinner("AI is analyzing and improving content..."):
                                # Use mapped document type for AI request
                                mapped_doc_type = map_document_category_to_specific_type(document['document_type'])
                                ai_response = get_ai_assistance(
                                    document_type=mapped_doc_type,
                                    document_content=document['content'],
                                    user_input=user_input,
                                    custom_prompt=custom_prompt,
                                    debug_mode=debug_mode
                                )
                                st.session_state.edit_ai_response = ai_response
                        else:
                            st.warning("Please describe what you want the AI to help with.")
                
                # Display AI response
                if st.session_state.get("edit_ai_response"):
                    ai_response = st.session_state.edit_ai_response
                    if ai_response.get("success"):
                        st.subheader("💡 AI Suggestions")
                        st.markdown(ai_response["response"])
                        
                        col_use, col_dismiss = st.columns(2)
                        with col_use:
                            if st.button("✅ Use This Content", key="edit_use_content", type="primary"):
                                st.session_state.ai_generated_content_edit = ai_response["response"]
                                st.session_state.show_ai_assist_edit = False
                                if "edit_ai_response" in st.session_state:
                                    del st.session_state.edit_ai_response
                                st.success("✅ Content will be loaded in the form below!")
                                st.rerun()
                        
                        with col_dismiss:
                            if st.button("❌ Dismiss", key="edit_dismiss_ai"):
                                del st.session_state.edit_ai_response
                                st.rerun()
                        
                        # Show metadata and debug info
                        if ai_response.get("metadata"):
                            metadata = ai_response["metadata"]
                            
                            # Regular metadata
                            with st.expander("ℹ️ Details", expanded=False):
                                st.write(f"**Model:** {metadata.get('model_used', 'N/A')}")
                                st.write(f"**Processing time:** {metadata.get('processing_time', 0):.1f}s")
                                st.write(f"**Response length:** {metadata.get('response_length', 0)} characters")
                            
                            # Debug log if available
                            if metadata.get("debug_log"):
                                with st.expander("🔍 Debug Information", expanded=False):
                                    display_debug_log(metadata["debug_log"])
                    else:
                        st.error(f"❌ {ai_response.get('error_message', 'Unknown error')}")
                        
                        # Show debug info for errors
                        if ai_response.get("metadata", {}).get("debug_log"):
                            with st.expander("🔍 Debug Information", expanded=False):
                                display_debug_log(ai_response["metadata"]["debug_log"])
                        
                        if st.button("🔄 Try Again", key="edit_ai_retry"):
                            del st.session_state.edit_ai_response
                            st.rerun()
        
        st.divider()
        
        with st.form("edit_document_form"):
            name = st.text_input("Document Name", value=document['name'])
            
            document_types = get_document_types()
            current_doc_type_idx = next((i for i, dt in enumerate(document_types) if dt['value'] == document['document_type']), 0)
            document_type = st.selectbox(
                "Document Type",
                options=[dt['value'] for dt in document_types],
                format_func=lambda x: next((dt['label'] for dt in document_types if dt['value'] == x), x),
                index=current_doc_type_idx,
                key="edit_document_type"
            )
            
            # Document content editor
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader("📝 Document Content")
            
            with col2:
                st.write("💡 Use AI Assistant above form")
            
            # Handle AI content updates
            current_content = document['content']
            if st.session_state.get("ai_generated_content_edit"):
                current_content = st.session_state.ai_generated_content_edit
                del st.session_state.ai_generated_content_edit
            
            content = st_ace(
                value=current_content,
                language='markdown',
                theme='github',
                key="edit_document_content",
                height=400,
                auto_update=False,
                placeholder="Enter your document content in Markdown format...",
                wrap=False,
                font_size=14
            )
            
            # Status and workflow
            current_status_idx = ["draft", "request_review", "approved"].index(document['status']) if document['status'] in ["draft", "request_review", "approved"] else 0
            status = st.selectbox(
                "Document Status",
                ["draft", "request_review", "approved"],
                format_func=lambda x: x.replace('_', ' ').title(),
                index=current_status_idx,
                key="edit_document_status"
            )
            
            # Comment for revision history (only when not draft)
            comment = ""
            if status != "draft":
                comment = st.text_area(
                    "Comment (for revision history)",
                    placeholder="Brief description of changes...",
                    key="edit_document_comment",
                    help="Required when changing status from draft"
                )
            
            # Reviewer selection if requesting review
            reviewers = []
            if status == "request_review":
                project_members = get_project_members(selected_project_id)
                if project_members:
                    current_reviewers = [r['user_id'] for r in document.get('reviewers', [])]
                    reviewer_options = st.multiselect(
                        "Choose Reviewers",
                        options=[member["user_id"] for member in project_members],
                        default=current_reviewers,
                        format_func=lambda x: next((member["username"] for member in project_members if member["user_id"] == x), "Unknown"),
                        key="edit_document_reviewers"
                    )
                    reviewers = reviewer_options
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.form_submit_button("💾 Save Changes"):
                    # Validation
                    errors = []
                    
                    if not name or not name.strip():
                        errors.append("Document name is required")
                    
                    if not content or not content.strip():
                        errors.append("Document content is required")
                    
                    if status == "request_review" and not reviewers:
                        errors.append("Please select at least one reviewer when requesting review")
                    
                    if status != "draft" and (not comment or not comment.strip()):
                        errors.append("Comment is required when status is not draft")
                    
                    if errors:
                        for error in errors:
                            st.error(f"❌ {error}")
                    else:
                        document_data = {
                            "name": name.strip(),
                            "document_type": document_type,
                            "content": content.strip(),
                            "status": status,
                            "comment": comment.strip()
                        }
                        
                        if status == "request_review":
                            document_data["reviewers"] = reviewers
                        
                        with st.spinner("Updating document..."):
                            result, status_code = update_document(st.session_state.edit_document_id, document_data)
                    
                    if status_code == 200:
                        st.success("✅ **Document Updated Successfully!**")
                        st.success(f"Document **'{name}'** has been updated.")
                        del st.session_state.edit_document_id
                        st.rerun()
                    else:
                        st.error("❌ **Document Update Failed**")
                        error_msg = result.get('error', 'Unknown error occurred')
                        st.error(f"**Error:** {error_msg}")
            
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    del st.session_state.edit_document_id
                    st.rerun()

# Handle revision content viewing
if 'view_revision_id' in st.session_state and 'view_revision_content' in st.session_state:
    st.subheader(f"📝 Revision Content")
    st.markdown(st.session_state.view_revision_content)
    
    if st.button("❌ Close Revision View"):
        del st.session_state.view_revision_id
        del st.session_state.view_revision_content
        st.rerun()