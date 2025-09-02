# frontend/pages/Records.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
from typing import Dict, Any
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers, BACKEND_URL

require_auth()

st.set_page_config(page_title="Records", page_icon="📋", layout="wide")

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
    .stButton > button {
        font-size: 14px;
        padding: 0.25rem 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .record-card {
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        background: #f8f9fa;
    }
    .metric-container {
        display: flex;
        justify-content: space-around;
        background: #f1f3f4;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("📋 Records Management")
st.markdown("*Comprehensive record management for ISO 13485 and FDA compliance*")

setup_authenticated_sidebar()

# Helper functions
def make_api_call(endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make API call to backend"""
    try:
        url = f"{BACKEND_URL}/{endpoint}"
        headers = get_auth_headers()
        headers['Content-Type'] = 'application/json'
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        else:
            return {"success": False, "error": f"Unsupported method: {method}"}
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def render_data_table(data: list, columns: list, key_field: str):
    """Render data in a table format with actions"""
    if not data:
        st.info("No records found")
        return
    
    df = pd.DataFrame(data)
    
    # Reorder columns to show key field first
    if key_field in df.columns:
        cols = [key_field] + [col for col in columns if col != key_field and col in df.columns]
        df = df[cols]
    
    st.dataframe(df, use_container_width=True, hide_index=True)

# Main interface with tabs for different record types
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏢 Supplier Management", 
    "📦 Parts & Inventory", 
    "🔬 Lab Equipment", 
    "😟 Customer Complaints", 
    "⚠️ Non-Conformances"
])

# Tab 1: Supplier Management
with tab1:
    st.subheader("🏢 Supplier Management")
    st.markdown("*Manage supplier information, evaluations, and performance per ISO 13485*")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📋 Supplier List")
        
        # Filters
        with st.expander("🔍 Filters"):
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            with filter_col1:
                approval_status = st.selectbox("Approval Status", ["", "Approved", "Conditional", "Rejected", "Pending"])
            with filter_col2:
                risk_level = st.selectbox("Risk Level", ["", "Low", "Medium", "High"])
            with filter_col3:
                search_term = st.text_input("Search", placeholder="Search suppliers...")
        
        # Fetch suppliers
        params = []
        if approval_status:
            params.append(f"approval_status={approval_status}")
        if risk_level:
            params.append(f"risk_level={risk_level}")
        if search_term:
            params.append(f"search={search_term}")
        
        query_string = "&".join(params)
        endpoint = f"records/suppliers?{query_string}" if query_string else "records/suppliers"
        
        suppliers_response = make_api_call(endpoint)
        
        if suppliers_response.get("success"):
            suppliers = suppliers_response.get("suppliers", [])
            
            if suppliers:
                # Display suppliers in expandable cards
                for supplier in suppliers:
                    with st.expander(f"🏢 {supplier['supplier_name']} ({supplier.get('approval_status', 'N/A')})"):
                        sup_col1, sup_col2 = st.columns(2)
                        with sup_col1:
                            st.write(f"**Contact:** {supplier.get('contact_person', 'N/A')}")
                            st.write(f"**Email:** {supplier.get('contact_email', 'N/A')}")
                            st.write(f"**Phone:** {supplier.get('contact_phone', 'N/A')}")
                            st.write(f"**Risk Level:** {supplier.get('risk_level', 'N/A')}")
                        with sup_col2:
                            st.write(f"**Performance Rating:** {supplier.get('performance_rating', 'N/A')}")
                            st.write(f"**On-Time Delivery:** {supplier.get('on_time_delivery_rate', 'N/A')}%")
                            st.write(f"**Quality Rating:** {supplier.get('quality_rating', 'N/A')}")
                            st.write(f"**Last Audit:** {supplier.get('last_audit_date', 'N/A')}")
            else:
                st.info("No suppliers found matching the criteria")
        else:
            st.error(f"Failed to load suppliers: {suppliers_response.get('error', 'Unknown error')}")
    
    with col2:
        st.markdown("### ➕ Add New Supplier")
        
        with st.form("new_supplier_form"):
            supplier_name = st.text_input("Supplier Name*", help="Unique supplier name")
            address = st.text_area("Address")
            contact_person = st.text_input("Contact Person")
            contact_email = st.text_input("Contact Email")
            contact_phone = st.text_input("Contact Phone")
            
            col_a, col_b = st.columns(2)
            with col_a:
                approval_status_new = st.selectbox("Approval Status", ["Pending", "Approved", "Conditional", "Rejected"])
                risk_level_new = st.selectbox("Risk Level", ["Low", "Medium", "High"])
            with col_b:
                performance_rating = st.number_input("Performance Rating", min_value=0.0, max_value=100.0, step=0.1)
                quality_rating = st.number_input("Quality Rating", min_value=0.0, max_value=100.0, step=0.1)
            
            certification_status = st.text_area("Certifications")
            last_audit_date = st.date_input("Last Audit Date", value=None)
            next_audit_date = st.date_input("Next Audit Date", value=None)
            contract_details = st.text_area("Contract Details")
            
            submitted = st.form_submit_button("➕ Create Supplier")
            
            if submitted and supplier_name:
                supplier_data = {
                    "supplier_name": supplier_name,
                    "address": address,
                    "contact_person": contact_person,
                    "contact_email": contact_email,
                    "contact_phone": contact_phone,
                    "approval_status": approval_status_new,
                    "risk_level": risk_level_new,
                    "certification_status": certification_status,
                    "last_audit_date": last_audit_date.isoformat() if last_audit_date else None,
                    "next_audit_date": next_audit_date.isoformat() if next_audit_date else None,
                    "performance_rating": performance_rating,
                    "quality_rating": quality_rating,
                    "contract_details": contract_details
                }
                
                result = make_api_call("records/suppliers", "POST", supplier_data)
                
                if result.get("success"):
                    st.success(f"✅ Supplier '{supplier_name}' created successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to create supplier: {result.get('error', 'Unknown error')}")

# Tab 2: Parts & Inventory Management
with tab2:
    st.subheader("📦 Parts & Inventory Management")
    st.markdown("*Track parts and inventory with traceability for medical devices*")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📋 Inventory List")
        
        # Filters
        with st.expander("🔍 Filters"):
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            with filter_col1:
                inv_status = st.selectbox("Status", ["", "In Stock", "Quarantined", "Expired", "Disposed"])
            with filter_col2:
                low_stock_only = st.checkbox("Low Stock Only")
            with filter_col3:
                inv_search = st.text_input("Search", placeholder="Search parts...", key="inv_search")
        
        # Fetch inventory
        params = []
        if inv_status:
            params.append(f"status={inv_status}")
        if low_stock_only:
            params.append("low_stock=true")
        if inv_search:
            params.append(f"search={inv_search}")
        
        query_string = "&".join(params)
        endpoint = f"records/parts-inventory?{query_string}" if query_string else "records/parts-inventory"
        
        inventory_response = make_api_call(endpoint)
        
        if inventory_response.get("success"):
            parts = inventory_response.get("parts", [])
            
            if parts:
                for part in parts:
                    status_color = {"In Stock": "🟢", "Quarantined": "🟡", "Expired": "🔴", "Disposed": "⚫"}.get(part.get('status', ''), "⚪")
                    
                    with st.expander(f"{status_color} {part['part_number']} - {part.get('description', 'N/A')[:50]}"):
                        part_col1, part_col2 = st.columns(2)
                        with part_col1:
                            st.write(f"**UDI:** {part.get('udi', 'N/A')}")
                            st.write(f"**Lot Number:** {part.get('lot_number', 'N/A')}")
                            st.write(f"**Serial Number:** {part.get('serial_number', 'N/A')}")
                            st.write(f"**Location:** {part.get('location', 'N/A')}")
                        with part_col2:
                            st.write(f"**Stock Quantity:** {part.get('quantity_in_stock', 0)}")
                            st.write(f"**Minimum Level:** {part.get('minimum_stock_level', 0)}")
                            st.write(f"**Cost:** ${part.get('cost', 0)}")
                            st.write(f"**Expiration:** {part.get('expiration_date', 'N/A')}")
            else:
                st.info("No inventory items found")
        else:
            st.error(f"Failed to load inventory: {inventory_response.get('error', 'Unknown error')}")
    
    with col2:
        st.markdown("### ➕ Add New Part")
        
        # First, get suppliers for dropdown
        suppliers_response = make_api_call("records/suppliers")
        supplier_options = {}
        if suppliers_response.get("success"):
            suppliers = suppliers_response.get("suppliers", [])
            supplier_options = {s["supplier_id"]: s["supplier_name"] for s in suppliers}
        
        with st.form("new_part_form"):
            part_number = st.text_input("Part Number*", help="Unique part number")
            description = st.text_area("Description")
            udi = st.text_input("UDI Code")
            lot_number = st.text_input("Lot Number")
            serial_number = st.text_input("Serial Number")
            
            supplier_id = None
            if supplier_options:
                supplier_id = st.selectbox("Supplier", options=[None] + list(supplier_options.keys()), 
                                         format_func=lambda x: "Select Supplier" if x is None else supplier_options.get(x, ""))
            else:
                st.info("No suppliers available. Create suppliers first.")
            
            col_a, col_b = st.columns(2)
            with col_a:
                quantity_in_stock = st.number_input("Stock Quantity", min_value=0, step=1)
                minimum_stock_level = st.number_input("Minimum Level", min_value=0, step=1)
            with col_b:
                cost = st.number_input("Unit Cost", min_value=0.0, step=0.01)
                part_status = st.selectbox("Status", ["In Stock", "Quarantined", "Expired", "Disposed"])
            
            location = st.text_input("Storage Location")
            expiration_date = st.date_input("Expiration Date", value=None)
            received_date = st.date_input("Received Date", value=datetime.now().date())
            
            submitted = st.form_submit_button("➕ Create Part")
            
            if submitted and part_number:
                part_data = {
                    "part_number": part_number,
                    "description": description,
                    "udi": udi,
                    "lot_number": lot_number,
                    "serial_number": serial_number,
                    "supplier_id": supplier_id,
                    "quantity_in_stock": quantity_in_stock,
                    "minimum_stock_level": minimum_stock_level,
                    "location": location,
                    "expiration_date": expiration_date.isoformat() if expiration_date else None,
                    "status": part_status,
                    "received_date": received_date.isoformat() if received_date else None,
                    "cost": cost
                }
                
                result = make_api_call("records/parts-inventory", "POST", part_data)
                
                if result.get("success"):
                    st.success(f"✅ Part '{part_number}' created successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to create part: {result.get('error', 'Unknown error')}")

# Tab 3: Lab Equipment Calibration
with tab3:
    st.subheader("🔬 Lab Equipment Calibration")
    st.markdown("*Track equipment calibration for accuracy and ISO 13485 compliance*")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📋 Equipment List")
        
        # Filters
        with st.expander("🔍 Filters"):
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            with filter_col1:
                cal_status = st.selectbox("Calibration Status", ["", "Calibrated", "Due", "Overdue", "Out of Service"])
            with filter_col2:
                due_soon_only = st.checkbox("Due Soon (30 days)")
            with filter_col3:
                eq_search = st.text_input("Search", placeholder="Search equipment...", key="eq_search")
        
        # Fetch equipment
        params = []
        if cal_status:
            params.append(f"calibration_status={cal_status}")
        if due_soon_only:
            params.append("due_soon=true")
        if eq_search:
            params.append(f"search={eq_search}")
        
        query_string = "&".join(params)
        endpoint = f"records/lab-equipment?{query_string}" if query_string else "records/lab-equipment"
        
        equipment_response = make_api_call(endpoint)
        
        if equipment_response.get("success"):
            equipment_list = equipment_response.get("equipment", [])
            
            if equipment_list:
                for equipment in equipment_list:
                    status_color = {
                        "Calibrated": "🟢", 
                        "Due": "🟡", 
                        "Overdue": "🔴", 
                        "Out of Service": "⚫"
                    }.get(equipment.get('calibration_status', ''), "⚪")
                    
                    with st.expander(f"{status_color} {equipment['equipment_name']} ({equipment.get('calibration_status', 'N/A')})"):
                        eq_col1, eq_col2 = st.columns(2)
                        with eq_col1:
                            st.write(f"**Serial Number:** {equipment.get('serial_number', 'N/A')}")
                            st.write(f"**Location:** {equipment.get('location', 'N/A')}")
                            st.write(f"**Frequency:** {equipment.get('calibration_frequency', 'N/A')}")
                            st.write(f"**Technician:** {equipment.get('technician', 'N/A')}")
                        with eq_col2:
                            st.write(f"**Last Calibration:** {equipment.get('last_calibration_date', 'N/A')}")
                            st.write(f"**Next Calibration:** {equipment.get('next_calibration_date', 'N/A')}")
                            st.write(f"**Adjustment Made:** {'Yes' if equipment.get('adjustment_made') else 'No'}")
                            st.write(f"**Standards Used:** {equipment.get('standards_used', 'N/A')}")
            else:
                st.info("No equipment found")
        else:
            st.error(f"Failed to load equipment: {equipment_response.get('error', 'Unknown error')}")
    
    with col2:
        st.markdown("### ➕ Add New Equipment")
        
        with st.form("new_equipment_form"):
            equipment_name = st.text_input("Equipment Name*")
            serial_number = st.text_input("Serial Number")
            location = st.text_input("Location")
            calibration_frequency = st.text_input("Calibration Frequency", placeholder="e.g., Annual, Quarterly")
            
            col_a, col_b = st.columns(2)
            with col_a:
                last_calibration_date = st.date_input("Last Calibration", value=None)
                calibration_status_new = st.selectbox("Status", ["Calibrated", "Due", "Overdue", "Out of Service"])
            with col_b:
                next_calibration_date = st.date_input("Next Calibration", value=None)
                adjustment_made = st.checkbox("Adjustment Made")
            
            technician = st.text_input("Technician")
            standards_used = st.text_area("Standards Used")
            results = st.text_area("Calibration Results")
            compliance_notes = st.text_area("Compliance Notes")
            
            submitted = st.form_submit_button("➕ Create Equipment Record")
            
            if submitted and equipment_name:
                equipment_data = {
                    "equipment_name": equipment_name,
                    "serial_number": serial_number,
                    "location": location,
                    "calibration_frequency": calibration_frequency,
                    "last_calibration_date": last_calibration_date.isoformat() if last_calibration_date else None,
                    "next_calibration_date": next_calibration_date.isoformat() if next_calibration_date else None,
                    "calibration_status": calibration_status_new,
                    "technician": technician,
                    "standards_used": standards_used,
                    "results": results,
                    "adjustment_made": adjustment_made,
                    "compliance_notes": compliance_notes
                }
                
                result = make_api_call("records/lab-equipment", "POST", equipment_data)
                
                if result.get("success"):
                    st.success(f"✅ Equipment '{equipment_name}' created successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to create equipment: {result.get('error', 'Unknown error')}")

# Tab 4: Customer Complaints
with tab4:
    st.subheader("😟 Customer Complaints")
    st.markdown("*Handle customer complaints per FDA 21 CFR 820 requirements*")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📋 Complaints List")
        
        # Filters
        with st.expander("🔍 Filters"):
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            with filter_col1:
                comp_status = st.selectbox("Status", ["", "Open", "Under Investigation", "Closed"])
            with filter_col2:
                mdr_only = st.checkbox("MDR Reportable Only")
            with filter_col3:
                comp_search = st.text_input("Search", placeholder="Search complaints...", key="comp_search")
        
        # Fetch complaints
        params = []
        if comp_status:
            params.append(f"status={comp_status}")
        if mdr_only:
            params.append("mdr_reportable=true")
        if comp_search:
            params.append(f"search={comp_search}")
        
        query_string = "&".join(params)
        endpoint = f"records/customer-complaints?{query_string}" if query_string else "records/customer-complaints"
        
        complaints_response = make_api_call(endpoint)
        
        if complaints_response.get("success"):
            complaints = complaints_response.get("complaints", [])
            
            if complaints:
                for complaint in complaints:
                    status_color = {"Open": "🔴", "Under Investigation": "🟡", "Closed": "🟢"}.get(complaint.get('status', ''), "⚪")
                    mdr_indicator = "🚨 MDR" if complaint.get('mdr_reportable') else ""
                    
                    with st.expander(f"{status_color} Complaint #{complaint['complaint_id']} - {complaint.get('complainant_name', 'Anonymous')} {mdr_indicator}"):
                        comp_col1, comp_col2 = st.columns(2)
                        with comp_col1:
                            st.write(f"**Received:** {complaint.get('received_date', 'N/A')}")
                            st.write(f"**Product ID:** {complaint.get('product_id', 'N/A')}")
                            st.write(f"**Lot Number:** {complaint.get('lot_number', 'N/A')}")
                            st.write(f"**Serial Number:** {complaint.get('serial_number', 'N/A')}")
                        with comp_col2:
                            st.write(f"**Contact:** {complaint.get('complainant_contact', 'N/A')}")
                            st.write(f"**Response Date:** {complaint.get('response_date', 'N/A')}")
                            st.write(f"**Status:** {complaint.get('status', 'N/A')}")
                            st.write(f"**MDR Reportable:** {'Yes' if complaint.get('mdr_reportable') else 'No'}")
                        
                        st.write("**Description:**")
                        st.write(complaint.get('complaint_description', 'N/A'))
                        
                        if complaint.get('root_cause'):
                            st.write("**Root Cause:**")
                            st.write(complaint.get('root_cause'))
            else:
                st.info("No complaints found")
        else:
            st.error(f"Failed to load complaints: {complaints_response.get('error', 'Unknown error')}")
    
    with col2:
        st.markdown("### ➕ Add New Complaint")
        
        with st.form("new_complaint_form"):
            received_date = st.date_input("Received Date*", value=datetime.now().date())
            complainant_name = st.text_input("Complainant Name")
            complainant_contact = st.text_input("Contact Information")
            
            col_a, col_b = st.columns(2)
            with col_a:
                product_id = st.text_input("Product ID")
                lot_number = st.text_input("Lot Number")
            with col_b:
                serial_number = st.text_input("Serial Number")
                mdr_reportable = st.checkbox("MDR Reportable")
            
            complaint_description = st.text_area("Complaint Description*", height=100)
            investigation_details = st.text_area("Investigation Details")
            root_cause = st.text_area("Root Cause")
            corrective_action = st.text_area("Corrective Action")
            response_date = st.date_input("Response Date", value=None)
            comp_status_new = st.selectbox("Status", ["Open", "Under Investigation", "Closed"])
            
            submitted = st.form_submit_button("➕ Create Complaint")
            
            if submitted and complaint_description:
                complaint_data = {
                    "received_date": received_date.isoformat(),
                    "complainant_name": complainant_name,
                    "complainant_contact": complainant_contact,
                    "product_id": product_id,
                    "lot_number": lot_number,
                    "serial_number": serial_number,
                    "complaint_description": complaint_description,
                    "investigation_details": investigation_details,
                    "root_cause": root_cause,
                    "corrective_action": corrective_action,
                    "response_date": response_date.isoformat() if response_date else None,
                    "mdr_reportable": mdr_reportable,
                    "status": comp_status_new
                }
                
                result = make_api_call("records/customer-complaints", "POST", complaint_data)
                
                if result.get("success"):
                    st.success(f"✅ Complaint #{result.get('complaint_id')} created successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to create complaint: {result.get('error', 'Unknown error')}")

# Tab 5: Non-Conformances
with tab5:
    st.subheader("⚠️ Non-Conformances")
    st.markdown("*Manage non-conformances with root cause analysis per ISO 13485*")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📋 Non-Conformances List")
        
        # Filters
        with st.expander("🔍 Filters"):
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            with filter_col1:
                nc_status = st.selectbox("Status", ["", "Open", "In Progress", "Closed"])
            with filter_col2:
                nc_severity = st.selectbox("Severity", ["", "Minor", "Major", "Critical"])
            with filter_col3:
                nc_search = st.text_input("Search", placeholder="Search NCs...", key="nc_search")
        
        # Fetch non-conformances
        params = []
        if nc_status:
            params.append(f"status={nc_status}")
        if nc_severity:
            params.append(f"severity={nc_severity}")
        if nc_search:
            params.append(f"search={nc_search}")
        
        query_string = "&".join(params)
        endpoint = f"records/non-conformances?{query_string}" if query_string else "records/non-conformances"
        
        ncs_response = make_api_call(endpoint)
        
        if ncs_response.get("success"):
            ncs = ncs_response.get("non_conformances", [])
            
            if ncs:
                for nc in ncs:
                    severity_color = {"Minor": "🟡", "Major": "🟠", "Critical": "🔴"}.get(nc.get('severity', ''), "⚪")
                    status_color = {"Open": "🔴", "In Progress": "🟡", "Closed": "🟢"}.get(nc.get('status', ''), "⚪")
                    
                    with st.expander(f"{severity_color} NC #{nc['nc_id']} - {nc.get('severity', 'N/A')} ({status_color} {nc.get('status', 'N/A')})"):
                        nc_col1, nc_col2 = st.columns(2)
                        with nc_col1:
                            st.write(f"**Detection Date:** {nc.get('detection_date', 'N/A')}")
                            st.write(f"**Product/Process:** {nc.get('product_process_involved', 'N/A')}")
                            st.write(f"**Risk Level:** {nc.get('risk_level', 'N/A')}")
                            st.write(f"**Responsible Person:** {nc.get('responsible_person', 'N/A')}")
                        with nc_col2:
                            st.write(f"**Severity:** {nc.get('severity', 'N/A')}")
                            st.write(f"**Disposition:** {nc.get('disposition', 'N/A')}")
                            st.write(f"**Closure Date:** {nc.get('closure_date', 'N/A')}")
                            st.write(f"**Status:** {nc.get('status', 'N/A')}")
                        
                        st.write("**Description:**")
                        st.write(nc.get('description', 'N/A'))
                        
                        if nc.get('root_cause'):
                            st.write("**Root Cause:**")
                            st.write(nc.get('root_cause'))
                        
                        if nc.get('corrective_action'):
                            st.write("**Corrective Action:**")
                            st.write(nc.get('corrective_action'))
            else:
                st.info("No non-conformances found")
        else:
            st.error(f"Failed to load non-conformances: {ncs_response.get('error', 'Unknown error')}")
    
    with col2:
        st.markdown("### ➕ Add New Non-Conformance")
        
        with st.form("new_nc_form"):
            detection_date = st.date_input("Detection Date*", value=datetime.now().date())
            nc_description = st.text_area("Description*", height=100)
            product_process_involved = st.text_input("Product/Process Involved")
            
            col_a, col_b = st.columns(2)
            with col_a:
                nc_severity_new = st.selectbox("Severity", ["Minor", "Major", "Critical"])
                nc_risk_level = st.selectbox("Risk Level", ["Low", "Medium", "High"])
            with col_b:
                nc_disposition = st.selectbox("Disposition", ["Use As Is", "Rework", "Scrap", "Return"])
                nc_status_new = st.selectbox("Status", ["Open", "In Progress", "Closed"])
            
            responsible_person = st.text_input("Responsible Person")
            root_cause = st.text_area("Root Cause")
            corrective_action = st.text_area("Corrective Action")
            preventive_action = st.text_area("Preventive Action")
            closure_date = st.date_input("Closure Date", value=None)
            
            submitted = st.form_submit_button("➕ Create Non-Conformance")
            
            if submitted and nc_description:
                nc_data = {
                    "detection_date": detection_date.isoformat(),
                    "description": nc_description,
                    "product_process_involved": product_process_involved,
                    "severity": nc_severity_new,
                    "risk_level": nc_risk_level,
                    "root_cause": root_cause,
                    "corrective_action": corrective_action,
                    "preventive_action": preventive_action,
                    "responsible_person": responsible_person,
                    "disposition": nc_disposition,
                    "status": nc_status_new,
                    "closure_date": closure_date.isoformat() if closure_date else None
                }
                
                result = make_api_call("records/non-conformances", "POST", nc_data)
                
                if result.get("success"):
                    st.success(f"✅ Non-Conformance #{result.get('nc_id')} created successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to create non-conformance: {result.get('error', 'Unknown error')}")

# Bottom section with summary metrics
st.markdown("---")
st.markdown("### 📊 Records Summary")

# Get summary data from all modules
summary_col1, summary_col2, summary_col3, summary_col4, summary_col5 = st.columns(5)

# Suppliers
suppliers_response = make_api_call("records/suppliers")
supplier_count = len(suppliers_response.get("suppliers", [])) if suppliers_response.get("success") else 0
with summary_col1:
    st.metric("🏢 Suppliers", supplier_count)

# Inventory
inventory_response = make_api_call("records/parts-inventory")
inventory_count = len(inventory_response.get("parts", [])) if inventory_response.get("success") else 0
with summary_col2:
    st.metric("📦 Inventory Items", inventory_count)

# Equipment
equipment_response = make_api_call("records/lab-equipment")
equipment_count = len(equipment_response.get("equipment", [])) if equipment_response.get("success") else 0
with summary_col3:
    st.metric("🔬 Equipment", equipment_count)

# Complaints
complaints_response = make_api_call("records/customer-complaints")
complaint_count = len(complaints_response.get("complaints", [])) if complaints_response.get("success") else 0
with summary_col4:
    st.metric("😟 Complaints", complaint_count)

# Non-Conformances
ncs_response = make_api_call("records/non-conformances")
nc_count = len(ncs_response.get("non_conformances", [])) if ncs_response.get("success") else 0
with summary_col5:
    st.metric("⚠️ Non-Conformances", nc_count)

st.markdown("*All records are maintained per ISO 13485 and FDA 21 CFR 820 requirements*")