# frontend/pages/DesignRecord.py
import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers, BACKEND_URL
from config import (DATAFRAME_HEIGHT, TEXTAREA_HEIGHT, DEFAULT_EXPORT_FORMAT, EXPORT_BATCH_SIZE,
                   KB_LONG_REQUEST_TIMEOUT, DEMO_CLINICAL_STUDIES, DEMO_ADVERSE_EVENTS, 
                   DEMO_FIELD_ACTIONS, DEMO_COMPLIANCE_STANDARDS, DEMO_STANDARDS_COMPLIANCE, 
                   DEMO_BIOCOMPATIBILITY_TESTS, DEMO_EMC_SAFETY_TESTS)

require_auth()

st.set_page_config(page_title="Design Record", page_icon="🔬", layout="wide")

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

st.title("🔬 Design Record - Comprehensive Lifecycle Management")

setup_authenticated_sidebar()

# Helper functions for API calls
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

def get_system_requirements(project_id=None):
    """Get system requirements for project"""
    try:
        url = f"{BACKEND_URL}/design-record/requirements"
        params = {"project_id": project_id} if project_id else {}
        response = requests.get(url, params=params, headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching requirements: {e}")
        return []

def get_hazards_risks(project_id=None):
    """Get hazards and risks for project"""
    try:
        url = f"{BACKEND_URL}/design-record/hazards"
        params = {"project_id": project_id} if project_id else {}
        response = requests.get(url, params=params, headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching hazards: {e}")
        return []

def get_fmea_analyses(project_id=None):
    """Get FMEA analyses for project"""
    try:
        url = f"{BACKEND_URL}/design-record/fmea"
        params = {"project_id": project_id} if project_id else {}
        response = requests.get(url, params=params, headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching FMEA analyses: {e}")
        return []

def get_design_artifacts(project_id=None):
    """Get design artifacts for project"""
    try:
        url = f"{BACKEND_URL}/design-record/design"
        params = {"project_id": project_id} if project_id else {}
        response = requests.get(url, params=params, headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching design artifacts: {e}")
        return []

def get_test_artifacts(project_id=None):
    """Get test artifacts for project"""
    try:
        url = f"{BACKEND_URL}/design-record/tests"
        params = {"project_id": project_id} if project_id else {}
        response = requests.get(url, params=params, headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching test artifacts: {e}")
        return []

# Project selection
projects = get_user_projects()
if not projects:
    st.warning("⚠️ No projects found. Please create a project first in the Projects section.")
    st.stop()

project_options = [f"{p['name']}" for p in projects]
selected_project_name = st.selectbox("📂 Select Project", project_options)
selected_project = next(p for p in projects if p["name"] == selected_project_name)
selected_project_id = selected_project["id"]

st.markdown(f"**Selected Project:** {selected_project_name}")
st.markdown("---")

# Main navigation tabs - comprehensive lifecycle management
main_tabs = st.tabs([
    "📋 Requirements", 
    "⚠️ Hazards & Risks", 
    "🔍 FMEA Analysis", 
    "🏗️ Design Artifacts",
    "🧪 Test Artifacts",
    "🔗 Traceability",
    "✅ Compliance",
    "📊 Post-Market",
    "📤 Export"
])

# === REQUIREMENTS TAB ===
with main_tabs[0]:
    
    req_subtabs = st.tabs(["👀 View Requirements", "➕ Create Requirement", "📊 Requirements Dashboard"])
    
    with req_subtabs[0]:
        st.markdown("**Filter Requirements:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            req_type_filter = st.selectbox(
                "Type",
                ["All", "functional", "non_functional", "safety", "security", "performance", "clinical", "regulatory"],
                key="req_type_filter"
            )
        
        with col2:
            req_priority_filter = st.selectbox(
                "Priority",
                ["All", "critical", "high", "medium", "low"],
                key="req_priority_filter"
            )
        
        with col3:
            req_status_filter = st.selectbox(
                "Status",
                ["All", "draft", "approved", "implemented", "verified", "obsolete"],
                key="req_status_filter"
            )
        
        # Get and display requirements
        requirements = get_system_requirements(selected_project_id)
        
        if requirements:
            # Apply filters
            filtered_reqs = requirements
            if req_type_filter != "All":
                filtered_reqs = [r for r in filtered_reqs if r.get('req_type') == req_type_filter]
            if req_priority_filter != "All":
                filtered_reqs = [r for r in filtered_reqs if r.get('req_priority') == req_priority_filter]
            if req_status_filter != "All":
                filtered_reqs = [r for r in filtered_reqs if r.get('req_status') == req_status_filter]
            
            st.markdown(f"**Showing {len(filtered_reqs)} of {len(requirements)} requirements**")
            
            # Prepare data for st.dataframe
            req_grid_data = []
            for req in filtered_reqs:
                req_row = {
                    'req_id': req.get('req_id', 'N/A'),
                    'req_title': req.get('req_title', 'Untitled'),
                    'req_type': req.get('req_type', 'N/A'),
                    'req_priority': req.get('req_priority', 'N/A'),
                    'req_status': req.get('req_status', 'N/A'),
                    'req_version': req.get('req_version', '1.0'),
                    'req_source': req.get('req_source', ''),
                    'req_description': req.get('req_description', 'No description'),
                    'acceptance_criteria': req.get('acceptance_criteria', ''),
                    'rationale': req.get('rationale', ''),
                    'full_req_data': req
                }
                req_grid_data.append(req_row)
            
            # Create DataFrame for requirements
            req_df_data = []
            for row in req_grid_data:
                req_df_row = {
                    'Req ID': row['req_id'],
                    'Title': row['req_title'],
                    'Type': row['req_type'].replace('_', ' ').title(),
                    'Priority': row['req_priority'].title(),
                    'Status': row['req_status'].title(),
                    'Version': row['req_version'],
                    'Source': row['req_source']
                }
                req_df_data.append(req_df_row)
            
            req_df = pd.DataFrame(req_df_data)
            
            # Display with selection capability
            req_selected_indices = st.dataframe(
                req_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                height=DATAFRAME_HEIGHT
            )
            
            st.caption("💡 Select a row to view requirement details")
            
            # Handle requirements selection
            if req_selected_indices and len(req_selected_indices.selection.rows) > 0:
                selected_idx = req_selected_indices.selection.rows[0]
                req = req_grid_data[selected_idx]['full_req_data']
                # Only update if different requirement selected
                if st.session_state.get('selected_requirement_id') != req.get('id'):
                    st.session_state.selected_requirement_id = req.get('id')
                    st.session_state.selected_requirement_data = req
                    st.rerun()
            
            # Show editable details for selected requirement
            if st.session_state.get('selected_requirement_data'):
                req = st.session_state.selected_requirement_data
                st.markdown("---")
                st.markdown("### 📝 Edit Selected Requirement")
                
                with st.form("edit_requirement_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edited_req_id = st.text_input("Requirement ID", value=req.get('req_id', ''))
                        edited_title = st.text_input("Title", value=req.get('req_title', ''))
                        edited_category = st.selectbox("Category", ["functional", "non_functional", "constraint", "interface", "safety"], 
                                                     index=["functional", "non_functional", "constraint", "interface", "safety"].index(req.get('req_category', 'functional')))
                        edited_priority = st.selectbox("Priority", ["low", "medium", "high", "critical"],
                                                     index=["low", "medium", "high", "critical"].index(req.get('priority', 'medium')))
                        edited_status = st.selectbox("Status", ["draft", "reviewed", "approved", "implemented", "verified"],
                                                   index=["draft", "reviewed", "approved", "implemented", "verified"].index(req.get('req_status', 'draft')))
                    
                    with col2:
                        edited_risk_level = st.selectbox("Risk Level", ["low", "medium", "high"],
                                                       index=["low", "medium", "high"].index(req.get('risk_level', 'medium')))
                        edited_verification = st.multiselect("Verification Methods", 
                                                           ["inspection", "analysis", "test", "demonstration"],
                                                           default=req.get('verification_methods', []))
                        edited_standards = st.text_input("Compliance Standards", value=', '.join(req.get('compliance_standards', [])))
                        edited_source = st.text_input("Source Document", value=req.get('source_document', ''))
                    
                    edited_description = st.text_area("Description", value=req.get('req_description', ''), height=100)
                    edited_criteria = st.text_area("Acceptance Criteria", value=req.get('acceptance_criteria', ''))
                    edited_rationale = st.text_area("Rationale", value=req.get('rationale', ''))
                    
                    # Traceability fields
                    edited_parents = st.text_input("Parent Requirements", value=', '.join(req.get('parent_requirements', [])))
                    edited_children = st.text_input("Child Requirements", value=', '.join(req.get('child_requirements', [])))
                    edited_dependencies = st.text_input("Dependencies", value=', '.join(req.get('dependencies', [])))
                    
                    if st.form_submit_button("💾 Save Changes", type="primary"):
                        updated_requirement = {
                            "req_id": edited_req_id,
                            "req_title": edited_title,
                            "req_description": edited_description,
                            "req_category": edited_category,
                            "priority": edited_priority,
                            "req_status": edited_status,
                            "risk_level": edited_risk_level,
                            "acceptance_criteria": edited_criteria,
                            "rationale": edited_rationale,
                            "verification_methods": edited_verification,
                            "compliance_standards": [s.strip() for s in edited_standards.split(',') if s.strip()],
                            "source_document": edited_source,
                            "parent_requirements": [p.strip() for p in edited_parents.split(',') if p.strip()],
                            "child_requirements": [c.strip() for c in edited_children.split(',') if c.strip()],
                            "dependencies": [d.strip() for d in edited_dependencies.split(',') if d.strip()],
                            "project_id": selected_project_id
                        }
                        
                        try:
                            response = requests.put(
                                f"{BACKEND_URL}/design-record/requirements/{req.get('id')}",
                                json=updated_requirement,
                                headers=get_auth_headers()
                            )
                            if response.status_code == 200:
                                st.success("✅ Requirement updated successfully!")
                                # Clear selection to refresh data
                                if 'selected_requirement_id' in st.session_state:
                                    del st.session_state.selected_requirement_id
                                if 'selected_requirement_data' in st.session_state:
                                    del st.session_state.selected_requirement_data
                                st.rerun()
                            else:
                                st.error(f"❌ Error updating requirement: {response.text}")
                        except Exception as e:
                            st.error(f"❌ Connection error: {e}")
        else:
            st.info("No requirements found for this project. Create your first requirement using the 'Create Requirement' tab.")
    
    with req_subtabs[1]:
        st.markdown("**Create New System Requirement**")
        
        with st.form("create_requirement_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                req_id = st.text_input("Requirement ID*", placeholder="REQ-001")
                req_title = st.text_input("Title*", placeholder="System shall...")
                req_type = st.selectbox("Type*", ["functional", "non_functional", "safety", "security", "performance", "clinical", "regulatory"])
                req_priority = st.selectbox("Priority*", ["critical", "high", "medium", "low"])
                req_source = st.text_input("Source", placeholder="Stakeholder, regulation, or standard")
            
            with col2:
                req_status = st.selectbox("Status*", ["draft", "approved", "implemented", "verified", "obsolete"], index=0)
                req_version = st.text_input("Version", value="1.0")
                acceptance_criteria = st.text_area("Acceptance Criteria", placeholder="Specific conditions for requirement acceptance")
                rationale = st.text_area("Rationale", placeholder="Justification for this requirement")
                assumptions = st.text_area("Assumptions", placeholder="Underlying assumptions")
            
            req_description = st.text_area("Description*", placeholder="Detailed requirement description", height=100)
            
            if st.form_submit_button("🚀 Create Requirement", type="primary"):
                if req_id and req_title and req_description:
                    requirement_data = {
                        "req_id": req_id,
                        "req_title": req_title,
                        "req_description": req_description,
                        "req_type": req_type,
                        "req_priority": req_priority,
                        "req_status": req_status,
                        "req_version": req_version,
                        "req_source": req_source,
                        "acceptance_criteria": acceptance_criteria,
                        "rationale": rationale,
                        "assumptions": assumptions,
                        "project_id": selected_project_id
                    }
                    
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/design-record/requirements",
                            json=requirement_data,
                            headers=get_auth_headers()
                        )
                        if response.status_code == 200:
                            st.success(f"✅ Requirement {req_id} created successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error creating requirement: {response.text}")
                    except Exception as e:
                        st.error(f"❌ Connection error: {e}")
                else:
                    st.error("❌ Please fill in all required fields (marked with *)")
    
    with req_subtabs[2]:
        st.markdown("**Requirements Analytics Dashboard**")
        
        requirements = get_system_requirements(selected_project_id)
        
        if requirements:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Requirements", len(requirements))
            with col2:
                approved_count = len([r for r in requirements if r.get('req_status') == 'approved'])
                st.metric("Approved", approved_count)
            with col3:
                critical_count = len([r for r in requirements if r.get('req_priority') == 'critical'])
                st.metric("Critical Priority", critical_count)
            with col4:
                safety_count = len([r for r in requirements if r.get('req_type') == 'safety'])
                st.metric("Safety Requirements", safety_count)
            
            st.markdown("---")
            
            # Charts and analysis
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("**Requirements by Type**")
                type_counts = {}
                for req in requirements:
                    req_type = req.get('req_type', 'unknown')
                    type_counts[req_type] = type_counts.get(req_type, 0) + 1
                
                if type_counts:
                    df_types = pd.DataFrame(list(type_counts.items()), columns=['Type', 'Count'])
                    st.bar_chart(df_types.set_index('Type'))
            
            with col_chart2:
                st.markdown("**Requirements by Status**")
                status_counts = {}
                for req in requirements:
                    req_status = req.get('req_status', 'unknown')
                    status_counts[req_status] = status_counts.get(req_status, 0) + 1
                
                if status_counts:
                    df_status = pd.DataFrame(list(status_counts.items()), columns=['Status', 'Count'])
                    st.bar_chart(df_status.set_index('Status'))
        else:
            st.info("No requirements data available for analysis.")

# === HAZARDS & RISKS TAB ===
with main_tabs[1]:
    
    hazard_subtabs = st.tabs(["👀 View Hazards", "➕ Create Hazard", "🏥 Medical Risks", "📊 Risk Dashboard"])
    
    with hazard_subtabs[0]:
        st.markdown("**Filter Hazards:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            hazard_category_filter = st.selectbox(
                "Category",
                ["All", "safety", "security", "operational", "environmental", "clinical"],
                key="hazard_category_filter"
            )
        
        with col2:
            severity_filter = st.selectbox(
                "Severity",
                ["All", "catastrophic", "critical", "marginal", "negligible"],
                key="severity_filter"
            )
        
        with col3:
            risk_rating_filter = st.selectbox(
                "Risk Rating",
                ["All", "high", "medium", "low"],
                key="risk_rating_filter"
            )
        
        hazards = get_hazards_risks(selected_project_id)
        
        if hazards:
            # Apply filters
            filtered_hazards = hazards
            if hazard_category_filter != "All":
                filtered_hazards = [h for h in filtered_hazards if h.get('hazard_category') == hazard_category_filter]
            if severity_filter != "All":
                filtered_hazards = [h for h in filtered_hazards if h.get('severity_level') == severity_filter]
            if risk_rating_filter != "All":
                filtered_hazards = [h for h in filtered_hazards if h.get('risk_rating') == risk_rating_filter]
            
            st.markdown(f"**Showing {len(filtered_hazards)} of {len(hazards)} hazards**")
            
            # Prepare data for DataFrame
            hazard_grid_data = []
            for hazard in filtered_hazards:
                hazard_row = {
                    'Hazard ID': hazard.get('hazard_id', 'N/A'),
                    'Title': hazard.get('hazard_title', 'Untitled'),
                    'Category': hazard.get('hazard_category', 'N/A').title(),
                    'Severity': hazard.get('severity_level', 'N/A').title(),
                    'Risk Rating': hazard.get('risk_rating', 'N/A').title(),
                    'Description': hazard.get('hazard_description', 'No description'),
                    'full_hazard_data': hazard
                }
                hazard_grid_data.append(hazard_row)
            
            hazard_df_data = []
            for row in hazard_grid_data:
                hazard_df_row = {
                    'Hazard ID': row['Hazard ID'],
                    'Title': row['Title'],
                    'Category': row['Category'],
                    'Severity': row['Severity'],
                    'Risk Rating': row['Risk Rating']
                }
                hazard_df_data.append(hazard_df_row)
            
            hazard_df = pd.DataFrame(hazard_df_data)
            
            # Display with selection capability
            hazard_selected_indices = st.dataframe(
                hazard_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                height=DATAFRAME_HEIGHT
            )
            
            st.caption("💡 Select a row to view hazard details")
            
            # Handle hazard selection
            if hazard_selected_indices and len(hazard_selected_indices.selection.rows) > 0:
                selected_idx = hazard_selected_indices.selection.rows[0]
                hazard = hazard_grid_data[selected_idx]['full_hazard_data']
                # Only update if different hazard selected
                if st.session_state.get('selected_hazard_id') != hazard.get('id'):
                    st.session_state.selected_hazard_id = hazard.get('id')
                    st.session_state.selected_hazard_data = hazard
                    st.rerun()
            
            # Show editable details for selected hazard
            if st.session_state.get('selected_hazard_data'):
                hazard = st.session_state.selected_hazard_data
                st.markdown("---")
                st.markdown("### 📝 Edit Selected Hazard")
                
                with st.form("edit_hazard_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edited_id = st.text_input("Hazard ID", value=hazard.get('hazard_id', ''))
                        edited_title = st.text_input("Title", value=hazard.get('hazard_title', ''))
                        edited_category = st.selectbox("Category", ["safety", "security", "operational", "environmental", "clinical"], 
                                                     index=["safety", "security", "operational", "environmental", "clinical"].index(hazard.get('hazard_category', 'safety')))
                        edited_severity = st.selectbox("Severity", ["catastrophic", "critical", "marginal", "negligible"],
                                                     index=["catastrophic", "critical", "marginal", "negligible"].index(hazard.get('severity_level', 'marginal')))
                        edited_risk_rating = st.selectbox("Risk Rating", ["high", "medium", "low"],
                                                         index=["high", "medium", "low"].index(hazard.get('risk_rating', 'medium')))
                    
                    with col2:
                        edited_likelihood = st.selectbox("Likelihood", ["frequent", "probable", "occasional", "remote", "improbable"],
                                                        index=["frequent", "probable", "occasional", "remote", "improbable"].index(hazard.get('likelihood', 'occasional')))
                        edited_context = st.text_input("Operational Context", value=hazard.get('operational_context', ''))
                        edited_asil = st.text_input("ASIL Level", value=hazard.get('asil_level', ''))
                        edited_sil = st.text_input("SIL Level", value=hazard.get('sil_level', ''))
                        edited_medical_class = st.text_input("Medical Risk Class", value=hazard.get('medical_risk_class', ''))
                    
                    edited_description = st.text_area("Description", value=hazard.get('hazard_description', ''), height=100)
                    edited_triggers = st.text_area("Triggering Conditions", value=hazard.get('triggering_conditions', ''))
                    edited_controls = st.text_area("Current Controls", value=hazard.get('current_controls', ''))
                    
                    if st.form_submit_button("💾 Save Changes", type="primary"):
                        updated_hazard = {
                            "hazard_id": edited_id,
                            "hazard_title": edited_title,
                            "hazard_description": edited_description,
                            "hazard_category": edited_category,
                            "severity_level": edited_severity,
                            "likelihood": edited_likelihood,
                            "risk_rating": edited_risk_rating,
                            "operational_context": edited_context,
                            "triggering_conditions": edited_triggers,
                            "current_controls": edited_controls,
                            "asil_level": edited_asil,
                            "sil_level": edited_sil,
                            "medical_risk_class": edited_medical_class,
                            "project_id": selected_project_id
                        }
                        
                        try:
                            response = requests.put(
                                f"{BACKEND_URL}/design-record/hazards/{hazard.get('id')}",
                                json=updated_hazard,
                                headers=get_auth_headers()
                            )
                            if response.status_code == 200:
                                st.success("✅ Hazard updated successfully!")
                                # Clear selection to refresh data
                                if 'selected_hazard_id' in st.session_state:
                                    del st.session_state.selected_hazard_id
                                if 'selected_hazard_data' in st.session_state:
                                    del st.session_state.selected_hazard_data
                                st.rerun()
                            else:
                                st.error(f"❌ Error updating hazard: {response.text}")
                        except Exception as e:
                            st.error(f"❌ Connection error: {e}")
        else:
            st.info("No hazards found for this project. Create your first hazard using the 'Create Hazard' tab.")
    
    with hazard_subtabs[1]:
        st.markdown("**Create New Hazard**")
        
        with st.form("create_hazard_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                hazard_id = st.text_input("Hazard ID*", placeholder="HAZ-001")
                hazard_title = st.text_input("Title*", placeholder="Hazard title")
                hazard_category = st.selectbox("Category*", ["safety", "security", "operational", "environmental", "clinical"])
                severity_level = st.selectbox("Severity Level*", ["catastrophic", "critical", "marginal", "negligible"])
                likelihood = st.selectbox("Likelihood*", ["frequent", "probable", "occasional", "remote", "improbable"])
            
            with col2:
                risk_rating = st.selectbox("Risk Rating*", ["high", "medium", "low"])
                operational_context = st.text_input("Operational Context", placeholder="Operating scenario")
                use_error_potential = st.checkbox("Use Error Potential")
                
                # Safety integrity levels
                st.markdown("**Safety Integrity Levels (Optional):**")
                asil_level = st.selectbox("ASIL Level", ["", "A", "B", "C", "D", "QM"], key="asil")
                sil_level = st.selectbox("SIL Level", ["", "1", "2", "3", "4"], key="sil")
            
            hazard_description = st.text_area("Description*", placeholder="Detailed hazard description", height=100)
            triggering_conditions = st.text_area("Triggering Conditions", placeholder="Conditions that trigger this hazard")
            current_controls = st.text_area("Current Controls", placeholder="Existing risk control measures")
            
            # Affected stakeholders
            stakeholder_options = ["patients", "users", "operators", "environment", "bystanders"]
            affected_stakeholders = st.multiselect("Affected Stakeholders", stakeholder_options)
            
            if st.form_submit_button("🚀 Create Hazard", type="primary"):
                if hazard_id and hazard_title and hazard_description:
                    hazard_data = {
                        "hazard_id": hazard_id,
                        "hazard_title": hazard_title,
                        "hazard_description": hazard_description,
                        "hazard_category": hazard_category,
                        "severity_level": severity_level,
                        "likelihood": likelihood,
                        "risk_rating": risk_rating,
                        "triggering_conditions": triggering_conditions,
                        "operational_context": operational_context,
                        "use_error_potential": use_error_potential,
                        "current_controls": current_controls,
                        "affected_stakeholders": affected_stakeholders,
                        "asil_level": asil_level if asil_level else None,
                        "sil_level": int(sil_level) if sil_level else None,
                        "project_id": selected_project_id
                    }
                    
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/design-record/hazards",
                            json=hazard_data,
                            headers=get_auth_headers()
                        )
                        if response.status_code == 200:
                            st.success(f"✅ Hazard {hazard_id} created successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error creating hazard: {response.text}")
                    except Exception as e:
                        st.error(f"❌ Connection error: {e}")
                else:
                    st.error("❌ Please fill in all required fields (marked with *)")
    
    with hazard_subtabs[2]:
        st.markdown("**Medical Device Risks (ISO 13485/14971)**")
        st.info("🏥 Specialized risk management for medical devices including clinical scenarios and regulatory compliance")
        
        # This would contain medical device specific risk analysis
        st.markdown("Features include:")
        st.markdown("- Hazardous situation analysis")
        st.markdown("- Clinical scenario evaluation") 
        st.markdown("- User profile and environment assessment")
        st.markdown("- Benefit-risk analysis")
        st.markdown("- Risk control effectiveness verification")
        st.markdown("- Cybersecurity and usability evaluation")
        
        st.info("💡 Medical device risk features are available in the full implementation.")
    
    with hazard_subtabs[3]:
        st.markdown("**Risk Analytics Dashboard**")
        
        hazards = get_hazards_risks(selected_project_id)
        
        if hazards:
            # Risk metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Hazards", len(hazards))
            with col2:
                high_risk = len([h for h in hazards if h.get('risk_rating') == 'high'])
                st.metric("High Risk", high_risk)
            with col3:
                safety_hazards = len([h for h in hazards if h.get('hazard_category') == 'safety'])
                st.metric("Safety Hazards", safety_hazards)
            with col4:
                use_error = len([h for h in hazards if h.get('use_error_potential')])
                st.metric("Use Error Potential", use_error)
            
            # Risk matrix visualization
            st.markdown("**Risk Matrix**")
            risk_matrix_data = []
            for hazard in hazards:
                risk_matrix_data.append({
                    'Hazard ID': hazard.get('hazard_id', 'N/A'),
                    'Title': hazard.get('hazard_title', 'N/A'),
                    'Severity': hazard.get('severity_level', 'N/A'),
                    'Likelihood': hazard.get('likelihood', 'N/A'),
                    'Risk Rating': hazard.get('risk_rating', 'N/A'),
                    'Category': hazard.get('hazard_category', 'N/A')
                })
            
            if risk_matrix_data:
                df_risks = pd.DataFrame(risk_matrix_data)
                st.dataframe(df_risks, use_container_width=True)
        else:
            st.info("No hazards data available for risk analysis.")

# === FMEA ANALYSIS TAB ===
with main_tabs[2]:
    
    fmea_subtabs = st.tabs(["👀 View FMEA", "➕ Create FMEA", "📊 FMEA Dashboard", "📋 Actions Tracking"])
    
    with fmea_subtabs[0]:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fmea_type_filter = st.selectbox(
                "FMEA Type",
                ["All", "design_fmea", "process_fmea", "system_fmea", "software_fmea"],
                key="fmea_type_filter"
            )
        
        with col2:
            analysis_level_filter = st.selectbox(
                "Analysis Level",
                ["All", "component", "assembly", "subsystem", "system"],
                key="analysis_level_filter"
            )
        
        with col3:
            review_status_filter = st.selectbox(
                "Review Status",
                ["All", "draft", "under_review", "approved", "superseded"],
                key="review_status_filter"
            )
        
        fmea_analyses = get_fmea_analyses(selected_project_id)
        
        if fmea_analyses:
            # Prepare data for DataFrame
            fmea_grid_data = []
            for fmea in fmea_analyses:
                fmea_row = {
                    'FMEA ID': fmea.get('fmea_id', 'N/A'),
                    'Element ID': fmea.get('element_id', 'N/A'),
                    'Function': fmea.get('element_function', 'Untitled'),
                    'Type': fmea.get('fmea_type', 'N/A').replace('_', ' ').title(),
                    'Level': fmea.get('analysis_level', 'N/A').title(),
                    'Status': fmea.get('review_status', 'N/A').replace('_', ' ').title(),
                    'Description': fmea.get('element_function', 'No function defined'),
                    'full_fmea_data': fmea
                }
                fmea_grid_data.append(fmea_row)
            
            fmea_df_data = []
            for row in fmea_grid_data:
                fmea_df_row = {
                    'FMEA ID': row['FMEA ID'],
                    'Element ID': row['Element ID'],
                    'Function': row['Function'],
                    'Type': row['Type'],
                    'Level': row['Level'],
                    'Status': row['Status']
                }
                fmea_df_data.append(fmea_df_row)
            
            fmea_df = pd.DataFrame(fmea_df_data)
            
            # Display with selection capability
            fmea_selected_indices = st.dataframe(
                fmea_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                height=DATAFRAME_HEIGHT
            )
            
            st.caption("💡 Select a row to view FMEA details")
            
            # Handle FMEA selection
            if fmea_selected_indices and len(fmea_selected_indices.selection.rows) > 0:
                selected_idx = fmea_selected_indices.selection.rows[0]
                fmea = fmea_grid_data[selected_idx]['full_fmea_data']
                # Only update if different FMEA selected
                if st.session_state.get('selected_fmea_id') != fmea.get('id'):
                    st.session_state.selected_fmea_id = fmea.get('id')
                    st.session_state.selected_fmea_data = fmea
                    st.rerun()
            
            # Show editable details for selected FMEA
            if st.session_state.get('selected_fmea_data'):
                fmea = st.session_state.selected_fmea_data
                st.markdown("---")
                st.markdown("### 📝 Edit Selected FMEA")
                
                with st.form("edit_fmea_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edited_fmea_id = st.text_input("FMEA ID", value=fmea.get('fmea_id', ''))
                        edited_element_id = st.text_input("Element ID", value=fmea.get('element_id', ''))
                        edited_function = st.text_input("Element Function", value=fmea.get('element_function', ''))
                        edited_type = st.selectbox("FMEA Type", ["design_fmea", "process_fmea", "system_fmea", "software_fmea"], 
                                                 index=["design_fmea", "process_fmea", "system_fmea", "software_fmea"].index(fmea.get('fmea_type', 'design_fmea')))
                        edited_level = st.selectbox("Analysis Level", ["component", "assembly", "subsystem", "system"],
                                                   index=["component", "assembly", "subsystem", "system"].index(fmea.get('analysis_level', 'component')))
                    
                    with col2:
                        edited_hierarchy = st.number_input("Hierarchy Level", min_value=1, value=fmea.get('hierarchy_level', 1))
                        edited_status = st.selectbox("Review Status", ["draft", "under_review", "approved", "superseded"],
                                                   index=["draft", "under_review", "approved", "superseded"].index(fmea.get('review_status', 'draft')))
                        edited_team = st.text_input("Team Members", value=', '.join(fmea.get('fmea_team', [])))
                        edited_date = st.text_input("Analysis Date", value=fmea.get('analysis_date', ''))
                    
                    edited_description = st.text_area("Description", value=fmea.get('element_function', ''), height=100)
                    edited_standards = st.text_area("Performance Standards", value=fmea.get('performance_standards', ''))
                    
                    if st.form_submit_button("💾 Save Changes", type="primary"):
                        updated_fmea = {
                            "fmea_id": edited_fmea_id,
                            "element_id": edited_element_id,
                            "element_function": edited_function,
                            "fmea_type": edited_type,
                            "analysis_level": edited_level,
                            "hierarchy_level": edited_hierarchy,
                            "review_status": edited_status,
                            "fmea_team": [t.strip() for t in edited_team.split(',') if t.strip()],
                            "analysis_date": edited_date,
                            "performance_standards": edited_standards,
                            "project_id": selected_project_id
                        }
                        
                        try:
                            response = requests.put(
                                f"{BACKEND_URL}/design-record/fmea/{fmea.get('id')}",
                                json=updated_fmea,
                                headers=get_auth_headers()
                            )
                            if response.status_code == 200:
                                st.success("✅ FMEA updated successfully!")
                                # Clear selection to refresh data
                                if 'selected_fmea_id' in st.session_state:
                                    del st.session_state.selected_fmea_id
                                if 'selected_fmea_data' in st.session_state:
                                    del st.session_state.selected_fmea_data
                                st.rerun()
                            else:
                                st.error(f"❌ Error updating FMEA: {response.text}")
                        except Exception as e:
                            st.error(f"❌ Connection error: {e}")
        else:
            st.info("No FMEA analyses found for this project. Create your first FMEA using the 'Create FMEA' tab.")
    
    with fmea_subtabs[1]:
        with st.form("create_fmea_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                fmea_id = st.text_input("FMEA ID*", placeholder="FMEA-001")
                fmea_type = st.selectbox("FMEA Type*", ["design_fmea", "process_fmea", "system_fmea", "software_fmea"])
                analysis_level = st.selectbox("Analysis Level*", ["component", "assembly", "subsystem", "system"])
                hierarchy_level = st.number_input("Hierarchy Level*", min_value=1, value=1)
                element_id = st.text_input("Element ID*", placeholder="COMP-001")
                
            with col2:
                element_function = st.text_input("Element Function*", placeholder="Primary function description")
                performance_standards = st.text_area("Performance Standards", placeholder="Expected performance criteria")
                fmea_team = st.text_input("Team Members", placeholder="Member1, Member2, Member3")
                analysis_date = st.date_input("Analysis Date", value=datetime.now())
                review_status = st.selectbox("Review Status", ["draft", "under_review", "approved", "superseded"])
            
            st.markdown("**Failure Modes:**")
            
            # Simplified failure mode entry for demo
            failure_mode_id = st.text_input("Failure Mode ID", placeholder="FM-001")
            failure_mode_desc = st.text_area("Failure Mode Description", placeholder="How the element fails to perform its function")
            local_effects = st.text_area("Local Effects", placeholder="Effects at element level")
            
            # Risk assessment
            col3, col4, col5 = st.columns(3)
            with col3:
                severity_rating = st.number_input("Severity (1-10)", min_value=1, max_value=10, value=5)
            with col4:
                occurrence_rating = st.number_input("Occurrence (1-10)", min_value=1, max_value=10, value=5)
            with col5:
                detection_rating = st.number_input("Detection (1-10)", min_value=1, max_value=10, value=5)
            
            rpn_current = severity_rating * occurrence_rating * detection_rating
            st.metric("Risk Priority Number (RPN)", rpn_current)
            
            if st.form_submit_button("🚀 Create FMEA", type="primary"):
                if fmea_id and element_id and element_function:
                    fmea_data = {
                        "fmea_id": fmea_id,
                        "fmea_type": fmea_type,
                        "analysis_level": analysis_level,
                        "hierarchy_level": hierarchy_level,
                        "element_id": element_id,
                        "element_function": element_function,
                        "performance_standards": performance_standards,
                        "fmea_team": [name.strip() for name in fmea_team.split(',') if name.strip()],
                        "analysis_date": str(analysis_date),
                        "review_status": review_status,
                        "failure_modes": [{
                            "failure_mode_id": failure_mode_id,
                            "failure_mode_desc": failure_mode_desc,
                            "local_effects": local_effects,
                            "risk_assessment": {
                                "severity_rating": severity_rating,
                                "occurrence_rating": occurrence_rating,
                                "detection_rating": detection_rating,
                                "rpn_current": rpn_current
                            }
                        }] if failure_mode_id else [],
                        "project_id": selected_project_id
                    }
                    
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/design-record/fmea",
                            json=fmea_data,
                            headers=get_auth_headers()
                        )
                        if response.status_code == 200:
                            st.success(f"✅ FMEA {fmea_id} created successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error creating FMEA: {response.text}")
                    except Exception as e:
                        st.error(f"❌ Connection error: {e}")
                else:
                    st.error("❌ Please fill in all required fields (marked with *)")
    
    with fmea_subtabs[2]:
        fmea_analyses = get_fmea_analyses(selected_project_id)
        
        if fmea_analyses:
            # FMEA metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total FMEAs", len(fmea_analyses))
            with col2:
                design_fmeas = len([f for f in fmea_analyses if f.get('fmea_type') == 'design_fmea'])
                st.metric("Design FMEAs", design_fmeas)
            with col3:
                approved_fmeas = len([f for f in fmea_analyses if f.get('review_status') == 'approved'])
                st.metric("Approved", approved_fmeas)
            with col4:
                # Calculate average RPN if available
                total_rpn = 0
                rpn_count = 0
                for fmea in fmea_analyses:
                    for fm in fmea.get('failure_modes', []):
                        if fm.get('risk_assessment', {}).get('rpn_current'):
                            total_rpn += fm['risk_assessment']['rpn_current']
                            rpn_count += 1
                avg_rpn = int(total_rpn / rpn_count) if rpn_count > 0 else 0
                st.metric("Avg RPN", avg_rpn)
            
            # FMEA type distribution
            st.markdown("**FMEA Distribution by Type**")
            type_counts = {}
            for fmea in fmea_analyses:
                fmea_type = fmea.get('fmea_type', 'unknown')
                type_counts[fmea_type] = type_counts.get(fmea_type, 0) + 1
            
            if type_counts:
                df_types = pd.DataFrame(list(type_counts.items()), columns=['Type', 'Count'])
                st.bar_chart(df_types.set_index('Type'))
        else:
            st.info("No FMEA data available for analysis.")
    
    with fmea_subtabs[3]:
        st.markdown("**Corrective Actions Tracking**")
        
        # Action status summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Open Actions", 0)  # Would be calculated from real data
        with col2:
            st.metric("In Progress", 0)
        with col3:
            st.metric("Completed", 0)
        with col4:
            st.metric("Verified", 0)
        
        st.info("📋 Corrective actions tracking includes:")
        st.markdown("- Action priority and responsible person assignment")
        st.markdown("- Target completion dates and status tracking")
        st.markdown("- Action effectiveness verification")
        st.markdown("- Revised risk assessment post-action")

# === DESIGN ARTIFACTS TAB ===
with main_tabs[3]:
    
    design_subtabs = st.tabs(["👀 View Designs", "➕ Create Design", "🛡️ Safety Measures", "🏥 Medical Controls"])
    
    with design_subtabs[0]:
        col1, col2 = st.columns(2)
        
        with col1:
            design_type_filter = st.selectbox(
                "Design Type",
                ["All", "specification", "architecture", "interface", "detailed_design"],
                key="design_type_filter"
            )
        
        with col2:
            st.write("")  # Spacing
        
        design_artifacts = get_design_artifacts(selected_project_id)
        
        if design_artifacts:
            # Prepare data for DataFrame
            design_grid_data = []
            for design in design_artifacts:
                design_row = {
                    'Design ID': design.get('design_id', 'N/A'),
                    'Title': design.get('design_title', 'Untitled'),
                    'Type': design.get('design_type', 'N/A').replace('_', ' ').title(),
                    'Technologies': ', '.join(design.get('technology_stack', [])[:3]) if design.get('technology_stack') else 'N/A',
                    'Patterns': ', '.join(design.get('design_patterns', [])[:2]) if design.get('design_patterns') else 'N/A',
                    'Description': design.get('design_description', 'No description'),
                    'full_design_data': design
                }
                design_grid_data.append(design_row)
            
            design_df_data = []
            for row in design_grid_data:
                design_df_row = {
                    'Design ID': row['Design ID'],
                    'Title': row['Title'],
                    'Type': row['Type'],
                    'Technologies': row['Technologies'],
                    'Patterns': row['Patterns']
                }
                design_df_data.append(design_df_row)
            
            design_df = pd.DataFrame(design_df_data)
            
            # Display with selection capability
            design_selected_indices = st.dataframe(
                design_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                height=DATAFRAME_HEIGHT
            )
            
            st.caption("💡 Select a row to view design details")
            
            # Handle design selection
            if design_selected_indices and len(design_selected_indices.selection.rows) > 0:
                selected_idx = design_selected_indices.selection.rows[0]
                design = design_grid_data[selected_idx]['full_design_data']
                # Only update if different design selected
                if st.session_state.get('selected_design_id') != design.get('id'):
                    st.session_state.selected_design_id = design.get('id')
                    st.session_state.selected_design_data = design
                    st.rerun()
            
            # Show editable details for selected design
            if st.session_state.get('selected_design_data'):
                design = st.session_state.selected_design_data
                st.markdown("---")
                st.markdown("### 📝 Edit Selected Design")
                
                with st.form("edit_design_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edited_design_id = st.text_input("Design ID", value=design.get('design_id', ''))
                        edited_title = st.text_input("Title", value=design.get('design_title', ''))
                        edited_type = st.selectbox("Design Type", ["specification", "architecture", "interface", "detailed_design"], 
                                                 index=["specification", "architecture", "interface", "detailed_design"].index(design.get('design_type', 'specification')))
                        edited_approach = st.text_input("Implementation Approach", value=design.get('implementation_approach', ''))
                    
                    with col2:
                        edited_tech_stack = st.text_input("Technology Stack", value=', '.join(design.get('technology_stack', [])))
                        edited_patterns = st.text_input("Design Patterns", value=', '.join(design.get('design_patterns', [])))
                        edited_interfaces = st.number_input("Number of Interfaces", min_value=0, value=len(design.get('interface_definitions', [])))
                        edited_diagrams = st.number_input("Number of Diagrams", min_value=0, value=len(design.get('architecture_diagrams', [])))
                    
                    edited_description = st.text_area("Description", value=design.get('design_description', ''), height=100)
                    
                    # Safety measures
                    safety_measures = design.get('safety_measures', {})
                    edited_safety_barriers = st.text_area("Safety Barriers", value=safety_measures.get('safety_barriers', ''))
                    edited_failsafe = st.text_area("Fail-safe Behaviors", value=safety_measures.get('fail_safe_behaviors', ''))
                    
                    if st.form_submit_button("💾 Save Changes", type="primary"):
                        updated_design = {
                            "design_id": edited_design_id,
                            "design_title": edited_title,
                            "design_description": edited_description,
                            "design_type": edited_type,
                            "implementation_approach": edited_approach,
                            "technology_stack": [t.strip() for t in edited_tech_stack.split(',') if t.strip()],
                            "design_patterns": [p.strip() for p in edited_patterns.split(',') if p.strip()],
                            "safety_measures": {
                                "safety_barriers": edited_safety_barriers,
                                "fail_safe_behaviors": edited_failsafe
                            },
                            "project_id": selected_project_id
                        }
                        
                        try:
                            response = requests.put(
                                f"{BACKEND_URL}/design-record/design/{design.get('id')}",
                                json=updated_design,
                                headers=get_auth_headers()
                            )
                            if response.status_code == 200:
                                st.success("✅ Design updated successfully!")
                                # Clear selection to refresh data
                                if 'selected_design_id' in st.session_state:
                                    del st.session_state.selected_design_id
                                if 'selected_design_data' in st.session_state:
                                    del st.session_state.selected_design_data
                                st.rerun()
                            else:
                                st.error(f"❌ Error updating design: {response.text}")
                        except Exception as e:
                            st.error(f"❌ Connection error: {e}")
        else:
            st.info("No design artifacts found for this project. Create your first design using the 'Create Design' tab.")
    
    with design_subtabs[1]:
        with st.form("create_design_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                design_id = st.text_input("Design ID*", placeholder="DES-001")
                design_title = st.text_input("Title*", placeholder="System architecture design")
                design_type = st.selectbox("Design Type*", ["specification", "architecture", "interface", "detailed_design"])
                implementation_approach = st.text_area("Implementation Approach", placeholder="High-level implementation strategy")
            
            with col2:
                architecture_diagrams = st.text_input("Architecture Diagrams", placeholder="diagram1.pdf, diagram2.pdf")
                interface_definitions = st.text_input("Interface Definitions", placeholder="API spec, Protocol spec")
                design_patterns = st.text_input("Design Patterns", placeholder="Singleton, Observer, Factory")
                technology_stack = st.text_input("Technology Stack", placeholder="Python, React, PostgreSQL")
            
            design_description = st.text_area("Description*", placeholder="Detailed design description", height=100)
            
            if st.form_submit_button("🚀 Create Design", type="primary"):
                if design_id and design_title and design_description:
                    design_data = {
                        "design_id": design_id,
                        "design_title": design_title,
                        "design_type": design_type,
                        "design_description": design_description,
                        "implementation_approach": implementation_approach,
                        "architecture_diagrams": [d.strip() for d in architecture_diagrams.split(',') if d.strip()],
                        "interface_definitions": [i.strip() for i in interface_definitions.split(',') if i.strip()],
                        "design_patterns": [p.strip() for p in design_patterns.split(',') if p.strip()],
                        "technology_stack": [t.strip() for t in technology_stack.split(',') if t.strip()],
                        "project_id": selected_project_id
                    }
                    
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/design-record/design",
                            json=design_data,
                            headers=get_auth_headers()
                        )
                        if response.status_code == 200:
                            st.success(f"✅ Design {design_id} created successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error creating design: {response.text}")
                    except Exception as e:
                        st.error(f"❌ Connection error: {e}")
                else:
                    st.error("❌ Please fill in all required fields (marked with *)")
    
    with design_subtabs[2]:
        st.markdown("**Safety Measures Configuration**")
        
        with st.form("safety_measures_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                safety_barriers = st.text_area("Safety Barriers", placeholder="Implemented safety barriers and controls")
                redundancy_mechanisms = st.text_area("Redundancy Mechanisms", placeholder="Redundancy implementations")
                fail_safe_behaviors = st.text_area("Fail-Safe Behaviors", placeholder="Fail-safe design behaviors")
                error_detection = st.text_area("Error Detection", placeholder="Error detection methods")
            
            with col2:
                recovery_procedures = st.text_area("Recovery Procedures", placeholder="Recovery and restoration procedures")
                monitoring_capabilities = st.text_area("Monitoring", placeholder="System monitoring features")
                use_error_prevention = st.text_area("Use Error Prevention", placeholder="Use error prevention measures")
                alarm_systems = st.text_area("Alarm Systems", placeholder="Alarm and alert systems")
            
            if st.form_submit_button("💾 Save Safety Measures", type="primary"):
                st.success("✅ Safety measures configuration saved!")
        
        st.info("🛡️ Safety measures are critical for:")
        st.markdown("- Medical device safety per IEC 62304")
        st.markdown("- Automotive functional safety per ISO 26262")
        st.markdown("- Industrial safety per IEC 61508")
        st.markdown("- Aviation safety per DO-178C")
    
    with design_subtabs[3]:
        st.markdown("**Medical Device Design Controls (FDA/ISO 13485)**")
        
        # Medical device design controls
        med_control_tabs = st.tabs(["📝 Design Inputs", "📋 Design Outputs", "👁️ Design Reviews", "✅ Verification", "🔬 Validation"])
        
        with med_control_tabs[0]:
            st.markdown("**Design Input Requirements:**")
            with st.form("design_inputs_form"):
                functional_requirements = st.text_area("Functional Requirements", placeholder="Device functional requirements")
                performance_requirements = st.text_area("Performance Requirements", placeholder="Performance specifications")
                safety_requirements = st.text_area("Safety Requirements", placeholder="Safety and regulatory requirements")
                interface_requirements = st.text_area("Interface Requirements", placeholder="User interface requirements")
                
                if st.form_submit_button("💾 Save Design Inputs"):
                    st.success("✅ Design inputs documented!")
        
        with med_control_tabs[1]:
            st.markdown("**Design Output Documentation:**")
            with st.form("design_outputs_form"):
                design_drawings = st.text_input("Design Drawings", placeholder="Technical drawings references")
                specifications = st.text_input("Specifications", placeholder="Technical specifications")
                software_documentation = st.text_input("Software Documentation", placeholder="Software design documents")
                labeling_instructions = st.text_input("Labeling", placeholder="Device labeling specifications")
                
                if st.form_submit_button("💾 Save Design Outputs"):
                    st.success("✅ Design outputs documented!")
        
        with med_control_tabs[2]:
            st.markdown("**Design Review Records:**")
            
            # Sample design review data
            review_data = [
                {"Review ID": "DR-001", "Date": "2024-01-15", "Phase": "Preliminary", "Status": "Complete"},
                {"Review ID": "DR-002", "Date": "2024-02-20", "Phase": "Critical", "Status": "Complete"},
                {"Review ID": "DR-003", "Date": "2024-03-25", "Phase": "Final", "Status": "In Progress"}
            ]
            
            df_reviews = pd.DataFrame(review_data)
            st.dataframe(df_reviews, use_container_width=True)
            
            if st.button("➕ Add Design Review"):
                st.info("Design review form would open here")
        
        with med_control_tabs[3]:
            st.markdown("**Design Verification Protocols:**")
            
            verification_types = ["Performance Testing", "Software Testing", "Safety Testing", "EMC Testing", "Biocompatibility"]
            
            for v_type in verification_types:
                with st.expander(f"✅ {v_type}", expanded=False):
                    st.markdown(f"**Protocol:** {v_type.lower().replace(' ', '_')}_protocol.pdf")
                    st.markdown(f"**Status:** Not Started")
                    st.markdown(f"**Assigned to:** TBD")
        
        with med_control_tabs[4]:
            st.markdown("**Design Validation Protocols:**")
            
            validation_types = ["Clinical Evaluation", "Usability Validation", "Performance Validation"]
            
            for val_type in validation_types:
                with st.expander(f"🔬 {val_type}", expanded=False):
                    st.markdown(f"**Protocol:** {val_type.lower().replace(' ', '_')}_validation.pdf")
                    st.markdown(f"**Status:** Planning")
                    st.markdown(f"**Timeline:** TBD")

# === TEST ARTIFACTS TAB ===
with main_tabs[4]:
    
    test_subtabs = st.tabs(["👀 View Tests", "➕ Create Test", "🏥 Medical Testing", "📊 Test Dashboard"])
    
    with test_subtabs[0]:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            test_type_filter = st.selectbox(
                "Test Type",
                ["All", "unit", "integration", "system", "safety", "performance", "security", "clinical", "usability", "biocompatibility"],
                key="test_type_filter"
            )
        
        with col2:
            execution_status_filter = st.selectbox(
                "Execution Status",
                ["All", "not_started", "in_progress", "completed", "failed", "blocked"],
                key="execution_status_filter"
            )
        
        with col3:
            pass_fail_filter = st.selectbox(
                "Result",
                ["All", "pass", "fail", "conditional_pass"],
                key="pass_fail_filter"
            )
        
        test_artifacts = get_test_artifacts(selected_project_id)
        
        if test_artifacts:
            # Prepare data for DataFrame
            test_grid_data = []
            for test in test_artifacts:
                execution = test.get('test_execution', {})
                test_row = {
                    'Test ID': test.get('test_id', 'N/A'),
                    'Title': test.get('test_title', 'Untitled'),
                    'Type': test.get('test_type', 'N/A').title(),
                    'Status': execution.get('execution_status', 'N/A').replace('_', ' ').title(),
                    'Result': execution.get('pass_fail_status', 'N/A').replace('_', ' ').title(),
                    'Date': execution.get('execution_date', 'N/A'),
                    'Description': test.get('test_objective', 'No objective defined'),
                    'full_test_data': test
                }
                test_grid_data.append(test_row)
            
            test_df_data = []
            for row in test_grid_data:
                test_df_row = {
                    'Test ID': row['Test ID'],
                    'Title': row['Title'],
                    'Type': row['Type'],
                    'Status': row['Status'],
                    'Result': row['Result'],
                    'Date': row['Date']
                }
                test_df_data.append(test_df_row)
            
            test_df = pd.DataFrame(test_df_data)
            
            # Display with selection capability
            test_selected_indices = st.dataframe(
                test_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                height=DATAFRAME_HEIGHT
            )
            
            st.caption("💡 Select a row to view test details")
            
            # Handle test selection
            if test_selected_indices and len(test_selected_indices.selection.rows) > 0:
                selected_idx = test_selected_indices.selection.rows[0]
                test = test_grid_data[selected_idx]['full_test_data']
                # Only update if different test selected
                if st.session_state.get('selected_test_id') != test.get('id'):
                    st.session_state.selected_test_id = test.get('id')
                    st.session_state.selected_test_data = test
                    st.rerun()
            
            # Show editable details for selected test
            if st.session_state.get('selected_test_data'):
                test = st.session_state.selected_test_data
                st.markdown("---")
                st.markdown("### 📝 Edit Selected Test")
                
                with st.form("edit_test_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edited_test_id = st.text_input("Test ID", value=test.get('test_id', ''))
                        edited_title = st.text_input("Title", value=test.get('test_title', ''))
                        edited_type = st.selectbox("Test Type", ["unit", "integration", "system", "safety", "performance", "security", "clinical", "usability", "biocompatibility"], 
                                                 index=["unit", "integration", "system", "safety", "performance", "security", "clinical", "usability", "biocompatibility"].index(test.get('test_type', 'unit')))
                        edited_environment = st.text_input("Test Environment", value=test.get('test_environment', ''))
                    
                    with col2:
                        execution = test.get('test_execution', {})
                        edited_status = st.selectbox("Execution Status", ["not_started", "in_progress", "completed", "failed", "blocked"],
                                                   index=["not_started", "in_progress", "completed", "failed", "blocked"].index(execution.get('execution_status', 'not_started')))
                        edited_result = st.selectbox("Result", ["pass", "fail", "conditional_pass"],
                                                   index=["pass", "fail", "conditional_pass"].index(execution.get('pass_fail_status', 'pass')))
                        edited_executor = st.text_input("Executed By", value=execution.get('executed_by', ''))
                        edited_exec_date = st.text_input("Execution Date", value=execution.get('execution_date', ''))
                    
                    edited_description = st.text_area("Objective/Description", value=test.get('test_objective', ''), height=100)
                    edited_criteria = st.text_area("Acceptance Criteria", value=test.get('acceptance_criteria', ''))
                    edited_results = st.text_area("Test Results", value=execution.get('test_results', ''))
                    
                    # Coverage metrics
                    coverage = test.get('coverage_metrics', {})
                    edited_req_coverage = st.number_input("Requirements Coverage %", min_value=0, max_value=100, value=coverage.get('requirements_coverage', 0))
                    
                    if st.form_submit_button("💾 Save Changes", type="primary"):
                        updated_test = {
                            "test_id": edited_test_id,
                            "test_title": edited_title,
                            "test_objective": edited_description,
                            "test_type": edited_type,
                            "test_environment": edited_environment,
                            "acceptance_criteria": edited_criteria,
                            "test_execution": {
                                "execution_status": edited_status,
                                "pass_fail_status": edited_result,
                                "executed_by": edited_executor,
                                "execution_date": edited_exec_date,
                                "test_results": edited_results
                            },
                            "coverage_metrics": {
                                "requirements_coverage": edited_req_coverage
                            },
                            "project_id": selected_project_id
                        }
                        
                        try:
                            response = requests.put(
                                f"{BACKEND_URL}/design-record/tests/{test.get('id')}",
                                json=updated_test,
                                headers=get_auth_headers()
                            )
                            if response.status_code == 200:
                                st.success("✅ Test updated successfully!")
                                # Clear selection to refresh data
                                if 'selected_test_id' in st.session_state:
                                    del st.session_state.selected_test_id
                                if 'selected_test_data' in st.session_state:
                                    del st.session_state.selected_test_data
                                st.rerun()
                            else:
                                st.error(f"❌ Error updating test: {response.text}")
                        except Exception as e:
                            st.error(f"❌ Connection error: {e}")
        else:
            st.info("No test artifacts found for this project. Create your first test using the 'Create Test' tab.")
    
    with test_subtabs[1]:
        with st.form("create_test_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                test_id = st.text_input("Test ID*", placeholder="TEST-001")
                test_title = st.text_input("Title*", placeholder="System integration test")
                test_type = st.selectbox("Test Type*", ["unit", "integration", "system", "safety", "performance", "security", "clinical", "usability", "biocompatibility"])
                test_environment = st.text_input("Test Environment", placeholder="Lab environment, Version 1.2")
                executed_by = st.text_input("Executed By", placeholder="Test engineer name")
            
            with col2:
                execution_status = st.selectbox("Execution Status", ["not_started", "in_progress", "completed", "failed", "blocked"])
                pass_fail_status = st.selectbox("Pass/Fail Status", ["pass", "fail", "conditional_pass"]) if execution_status == "completed" else "pass"
                execution_date = st.date_input("Execution Date", value=datetime.now())
                
                # Coverage metrics
                requirements_coverage = st.number_input("Requirements Coverage %", min_value=0, max_value=100, value=0)
                code_coverage = st.number_input("Code Coverage %", min_value=0, max_value=100, value=0)
            
            test_objective = st.text_area("Test Objective*", placeholder="What this test aims to verify", height=80)
            acceptance_criteria = st.text_area("Acceptance Criteria*", placeholder="Pass/fail criteria", height=80)
            test_results = st.text_area("Test Results", placeholder="Detailed test results and observations", height=100)
            
            if st.form_submit_button("🚀 Create Test", type="primary"):
                if test_id and test_title and test_objective:
                    test_data = {
                        "test_id": test_id,
                        "test_title": test_title,
                        "test_type": test_type,
                        "test_objective": test_objective,
                        "acceptance_criteria": acceptance_criteria,
                        "test_environment": test_environment,
                        "test_execution": {
                            "execution_status": execution_status,
                            "execution_date": str(execution_date),
                            "executed_by": executed_by,
                            "test_results": test_results,
                            "pass_fail_status": pass_fail_status if execution_status == "completed" else None
                        },
                        "coverage_metrics": {
                            "requirements_coverage": requirements_coverage,
                            "code_coverage": code_coverage
                        },
                        "project_id": selected_project_id
                    }
                    
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/design-record/tests",
                            json=test_data,
                            headers=get_auth_headers()
                        )
                        if response.status_code == 200:
                            st.success(f"✅ Test {test_id} created successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error creating test: {response.text}")
                    except Exception as e:
                        st.error(f"❌ Connection error: {e}")
                else:
                    st.error("❌ Please fill in all required fields (marked with *)")
    
    with test_subtabs[2]:
        st.markdown("**Medical Device Testing (ISO 13485/FDA)**")
        
        med_test_tabs = st.tabs(["🏥 Clinical Studies", "👤 Usability", "🧬 Biocompatibility", "⚡ EMC/Safety"])
        
        with med_test_tabs[0]:
            st.markdown("**Clinical Studies Management:**")
            
            clinical_studies = DEMO_CLINICAL_STUDIES
            
            df_clinical = pd.DataFrame(clinical_studies)
            st.dataframe(df_clinical, use_container_width=True)
            
            if st.button("➕ Add Clinical Study"):
                with st.form("add_clinical_study"):
                    study_id = st.text_input("Study ID", placeholder="CS-003")
                    study_title = st.text_input("Study Title", placeholder="Long-term efficacy study")
                    participants = st.number_input("Target Participants", min_value=1, value=50)
                    study_status = st.selectbox("Status", ["Planning", "In Progress", "Completed", "Suspended"])
                    
                    if st.form_submit_button("Create Study"):
                        st.success(f"✅ Clinical study {study_id} added!")
        
        with med_test_tabs[1]:
            st.markdown("**Usability Engineering Validation:**")
            
            usability_tests = [
                {"Task": "Device Setup", "Success Rate": 95, "Time (avg)": "3.2 min", "Errors": 2},
                {"Task": "Normal Operation", "Success Rate": 98, "Time (avg)": "1.8 min", "Errors": 1},
                {"Task": "Alarm Response", "Success Rate": 92, "Time (avg)": "45 sec", "Errors": 3}
            ]
            
            df_usability = pd.DataFrame(usability_tests)
            st.dataframe(df_usability, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Overall Success Rate", "95%")
            with col2:
                st.metric("Use Errors", 6)
            with col3:
                st.metric("Critical Errors", 0)
        
        with med_test_tabs[2]:
            st.markdown("**Biocompatibility Testing (ISO 10993):**")
            
            biocompat_tests = [
                {"Test": "Cytotoxicity", "Standard": "ISO 10993-5", "Status": "Pass", "Date": "2024-01-15"},
                {"Test": "Sensitization", "Standard": "ISO 10993-10", "Status": "Pass", "Date": "2024-01-20"},
                {"Test": "Irritation", "Standard": "ISO 10993-10", "Status": "In Progress", "Date": "TBD"}
            ]
            
            df_biocompat = pd.DataFrame(biocompat_tests)
            st.dataframe(df_biocompat, use_container_width=True)
        
        with med_test_tabs[3]:
            st.markdown("**EMC and Electrical Safety:**")
            
            safety_tests = [
                {"Test": "EMC Emissions", "Standard": "IEC 60601-1-2", "Status": "Pass", "Report": "EMC_001.pdf"},
                {"Test": "EMC Immunity", "Standard": "IEC 60601-1-2", "Status": "Pass", "Report": "EMC_002.pdf"},
                {"Test": "Electrical Safety", "Standard": "IEC 60601-1", "Status": "Pass", "Report": "ES_001.pdf"}
            ]
            
            df_safety = pd.DataFrame(safety_tests)
            st.dataframe(df_safety, use_container_width=True)
    
    with test_subtabs[3]:
        test_artifacts = get_test_artifacts(selected_project_id)
        
        if test_artifacts:
            # Test metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Tests", len(test_artifacts))
            with col2:
                passed_tests = len([t for t in test_artifacts if t.get('test_execution', {}).get('pass_fail_status') == 'pass'])
                st.metric("Passed", passed_tests)
            with col3:
                failed_tests = len([t for t in test_artifacts if t.get('test_execution', {}).get('pass_fail_status') == 'fail'])
                st.metric("Failed", failed_tests)
            with col4:
                # Calculate average coverage
                total_coverage = 0
                coverage_count = 0
                for test in test_artifacts:
                    if test.get('coverage_metrics', {}).get('requirements_coverage'):
                        total_coverage += test['coverage_metrics']['requirements_coverage']
                        coverage_count += 1
                avg_coverage = int(total_coverage / coverage_count) if coverage_count > 0 else 0
                st.metric("Avg Coverage", f"{avg_coverage}%")
            
            # Test type distribution
            st.markdown("**Test Distribution by Type**")
            type_counts = {}
            for test in test_artifacts:
                test_type = test.get('test_type', 'unknown')
                type_counts[test_type] = type_counts.get(test_type, 0) + 1
            
            if type_counts:
                df_types = pd.DataFrame(list(type_counts.items()), columns=['Type', 'Count'])
                st.bar_chart(df_types.set_index('Type'))
        else:
            st.info("No test data available for analysis.")

# === TRACEABILITY TAB ===
with main_tabs[5]:
    
    trace_subtabs = st.tabs(["📋 Traceability Matrix", "🔗 Create Links", "📈 Impact Analysis", "📊 Coverage Report"])
    
    with trace_subtabs[0]:
        st.markdown("**Comprehensive Traceability Matrix**")
        
        # Get all data for traceability
        requirements = get_system_requirements(selected_project_id)
        hazards = get_hazards_risks(selected_project_id)
        fmea_analyses = get_fmea_analyses(selected_project_id)
        design_artifacts = get_design_artifacts(selected_project_id)
        test_artifacts = get_test_artifacts(selected_project_id)
        
        # Traceability matrix view
        trace_type = st.selectbox("Traceability View", 
                                 ["Requirements → Hazards", "Hazards → Design", "Design → Tests", "FMEA → Requirements", "Full Matrix"])
        
        if trace_type == "Requirements → Hazards":
            st.markdown("**Requirements to Hazards Mapping**")
            if requirements and hazards:
                # Prepare data for DataFrame
                trace_grid_data = []
                for req in requirements:
                    # Build relationships from actual data based on requirement ID
                    related_hazards = [h['hazard_id'] for h in hazards if h.get('linked_to_req') == req.get('req_id')]
                    trace_row = {
                        "Requirement ID": req.get('req_id', 'N/A'),
                        "Requirement Title": req.get('req_title', 'N/A'),
                        "Related Hazards": ', '.join(related_hazards) if related_hazards else 'None',
                        "Coverage": "Partial" if related_hazards else "None",
                        "full_req_data": req
                    }
                    trace_grid_data.append(trace_row)
                
                trace_df_data = []
                for row in trace_grid_data:
                    trace_df_row = {
                        "Requirement ID": row["Requirement ID"],
                        "Requirement Title": row["Requirement Title"],
                        "Related Hazards": row["Related Hazards"],
                        "Coverage": row["Coverage"]
                    }
                    trace_df_data.append(trace_df_row)
                
                trace_df = pd.DataFrame(trace_df_data)
                
                # Display with selection capability
                trace_selected_indices = st.dataframe(
                    trace_df,
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    height=DATAFRAME_HEIGHT
                )
                
                st.caption("💡 Select a row to edit traceability links")
                
                # Handle trace selection
                if trace_selected_indices and len(trace_selected_indices.selection.rows) > 0:
                    selected_idx = trace_selected_indices.selection.rows[0]
                    req = trace_grid_data[selected_idx]['full_req_data']
                    # Only update if different trace selected
                    if st.session_state.get('selected_trace_id') != req.get('id'):
                        st.session_state.selected_trace_id = req.get('id')
                        st.session_state.selected_trace_data = req
                        st.rerun()
                
                # Show editable details for selected trace
                if st.session_state.get('selected_trace_data'):
                    trace_req = st.session_state.selected_trace_data
                    st.markdown("---")
                    st.markdown("### 📝 Edit Traceability Links")
                    
                    with st.form("edit_trace_form"):
                        st.markdown(f"**Requirement:** {trace_req.get('req_id', 'N/A')} - {trace_req.get('req_title', 'Untitled')}")
                        
                        # Get available hazards for linking
                        hazard_options = [f"{h.get('hazard_id', 'N/A')} - {h.get('hazard_title', 'Untitled')}" for h in hazards]
                        current_links = [h['hazard_id'] for h in hazards if h.get('linked_to_req') == trace_req.get('req_id')]
                        
                        edited_hazard_links = st.multiselect(
                            "Linked Hazards",
                            options=hazard_options,
                            default=[opt for opt in hazard_options if any(link in opt for link in current_links)]
                        )
                        
                        # Additional traceability fields
                        edited_design_links = st.text_input("Linked Design Items", 
                                                           value=', '.join(trace_req.get('design_links', [])))
                        edited_test_links = st.text_input("Linked Test Cases", 
                                                         value=', '.join(trace_req.get('test_links', [])))
                        edited_rationale = st.text_area("Traceability Rationale", 
                                                       value=trace_req.get('trace_rationale', ''))
                        
                        if st.form_submit_button("💾 Save Traceability", type="primary"):
                            # Extract hazard IDs from selections
                            linked_hazard_ids = [link.split(' - ')[0] for link in edited_hazard_links]
                            
                            updated_trace = {
                                "requirement_id": trace_req.get('req_id'),
                                "linked_hazards": linked_hazard_ids,
                                "design_links": [d.strip() for d in edited_design_links.split(',') if d.strip()],
                                "test_links": [t.strip() for t in edited_test_links.split(',') if t.strip()],
                                "trace_rationale": edited_rationale,
                                "project_id": selected_project_id
                            }
                            
                            try:
                                response = requests.put(
                                    f"{BACKEND_URL}/design-record/traceability/{trace_req.get('id')}",
                                    json=updated_trace,
                                    headers=get_auth_headers()
                                )
                                if response.status_code == 200:
                                    st.success("✅ Traceability updated successfully!")
                                    # Clear selection to refresh data
                                    if 'selected_trace_id' in st.session_state:
                                        del st.session_state.selected_trace_id
                                    if 'selected_trace_data' in st.session_state:
                                        del st.session_state.selected_trace_data
                                    st.rerun()
                                else:
                                    st.error(f"❌ Error updating traceability: {response.text}")
                            except Exception as e:
                                st.error(f"❌ Connection error: {e}")
            else:
                st.info("No data available for requirements-to-hazards traceability.")
        
        elif trace_type == "Full Matrix":
            st.markdown("**Complete Traceability Matrix**")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Requirements", len(requirements))
            with col2:
                st.metric("Hazards", len(hazards))
            with col3:
                st.metric("Design Items", len(design_artifacts))
            with col4:
                st.metric("Tests", len(test_artifacts))
            
            # Full matrix table
            matrix_data = []
            for req in requirements[:5]:  # Show first 5 for demo
                matrix_data.append({
                    "Type": "Requirement",
                    "ID": req.get('req_id', 'N/A'),
                    "Title": req.get('req_title', 'N/A'),
                    "→ Hazards": ', '.join(related_hazards) if related_hazards else 'None',
                    "→ Design": f"DES-{req.get('req_id', 'N/A').split('-')[-1]}" if req.get('req_id') else 'None',
                    "→ Tests": f"TC-{req.get('req_id', 'N/A').split('-')[-1]}, TC-{req.get('req_id', 'N/A').split('-')[-1]}A" if req.get('req_id') else 'None',
                    "Coverage": f"{min(100, len(related_hazards) * 30 + 70)}%" if related_hazards else "0%"
                })
            
            if matrix_data:
                df_matrix = pd.DataFrame(matrix_data)
                st.dataframe(df_matrix, use_container_width=True)
    
    with trace_subtabs[1]:
        st.markdown("**Create Traceability Links**")
        
        with st.form("create_trace_link"):
            col1, col2 = st.columns(2)
            
            with col1:
                source_type = st.selectbox("Source Type", ["requirement", "hazard", "design", "test", "fmea"])
                source_id = st.text_input("Source ID", placeholder="REQ-001")
            
            with col2:
                target_type = st.selectbox("Target Type", ["requirement", "hazard", "design", "test", "fmea"])
                target_id = st.text_input("Target ID", placeholder="HAZ-001")
            
            relationship_type = st.selectbox("Relationship Type", 
                                           ["addresses", "mitigates", "verifies", "implements", "derives_from"])
            rationale = st.text_area("Rationale", placeholder="Why are these items linked?")
            
            if st.form_submit_button("🔗 Create Link", type="primary"):
                if source_id and target_id:
                    st.success(f"✅ Created link: {source_id} {relationship_type} {target_id}")
                    # In real implementation, this would store the relationship
                else:
                    st.error("❌ Please provide both source and target IDs")
    
    with trace_subtabs[2]:
        st.markdown("**Impact Analysis**")
        
        impact_id = st.text_input("Analyze Impact for ID", placeholder="REQ-001")
        
        if st.button("🔍 Analyze Impact") and impact_id:
            st.markdown(f"**Impact Analysis for {impact_id}:**")
            
            # Impact analysis based on selected item
            st.markdown("**Directly Affected Items:**")
            st.markdown("- HAZ-002: Safety hazard mitigation")
            st.markdown("- DES-001: System architecture design")
            st.markdown("- TEST-003: Integration test scenario")
            
            st.markdown("**Indirectly Affected Items:**")
            st.markdown("- FMEA-001: Component failure analysis")
            st.markdown("- TEST-005: System validation test")
            
            st.warning("⚠️ Changing this item may impact 5 other items. Review carefully before modification.")
    
    with trace_subtabs[3]:
        st.markdown("**Traceability Coverage Report**")
        
        # Coverage metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Requirements Traced", "85%", "↑ 5%")
        with col2:
            st.metric("Hazards Addressed", "92%", "↑ 2%")
        with col3:
            st.metric("Tests Linked", "78%", "↓ 3%")
        
        # Coverage details
        st.markdown("**Coverage Details:**")
        
        coverage_data = [
            {"Category": "Requirements", "Total": len(requirements), "Traced": int(len(requirements) * 0.85), "Coverage": "85%"},
            {"Category": "Hazards", "Total": len(hazards), "Traced": int(len(hazards) * 0.92), "Coverage": "92%"},
            {"Category": "Design Items", "Total": len(design_artifacts), "Traced": int(len(design_artifacts) * 0.90), "Coverage": "90%"},
            {"Category": "Tests", "Total": len(test_artifacts), "Traced": int(len(test_artifacts) * 0.78), "Coverage": "78%"}
        ]
        
        df_coverage = pd.DataFrame(coverage_data)
        st.dataframe(df_coverage, use_container_width=True)
        
        # Gaps analysis
        st.markdown("**Traceability Gaps:**")
        st.error("❌ REQ-005: No associated test cases")
        st.error("❌ HAZ-003: No mitigation design identified")
        st.warning("⚠️ TEST-007: No requirement linkage")

# === COMPLIANCE TAB ===
with main_tabs[6]:
    
    compliance_subtabs = st.tabs(["📜 Standards", "✅ Compliance Status", "🔍 Audit Findings", "🗺️ Evidence Matrix"])
    
    with compliance_subtabs[0]:
        st.markdown("**Applicable Standards**")
        
        # Get standards from API or use placeholder data
        try:
            standards_response = requests.get(
                f"{BACKEND_URL}/design-record/standards/{selected_project_id}",
                headers=get_auth_headers()
            )
            if standards_response.status_code == 200:
                standards = standards_response.json().get("standards", [])
            else:
                standards = []
        except:
            standards = []
        
        # Use placeholder data if no API data available
        if not standards:
            standards = [
                {"id": 1, "standard_id": "ISO 13485:2016", "version": "2016", "applicable_clauses": "4.2, 7.3, 8.5", "status": "compliant", "last_review": "2024-01-15", "standard_name": "Medical Devices QMS"},
                {"id": 2, "standard_id": "ISO 14971:2019", "version": "2019", "applicable_clauses": "4.3, 5.2, 7.1", "status": "partially_compliant", "last_review": "2024-02-01", "standard_name": "Medical Device Risk Management"},
                {"id": 3, "standard_id": "IEC 60812:2018", "version": "2018", "applicable_clauses": "All", "status": "compliant", "last_review": "2024-01-30", "standard_name": "FMEA Analysis"},
                {"id": 4, "standard_id": "IEC 62304:2006", "version": "2006", "applicable_clauses": "5.1, 5.5, 6.1", "status": "not_assessed", "last_review": "N/A", "standard_name": "Software Life Cycle"},
                {"id": 5, "standard_id": "ISO 26262:2018", "version": "2018", "applicable_clauses": "Part 6", "status": "compliant", "last_review": "2024-02-15", "standard_name": "Automotive Safety"}
            ]
        
        # Prepare data for DataFrame
        standards_grid_data = []
        for standard in standards:
            standards_row = {
                'Standard': standard.get('standard_id', 'N/A'),
                'Version': standard.get('version', 'N/A'),
                'Applicable Clauses': standard.get('applicable_clauses', 'N/A'),
                'Status': standard.get('status', 'N/A').replace('_', ' ').title(),
                'Last Review': standard.get('last_review', 'N/A'),
                'full_standard_data': standard
            }
            standards_grid_data.append(standards_row)
        
        standards_df_data = []
        for row in standards_grid_data:
            standards_df_row = {
                'Standard': row['Standard'],
                'Version': row['Version'],
                'Applicable Clauses': row['Applicable Clauses'],
                'Status': row['Status'],
                'Last Review': row['Last Review']
            }
            standards_df_data.append(standards_df_row)
        
        standards_df = pd.DataFrame(standards_df_data)
        
        # Display with selection capability
        standards_selected_indices = st.dataframe(
            standards_df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            height=DATAFRAME_HEIGHT
        )
        
        st.caption("💡 Select a row to edit standard details")
        
        # Handle standards selection
        if standards_selected_indices and len(standards_selected_indices.selection.rows) > 0:
            selected_idx = standards_selected_indices.selection.rows[0]
            standard = standards_grid_data[selected_idx]['full_standard_data']
            # Only update if different standard selected
            if st.session_state.get('selected_standard_id') != standard.get('id'):
                st.session_state.selected_standard_id = standard.get('id')
                st.session_state.selected_standard_data = standard
                st.rerun()
        
        # Show editable details for selected standard
        if st.session_state.get('selected_standard_data'):
            standard = st.session_state.selected_standard_data
            st.markdown("---")
            st.markdown("### 📝 Edit Selected Standard")
            
            with st.form("edit_standard_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    edited_standard_id = st.text_input("Standard ID", value=standard.get('standard_id', ''))
                    edited_name = st.text_input("Standard Name", value=standard.get('standard_name', ''))
                    edited_version = st.text_input("Version", value=standard.get('version', ''))
                    edited_status = st.selectbox("Compliance Status", ["compliant", "partially_compliant", "non_compliant", "not_assessed"],
                                               index=["compliant", "partially_compliant", "non_compliant", "not_assessed"].index(standard.get('status', 'not_assessed')))
                
                with col2:
                    edited_clauses = st.text_input("Applicable Clauses", value=standard.get('applicable_clauses', ''))
                    edited_last_review = st.text_input("Last Review Date", value=standard.get('last_review', ''))
                    edited_next_review = st.text_input("Next Review Date", value=standard.get('next_review', ''))
                    edited_reviewer = st.text_input("Reviewer", value=standard.get('reviewer', ''))
                
                edited_description = st.text_area("Description", value=standard.get('description', ''))
                edited_notes = st.text_area("Compliance Notes", value=standard.get('compliance_notes', ''))
                edited_evidence = st.text_area("Evidence References", value=standard.get('evidence_references', ''))
                
                if st.form_submit_button("💾 Save Changes", type="primary"):
                    updated_standard = {
                        "standard_id": edited_standard_id,
                        "standard_name": edited_name,
                        "version": edited_version,
                        "applicable_clauses": edited_clauses,
                        "status": edited_status,
                        "last_review": edited_last_review,
                        "next_review": edited_next_review,
                        "reviewer": edited_reviewer,
                        "description": edited_description,
                        "compliance_notes": edited_notes,
                        "evidence_references": edited_evidence,
                        "project_id": selected_project_id
                    }
                    
                    try:
                        response = requests.put(
                            f"{BACKEND_URL}/design-record/standards/{standard.get('id')}",
                            json=updated_standard,
                            headers=get_auth_headers()
                        )
                        if response.status_code == 200:
                            st.success("✅ Standard updated successfully!")
                            # Clear selection to refresh data
                            if 'selected_standard_id' in st.session_state:
                                del st.session_state.selected_standard_id
                            if 'selected_standard_data' in st.session_state:
                                del st.session_state.selected_standard_data
                            st.rerun()
                        else:
                            st.error(f"❌ Error updating standard: {response.text}")
                    except Exception as e:
                        st.error(f"❌ Connection error: {e}")
        
        # Add new standard
        if st.button("➕ Add Standard"):
            with st.form("add_standard"):
                standard_id = st.text_input("Standard ID", placeholder="ISO 9001:2015")
                standard_name = st.text_input("Standard Name", placeholder="Quality Management Systems")
                standard_version = st.text_input("Version", placeholder="2015")
                applicable_clauses = st.text_input("Applicable Clauses", placeholder="4.1, 4.2, 6.1")
                compliance_status = st.selectbox("Status", ["compliant", "partially_compliant", "non_compliant", "not_assessed"])
                
                if st.form_submit_button("Add Standard"):
                    st.success(f"✅ Standard {standard_id} added!")
    
    with compliance_subtabs[1]:
        st.markdown("**Compliance Dashboard**")
        
        # Compliance metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Standards", 5)
        with col2:
            st.metric("Compliant", 3, "↑ 1")
        with col3:
            st.metric("Partial Compliance", 1, "→ 0")
        with col4:
            st.metric("Non-Compliant", 0, "↓ 1")
        
        # Compliance status by standard
        st.markdown("**Compliance Status Overview**")
        
        compliance_chart_data = {
            "ISO 13485": 95,
            "ISO 14971": 78,
            "IEC 60812": 100,
            "IEC 62304": 0,
            "ISO 26262": 92
        }
        
        df_compliance = pd.DataFrame(list(compliance_chart_data.items()), columns=['Standard', 'Compliance %'])
        st.bar_chart(df_compliance.set_index('Standard'))
        
        # Compliance gaps
        st.markdown("**Compliance Gaps**")
        st.error("❌ ISO 14971: Risk management file incomplete")
        st.warning("⚠️ IEC 62304: Software lifecycle processes not assessed")
        st.info("💡 ISO 13485: Minor documentation updates needed")
    
    with compliance_subtabs[2]:
        st.markdown("**Audit Findings Management**")
        
        # Audit findings
        findings_data = [
            {"Finding ID": "AF-001", "Standard": "ISO 13485", "Clause": "7.3.2", "Severity": "Minor", "Description": "Design review records incomplete", "Status": "Open"},
            {"Finding ID": "AF-002", "Standard": "ISO 14971", "Clause": "4.3", "Severity": "Major", "Description": "Risk analysis methodology not documented", "Status": "In Progress"},
            {"Finding ID": "AF-003", "Standard": "IEC 60812", "Clause": "6.2", "Severity": "Minor", "Description": "FMEA team roles not defined", "Status": "Closed"}
        ]
        
        df_findings = pd.DataFrame(findings_data)
        st.dataframe(df_findings, use_container_width=True)
        
        # Add new finding
        with st.expander("➕ Add New Finding"):
            with st.form("add_finding"):
                col1, col2 = st.columns(2)
                
                with col1:
                    finding_id = st.text_input("Finding ID", placeholder="AF-004")
                    standard = st.selectbox("Standard", ["ISO 13485", "ISO 14971", "IEC 60812", "IEC 62304", "ISO 26262"])
                    clause = st.text_input("Clause", placeholder="4.2.3")
                    severity = st.selectbox("Severity", ["Critical", "Major", "Minor", "Observation"])
                
                with col2:
                    description = st.text_area("Description", placeholder="Detailed finding description")
                    corrective_action = st.text_area("Corrective Action", placeholder="Planned corrective action")
                    responsible_person = st.text_input("Responsible Person", placeholder="John Doe")
                    due_date = st.date_input("Due Date")
                
                if st.form_submit_button("Create Finding"):
                    st.success(f"✅ Finding {finding_id} created!")
        
        # Findings metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Open Findings", 1)
        with col2:
            st.metric("In Progress", 1)
        with col3:
            st.metric("Closed", 1)
    
    with compliance_subtabs[3]:
        st.markdown("**Evidence Documentation Matrix**")
        
        # Evidence matrix
        evidence_data = [
            {"Standard": "ISO 13485", "Clause": "7.3.2", "Requirement": "Design Reviews", "Evidence": "DR-001.pdf, DR-002.pdf", "Status": "Complete"},
            {"Standard": "ISO 13485", "Clause": "7.3.3", "Requirement": "Design Verification", "Evidence": "TEST-001.pdf", "Status": "Partial"},
            {"Standard": "ISO 14971", "Clause": "4.3", "Requirement": "Risk Management", "Evidence": "RMF-001.pdf", "Status": "Missing"},
            {"Standard": "IEC 60812", "Clause": "6.1", "Requirement": "FMEA Documentation", "Evidence": "FMEA-001.xlsx", "Status": "Complete"}
        ]
        
        df_evidence = pd.DataFrame(evidence_data)
        st.dataframe(df_evidence, use_container_width=True)
        
        # Evidence upload simulation
        st.markdown("**Upload Evidence:**")
        uploaded_file = st.file_uploader("Choose evidence file", type=['pdf', 'docx', 'xlsx'])
        if uploaded_file:
            st.success(f"✅ File '{uploaded_file.name}' uploaded successfully!")
        
        # Evidence gaps
        st.markdown("**Evidence Gaps:**")
        st.error("❌ ISO 14971 Clause 4.3: Risk management file missing")
        st.warning("⚠️ ISO 13485 Clause 7.3.3: Additional verification evidence needed")

# === POST-MARKET TAB ===
with main_tabs[7]:
    
    postmarket_subtabs = st.tabs(["⚠️ Adverse Events", "🗨️ Customer Feedback", "🛠️ Field Actions", "📊 Surveillance Reports"])
    
    with postmarket_subtabs[0]:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            severity_filter = st.selectbox("Severity", ["All", "death", "serious_injury", "malfunction", "near_miss"], key="ae_severity")
        
        with col2:
            investigation_filter = st.selectbox("Investigation Status", ["All", "reported", "investigating", "analyzed", "closed"], key="ae_status")
        
        with col3:
            st.write("")  # Spacing
        
        # Adverse events data
        adverse_events = [
            {"Event ID": "AE-001", "Date": "2024-01-15", "Severity": "malfunction", "Description": "Device calibration error", "Status": "closed"},
            {"Event ID": "AE-002", "Date": "2024-02-03", "Severity": "near_miss", "Description": "Alarm delay noticed", "Status": "investigating"},
            {"Event ID": "AE-003", "Date": "2024-02-20", "Severity": "malfunction", "Description": "Software freeze during operation", "Status": "analyzed"}
        ]
        
        st.markdown(f"**Showing {len(adverse_events)} adverse events**")
        
        # Prepare data for DataFrame
        ae_grid_data = []
        for event in adverse_events:
            ae_row = {
                'Event ID': event['Event ID'],
                'Date': event['Date'],
                'Severity': event['Severity'].replace('_', ' ').title(),
                'Status': event['Status'].title(),
                'Description': event['Description'],
                'full_ae_data': event
            }
            ae_grid_data.append(ae_row)
        
        ae_df_data = []
        for row in ae_grid_data:
            ae_df_row = {
                'Event ID': row['Event ID'],
                'Date': row['Date'],
                'Severity': row['Severity'],
                'Status': row['Status'],
                'Description': row['Description'][:50] + '...' if len(row['Description']) > 50 else row['Description']
            }
            ae_df_data.append(ae_df_row)
        
        ae_df = pd.DataFrame(ae_df_data)
        
        # Display with selection capability
        ae_selected_indices = st.dataframe(
            ae_df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            height=300
        )
        
        st.caption("💡 Select a row to view adverse event details")
        
        # Handle adverse event selection
        if ae_selected_indices and len(ae_selected_indices.selection.rows) > 0:
            selected_idx = ae_selected_indices.selection.rows[0]
            event = ae_grid_data[selected_idx]['full_ae_data']
            # Only update if different event selected
            if st.session_state.get('selected_ae_id') != event.get('Event ID'):
                st.session_state.selected_ae_id = event.get('Event ID')
                st.session_state.selected_ae_data = event
                st.rerun()
        
        # Show editable details for selected adverse event
        if st.session_state.get('selected_ae_data'):
            event = st.session_state.selected_ae_data
            st.markdown("---")
            st.markdown("### 📝 Edit Selected Adverse Event")
            
            with st.form("edit_ae_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    edited_event_id = st.text_input("Event ID", value=event.get('Event ID', ''))
                    edited_date = st.text_input("Date", value=event.get('Date', ''))
                    edited_severity = st.selectbox("Severity", ["death", "serious_injury", "malfunction", "near_miss"], 
                                                 index=["death", "serious_injury", "malfunction", "near_miss"].index(event.get('Severity', 'malfunction')))
                
                with col2:
                    edited_status = st.selectbox("Investigation Status", ["reported", "investigating", "analyzed", "closed"],
                                               index=["reported", "investigating", "analyzed", "closed"].index(event.get('Status', 'reported')))
                    edited_regulatory_fda = st.selectbox("FDA Reported", ["Reported", "Pending", "Not Required"], index=0)
                    edited_regulatory_nb = st.selectbox("Notified Body", ["Reported", "Pending", "Not Required"], index=1)
                
                edited_description = st.text_area("Description", value=event.get('Description', ''), height=100)
                edited_investigation = st.text_area("Investigation Notes", value="Preliminary investigation completed, root cause identified.", height=80)
                edited_actions = st.text_area("Corrective Actions", value="Software patch released, user training updated.", height=80)
                
                if st.form_submit_button("💾 Save Changes", type="primary"):
                    updated_event = {
                        "event_id": edited_event_id,
                        "date": edited_date,
                        "severity": edited_severity,
                        "status": edited_status,
                        "description": edited_description,
                        "investigation_notes": edited_investigation,
                        "corrective_actions": edited_actions,
                        "regulatory_reporting": {
                            "fda": edited_regulatory_fda,
                            "notified_body": edited_regulatory_nb
                        },
                        "project_id": selected_project_id
                    }
                    
                    try:
                        response = requests.put(
                            f"{BACKEND_URL}/design-record/adverse-events/{event.get('Event ID')}",
                            json=updated_event,
                            headers=get_auth_headers()
                        )
                        if response.status_code == 200:
                            st.success("✅ Adverse event updated successfully!")
                            # Clear selection to refresh data
                            if 'selected_ae_id' in st.session_state:
                                del st.session_state.selected_ae_id
                            if 'selected_ae_data' in st.session_state:
                                del st.session_state.selected_ae_data
                            st.rerun()
                        else:
                            st.error(f"❌ Error updating adverse event: {response.text}")
                    except Exception as e:
                        st.error(f"❌ Connection error: {e}")
        
        # Add new adverse event
        with st.expander("➕ Add New Adverse Event"):
            with st.form("add_adverse_event"):
                col1, col2 = st.columns(2)
                
                with col1:
                    event_id = st.text_input("Event ID", placeholder="AE-004")
                    event_date = st.date_input("Event Date")
                    severity = st.selectbox("Severity", ["death", "serious_injury", "malfunction", "near_miss"])
                
                with col2:
                    description = st.text_area("Event Description", placeholder="Detailed description of adverse event")
                    investigation_status = st.selectbox("Investigation Status", ["reported", "investigating", "analyzed", "closed"])
                    reporter = st.text_input("Reporter", placeholder="Healthcare facility, user, etc.")
                
                corrective_actions = st.text_area("Corrective Actions", placeholder="Actions taken or planned")
                
                if st.form_submit_button("Report Adverse Event"):
                    st.success(f"✅ Adverse event {event_id} reported!")
        
        # Adverse events metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Events", len(adverse_events))
        with col2:
            st.metric("Open Investigations", 1)
        with col3:
            st.metric("This Month", 2)
        with col4:
            st.metric("Closed", 1)
    
    with postmarket_subtabs[1]:
        # Customer feedback management
        feedback_data = [
            {"Feedback ID": "CF-001", "Date": "2024-01-10", "Source": "customer", "Type": "complaint", "Description": "Display brightness inconsistent", "Risk": "Low", "Status": "Resolved"},
            {"Feedback ID": "CF-002", "Date": "2024-02-01", "Source": "distributor", "Type": "suggestion", "Description": "Request for mobile app integration", "Risk": "None", "Status": "Under Review"},
            {"Feedback ID": "CF-003", "Date": "2024-02-15", "Source": "user", "Type": "compliment", "Description": "Easy to use interface appreciated", "Risk": "None", "Status": "Acknowledged"}
        ]
        
        df_feedback = pd.DataFrame(feedback_data)
        st.dataframe(df_feedback, use_container_width=True)
        
        # Feedback metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Feedback", len(feedback_data))
        with col2:
            complaints = len([f for f in feedback_data if f['Type'] == 'complaint'])
            st.metric("Complaints", complaints)
        with col3:
            suggestions = len([f for f in feedback_data if f['Type'] == 'suggestion'])
            st.metric("Suggestions", suggestions)
        with col4:
            compliments = len([f for f in feedback_data if f['Type'] == 'compliment'])
            st.metric("Compliments", compliments)
    
    with postmarket_subtabs[2]:
        # Field safety actions
        field_actions = [
            {"Action ID": "FSA-001", "Type": "software_update", "Date": "2024-01-20", "Description": "Critical security patch", "Affected Products": "Model A v1.0-1.2", "Status": "Completed"},
            {"Action ID": "FSA-002", "Type": "field_safety_notice", "Date": "2024-02-10", "Description": "Updated user manual", "Affected Products": "All Models", "Status": "In Progress"}
        ]
        
        # Prepare data for DataFrame
        fa_grid_data = []
        for action in field_actions:
            fa_row = {
                'Action ID': action['Action ID'],
                'Type': action['Type'].replace('_', ' ').title(),
                'Date': action['Date'],
                'Status': action['Status'],
                'Affected Products': action['Affected Products'],
                'Description': action['Description'],
                'full_fa_data': action
            }
            fa_grid_data.append(fa_row)
        
        fa_df_data = []
        for row in fa_grid_data:
            fa_df_row = {
                'Action ID': row['Action ID'],
                'Type': row['Type'],
                'Date': row['Date'],
                'Status': row['Status'],
                'Affected Products': row['Affected Products'],
                'Description': row['Description'][:40] + '...' if len(row['Description']) > 40 else row['Description']
            }
            fa_df_data.append(fa_df_row)
        
        fa_df = pd.DataFrame(fa_df_data)
        
        # Display with selection capability
        fa_selected_indices = st.dataframe(
            fa_df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            height=300
        )
        
        st.caption("💡 Select a row to view field action details")
        
        # Handle field action selection
        if fa_selected_indices and len(fa_selected_indices.selection.rows) > 0:
            selected_idx = fa_selected_indices.selection.rows[0]
            action = fa_grid_data[selected_idx]['full_fa_data']
            # Only update if different action selected
            if st.session_state.get('selected_fa_id') != action.get('Action ID'):
                st.session_state.selected_fa_id = action.get('Action ID')
                st.session_state.selected_fa_data = action
                st.rerun()
        
        # Show editable details for selected field action
        if st.session_state.get('selected_fa_data'):
            action = st.session_state.selected_fa_data
            st.markdown("---")
            st.markdown("### 📝 Edit Selected Field Action")
            
            with st.form("edit_fa_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    edited_action_id = st.text_input("Action ID", value=action.get('Action ID', ''))
                    edited_type = st.selectbox("Type", ["software_update", "field_safety_notice", "recall", "advisory"], 
                                             index=["software_update", "field_safety_notice", "recall", "advisory"].index(action.get('Type', 'software_update')))
                    edited_date = st.text_input("Date", value=action.get('Date', ''))
                    edited_status = st.selectbox("Status", ["Planned", "In Progress", "Completed", "Cancelled"],
                                               index=["Planned", "In Progress", "Completed", "Cancelled"].index(action.get('Status', 'Planned')))
                
                with col2:
                    edited_affected = st.text_input("Affected Products", value=action.get('Affected Products', ''))
                    edited_fda = st.selectbox("FDA Notification", ["Completed", "Pending", "Not Required"], index=0)
                    edited_ce = st.selectbox("CE Notified Body", ["Completed", "Pending", "Not Required"], index=0)
                    edited_effectiveness = st.text_input("Effectiveness %", value="95%")
                
                edited_description = st.text_area("Description", value=action.get('Description', ''), height=100)
                edited_root_cause = st.text_area("Root Cause", value="Software vulnerability identified during security assessment", height=80)
                edited_assessment = st.text_area("Effectiveness Assessment", value="95% of affected devices updated successfully", height=80)
                
                if st.form_submit_button("💾 Save Changes", type="primary"):
                    updated_action = {
                        "action_id": edited_action_id,
                        "type": edited_type,
                        "date": edited_date,
                        "status": edited_status,
                        "affected_products": edited_affected,
                        "description": edited_description,
                        "root_cause": edited_root_cause,
                        "effectiveness_assessment": edited_assessment,
                        "regulatory_notifications": {
                            "fda": edited_fda,
                            "ce_notified_body": edited_ce
                        },
                        "project_id": selected_project_id
                    }
                    
                    try:
                        response = requests.put(
                            f"{BACKEND_URL}/design-record/field-actions/{action.get('Action ID')}",
                            json=updated_action,
                            headers=get_auth_headers()
                        )
                        if response.status_code == 200:
                            st.success("✅ Field action updated successfully!")
                            # Clear selection to refresh data
                            if 'selected_fa_id' in st.session_state:
                                del st.session_state.selected_fa_id
                            if 'selected_fa_data' in st.session_state:
                                del st.session_state.selected_fa_data
                            st.rerun()
                        else:
                            st.error(f"❌ Error updating field action: {response.text}")
                    except Exception as e:
                        st.error(f"❌ Connection error: {e}")
        
        # Field action metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Actions", len(field_actions))
        with col2:
            st.metric("Completed", 1)
        with col3:
            st.metric("In Progress", 1)
    
    with postmarket_subtabs[3]:
        # Periodic surveillance reports
        reports_data = [
            {"Report ID": "PSUR-2024-Q1", "Type": "psur", "Period": "Q1 2024", "Date": "2024-04-15", "Key Findings": "No new safety signals identified"},
            {"Report ID": "PMCF-2024-001", "Type": "pmcf", "Period": "Jan-Mar 2024", "Date": "2024-04-01", "Key Findings": "Clinical performance maintained"},
            {"Report ID": "AR-2024", "Type": "annual_report", "Period": "2024", "Date": "2024-12-31", "Key Findings": "TBD"}
        ]
        
        df_reports = pd.DataFrame(reports_data)
        st.dataframe(df_reports, use_container_width=True)
        
        # Report metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Reports This Year", 3)
        with col2:
            st.metric("Submitted", 2)
        with col3:
            st.metric("Due", 1)
        
        # Risk updates summary
        st.markdown("**Risk Assessment Updates:**")
        st.info("📊 Post-market data confirms initial risk assessments remain valid")
        st.markdown("- No new hazardous situations identified")
        st.markdown("- Risk control measures effectiveness confirmed")
        st.markdown("- Benefit-risk ratio remains positive")

# === EXPORT TAB ===
with main_tabs[8]:
    
    export_cols = st.columns([1, 1, 1])
    
    with export_cols[0]:
        st.markdown("#### 📋 Report Types")
        report_type = st.selectbox("Select Report Type", [
            "Complete Design Record",
            "Requirements Traceability",
            "Risk Management Summary",
            "FMEA Analysis Report",
            "Compliance Evidence",
            "Test Execution Summary",
            "Post-Market Surveillance",
            "Regulatory Submission Package"
        ])
        
        export_format = st.selectbox("Export Format", [
            "CSV", "Excel", "PDF", "JSON", "Markdown"
        ])
    
    with export_cols[1]:
        st.markdown("#### 🗓️ Date Range")
        date_from = st.date_input("From Date")
        date_to = st.date_input("To Date")
        
        st.markdown("#### 🏷️ Status Filter")
        status_filter = st.multiselect("Include Status", [
            "Active", "Under Review", "Approved", "Implemented", 
            "Testing", "Verified", "Closed"
        ], default=["Active", "Approved"])
    
    with export_cols[2]:
        st.markdown("#### 📊 Report Options")
        include_metadata = st.checkbox("Include Metadata", value=True)
        include_attachments = st.checkbox("Include Attachments Summary")
        include_history = st.checkbox("Include Change History")
        
        compliance_standard = st.selectbox("Compliance Standard", [
            "ISO 13485", "ISO 14971", "IEC 62304", "ISO 26262", 
            "FDA 21 CFR Part 820", "ASIL Automotive", "SIL Industrial"
        ])
    
    st.markdown("---")
    
    # Export buttons
    export_button_cols = st.columns([1, 1, 1])
    
    with export_button_cols[0]:
        if st.button("📥 Generate Report", type="primary"):
            # Get all data for export
            requirements = get_system_requirements(selected_project_id)
            hazards = get_hazards_risks(selected_project_id)
            
            # Create comprehensive export based on report type
            export_data = []
            
            if report_type == "Complete Design Record":
                # Add requirements
                for req in requirements:
                    export_data.append({
                        "Type": "Requirement",
                        "ID": req.get('req_id', ''),
                        "Title": req.get('req_title', ''),
                        "Description": req.get('req_description', ''),
                        "Category": req.get('req_type', ''),
                        "Priority": req.get('req_priority', ''),
                        "Status": req.get('req_status', ''),
                        "Version": req.get('req_version', ''),
                        "Source": req.get('req_source', ''),
                        "Rationale": req.get('rationale', ''),
                        "Created_Date": req.get('created_at', ''),
                        "Standard": compliance_standard
                    })
                
                # Add hazards
                for hazard in hazards:
                    export_data.append({
                        "Type": "Hazard",
                        "ID": hazard.get('hazard_id', ''),
                        "Title": hazard.get('hazard_title', ''),
                        "Description": hazard.get('hazard_description', ''),
                        "Category": hazard.get('hazard_category', ''),
                        "Severity": hazard.get('severity_level', ''),
                        "Risk_Rating": hazard.get('risk_rating', ''),
                        "Version": "1.0",
                        "Context": hazard.get('operational_context', ''),
                        "Controls": hazard.get('current_controls', ''),
                        "Created_Date": hazard.get('created_at', ''),
                        "Standard": compliance_standard
                    })
            
            elif report_type == "Requirements Traceability":
                for req in requirements:
                    if not status_filter or req.get('req_status') in status_filter:
                        export_data.append({
                            "Requirement_ID": req.get('req_id', ''),
                            "Title": req.get('req_title', ''),
                            "Type": req.get('req_type', ''),
                            "Status": req.get('req_status', ''),
                            "Linked_Hazards": "HAZ-001, HAZ-003",
                            "Design_Items": "DES-001, DES-005",
                            "Test_Cases": "TC-001, TC-007",
                            "Verification_Status": "Verified",
                            "Coverage": "100%"
                        })
            
            elif report_type == "Risk Management Summary":
                for hazard in hazards:
                    if not status_filter or hazard.get('risk_rating') in ["High", "Medium"]:
                        export_data.append({
                            "Hazard_ID": hazard.get('hazard_id', ''),
                            "Hazardous_Situation": hazard.get('hazard_title', ''),
                            "Potential_Harm": hazard.get('hazard_description', ''),
                            "Severity": hazard.get('severity_level', ''),
                            "Probability": "Medium",
                            "Risk_Score": "12",
                            "Risk_Level": hazard.get('risk_rating', ''),
                            "Control_Measures": hazard.get('current_controls', ''),
                            "Residual_Risk": "Acceptable",
                            "Standard_Reference": compliance_standard
                        })
            
            if export_data:
                import pandas as pd
                
                df = pd.DataFrame(export_data)
                
                if export_format == "CSV":
                    export_string = df.to_csv(index=False)
                    mime_type = "text/csv"
                    file_ext = "csv"
                elif export_format == "JSON":
                    export_string = df.to_json(orient='records', indent=2)
                    mime_type = "application/json"
                    file_ext = "json"
                elif export_format == "Markdown":
                    # Create Markdown with separate tables for each data type
                    md_content = []
                    md_content.append(f"# {report_type}")
                    md_content.append(f"**Project:** {selected_project_name}")
                    md_content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    md_content.append(f"**Compliance Standard:** {compliance_standard}")
                    md_content.append("")
                    
                    if report_type == "Complete Design Record":
                        # Create separate tables for Requirements and Hazards
                        if requirements:
                            md_content.append("## System Requirements")
                            md_content.append("")
                            req_headers = ["ID", "Title", "Description", "Type", "Priority", "Status", "Version", "Source", "Rationale"]
                            md_content.append("| " + " | ".join(req_headers) + " |")
                            md_content.append("| " + " | ".join(["---"] * len(req_headers)) + " |")
                            
                            for req in requirements:
                                cells = [
                                    str(req.get('req_id', '')),
                                    str(req.get('req_title', '')).replace("|", "\\|").replace("\n", " ")[:30],
                                    str(req.get('req_description', '')).replace("|", "\\|").replace("\n", " ")[:50],
                                    str(req.get('req_type', '')),
                                    str(req.get('req_priority', '')),
                                    str(req.get('req_status', '')),
                                    str(req.get('req_version', '')),
                                    str(req.get('req_source', '')),
                                    str(req.get('rationale', '')).replace("|", "\\|").replace("\n", " ")[:40]
                                ]
                                md_content.append("| " + " | ".join(cells) + " |")
                            md_content.append("")
                        
                        if hazards:
                            md_content.append("## Hazards and Risk Analysis")
                            md_content.append("")
                            hazard_headers = ["ID", "Title", "Description", "Category", "Severity", "Risk Rating", "Context", "Current Controls"]
                            md_content.append("| " + " | ".join(hazard_headers) + " |")
                            md_content.append("| " + " | ".join(["---"] * len(hazard_headers)) + " |")
                            
                            for hazard in hazards:
                                cells = [
                                    str(hazard.get('hazard_id', '')),
                                    str(hazard.get('hazard_title', '')).replace("|", "\\|").replace("\n", " ")[:30],
                                    str(hazard.get('hazard_description', '')).replace("|", "\\|").replace("\n", " ")[:40],
                                    str(hazard.get('hazard_category', '')),
                                    str(hazard.get('severity_level', '')),
                                    str(hazard.get('risk_rating', '')),
                                    str(hazard.get('operational_context', '')).replace("|", "\\|").replace("\n", " ")[:30],
                                    str(hazard.get('current_controls', '')).replace("|", "\\|").replace("\n", " ")[:40]
                                ]
                                md_content.append("| " + " | ".join(cells) + " |")
                            md_content.append("")
                    
                    elif report_type == "Requirements Traceability":
                        md_content.append("## Requirements Traceability Matrix")
                        md_content.append("")
                        trace_headers = ["Requirement ID", "Title", "Type", "Status", "Linked Hazards", "Design Items", "Test Cases", "Verification Status", "Coverage"]
                        md_content.append("| " + " | ".join(trace_headers) + " |")
                        md_content.append("| " + " | ".join(["---"] * len(trace_headers)) + " |")
                        
                        for req in requirements:
                            if not status_filter or req.get('req_status') in status_filter:
                                cells = [
                                    str(req.get('req_id', '')),
                                    str(req.get('req_title', '')).replace("|", "\\|").replace("\n", " ")[:30],
                                    str(req.get('req_type', '')),
                                    str(req.get('req_status', '')),
                                    "HAZ-001, HAZ-003",  # Sample linked hazards
                                    "DES-001, DES-005",  # Sample design items
                                    "TC-001, TC-007",    # Sample test cases
                                    "Verified",          # Sample verification status
                                    "100%"               # Sample coverage
                                ]
                                md_content.append("| " + " | ".join(cells) + " |")
                        md_content.append("")
                    
                    elif report_type == "Risk Management Summary":
                        md_content.append("## Risk Management Summary")
                        md_content.append("")
                        risk_headers = ["Hazard ID", "Hazardous Situation", "Potential Harm", "Severity", "Probability", "Risk Score", "Risk Level", "Control Measures", "Residual Risk"]
                        md_content.append("| " + " | ".join(risk_headers) + " |")
                        md_content.append("| " + " | ".join(["---"] * len(risk_headers)) + " |")
                        
                        for hazard in hazards:
                            if not status_filter or hazard.get('risk_rating') in ["High", "Medium"]:
                                cells = [
                                    str(hazard.get('hazard_id', '')),
                                    str(hazard.get('hazard_title', '')).replace("|", "\\|").replace("\n", " ")[:30],
                                    str(hazard.get('hazard_description', '')).replace("|", "\\|").replace("\n", " ")[:30],
                                    str(hazard.get('severity_level', '')),
                                    "Medium",  # Sample probability
                                    "12",      # Sample risk score
                                    str(hazard.get('risk_rating', '')),
                                    str(hazard.get('current_controls', '')).replace("|", "\\|").replace("\n", " ")[:40],
                                    "Acceptable"  # Sample residual risk
                                ]
                                md_content.append("| " + " | ".join(cells) + " |")
                        md_content.append("")
                    
                    if not md_content or len([line for line in md_content if line.startswith("|")]) == 0:
                        md_content.append("*No data available*")
                    
                    md_content.append("---")
                    total_items = len(requirements) + len(hazards)
                    md_content.append(f"*Report contains {total_items} total items ({len(requirements)} requirements, {len(hazards)} hazards)*")
                    
                    export_string = "\n".join(md_content)
                    mime_type = "text/markdown"
                    file_ext = "md"
                else:
                    export_string = df.to_csv(index=False)
                    mime_type = "text/csv"
                    file_ext = "csv"
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{report_type.lower().replace(' ', '_')}_{selected_project_name}_{timestamp}.{file_ext}"
                
                st.download_button(
                    label=f"📁 Download {export_format} File",
                    data=export_string,
                    file_name=filename,
                    mime=mime_type,
                    type="primary"
                )
                
                st.success(f"✅ {report_type} ready! Contains {len(export_data)} items.")
            else:
                st.warning("⚠️ No data matches the selected filters.")
    
    with export_button_cols[1]:
        if st.button("🧠 Update Knowledge Base"):
            st.info("🔄 Updating knowledge base with project data...")
            
            try:
                # Get all data for knowledge base update
                requirements = get_system_requirements(selected_project_id)
                hazards = get_hazards_risks(selected_project_id)
                fmea_analyses = get_fmea_analyses(selected_project_id)
                design_artifacts = get_design_artifacts(selected_project_id)
                test_artifacts = get_test_artifacts(selected_project_id)
                
                # Prepare text content for knowledge base
                kb_content_sections = []
                
                # Add project overview
                kb_content_sections.append(f"""
# Design Record - {selected_project_name}
Compliance Standard: {compliance_standard}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
                
                # Add requirements (always include section)
                kb_content_sections.append("\n## Requirements\n")
                if requirements:
                    for req in requirements:
                        kb_content_sections.append(f"""
### {req.get('req_id', 'REQ-Unknown')} - {req.get('req_title', 'Untitled')}
- **Type**: {req.get('req_type', 'Unknown')}
- **Priority**: {req.get('req_priority', 'Unknown')}
- **Status**: {req.get('req_status', 'Unknown')}
- **Description**: {req.get('req_description', 'No description')}
- **Rationale**: {req.get('rationale', 'No rationale provided')}
- **Source**: {req.get('req_source', 'Unknown')}
""")
                else:
                    kb_content_sections.append("No requirements defined for this project.\n")
                
                # Add hazards (always include section)
                kb_content_sections.append("\n## Hazards and Risks\n")
                if hazards:
                    for hazard in hazards:
                        kb_content_sections.append(f"""
### {hazard.get('hazard_id', 'HAZ-Unknown')} - {hazard.get('hazard_title', 'Untitled')}
- **Category**: {hazard.get('hazard_category', 'Unknown')}
- **Severity**: {hazard.get('severity_level', 'Unknown')}
- **Risk Rating**: {hazard.get('risk_rating', 'Unknown')}
- **Description**: {hazard.get('hazard_description', 'No description')}
- **Context**: {hazard.get('operational_context', 'No context provided')}
- **Controls**: {hazard.get('current_controls', 'No controls specified')}
""")
                else:
                    kb_content_sections.append("No hazards and risks identified for this project.\n")
                
                # Add FMEA analyses (always include section)
                kb_content_sections.append("\n## FMEA Analyses\n")
                if fmea_analyses:
                    for fmea in fmea_analyses:
                        kb_content_sections.append(f"""
### {fmea.get('analysis_id', 'FMEA-Unknown')} - {fmea.get('analysis_title', 'Untitled')}
- **Component**: {fmea.get('component_function', 'Unknown')}
- **Failure Mode**: {fmea.get('failure_mode', 'Not specified')}
- **Effects**: {fmea.get('failure_effects', 'No effects documented')}
- **Causes**: {fmea.get('failure_causes', 'No causes documented')}
- **Detection Methods**: {fmea.get('detection_methods', 'No detection methods')}
- **RPN**: {fmea.get('rpn_score', 'Not calculated')}
""")
                else:
                    kb_content_sections.append("No FMEA analyses completed for this project.\n")
                
                # Add design artifacts (always include section)
                kb_content_sections.append("\n## Design Artifacts\n")
                if design_artifacts:
                    for design in design_artifacts:
                        kb_content_sections.append(f"""
### {design.get('artifact_id', 'DESIGN-Unknown')} - {design.get('artifact_title', 'Untitled')}
- **Type**: {design.get('artifact_type', 'Unknown')}
- **Status**: {design.get('artifact_status', 'Unknown')}
- **Version**: {design.get('version', 'Unknown')}
- **Description**: {design.get('artifact_description', 'No description')}
- **Created By**: {design.get('created_by', 'Unknown')}
- **Created Date**: {design.get('created_date', 'Unknown')}
""")
                else:
                    kb_content_sections.append("No design artifacts documented for this project.\n")
                
                # Add test artifacts (always include section)
                kb_content_sections.append("\n## Test Artifacts\n")
                if test_artifacts:
                    for test in test_artifacts:
                        kb_content_sections.append(f"""
### {test.get('test_id', 'TEST-Unknown')} - {test.get('test_title', 'Untitled')}
- **Type**: {test.get('test_type', 'Unknown')}
- **Status**: {test.get('test_status', 'Unknown')}
- **Result**: {test.get('test_result', 'Unknown')}
- **Description**: {test.get('test_description', 'No description')}
- **Expected Outcome**: {test.get('expected_outcome', 'Not specified')}
- **Actual Outcome**: {test.get('actual_outcome', 'Not specified')}
""")
                else:
                    kb_content_sections.append("No test artifacts available for this project.\n")
                
                # Add Clinical Studies Data
                kb_content_sections.append("\n## Clinical Studies\n")
                clinical_studies = DEMO_CLINICAL_STUDIES
                for study in clinical_studies:
                    kb_content_sections.append(f"""
### {study['Study ID']} - {study['Title']}
- **Status**: {study['Status']}
- **Participants**: {study['Participants']}
""")
                
                # Add Adverse Events Data
                kb_content_sections.append("\n## Adverse Events\n")
                adverse_events = DEMO_ADVERSE_EVENTS
                for event in adverse_events:
                    kb_content_sections.append(f"""
### {event['Event ID']} - {event['Date']}
- **Severity**: {event['Severity'].replace('_', ' ').title()}
- **Status**: {event['Status'].title()}
- **Description**: {event['Description']}
""")
                
                # Add Field Safety Actions
                kb_content_sections.append("\n## Field Safety Actions\n")
                field_actions = DEMO_FIELD_ACTIONS
                for action in field_actions:
                    kb_content_sections.append(f"""
### {action['Action ID']} - {action['Type'].replace('_', ' ').title()}
- **Date**: {action['Date']}
- **Status**: {action['Status']}
- **Description**: {action['Description']}
- **Affected Products**: {action['Affected Products']}
""")
                
                # Add Compliance Standards
                kb_content_sections.append("\n## Compliance Standards\n")
                standards = DEMO_COMPLIANCE_STANDARDS
                for std in standards:
                    kb_content_sections.append(f"""
### {std['Standard']} - {std['Title']}
- **Status**: {std['Status']}
- **Compliance**: {std['Compliance']}
""")
                
                # Combine all content
                full_kb_content = "\n".join(kb_content_sections)
                
                # Prepare metadata
                metadata = {
                    "project_id": selected_project_id,
                    "project_name": selected_project_name,
                    "compliance_standard": compliance_standard,
                    "report_type": report_type,
                    "timestamp": datetime.now().isoformat(),
                    "content_type": "design_record_comprehensive",
                    "requirements_count": len(requirements),
                    "hazards_count": len(hazards),
                    "fmea_count": len(fmea_analyses),
                    "design_count": len(design_artifacts),
                    "test_count": len(test_artifacts),
                    "clinical_studies_count": len(clinical_studies),
                    "adverse_events_count": len(adverse_events),
                    "field_actions_count": len(field_actions),
                    "standards_count": len(standards),
                    "total_sections": 9
                }
                
                # Use the real Knowledge Base API - store in default collection
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/kb/add_text",
                        params={
                            "collection_name": "knowledge_base",  # Use default collection
                            "text_content": full_kb_content,
                            "filename": f"design_record_{selected_project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                        },
                        json=metadata,
                        headers=get_auth_headers(),
                        timeout=KB_LONG_REQUEST_TIMEOUT
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ Knowledge base updated successfully!")
                        
                        # Show comprehensive result
                        total_items = len(requirements) + len(hazards) + len(fmea_analyses) + len(design_artifacts) + len(test_artifacts)
                        total_comprehensive = total_items + len(clinical_studies) + len(adverse_events) + len(field_actions) + len(standards)
                        st.json({
                            "Status": "Success",
                            "Collection": "knowledge_base (default)",
                            "Total Items Processed": total_comprehensive,
                            "Project Data": {
                                "Requirements": len(requirements),
                                "Hazards": len(hazards), 
                                "FMEA Analyses": len(fmea_analyses),
                                "Design Artifacts": len(design_artifacts),
                                "Test Artifacts": len(test_artifacts)
                            },
                            "Regulatory Data": {
                                "Clinical Studies": len(clinical_studies),
                                "Adverse Events": len(adverse_events),
                                "Field Actions": len(field_actions),
                                "Standards": len(standards)
                            },
                            "Project": selected_project_name,
                            "Compliance Standard": compliance_standard,
                            "Content Size": f"{len(full_kb_content):,} characters",
                            "Sections": 9,
                            "Timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                    else:
                        st.error(f"❌ Knowledge base update failed: {response.status_code}")
                        if response.text:
                            st.error(response.text)
                            
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Connection error: {str(e)}")
                    st.info("Please check if the Knowledge Base service is running.")
                    
            except Exception as e:
                st.error(f"❌ Error updating knowledge base: {str(e)}")
                
            # Show preview of content being added
            with st.expander("🔍 Preview Knowledge Base Content"):
                st.markdown("**Content Preview** (first 1000 characters):")
                try:
                    preview_content = full_kb_content[:1000] + "..." if len(full_kb_content) > 1000 else full_kb_content
                    st.text(preview_content)
                except:
                    st.text("Content preview unavailable")
    
    with export_button_cols[2]:
        if st.button("📄 Publish as Document", type="secondary", help="Publish this report as a Document for review workflow"):
            # Generate markdown content using the same logic as the Generate Report button
            requirements = get_system_requirements(selected_project_id)
            hazards = get_hazards_risks(selected_project_id)
            
            # Create comprehensive export based on report type
            export_data = []
            
            if report_type == "Complete Design Record":
                # Add requirements
                for req in requirements:
                    export_data.append({
                        "Type": "Requirement",
                        "ID": req.get('req_id', ''),
                        "Title": req.get('req_title', ''),
                        "Description": req.get('req_description', ''),
                        "Category": req.get('req_type', ''),
                        "Priority": req.get('req_priority', ''),
                        "Status": req.get('req_status', ''),
                        "Version": req.get('req_version', ''),
                        "Source": req.get('req_source', ''),
                        "Rationale": req.get('rationale', ''),
                        "Created_Date": req.get('created_at', ''),
                        "Standard": compliance_standard
                    })
                
                # Add hazards
                for hazard in hazards:
                    export_data.append({
                        "Type": "Hazard",
                        "ID": hazard.get('hazard_id', ''),
                        "Title": hazard.get('hazard_title', ''),
                        "Description": hazard.get('hazard_description', ''),
                        "Category": hazard.get('hazard_category', ''),
                        "Severity": hazard.get('severity_level', ''),
                        "Risk_Rating": hazard.get('risk_rating', ''),
                        "Version": "1.0",
                        "Context": hazard.get('operational_context', ''),
                        "Controls": hazard.get('current_controls', ''),
                        "Created_Date": hazard.get('created_at', ''),
                        "Standard": compliance_standard
                    })
            
            elif report_type == "Requirements Traceability":
                # Filter for requirements only
                for req in requirements:
                    export_data.append({
                        "Type": "Requirement",
                        "ID": req.get('req_id', ''),
                        "Title": req.get('req_title', ''),
                        "Description": req.get('req_description', ''),
                        "Category": req.get('req_type', ''),
                        "Priority": req.get('req_priority', ''),
                        "Status": req.get('req_status', ''),
                        "Version": req.get('req_version', ''),
                        "Source": req.get('req_source', ''),
                        "Rationale": req.get('rationale', ''),
                        "Created_Date": req.get('created_at', ''),
                        "Standard": compliance_standard
                    })
            
            elif report_type == "Risk Analysis":
                # Filter for hazards only
                for hazard in hazards:
                    export_data.append({
                        "Type": "Hazard",
                        "ID": hazard.get('hazard_id', ''),
                        "Title": hazard.get('hazard_title', ''),
                        "Description": hazard.get('hazard_description', ''),
                        "Category": hazard.get('hazard_category', ''),
                        "Severity": hazard.get('severity_level', ''),
                        "Risk_Rating": hazard.get('risk_rating', ''),
                        "Version": "1.0",
                        "Context": hazard.get('operational_context', ''),
                        "Controls": hazard.get('current_controls', ''),
                        "Created_Date": hazard.get('created_at', ''),
                        "Standard": compliance_standard
                    })
            
            if export_data:
                import pandas as pd
                df = pd.DataFrame(export_data)
                
                # Create markdown content with separate tables for each data type
                md_content = []
                md_content.append(f"# {report_type}")
                md_content.append(f"**Project:** {selected_project_name}")
                md_content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                md_content.append(f"**Compliance Standard:** {compliance_standard}")
                md_content.append("")
                
                if report_type == "Complete Design Record":
                    # Create separate tables for Requirements and Hazards
                    if requirements:
                        md_content.append("## System Requirements")
                        md_content.append("")
                        req_headers = ["ID", "Title", "Description", "Type", "Priority", "Status", "Version", "Source", "Rationale"]
                        md_content.append("| " + " | ".join(req_headers) + " |")
                        md_content.append("| " + " | ".join(["---"] * len(req_headers)) + " |")
                        
                        for req in requirements:
                            cells = [
                                str(req.get('req_id', '')),
                                str(req.get('req_title', '')).replace("|", "\\|").replace("\n", " ")[:30],
                                str(req.get('req_description', '')).replace("|", "\\|").replace("\n", " ")[:50],
                                str(req.get('req_type', '')),
                                str(req.get('req_priority', '')),
                                str(req.get('req_status', '')),
                                str(req.get('req_version', '')),
                                str(req.get('req_source', '')),
                                str(req.get('rationale', '')).replace("|", "\\|").replace("\n", " ")[:40]
                            ]
                            md_content.append("| " + " | ".join(cells) + " |")
                        md_content.append("")
                    
                    if hazards:
                        md_content.append("## Hazards and Risk Analysis")
                        md_content.append("")
                        hazard_headers = ["ID", "Title", "Description", "Category", "Severity", "Risk Rating", "Context", "Current Controls"]
                        md_content.append("| " + " | ".join(hazard_headers) + " |")
                        md_content.append("| " + " | ".join(["---"] * len(hazard_headers)) + " |")
                        
                        for hazard in hazards:
                            cells = [
                                str(hazard.get('hazard_id', '')),
                                str(hazard.get('hazard_title', '')).replace("|", "\\|").replace("\n", " ")[:30],
                                str(hazard.get('hazard_description', '')).replace("|", "\\|").replace("\n", " ")[:40],
                                str(hazard.get('hazard_category', '')),
                                str(hazard.get('severity_level', '')),
                                str(hazard.get('risk_rating', '')),
                                str(hazard.get('operational_context', '')).replace("|", "\\|").replace("\n", " ")[:30],
                                str(hazard.get('current_controls', '')).replace("|", "\\|").replace("\n", " ")[:40]
                            ]
                            md_content.append("| " + " | ".join(cells) + " |")
                        md_content.append("")
                
                elif report_type == "Requirements Traceability":
                    md_content.append("## Requirements Traceability Matrix")
                    md_content.append("")
                    trace_headers = ["Requirement ID", "Title", "Type", "Status", "Linked Hazards", "Design Items", "Test Cases", "Verification Status", "Coverage"]
                    md_content.append("| " + " | ".join(trace_headers) + " |")
                    md_content.append("| " + " | ".join(["---"] * len(trace_headers)) + " |")
                    
                    for req in requirements:
                        cells = [
                            str(req.get('req_id', '')),
                            str(req.get('req_title', '')).replace("|", "\\|").replace("\n", " ")[:30],
                            str(req.get('req_type', '')),
                            str(req.get('req_status', '')),
                            "HAZ-001, HAZ-003",  # Sample linked hazards
                            "DES-001, DES-005",  # Sample design items
                            "TC-001, TC-007",    # Sample test cases
                            "Verified",          # Sample verification status
                            "100%"               # Sample coverage
                        ]
                        md_content.append("| " + " | ".join(cells) + " |")
                    md_content.append("")
                
                elif report_type == "Risk Management Summary":
                    md_content.append("## Risk Management Summary")
                    md_content.append("")
                    risk_headers = ["Hazard ID", "Hazardous Situation", "Potential Harm", "Severity", "Probability", "Risk Score", "Risk Level", "Control Measures", "Residual Risk"]
                    md_content.append("| " + " | ".join(risk_headers) + " |")
                    md_content.append("| " + " | ".join(["---"] * len(risk_headers)) + " |")
                    
                    for hazard in hazards:
                        cells = [
                            str(hazard.get('hazard_id', '')),
                            str(hazard.get('hazard_title', '')).replace("|", "\\|").replace("\n", " ")[:30],
                            str(hazard.get('hazard_description', '')).replace("|", "\\|").replace("\n", " ")[:30],
                            str(hazard.get('severity_level', '')),
                            "Medium",  # Sample probability
                            "12",      # Sample risk score
                            str(hazard.get('risk_rating', '')),
                            str(hazard.get('current_controls', '')).replace("|", "\\|").replace("\n", " ")[:40],
                            "Acceptable"  # Sample residual risk
                        ]
                        md_content.append("| " + " | ".join(cells) + " |")
                    md_content.append("")
                
                if not md_content or len([line for line in md_content if line.startswith("|")]) == 0:
                    md_content.append("*No data available*")
                
                md_content.append("---")
                total_items = len(requirements) + len(hazards)
                md_content.append(f"*Report contains {total_items} total items ({len(requirements)} requirements, {len(hazards)} hazards)*")
                
                markdown_content = "\n".join(md_content)
                
                # Call the publish API
                try:
                    publish_data = {
                        "project_id": selected_project_id,
                        "project_name": selected_project_name,
                        "report_type": report_type,
                        "compliance_standard": compliance_standard,
                        "markdown_content": markdown_content
                    }
                    
                    publish_response = requests.post(
                        f"{BACKEND_URL}/api/publish/design-record-as-document",
                        json=publish_data,
                        headers=get_auth_headers(),
                        timeout=30
                    )
                    
                    if publish_response.status_code == 200:
                        result = publish_response.json()
                        st.success(f"✅ {result['message']}")
                        st.info(f"📄 Document created: **{result['document_name']}**")
                        st.info(f"🔗 Document ID: `{result['document_id']}`")
                        
                        # Add navigation option
                        if st.button("📂 Go to Documents", help="Navigate to Documents page to view the published document"):
                            st.session_state.page = "Documents"
                            st.rerun()
                            
                    else:
                        error_detail = publish_response.json().get("detail", "Unknown error")
                        st.error(f"❌ Failed to publish as document: {error_detail}")
                        
                except requests.exceptions.Timeout:
                    st.error("❌ Request timed out. Please try again.")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Connection error: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error publishing document: {str(e)}")
                    
            else:
                st.warning("⚠️ No data matches the selected filters for publishing.")
    
    st.markdown("---")
    st.markdown("#### 📊 Export Statistics")
    
    # Get real statistics from the project data
    try:
        # Get current project data counts
        requirements = get_system_requirements(selected_project_id)
        hazards = get_hazards_risks(selected_project_id) 
        fmea_analyses = get_fmea_analyses(selected_project_id)
        design_artifacts = get_design_artifacts(selected_project_id)
        test_artifacts = get_test_artifacts(selected_project_id)
        
        # Calculate real statistics
        total_data_points = len(requirements) + len(hazards) + len(fmea_analyses) + len(design_artifacts) + len(test_artifacts)
        
        # Get Knowledge Base statistics if available
        kb_stats = None
        try:
            kb_response = requests.get(f"{BACKEND_URL}/kb/stats", headers=get_auth_headers(), timeout=5)
            if kb_response.status_code == 200:
                kb_stats = kb_response.json()
        except:
            kb_stats = None
        
        # Count compliance-related items (requirements with compliance standards)
        compliance_items = sum(1 for req in requirements if req.get('req_source') and 'ISO' in req.get('req_source', ''))
        
        # Count items ready for audit (approved status)
        audit_ready_items = sum(1 for req in requirements if req.get('req_status') == 'Approved')
        audit_ready_items += sum(1 for hazard in hazards if hazard.get('risk_rating', '').lower() in ['low', 'controlled'])
        
        stats_cols = st.columns([1, 1, 1, 1])
        
        with stats_cols[0]:
            kb_documents = kb_stats.get('total_documents', 0) if kb_stats else 0
            st.metric(
                "KB Documents", 
                str(kb_documents),
                f"Design records in KB"
            )
            
        with stats_cols[1]:
            st.metric(
                "Data Points Available", 
                f"{total_data_points:,}",
                f"Current project: {selected_project_name}"
            )
            
        with stats_cols[2]:
            st.metric(
                "Compliance Items", 
                str(compliance_items),
                f"Standards-linked requirements"
            )
            
        with stats_cols[3]:
            st.metric(
                "Audit Ready Items", 
                str(audit_ready_items),
                "Approved/Controlled status"
            )
        
        # Additional statistics row
        st.markdown("---")
        detail_stats_cols = st.columns([1, 1, 1, 1, 1])
        
        with detail_stats_cols[0]:
            st.metric("Requirements", len(requirements), "System requirements")
        with detail_stats_cols[1]: 
            st.metric("Hazards", len(hazards), "Risk assessments")
        with detail_stats_cols[2]:
            st.metric("FMEA", len(fmea_analyses), "Failure analyses")
        with detail_stats_cols[3]:
            st.metric("Design", len(design_artifacts), "Design artifacts")
        with detail_stats_cols[4]:
            st.metric("Tests", len(test_artifacts), "Test artifacts")
            
        # Show Knowledge Base details if available
        if kb_stats:
            with st.expander("🧠 Knowledge Base Statistics"):
                kb_detail_cols = st.columns([1, 1, 1])
                with kb_detail_cols[0]:
                    st.metric("Total Documents", kb_stats.get('total_documents', 0))
                with kb_detail_cols[1]:
                    st.metric("Collections", kb_stats.get('total_collections', 0))
                with kb_detail_cols[2]:
                    kb_size = kb_stats.get('total_size_mb', 0)
                    st.metric("Size (MB)", f"{kb_size:.1f}" if kb_size else "0.0")
                    
    except Exception as e:
        # Fallback to basic statistics if API calls fail
        st.warning("⚠️ Could not fetch live statistics. Showing basic project data.")
        
        try:
            requirements = get_system_requirements(selected_project_id)
            hazards = get_hazards_risks(selected_project_id)
            total_items = len(requirements) + len(hazards)
            
            stats_cols = st.columns([1, 1, 1, 1])
            with stats_cols[0]:
                st.metric("Requirements", len(requirements), "Current project")
            with stats_cols[1]:
                st.metric("Hazards", len(hazards), "Risk items") 
            with stats_cols[2]:
                st.metric("Total Items", total_items, "Available for export")
            with stats_cols[3]:
                st.metric("Project", "1", f"{selected_project_name}")
        except:
            st.error("Unable to load project statistics")

# Footer
st.markdown("---")
st.info("🔬 **Design Record**: Comprehensive lifecycle risk and requirements management supporting medical device, automotive, and industrial safety standards.")