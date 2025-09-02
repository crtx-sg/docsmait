# frontend/pages/Audit.py
import streamlit as st
import requests
from datetime import datetime, date
import pandas as pd
from typing import List, Dict, Any
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers
from config import BACKEND_URL

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
tab1, tab2, tab3, tab4 = st.tabs(["Audit Dashboard", "Manage Audits", "Findings & Actions", "Reports"])

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
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No audits found. Create your first audit in the 'Manage Audits' tab.")

with tab2:
    
    action = st.radio("Select Action", ["Create New Audit", "View/Edit Existing"])
    
    if action == "Create New Audit":
        
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
    
    else:  # View/Edit Existing
        
        audits = get_audits()
        if audits:
            audit_options = [f"{a['audit_number']} - {a['title']}" for a in audits]
            selected_audit_str = st.selectbox("Select Audit", audit_options)
            selected_audit = audits[audit_options.index(selected_audit_str)]
            
            # Display audit details
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Audit Number:** {selected_audit['audit_number']}")
                st.markdown(f"**Type:** {selected_audit['audit_type'].title()}")
                st.markdown(f"**Status:** {selected_audit['status'].title()}")
                st.markdown(f"**Lead Auditor:** {selected_audit['lead_auditor_username']}")
                st.markdown(f"**Department:** {selected_audit['auditee_department']}")
            
            with col2:
                st.markdown(f"**Start Date:** {selected_audit['planned_start_date']}")
                st.markdown(f"**End Date:** {selected_audit['planned_end_date']}")
                st.markdown(f"**Project:** {selected_audit['project_name']}")
                st.markdown(f"**Findings:** {selected_audit['open_findings_count']}/{selected_audit['findings_count']}")
                st.markdown(f"**Standard:** {selected_audit['compliance_standard']}")
            
            st.markdown(f"**Scope:** {selected_audit['scope']}")
            
            # Status update using form to avoid nested button issues
            st.markdown("**Update Status:**")
            with st.form(f"update_status_form_{selected_audit['id']}"):
                current_status = selected_audit.get('status', 'planned')
                status_options = ["planned", "in_progress", "completed", "cancelled"]
                current_index = status_options.index(current_status) if current_status in status_options else 0
                
                new_status = st.selectbox(
                    "New Status", 
                    status_options,
                    index=current_index,
                    key=f"status_select_{selected_audit['id']}"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("🔄 Update Status", type="primary"):
                        if new_status != current_status:
                            try:
                                update_data = {"status": new_status}
                                response = requests.put(
                                    f"{BACKEND_URL}/audits/{selected_audit['id']}", 
                                    json=update_data, 
                                    headers=get_auth_headers()
                                )
                                if response.status_code == 200:
                                    st.success(f"✅ Status updated from '{current_status.title()}' to '{new_status.title()}'!")
                                    st.rerun()
                                else:
                                    try:
                                        error_detail = response.json()
                                        st.error(f"❌ Error updating status: {error_detail.get('error', 'Unknown error')}")
                                    except:
                                        st.error(f"❌ Error updating status: {response.text}")
                            except Exception as e:
                                st.error(f"❌ Connection error: {e}")
                        else:
                            st.info("💡 Status unchanged - select a different status to update.")
                
                with col2:
                    st.form_submit_button("❌ Cancel")
        else:
            st.info("No audits found.")

with tab3:
    
    # Select audit for findings management
    audits = get_audits()
    if audits:
        audit_options = [f"{a['audit_number']} - {a['title']}" for a in audits]
        selected_audit_str = st.selectbox("Select Audit for Findings", audit_options, key="findings_audit")
        selected_audit = audits[audit_options.index(selected_audit_str)]
        
        findings_tab1, findings_tab2 = st.tabs(["View Findings", "Add Finding"])
        
        with findings_tab1:
            findings = get_findings(selected_audit["id"])
            
            if findings:
                
                for finding in findings:
                    with st.expander(f"{finding['finding_number']}: {finding['title']} ({finding['severity'].upper()})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Category:** {finding['category']}")
                            st.markdown(f"**Status:** {finding['status'].title()}")
                            st.markdown(f"**Identified By:** {finding['identified_by_username']}")
                            st.markdown(f"**Date:** {finding['identified_date']}")
                        
                        with col2:
                            if finding['clause_reference']:
                                st.markdown(f"**Clause:** {finding['clause_reference']}")
                            if finding['due_date']:
                                st.markdown(f"**Due Date:** {finding['due_date']}")
                            st.markdown(f"**Corrective Actions:** {finding['corrective_actions_count']}")
                        
                        st.markdown(f"**Description:** {finding['description']}")
                        
                        if finding['evidence']:
                            st.markdown(f"**Evidence:** {finding['evidence']}")
                        
                        if finding['root_cause']:
                            st.markdown(f"**Root Cause:** {finding['root_cause']}")
                        
                        # Show corrective actions
                        actions = get_corrective_actions(finding['id'])
                        if actions:
                            st.markdown("**Corrective Actions:**")
                            for action in actions:
                                status_color = {"assigned": "🔵", "in_progress": "🟡", "completed": "✅", "overdue": "🔴"}
                                st.markdown(f"- {status_color.get(action['status'], '⚪')} {action['action_number']}: {action['description']} (Due: {action['target_date']}, Assigned: {action['responsible_person_username']})")
                        
                        # Edit/Delete buttons
                        st.markdown("---")
                        col_edit, col_delete, col_spacer = st.columns([1, 1, 3])
                        
                        with col_edit:
                            if st.button(f"✏️ Edit", key=f"edit_{finding['id']}"):
                                st.session_state[f"edit_finding_{finding['id']}"] = True
                        
                        with col_delete:
                            if st.button(f"🗑️ Delete", key=f"delete_{finding['id']}", type="secondary"):
                                if st.button(f"⚠️ Confirm Delete", key=f"confirm_delete_{finding['id']}", type="secondary"):
                                    try:
                                        response = requests.delete(f"{BACKEND_URL}/findings/{finding['id']}", headers=get_auth_headers())
                                        if response.status_code == 200:
                                            st.success("✅ Finding deleted successfully!")
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Failed to delete finding: {response.text}")
                                    except Exception as e:
                                        st.error(f"❌ Connection error: {e}")
                        
                        # Edit form
                        if st.session_state.get(f"edit_finding_{finding['id']}", False):
                            st.markdown("### Edit Finding")
                            with st.form(f"edit_finding_form_{finding['id']}"):
                                edit_col1, edit_col2 = st.columns(2)
                                
                                with edit_col1:
                                    edit_title = st.text_input("Title*", value=finding['title'])
                                    edit_severity = st.selectbox("Severity*", ["observation", "minor", "major", "critical"], 
                                                                index=["observation", "minor", "major", "critical"].index(finding['severity']))
                                    edit_category = st.text_input("Category*", value=finding['category'])
                                    edit_clause = st.text_input("ISO Clause Reference", value=finding['clause_reference'] or "")
                                
                                with edit_col2:
                                    edit_status = st.selectbox("Status", ["open", "closed", "verified"], 
                                                              index=["open", "closed", "verified"].index(finding['status']))
                                    edit_due_date = st.date_input("Due Date", value=datetime.strptime(finding['due_date'], "%Y-%m-%d").date() if finding['due_date'] else None)
                                
                                edit_description = st.text_area("Description*", value=finding['description'], height=100)
                                edit_evidence = st.text_area("Evidence", value=finding['evidence'] or "", height=80)
                                edit_root_cause = st.text_area("Root Cause", value=finding['root_cause'] or "", height=80)
                                
                                edit_col_submit, edit_col_cancel = st.columns(2)
                                with edit_col_submit:
                                    edit_submitted = st.form_submit_button("💾 Update Finding", type="primary")
                                with edit_col_cancel:
                                    cancel_edit = st.form_submit_button("❌ Cancel")
                                
                                if cancel_edit:
                                    st.session_state[f"edit_finding_{finding['id']}"] = False
                                    st.rerun()
                                
                                if edit_submitted:
                                    if not all([edit_title, edit_severity, edit_category, edit_description]):
                                        st.error("Please fill in all required fields marked with *")
                                    else:
                                        try:
                                            update_data = {
                                                "title": edit_title,
                                                "description": edit_description,
                                                "severity": edit_severity,
                                                "category": edit_category,
                                                "clause_reference": edit_clause or None,
                                                "evidence": edit_evidence or None,
                                                "status": edit_status,
                                                "root_cause": edit_root_cause or None,
                                                "due_date": edit_due_date.isoformat() if edit_due_date else None
                                            }
                                            
                                            response = requests.put(f"{BACKEND_URL}/findings/{finding['id']}", 
                                                                   json=update_data, headers=get_auth_headers())
                                            
                                            if response.status_code == 200:
                                                st.success("✅ Finding updated successfully!")
                                                st.session_state[f"edit_finding_{finding['id']}"] = False
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
        
        if st.button("📥 Download Audit Report (csv)", type="primary", help="Download comprehensive audit report as CSV"):
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
                
                df = pd.DataFrame(csv_data)
                csv_string = df.to_csv(index=False)
                
                # Generate filename with audit number and timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"audit_report_{selected_audit['audit_number']}_{timestamp}.csv"
                
                st.download_button(
                    label="📁 Download CSV Report",
                    data=csv_string,
                    file_name=filename,
                    mime="text/csv",
                    type="primary"
                )
                
                findings_count = len([item for item in csv_data if item['Item Type'] == 'Finding' and item['ID'] != 'N/A'])
                actions_count = len([item for item in csv_data if item['Item Type'] == 'Corrective Action'])
                
                st.success(f"✅ Audit report ready! Contains {findings_count} findings and {actions_count} corrective actions.")
            else:
                st.error("❌ No audit data available for download.")
    else:
        st.info("No audits available for reporting.")