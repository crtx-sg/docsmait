# frontend/pages/Audit.py
import streamlit as st
import requests
from datetime import datetime, date
import pandas as pd
from typing import List, Dict, Any
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers
from config import BACKEND_URL, DATAFRAME_HEIGHT, EXPORT_FILENAME_FORMAT, MARKDOWN_TRUNCATE_LENGTH, KB_REQUEST_TIMEOUT

require_auth()

st.set_page_config(page_title="Audit Management", page_icon="📊", layout="wide")

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

st.title("📊 Audit Management")

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

def get_audits(project_id=None, status=None):
    """Get audits with optional filtering"""
    try:
        params = {}
        if project_id:
            params["project_id"] = project_id
        if status:
            params["status"] = status
        
        response = requests.get(f"{BACKEND_URL}/audits", headers=get_auth_headers(), params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_findings(audit_id=None):
    """Get findings for an audit"""
    try:
        params = {}
        if audit_id:
            params["audit_id"] = audit_id
        
        response = requests.get(f"{BACKEND_URL}/findings", headers=get_auth_headers(), params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_corrective_actions(finding_id=None):
    """Get corrective actions for a finding"""
    try:
        params = {}
        if finding_id:
            params["finding_id"] = finding_id
        
        response = requests.get(f"{BACKEND_URL}/corrective-actions", headers=get_auth_headers(), params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# Main tab navigation
tab1, tab2, tab3, tab4 = st.tabs(["📊 Audit Dashboard", "📋 Manage Audits", "🔍 Findings & Actions", "📄 Reports"])

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
        status_filter = st.selectbox("Filter by Status", ["All", "planned", "in_progress", "completed", "cancelled"])
        status = None if status_filter == "All" else status_filter
    
    # Get and display audits
    audits = get_audits(project_id, status)
    
    if audits:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Audits", len(audits))
        with col2:
            planned_count = len([a for a in audits if a["status"] == "planned"])
            st.metric("Planned", planned_count)
        with col3:
            in_progress_count = len([a for a in audits if a["status"] == "in_progress"])
            st.metric("In Progress", in_progress_count)
        with col4:
            total_findings = sum(a["open_findings_count"] for a in audits)
            st.metric("Open Findings", total_findings)
        
        # Audits table
        st.subheader("Recent Audits")
        audit_data = []
        for audit in audits:
            audit_data.append({
                "Audit #": audit["audit_number"],
                "Title": audit["title"],
                "Type": audit["audit_type"].title(),
                "Status": audit["status"].title(),
                "Lead Auditor": audit["lead_auditor_username"],
                "Start Date": audit["planned_start_date"],
                "Findings": f"{audit['open_findings_count']}/{audit['findings_count']}",
                "Project": audit["project_name"]
            })
        
        df = pd.DataFrame(audit_data)
        st.dataframe(df, use_container_width=True, height=DATAFRAME_HEIGHT)
    else:
        st.info("No audits found. Create your first audit in the 'Manage Audits' tab.")

with tab2:
    
    audit_subtabs = st.tabs(["👀 View/Edit Existing", "➕ Create New Audit"])
    
    with audit_subtabs[0]:
        st.markdown("**View and Edit Audits**")
        
        # Filters for audits
        col1, col2, col3 = st.columns(3)
        
        with col1:
            audit_type_filter = st.selectbox(
                "Type",
                ["All", "internal", "external", "supplier", "regulatory"],
                key="audit_type_filter"
            )
        
        with col2:
            audit_status_filter = st.selectbox(
                "Status",
                ["All", "planned", "in_progress", "completed", "cancelled"],
                key="audit_status_filter"
            )
        
        with col3:
            projects = get_projects()
            project_options = ["All Projects"] + [p["name"] for p in projects]
            audit_project_filter = st.selectbox("Project", project_options, key="audit_project_filter")
        
        # Get and display audits
        audits = get_audits()
        
        if audits:
            # Apply filters
            filtered_audits = audits
            if audit_type_filter != "All":
                filtered_audits = [a for a in filtered_audits if a.get('audit_type') == audit_type_filter]
            if audit_status_filter != "All":
                filtered_audits = [a for a in filtered_audits if a.get('status') == audit_status_filter]
            if audit_project_filter != "All Projects":
                filtered_audits = [a for a in filtered_audits if a.get('project_name') == audit_project_filter]
            
            st.markdown(f"**Showing {len(filtered_audits)} of {len(audits)} audits**")
            
            # Prepare data for st.dataframe
            audit_grid_data = []
            for audit in filtered_audits:
                audit_row = {
                    'Audit #': audit['audit_number'],
                    'Title': audit['title'],
                    'Type': audit['audit_type'].title(),
                    'Status': audit['status'].title(),
                    'Lead Auditor': audit['lead_auditor_username'],
                    'Start Date': audit['planned_start_date'],
                    'End Date': audit['planned_end_date'],
                    'Project': audit['project_name'],
                    'Findings': f"{audit['open_findings_count']}/{audit['findings_count']}",
                    'full_audit_data': audit
                }
                audit_grid_data.append(audit_row)
            
            # Create DataFrame for display
            audit_df_data = []
            for row in audit_grid_data:
                audit_df_row = {
                    'Audit #': row['Audit #'],
                    'Title': row['Title'],
                    'Type': row['Type'],
                    'Status': row['Status'],
                    'Lead Auditor': row['Lead Auditor'],
                    'Start Date': row['Start Date'],
                    'Project': row['Project'],
                    'Findings': row['Findings']
                }
                audit_df_data.append(audit_df_row)
            
            audit_df = pd.DataFrame(audit_df_data)
            
            # Display with selection capability
            audit_selected_indices = st.dataframe(
                audit_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                height=DATAFRAME_HEIGHT
            )
            
            st.caption("💡 Select a row to view audit details")
            
            # Handle audit selection
            if audit_selected_indices and len(audit_selected_indices.selection.rows) > 0:
                selected_idx = audit_selected_indices.selection.rows[0]
                audit = audit_grid_data[selected_idx]['full_audit_data']
                # Only update if different audit selected
                if st.session_state.get('selected_audit_id') != audit.get('id'):
                    st.session_state.selected_audit_id = audit.get('id')
                    st.session_state.selected_audit_data = audit
                    st.rerun()
            
            # Show editable details for selected audit
            if st.session_state.get('selected_audit_data'):
                audit = st.session_state.selected_audit_data
                st.markdown("---")
                st.markdown("### 📝 Edit Selected Audit")
                
                with st.form("edit_audit_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edited_title = st.text_input("Audit Title", value=audit.get('title', ''))
                        edited_type = st.selectbox("Audit Type", ["internal", "external", "supplier", "regulatory"], 
                                                 index=["internal", "external", "supplier", "regulatory"].index(audit.get('audit_type', 'internal')))
                        edited_status = st.selectbox("Status", ["planned", "in_progress", "completed", "cancelled"],
                                                   index=["planned", "in_progress", "completed", "cancelled"].index(audit.get('status', 'planned')))
                        edited_auditee_dept = st.text_input("Auditee Department", value=audit.get('auditee_department', ''))
                    
                    with col2:
                        edited_start_date = st.date_input("Planned Start Date", 
                                                        value=datetime.strptime(audit.get('planned_start_date', '2024-01-01'), '%Y-%m-%d').date())
                        edited_end_date = st.date_input("Planned End Date", 
                                                      value=datetime.strptime(audit.get('planned_end_date', '2024-01-01'), '%Y-%m-%d').date())
                        edited_compliance_standard = st.text_input("Compliance Standard", value=audit.get('compliance_standard', ''))
                        
                        # Lead Auditor selection
                        users = get_users()
                        if users:
                            lead_auditor_names = [f"{u['username']} ({u['email']})" for u in users]
                            current_lead = audit.get('lead_auditor_username', '')
                            current_lead_index = 0
                            for i, name in enumerate(lead_auditor_names):
                                if current_lead in name:
                                    current_lead_index = i
                                    break
                            selected_lead = st.selectbox("Lead Auditor", lead_auditor_names, index=current_lead_index)
                            lead_auditor_id = users[lead_auditor_names.index(selected_lead)]["id"]
                        else:
                            lead_auditor_id = audit.get('lead_auditor')
                    
                    edited_scope = st.text_area("Audit Scope", value=audit.get('scope', ''), height=100)
                    
                    col3, col4 = st.columns(2)
                    with col3:
                        if st.form_submit_button("💾 Save Changes", type="primary"):
                            try:
                                updated_audit = {
                                    "title": edited_title,
                                    "audit_type": edited_type,
                                    "status": edited_status,
                                    "scope": edited_scope,
                                    "planned_start_date": edited_start_date.isoformat(),
                                    "planned_end_date": edited_end_date.isoformat(),
                                    "auditee_department": edited_auditee_dept,
                                    "compliance_standard": edited_compliance_standard,
                                    "lead_auditor": lead_auditor_id
                                }
                                
                                response = requests.put(
                                    f"{BACKEND_URL}/audits/{audit['id']}", 
                                    json=updated_audit, 
                                    headers=get_auth_headers()
                                )
                                
                                if response.status_code == 200:
                                    st.success("✅ Audit updated successfully!")
                                    
                                    # Send completed audit report to Knowledge Base if status is completed
                                    if edited_status == "completed":
                                        try:
                                            kb_content = f"""# Audit Report: {edited_title}
**Audit Number**: {audit.get('audit_number', 'N/A')}
**Type**: {edited_type.replace('_', ' ').title()}
**Status**: Completed
**Completion Date**: {datetime.now().strftime('%Y-%m-%d')}
**Lead Auditor**: {audit.get('lead_auditor_username', 'Unknown')}
**Auditee Department**: {edited_auditee_dept}
**Compliance Standard**: {edited_compliance_standard}

## Audit Details

**Planned Start Date**: {edited_start_date}
**Planned End Date**: {edited_end_date}
**Scope**: {edited_scope}

## Audit Summary

This audit has been completed successfully. The audit covered the scope defined above and was conducted according to the specified compliance standard.

**Key Information:**
- Audit conducted by: {audit.get('lead_auditor_username', 'Unknown')}
- Department audited: {edited_auditee_dept}
- Compliance framework: {edited_compliance_standard}
- Duration: {edited_start_date} to {edited_end_date}
"""
                                            
                                            metadata = {
                                                "audit_id": audit['id'],
                                                "audit_number": audit.get('audit_number', ''),
                                                "audit_title": edited_title,
                                                "audit_type": edited_type,
                                                "completion_date": datetime.now().isoformat(),
                                                "lead_auditor": audit.get('lead_auditor_username', ''),
                                                "compliance_standard": edited_compliance_standard,
                                                "content_type": "completed_audit_report"
                                            }
                                            
                                            kb_response = requests.post(
                                                f"{BACKEND_URL}/kb/add_text",
                                                params={
                                                    "collection_name": "knowledge_base",  # Use default collection
                                                    "text_content": kb_content,
                                                    "filename": f"audit_report_{edited_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                                                },
                                                json=metadata,
                                                headers=get_auth_headers(),
                                                timeout=KB_REQUEST_TIMEOUT
                                            )
                                            
                                            if kb_response.status_code == 200:
                                                st.info("📚 Completed audit report also added to Knowledge Base")
                                                
                                        except Exception:
                                            pass  # Silently handle KB integration failures
                                    
                                    # Clear selection and rerun to refresh data
                                    if 'selected_audit_id' in st.session_state:
                                        del st.session_state.selected_audit_id
                                    if 'selected_audit_data' in st.session_state:
                                        del st.session_state.selected_audit_data
                                    st.rerun()
                                else:
                                    error_msg = response.text
                                    try:
                                        error_json = response.json()
                                        if "detail" in error_json:
                                            error_msg = error_json["detail"]
                                    except:
                                        pass
                                    st.error(f"❌ Failed to update audit: {error_msg}")
                            except Exception as e:
                                st.error(f"❌ Connection error: {e}")
                    
                    with col4:
                        if st.form_submit_button("❌ Cancel"):
                            # Clear selection
                            if 'selected_audit_id' in st.session_state:
                                del st.session_state.selected_audit_id
                            if 'selected_audit_data' in st.session_state:
                                del st.session_state.selected_audit_data
                            st.rerun()
        
        else:
            st.info("No audits found. Create your first audit in the 'Create New Audit' tab.")
    
    with audit_subtabs[1]:
        st.markdown("**Create New Audit**")
        
        with st.form("create_audit_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Audit Title*", placeholder="Annual QMS Internal Audit")
                audit_type = st.selectbox("Audit Type*", ["internal", "external", "supplier", "regulatory"])
                scope = st.text_area("Audit Scope*", placeholder="Quality Management System processes...")
                auditee_dept = st.text_input("Auditee Department*", placeholder="Quality Assurance")
                
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
                
                users = get_users()
                if users:
                    lead_auditor_names = [f"{u['username']} ({u['email']})" for u in users]
                    selected_lead = st.selectbox("Lead Auditor*", lead_auditor_names)
                    lead_auditor_id = users[lead_auditor_names.index(selected_lead)]["id"]
                    
                    audit_team_names = st.multiselect("Audit Team", lead_auditor_names)
                    audit_team_ids = [users[lead_auditor_names.index(name)]["id"] for name in audit_team_names]
                else:
                    st.error("No users available.")
                    lead_auditor_id = None
                    audit_team_ids = []
            
            col3, col4 = st.columns(2)
            with col3:
                start_date = st.date_input("Planned Start Date*", value=date.today())
            with col4:
                end_date = st.date_input("Planned End Date*", value=date.today())
            
            compliance_standard = st.text_input("Compliance Standard", value="ISO 13485:2016")
            
            submitted = st.form_submit_button("Create Audit", type="primary")
            
            if submitted:
                if not all([title, audit_type, scope, auditee_dept, selected_project_id, lead_auditor_id]):
                    st.error("Please fill in all required fields marked with *")
                elif end_date < start_date:
                    st.error("End date must be after start date")
                else:
                    try:
                        audit_data = {
                            "title": title,
                            "audit_type": audit_type,
                            "scope": scope,
                            "planned_start_date": start_date.isoformat(),
                            "planned_end_date": end_date.isoformat(),
                            "lead_auditor": lead_auditor_id,
                            "audit_team": audit_team_ids,
                            "auditee_department": auditee_dept,
                            "compliance_standard": compliance_standard,
                            "project_id": selected_project_id
                        }
                        
                        response = requests.post(f"{BACKEND_URL}/audits", json=audit_data, headers=get_auth_headers())
                        
                        if response.status_code == 200:
                            audit_result = response.json()
                            st.success(f"✅ Audit created successfully! Audit Number: {audit_result['audit_number']}")
                            st.balloons()
                            # Clear form by rerunning the page
                            st.rerun()
                        else:
                            error_msg = response.text
                            try:
                                error_json = response.json()
                                if "detail" in error_json:
                                    error_msg = error_json["detail"]
                            except:
                                pass
                            st.error(f"❌ Failed to create audit: {error_msg}")
                    except Exception as e:
                        st.error(f"❌ Connection error: {e}")

with tab3:
    
    # Select audit for findings management
    audits = get_audits()
    if audits:
        audit_options = [f"{a['audit_number']} - {a['title']}" for a in audits]
        selected_audit_str = st.selectbox("Select Audit for Findings", audit_options, key="findings_audit")
        selected_audit = audits[audit_options.index(selected_audit_str)]
        
        findings_tab1, findings_tab2 = st.tabs(["👀 View Findings", "➕ Add Finding"])
        
        with findings_tab1:
            findings = get_findings(selected_audit["id"])
            
            if findings:
                # Prepare data for st.dataframe
                findings_grid_data = []
                for finding in findings:
                    findings_row = {
                        'finding_number': finding['finding_number'],
                        'title': finding['title'],
                        'category': finding['category'],
                        'severity': finding['severity'].upper(),
                        'status': finding['status'].title(),
                        'identified_by': finding['identified_by_username'],
                        'identified_date': finding['identified_date'],
                        'due_date': finding.get('due_date', 'N/A'),
                        'corrective_actions': finding['corrective_actions_count'],
                        'full_finding_data': finding
                    }
                    findings_grid_data.append(findings_row)
                
                # Create DataFrame for findings
                findings_df_data = []
                for row in findings_grid_data:
                    findings_df_row = {
                        'Finding #': row['finding_number'],
                        'Title': row['title'],
                        'Category': row['category'],
                        'Severity': row['severity'],
                        'Status': row['status'],
                        'Identified By': row['identified_by'],
                        'Date': row['identified_date'],
                        'Due Date': row['due_date'],
                        'Actions': row['corrective_actions']
                    }
                    findings_df_data.append(findings_df_row)
                
                findings_df = pd.DataFrame(findings_df_data)
                
                # Display with selection capability
                findings_selected_indices = st.dataframe(
                    findings_df,
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    height=DATAFRAME_HEIGHT
                )
                
                st.caption("💡 Select a row to view finding details")
                
                # Handle findings selection
                if findings_selected_indices and len(findings_selected_indices.selection.rows) > 0:
                    selected_idx = findings_selected_indices.selection.rows[0]
                    finding = findings_grid_data[selected_idx]['full_finding_data']
                    # Only update if different finding selected
                    if st.session_state.get('selected_finding_id') != finding.get('id'):
                        st.session_state.selected_finding_id = finding.get('id')
                        st.session_state.selected_finding_data = finding
                        st.rerun()
                
                # Show editable details for selected finding
                if st.session_state.get('selected_finding_data'):
                    finding = st.session_state.selected_finding_data
                    st.markdown("---")
                    st.markdown("### 📝 Edit Selected Finding")
                    
                    with st.form("edit_finding_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            edited_title = st.text_input("Finding Title", value=finding.get('title', ''))
                            
                            # Handle category with safe index lookup
                            category_options = ["major_nonconformity", "minor_nonconformity", "observation", "opportunity_for_improvement"]
                            current_category = finding.get('category', 'minor_nonconformity')
                            try:
                                category_index = category_options.index(current_category)
                            except ValueError:
                                category_index = 1  # Default to minor_nonconformity
                            edited_category = st.selectbox("Category", category_options, index=category_index)
                            
                            # Handle severity with safe index lookup
                            severity_options = ["observation", "minor", "major", "critical"]
                            current_severity = finding.get('severity', 'minor')
                            try:
                                severity_index = severity_options.index(current_severity)
                            except ValueError:
                                severity_index = 1  # Default to minor
                            edited_severity = st.selectbox("Severity", severity_options, index=severity_index)
                            
                            # Handle status with safe index lookup
                            status_options = ["open", "in_progress", "closed", "verified"]
                            current_status = finding.get('status', 'open')
                            try:
                                status_index = status_options.index(current_status)
                            except ValueError:
                                status_index = 0  # Default to open
                            edited_status = st.selectbox("Status", status_options, index=status_index)
                        
                        with col2:
                            edited_clause_reference = st.text_input("Clause Reference", value=finding.get('clause_reference', ''))
                            edited_due_date = None
                            if finding.get('due_date'):
                                try:
                                    edited_due_date = st.date_input("Due Date", 
                                                                  value=datetime.strptime(finding.get('due_date'), '%Y-%m-%d').date())
                                except:
                                    edited_due_date = st.date_input("Due Date", value=date.today())
                            else:
                                edited_due_date = st.date_input("Due Date", value=date.today())
                            
                            # Risk level with safe index lookup
                            risk_options = ["low", "medium", "high"]
                            current_risk = finding.get('risk_level', 'medium')
                            try:
                                risk_index = risk_options.index(current_risk) if current_risk else 1
                            except ValueError:
                                risk_index = 1  # Default to medium
                            edited_risk_level = st.selectbox("Risk Level", risk_options, index=risk_index)
                            
                            # Regulatory impact with safe index lookup
                            regulatory_options = ["none", "low", "medium", "high"]
                            current_regulatory = finding.get('regulatory_impact', 'low')
                            try:
                                regulatory_index = regulatory_options.index(current_regulatory) if current_regulatory else 1
                            except ValueError:
                                regulatory_index = 1  # Default to low
                            edited_regulatory_impact = st.selectbox("Regulatory Impact", regulatory_options, index=regulatory_index)
                        
                        edited_description = st.text_area("Description", value=finding.get('description', ''), height=100)
                        edited_evidence = st.text_area("Evidence", value=finding.get('evidence', ''))
                        edited_root_cause = st.text_area("Root Cause Analysis", value=finding.get('root_cause', ''))
                        edited_recommendation = st.text_area("Recommendation", value=finding.get('recommendation', ''))
                        
                        col3, col4 = st.columns(2)
                        with col3:
                            if st.form_submit_button("💾 Save Changes", type="primary"):
                                try:
                                    updated_finding = {
                                        "title": edited_title,
                                        "category": edited_category,
                                        "severity": edited_severity,
                                        "status": edited_status,
                                        "description": edited_description,
                                        "evidence": edited_evidence,
                                        "clause_reference": edited_clause_reference,
                                        "due_date": edited_due_date.isoformat() if edited_due_date else None,
                                        "root_cause": edited_root_cause,
                                        "recommendation": edited_recommendation,
                                        "risk_level": edited_risk_level,
                                        "regulatory_impact": edited_regulatory_impact
                                    }
                                    
                                    response = requests.put(
                                        f"{BACKEND_URL}/findings/{finding['id']}", 
                                        json=updated_finding, 
                                        headers=get_auth_headers()
                                    )
                                    
                                    if response.status_code == 200:
                                        st.success("✅ Finding updated successfully!")
                                        # Clear selection and rerun to refresh data
                                        if 'selected_finding_id' in st.session_state:
                                            del st.session_state.selected_finding_id
                                        if 'selected_finding_data' in st.session_state:
                                            del st.session_state.selected_finding_data
                                        st.rerun()
                                    else:
                                        error_msg = response.text
                                        try:
                                            error_json = response.json()
                                            if "detail" in error_json:
                                                error_msg = error_json["detail"]
                                        except:
                                            pass
                                        st.error(f"❌ Failed to update finding: {error_msg}")
                                except Exception as e:
                                    st.error(f"❌ Connection error: {e}")
                        
                        with col4:
                            if st.form_submit_button("❌ Cancel"):
                                # Clear selection
                                if 'selected_finding_id' in st.session_state:
                                    del st.session_state.selected_finding_id
                                if 'selected_finding_data' in st.session_state:
                                    del st.session_state.selected_finding_data
                                st.rerun()
            else:
                st.info("No findings recorded for this audit yet.")
        
        with findings_tab2:
            
            with st.form("create_finding_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    finding_title = st.text_input("Finding Title*")
                    severity = st.selectbox("Severity*", ["observation", "minor", "major", "critical"])
                    category = st.text_input("Category*", placeholder="Documentation, Process, Training, etc.")
                    clause_ref = st.text_input("ISO Clause Reference", placeholder="7.5.3")
                
                with col2:
                    identified_date = st.date_input("Identified Date*", value=date.today())
                    due_date = st.date_input("Due Date", value=None)
                
                description = st.text_area("Description*", height=100)
                evidence = st.text_area("Evidence", height=80)
                root_cause = st.text_area("Root Cause Analysis", height=80)
                immediate_action = st.text_area("Immediate Action Taken", height=80)
                
                submitted = st.form_submit_button("Create Finding", type="primary")
                
                if submitted:
                    if not all([finding_title, severity, category, description]):
                        st.error("Please fill in all required fields marked with *")
                    else:
                        try:
                            finding_data = {
                                "audit_id": selected_audit["id"],
                                "title": finding_title,
                                "description": description,
                                "severity": severity,
                                "category": category,
                                "clause_reference": clause_ref or None,
                                "evidence": evidence or None,
                                "root_cause": root_cause or None,
                                "immediate_action": immediate_action or None,
                                "identified_date": identified_date.isoformat(),
                                "due_date": due_date.isoformat() if due_date else None
                            }
                            
                            response = requests.post(f"{BACKEND_URL}/findings", json=finding_data, headers=get_auth_headers())
                            
                            if response.status_code == 200:
                                finding_result = response.json()
                                st.success(f"✅ Finding created successfully! Finding Number: {finding_result['finding_number']}")
                                st.balloons()
                                # Clear form by rerunning
                                st.rerun()
                            else:
                                error_msg = response.text
                                try:
                                    error_json = response.json()
                                    if "detail" in error_json:
                                        error_msg = error_json["detail"]
                                except:
                                    pass
                                st.error(f"❌ Failed to create finding: {error_msg}")
                        except Exception as e:
                            st.error(f"❌ Connection error: {e}")
    else:
        st.info("No audits available. Create an audit first.")

with tab4:
    
    audits = get_audits()
    if audits:
        audit_options = [f"{a['audit_number']} - {a['title']}" for a in audits]
        selected_audit_str = st.selectbox("Select Audit for Report", audit_options, key="report_audit")
        selected_audit = audits[audit_options.index(selected_audit_str)]
        
        # Format selection
        col1, col2 = st.columns([1, 1])
        with col1:
            report_format = st.selectbox(
                "Report Format",
                options=["CSV", "Markdown"],
                help="Choose the format for your audit report download"
            )
        
        with col2:
            st.write("")  # Add spacing
        
        if st.button(f"📥 Download Audit Report ({report_format})", type="primary", help=f"Download comprehensive audit report as {report_format}"):
            # Get findings and corrective actions for the selected audit
            findings = get_findings(selected_audit["id"])
            
            # Create comprehensive CSV data
            csv_data = []
            
            # Add audit header information
            csv_data.append({
                "Section": "Audit Details",
                "Item Type": "Audit Information",
                "ID": selected_audit['audit_number'],
                "Title": selected_audit['title'],
                "Description": f"Type: {selected_audit['audit_type'].title()} | Standard: {selected_audit['compliance_standard']}",
                "Status": selected_audit.get('status', ''),
                "Department": selected_audit['auditee_department'],
                "Lead Auditor": selected_audit['lead_auditor_username'],
                "Date Range": f"{selected_audit['planned_start_date']} to {selected_audit['planned_end_date']}",
                "Additional Info": selected_audit['scope'][:200] + "..." if len(selected_audit['scope']) > 200 else selected_audit['scope'],
                "Severity": "",
                "Category": "",
                "Clause Reference": "",
                "Responsible Person": "",
                "Due Date": "",
                "Root Cause": ""
            })
            
            # Add findings
            if findings:
                for finding in findings:
                    # Add finding details
                    csv_data.append({
                        "Section": "Findings",
                        "Item Type": "Finding",
                        "ID": finding['finding_number'],
                        "Title": finding['title'],
                        "Description": finding['description'][:500] + "..." if len(finding['description']) > 500 else finding['description'],
                        "Status": finding.get('status', ''),
                        "Department": selected_audit['auditee_department'],
                        "Lead Auditor": selected_audit['lead_auditor_username'],
                        "Date Range": finding.get('identified_date', ''),
                        "Additional Info": finding.get('evidence', '')[:200] + "..." if finding.get('evidence') and len(finding.get('evidence')) > 200 else finding.get('evidence', ''),
                        "Severity": finding['severity'],
                        "Category": finding['category'],
                        "Clause Reference": finding.get('clause_reference', ''),
                        "Responsible Person": finding.get('identified_by_username', ''),
                        "Due Date": finding.get('due_date', ''),
                        "Root Cause": finding.get('root_cause', '')[:200] + "..." if finding.get('root_cause') and len(finding.get('root_cause')) > 200 else finding.get('root_cause', '')
                    })
                    
                    # Add corrective actions for this finding
                    actions = get_corrective_actions(finding['id'])
                    if actions:
                        for action in actions:
                            csv_data.append({
                                "Section": "Corrective Actions",
                                "Item Type": "Corrective Action",
                                "ID": action['action_number'],
                                "Title": f"Action for {finding['finding_number']}",
                                "Description": action['description'][:500] + "..." if len(action['description']) > 500 else action['description'],
                                "Status": action.get('status', ''),
                                "Department": selected_audit['auditee_department'],
                                "Lead Auditor": selected_audit['lead_auditor_username'],
                                "Date Range": action.get('created_date', ''),
                                "Additional Info": action.get('verification_notes', '')[:200] + "..." if action.get('verification_notes') and len(action.get('verification_notes')) > 200 else action.get('verification_notes', ''),
                                "Severity": finding['severity'],
                                "Category": finding['category'],
                                "Clause Reference": finding.get('clause_reference', ''),
                                "Responsible Person": action['responsible_person_username'],
                                "Due Date": action['target_date'],
                                "Root Cause": ""
                            })
            else:
                # Add empty findings entry
                csv_data.append({
                    "Section": "Findings",
                    "Item Type": "No Findings",
                    "ID": "N/A",
                    "Title": "No findings recorded",
                    "Description": "No findings were recorded for this audit",
                    "Status": "",
                    "Department": selected_audit['auditee_department'],
                    "Lead Auditor": selected_audit['lead_auditor_username'],
                    "Date Range": "",
                    "Additional Info": "",
                    "Severity": "",
                    "Category": "",
                    "Clause Reference": "",
                    "Responsible Person": "",
                    "Due Date": "",
                    "Root Cause": ""
                })
            
            if csv_data:
                import pandas as pd
                from datetime import datetime
                
                # Generate filename with audit number and timestamp
                timestamp = datetime.now().strftime(EXPORT_FILENAME_FORMAT)
                
                if report_format == "CSV":
                    df = pd.DataFrame(csv_data)
                    report_data = df.to_csv(index=False)
                    filename = f"audit_report_{selected_audit['audit_number']}_{timestamp}.csv"
                    mime_type = "text/csv"
                    
                else:  # Markdown format
                    # Create Markdown report
                    markdown_lines = []
                    
                    # Header
                    markdown_lines.append(f"# Audit Report: {selected_audit['audit_number']}")
                    markdown_lines.append(f"## {selected_audit['title']}")
                    markdown_lines.append("")
                    
                    # Audit Details Section
                    markdown_lines.append("## 📋 Audit Details")
                    markdown_lines.append("")
                    markdown_lines.append(f"- **Audit Number**: {selected_audit['audit_number']}")
                    markdown_lines.append(f"- **Title**: {selected_audit['title']}")
                    markdown_lines.append(f"- **Type**: {selected_audit['audit_type'].title()}")
                    markdown_lines.append(f"- **Standard**: {selected_audit['compliance_standard']}")
                    markdown_lines.append(f"- **Status**: {selected_audit.get('status', '').title()}")
                    markdown_lines.append(f"- **Department**: {selected_audit['auditee_department']}")
                    markdown_lines.append(f"- **Lead Auditor**: {selected_audit['lead_auditor_username']}")
                    markdown_lines.append(f"- **Date Range**: {selected_audit['planned_start_date']} to {selected_audit['planned_end_date']}")
                    markdown_lines.append("")
                    markdown_lines.append(f"**Scope**: {selected_audit['scope']}")
                    markdown_lines.append("")
                    
                    # Findings Section
                    if findings:
                        markdown_lines.append("## 🔍 Findings")
                        markdown_lines.append("")
                        
                        for i, finding in enumerate(findings, 1):
                            markdown_lines.append(f"### {i}. Finding {finding['finding_number']}")
                            markdown_lines.append("")
                            markdown_lines.append(f"**Title**: {finding['title']}")
                            markdown_lines.append(f"**Severity**: {finding['severity']}")
                            markdown_lines.append(f"**Category**: {finding['category']}")
                            if finding.get('clause_reference'):
                                markdown_lines.append(f"**Clause Reference**: {finding['clause_reference']}")
                            markdown_lines.append(f"**Status**: {finding.get('status', '')}")
                            if finding.get('identified_date'):
                                markdown_lines.append(f"**Identified Date**: {finding['identified_date']}")
                            if finding.get('identified_by_username'):
                                markdown_lines.append(f"**Identified By**: {finding['identified_by_username']}")
                            markdown_lines.append("")
                            markdown_lines.append(f"**Description**:")
                            markdown_lines.append(f"{finding['description']}")
                            markdown_lines.append("")
                            
                            if finding.get('evidence'):
                                markdown_lines.append(f"**Evidence**:")
                                markdown_lines.append(f"{finding['evidence']}")
                                markdown_lines.append("")
                            
                            if finding.get('root_cause'):
                                markdown_lines.append(f"**Root Cause**:")
                                markdown_lines.append(f"{finding['root_cause']}")
                                markdown_lines.append("")
                            
                            # Add corrective actions for this finding
                            actions = get_corrective_actions(finding['id'])
                            if actions:
                                markdown_lines.append(f"#### Corrective Actions for Finding {finding['finding_number']}")
                                markdown_lines.append("")
                                
                                for j, action in enumerate(actions, 1):
                                    markdown_lines.append(f"**Action {action['action_number']}**:")
                                    markdown_lines.append(f"- **Description**: {action['description']}")
                                    markdown_lines.append(f"- **Responsible Person**: {action['responsible_person_username']}")
                                    markdown_lines.append(f"- **Target Date**: {action['target_date']}")
                                    markdown_lines.append(f"- **Status**: {action.get('status', '')}")
                                    if action.get('verification_notes'):
                                        markdown_lines.append(f"- **Verification Notes**: {action['verification_notes']}")
                                    markdown_lines.append("")
                            
                            markdown_lines.append("---")
                            markdown_lines.append("")
                    
                    else:
                        markdown_lines.append("## 🔍 Findings")
                        markdown_lines.append("")
                        markdown_lines.append("No findings were recorded for this audit.")
                        markdown_lines.append("")
                    
                    # Summary Section
                    findings_count = len([item for item in csv_data if item['Item Type'] == 'Finding' and item['ID'] != 'N/A'])
                    actions_count = len([item for item in csv_data if item['Item Type'] == 'Corrective Action'])
                    
                    markdown_lines.append("## 📊 Summary")
                    markdown_lines.append("")
                    markdown_lines.append(f"- **Total Findings**: {findings_count}")
                    markdown_lines.append(f"- **Total Corrective Actions**: {actions_count}")
                    markdown_lines.append("")
                    markdown_lines.append(f"*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
                    
                    report_data = "\n".join(markdown_lines)
                    filename = f"audit_report_{selected_audit['audit_number']}_{timestamp}.md"
                    mime_type = "text/markdown"
                
                st.download_button(
                    label=f"📁 Download {report_format} Report",
                    data=report_data,
                    file_name=filename,
                    mime=mime_type,
                    type="primary"
                )
                
                findings_count = len([item for item in csv_data if item['Item Type'] == 'Finding' and item['ID'] != 'N/A'])
                actions_count = len([item for item in csv_data if item['Item Type'] == 'Corrective Action'])
                
                st.success(f"✅ {report_format} audit report ready! Contains {findings_count} findings and {actions_count} corrective actions.")
            else:
                st.error("❌ No audit data available for download.")
    else:
        st.info("No audits available for reporting.")