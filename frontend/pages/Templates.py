# frontend/pages/Templates.py
import streamlit as st
import requests
import json
import time
import pandas as pd
from datetime import datetime
from streamlit_ace import st_ace
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers, BACKEND_URL

require_auth()

st.set_page_config(page_title="Templates", page_icon="📄", layout="wide")

# Add CSS for more compact layout
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
    .stMetric {
        font-size: 14px;
    }
    .stButton > button {
        font-size: 14px;
        padding: 0.25rem 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("📄 Templates Management")

setup_authenticated_sidebar()


# Display persistent success message if present
if hasattr(st.session_state, 'template_success_message') and hasattr(st.session_state, 'show_success_until'):
    if time.time() < st.session_state.show_success_until:
        st.success(f"✅ {st.session_state.template_success_message}")
    else:
        # Clear the message after timeout
        delattr(st.session_state, 'template_success_message')
        delattr(st.session_state, 'show_success_until')

# Utility functions
def get_document_types():
    return [
        {"label": "Planning Documents", "value": "planning_documents"},
        {"label": "Process Documents", "value": "process_documents"},
        {"label": "Specifications", "value": "specifications"},
        {"label": "Records", "value": "records"},
        {"label": "Templates", "value": "templates"},
        {"label": "Policies", "value": "policies"},
        {"label": "Manuals", "value": "manuals"}
    ]

def create_template(template_data):
    try:
        response = requests.post(f"{BACKEND_URL}/templates", json=template_data, headers=get_auth_headers())
        if response.status_code == 200:
            return response.json(), response.status_code
        elif response.status_code == 401:
            return {"error": "Authentication failed. Please log in again."}, response.status_code
        elif response.status_code == 422:
            try:
                error_json = response.json()
                return {"error": f"Validation error: {error_json}"}, response.status_code
            except:
                return {"error": f"Validation error: {response.text}"}, response.status_code
        else:
            try:
                return error_json, response.status_code
            except:
                return {"error": f"Server returned {response.status_code}: {response.text}"}, response.status_code
    except Exception as e:
        return {"error": f"Network error: {str(e)}"}, None

def get_templates(status=None, document_type=None):
    try:
        params = {}
        if status:
            params["status"] = status
        if document_type:
            params["document_type"] = document_type
        
        response = requests.get(f"{BACKEND_URL}/templates", params=params, headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
    except Exception:
        return []
    return []

def get_template_by_id(template_id):
    try:
        response = requests.get(f"{BACKEND_URL}/templates/{template_id}", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None
    return None

def update_template(template_id, template_data):
    try:
        response = requests.put(f"{BACKEND_URL}/templates/{template_id}", json=template_data, headers=get_auth_headers())
        if response.status_code == 200:
            return response.json(), response.status_code
        else:
            # Handle non-200 responses
            try:
                error_json = response.json()
                return {"error": f"Server error: {error_json}"}, response.status_code
            except:
                return {"error": f"Server returned {response.status_code}: {response.text}"}, response.status_code
    except Exception as e:
        return {"error": f"Network error: {str(e)}"}, None

def delete_template(template_id):
    response = requests.delete(f"{BACKEND_URL}/templates/{template_id}", headers=get_auth_headers())
    return response.json(), response.status_code

def export_template_pdf(template_id):
    try:
        response = requests.post(
            f"{BACKEND_URL}/templates/{template_id}/export",
            json={"format": "pdf", "include_metadata": True},
            headers=get_auth_headers()
        )
        result = response.json()
        
        if response.status_code == 200 and result.get("success"):
            # Handle successful export
            if "pdf_data" in result:
                # Decode PDF and offer download
                import base64
                pdf_bytes = base64.b64decode(result["pdf_data"])
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_bytes,
                    file_name=result["filename"],
                    mime="application/pdf",
                    type="primary"
                )
                return {"message": "PDF generated successfully!"}, 200
            elif "html_data" in result:
                # Fallback HTML export
                import base64
                html_bytes = base64.b64decode(result["html_data"])
                st.download_button(
                    label="📥 Download HTML",
                    data=html_bytes,
                    file_name=result["filename"],
                    mime="text/html",
                    type="primary"
                )
                message = result.get("message", "HTML export generated successfully!")
                return {"message": message}, 200
        else:
            # Enhanced error reporting
            error_msg = f"Status: {response.status_code}, Response: {result}"
            return {"error": error_msg}, response.status_code
        
        return result, response.status_code
    except Exception as e:
        return {"error": f"Export failed: {str(e)}"}, 500

# Main interface
col1, col2 = st.columns([3, 1])
with col1:
    st.write("")  # Empty space
with col2:
    if st.button("➕ New Template", type="primary"):
        st.session_state.show_create_template = True

# Filters
filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    status_filter = st.selectbox(
        "📊 Filter by Status",
        ["All", "active", "draft", "request_review", "approved"],
        key="status_filter"
    )

with filter_col2:
    document_types = get_document_types()
    doc_type_options = ["All"] + [dt["value"] for dt in document_types]
    doc_type_labels = ["All"] + [dt["label"] for dt in document_types]
    doc_type_filter = st.selectbox(
        "📁 Filter by Type",
        options=doc_type_options,
        format_func=lambda x: doc_type_labels[doc_type_options.index(x)] if x in doc_type_options else x,
        key="doc_type_filter"
    )

with filter_col3:
    search_term = st.text_input("🔍 Search templates", placeholder="Search by name...")

# Get templates
status = None if status_filter == "All" else status_filter
document_type = None if doc_type_filter == "All" else doc_type_filter
templates = get_templates(status, document_type)

# Filter by search term
if search_term and templates:
    templates = [t for t in templates if 
                search_term.lower() in t['name'].lower() or 
                search_term.lower() in t['description'].lower()]

# Split into two columns - template list on left, editor on right
if templates:
    st.markdown(f"**Found {len(templates)} templates**")
    
    main_col1, main_col2 = st.columns([2, 3])  # Template List:Document Editor ratio 2:3
    
    with main_col1:
        st.markdown("### Templates List")
        
        # Prepare data for dataframe - only File, Description, Status columns
        df_data = []
        for template in templates:
            # Truncate description for display
            desc_display = template['description'][:60] + "..." if len(template['description']) > 60 else template['description']
            
            df_row = {
                'File': f"{template['name']} (v{template['version']})",
                'Description': desc_display,
                'Status': template['status'].title()
            }
            df_data.append(df_row)
        
        # Create DataFrame for templates
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
        
        st.caption("💡 Select a row to edit the template")
        
        # Handle template selection for editing
        if selected_indices and len(selected_indices.selection.rows) > 0:
            selected_idx = selected_indices.selection.rows[0]
            template_id = templates[selected_idx]['id']
            # Only rerun if this is a different template
            if st.session_state.get('edit_template_id') != template_id:
                st.session_state.edit_template_id = template_id
                st.session_state.show_edit_in_editor = True
                st.rerun()
    
    with main_col2:
        st.markdown("### Document Editor")
        
        # Show editor based on current state
        if st.session_state.get("show_edit_in_editor", False) and st.session_state.get("edit_template_id"):
            template = get_template_by_id(st.session_state.edit_template_id)
            if template:
                st.markdown(f"**Editing:** {template['name']}")
                
                with st.form("editor_form"):
                    # Basic template info - each field gets full width for visibility
                    edit_name = st.text_input("Name", value=template['name'])
                    
                    edit_status = st.selectbox("Status", ["active", "draft", "request_review", "approved"], 
                                             index=["active", "draft", "request_review", "approved"].index(template['status']))
                    
                    # Document type selection - full width for visibility
                    document_types = get_document_types()
                    current_doc_type = template['document_type']
                    doc_type_values = [dt["value"] for dt in document_types]
                    doc_type_labels = [dt["label"] for dt in document_types]
                    
                    try:
                        current_index = doc_type_values.index(current_doc_type)
                    except ValueError:
                        # If not found, default to first option
                        current_index = 0
                    
                    edit_document_type = st.selectbox(
                        "Document Type",
                        options=doc_type_values,
                        format_func=lambda x: doc_type_labels[doc_type_values.index(x)] if x in doc_type_values else x,
                        index=current_index,
                        key=f"doc_type_inline_{template['id']}"
                    )
                    
                    # Tags and description fields
                    edit_tags = st.text_input("Tags", value=", ".join(template['tags']))
                    edit_description = st.text_area("Description", value=template['description'], height=60)
                    
                    # Editor
                    edit_content = st_ace(
                        value=template['content'],
                        language='markdown',
                        theme='github',
                        key=f"editor_{template['id']}",
                        height=300,
                        auto_update=False
                    )
                    
                    # Action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Save", type="primary"):
                            # Validate required fields
                            if not edit_name or not edit_name.strip():
                                st.error("Template name is required")
                            elif not edit_content or not edit_content.strip():
                                st.error("Template content is required")
                            else:
                                template_data = {
                                    "name": edit_name.strip(),
                                    "description": edit_description.strip() if edit_description else "",
                                    "document_type": edit_document_type,
                                    "content": edit_content.strip(),
                                    "tags": [tag.strip() for tag in edit_tags.split(",") if tag.strip()] if edit_tags else [],
                                    "status": edit_status
                                }
                                
                                result, status_code = update_template(st.session_state.edit_template_id, template_data)
                                
                                if status_code == 200:
                                    st.session_state.template_success_message = f"Template '{edit_name}' updated successfully!"
                                    st.session_state.show_success_until = time.time() + 5
                                    st.session_state.show_edit_in_editor = False
                                    st.rerun()
                                else:
                                    error_msg = result.get('error', 'Unknown error')
                                    if status_code == 403:
                                        st.error("🚫 **Permission Denied**: You can only edit templates that you created, or you need admin privileges.")
                                        st.info("💡 **Tip**: If you need to modify this template, contact the template creator or an administrator.")
                                    else:
                                        st.error(f"Failed to update: {error_msg}")
                    
                    with col2:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state.show_edit_in_editor = False
                            st.rerun()
        else:
            st.info("Select a template from the list to edit it here.")

else:
    st.info("No templates found matching your criteria. Create your first template to get started!")

# Create Template Form
if st.session_state.get("show_create_template", False):
    st.markdown("---")
    st.markdown("### ➕ Create New Template")
    
    with st.form("create_template_form"):
        create_col1, create_col2 = st.columns(2)
        
        with create_col1:
            create_name = st.text_input("Template Name", placeholder="Enter template name...")
            create_document_type = st.selectbox(
                "Document Type",
                options=[dt["value"] for dt in document_types],
                format_func=lambda x: next(dt["label"] for dt in document_types if dt["value"] == x)
            )
        
        with create_col2:
            create_tags = st.text_input("Tags (comma-separated)", placeholder="tag1, tag2, tag3...")
            create_description = st.text_area("Description", placeholder="Brief description...")
        
        create_content = st_ace(
            value="",
            language='markdown',
            theme='github',
            key="create_template_content",
            height=400,
            auto_update=False,
            placeholder="Enter your template content in Markdown format..."
        )
        
        form_col1, form_col2 = st.columns(2)
        with form_col1:
            if st.form_submit_button("🚀 Create Template", type="primary"):
                if create_name and create_content:
                    template_data = {
                        "name": create_name,
                        "description": create_description,
                        "document_type": create_document_type,
                        "content": create_content,
                        "tags": [tag.strip() for tag in create_tags.split(",") if tag.strip()]
                    }
                    
                    result, status_code = create_template(template_data)
                    
                    if status_code == 200:
                        st.session_state.template_success_message = f"Template '{create_name}' created successfully!"
                        st.session_state.show_success_until = time.time() + 5
                        st.session_state.show_create_template = False
                        st.rerun()
                    else:
                        st.error(f"Failed to create template: {result.get('error', 'Unknown error')}")
                else:
                    st.error("Please fill in at least the template name and content.")
        
        with form_col2:
            if st.form_submit_button("❌ Cancel"):
                st.session_state.show_create_template = False
                st.rerun()

# Edit Template Form  
if st.session_state.get("show_edit_template", False):
    template = get_template_by_id(st.session_state.edit_template_id)
    if template:
        st.markdown("---")
        st.markdown("### ✏️ Edit Template")
        
        with st.form("edit_template_form"):
            edit_col1, edit_col2 = st.columns(2)
            
            with edit_col1:
                edit_name = st.text_input("Template Name", value=template['name'])
                status_options = ["active", "draft", "request_review", "approved"]
                current_status_index = status_options.index(template['status']) if template['status'] in status_options else 0
                edit_status = st.selectbox("Status", status_options, index=current_status_index)
            
            with edit_col2:
                # Map database document type to frontend format
                doc_type_mapping = {
                    "Planning Documents": "planning_documents",
                    "Process Documents": "process_documents",
                    "Specifications": "specifications",
                    "Records": "records",
                    "Templates": "templates",
                    "Policies": "policies",
                    "Manuals": "manuals"
                }
                
                current_doc_type = doc_type_mapping.get(template['document_type'], "process_documents")
                doc_type_values = [dt["value"] for dt in document_types]
                current_doc_type_index = doc_type_values.index(current_doc_type) if current_doc_type in doc_type_values else 0
                
                edit_document_type = st.selectbox(
                    "Document Type",
                    options=doc_type_values,
                    format_func=lambda x: next(dt["label"] for dt in document_types if dt["value"] == x),
                    index=current_doc_type_index
                )
                edit_tags = st.text_input("Tags (comma-separated)", value=", ".join(template['tags']))
            
            edit_description = st.text_area("Description", value=template['description'])
            
            edit_content = st_ace(
                value=template['content'],
                language='markdown',
                theme='github',
                key=f"edit_template_content_{template['id']}",
                height=400,
                auto_update=False,
                placeholder="Enter your template content in Markdown format..."
            )
            
            form_col1, form_col2 = st.columns(2)
            with form_col1:
                if st.form_submit_button("💾 Update Template", type="primary"):
                    template_data = {
                        "name": edit_name,
                        "description": edit_description,
                        "document_type": edit_document_type,
                        "content": edit_content,
                        "tags": [tag.strip() for tag in edit_tags.split(",") if tag.strip()],
                        "status": edit_status
                    }
                    
                    result, status_code = update_template(st.session_state.edit_template_id, template_data)
                    
                    if status_code == 200:
                        st.session_state.template_success_message = f"Template '{edit_name}' updated successfully!"
                        st.session_state.show_success_until = time.time() + 5
                        st.session_state.show_edit_template = False
                        st.rerun()
                    else:
                        st.error(f"Failed to update template: {result.get('error', 'Unknown error')}")
            
            with form_col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state.show_edit_template = False
                    st.rerun()

# Delete confirmation
if st.session_state.get("show_delete_confirm", False):
    st.markdown("---")
    st.warning("### ⚠️ Confirm Deletion")
    st.write("Are you sure you want to delete this template? This action cannot be undone.")
    
    del_col1, del_col2 = st.columns(2)
    with del_col1:
        if st.button("🗑️ Delete Template", type="primary"):
            result, status_code = delete_template(st.session_state.delete_template_id)
            if status_code == 200:
                st.session_state.template_success_message = "Template deleted successfully!"
                st.session_state.show_success_until = time.time() + 5
                st.session_state.show_delete_confirm = False
                st.rerun()
            else:
                st.error(f"Failed to delete template: {result.get('error', 'Unknown error')}")
    
    with del_col2:
        if st.button("❌ Cancel"):
            st.session_state.show_delete_confirm = False
            st.rerun()

# Footer stats
if templates:
    st.markdown("---")
    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
    
    total_templates = len(templates)
    draft_count = len([t for t in templates if t['status'] == 'draft'])
    approved_count = len([t for t in templates if t['status'] == 'approved'])
    review_count = len([t for t in templates if t['status'] == 'request_review'])
    active_count = len([t for t in templates if t['status'] == 'active'])
    
    with stats_col1:
        st.metric("Total Templates", total_templates)
    with stats_col2:
        st.metric("Active", active_count)
    with stats_col3:
        st.metric("Draft", draft_count)
    with stats_col4:
        st.metric("Approved", approved_count)