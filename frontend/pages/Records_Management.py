# frontend/pages/Records_Management.py
import streamlit as st
import requests
from datetime import datetime
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers, BACKEND_URL

require_auth()

st.set_page_config(page_title="Records Management", page_icon="📋", layout="wide")

st.title("📋 Records Management")
st.markdown("*Comprehensive record management for ISO 13485 and FDA compliance*")

setup_authenticated_sidebar()

# Helper function
def make_api_call(endpoint: str, method: str = "GET", data: dict = None):
    """Make API call to backend"""
    try:
        url = f"{BACKEND_URL}/{endpoint}"
        headers = get_auth_headers()
        headers['Content-Type'] = 'application/json'
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            return {"success": False, "error": f"Unsupported method: {method}"}
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

# Main interface with tabs for different record types
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏢 Suppliers", 
    "📦 Inventory", 
    "🔬 Equipment", 
    "😟 Complaints", 
    "⚠️ Non-Conformances"
])

# Tab 1: Supplier Management
with tab1:
    st.subheader("🏢 Supplier Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📋 Supplier List")
        
        suppliers_response = make_api_call("records/suppliers")
        
        if suppliers_response.get("success"):
            suppliers = suppliers_response.get("suppliers", [])
            
            if suppliers:
                for supplier in suppliers:
                    with st.expander(f"🏢 {supplier['supplier_name']} ({supplier.get('approval_status', 'N/A')})"):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.write(f"**Contact:** {supplier.get('contact_person', 'N/A')}")
                            st.write(f"**Email:** {supplier.get('contact_email', 'N/A')}")
                            st.write(f"**Phone:** {supplier.get('contact_phone', 'N/A')}")
                        with col_b:
                            st.write(f"**Risk Level:** {supplier.get('risk_level', 'N/A')}")
                            st.write(f"**Performance:** {supplier.get('performance_rating', 'N/A')}")
                            st.write(f"**Quality:** {supplier.get('quality_rating', 'N/A')}")
            else:
                st.info("No suppliers found")
        else:
            st.error(f"Failed to load suppliers: {suppliers_response.get('error', 'Unknown error')}")
    
    with col2:
        st.markdown("### ➕ Add New Supplier")
        
        with st.form("new_supplier_form"):
            supplier_name = st.text_input("Supplier Name*")
            contact_person = st.text_input("Contact Person")
            contact_email = st.text_input("Contact Email")
            approval_status = st.selectbox("Approval Status", ["Pending", "Approved", "Conditional", "Rejected"])
            
            submitted = st.form_submit_button("➕ Create Supplier")
            
            if submitted and supplier_name:
                supplier_data = {
                    "supplier_name": supplier_name,
                    "contact_person": contact_person,
                    "contact_email": contact_email,
                    "approval_status": approval_status
                }
                
                result = make_api_call("records/suppliers", "POST", supplier_data)
                
                if result.get("success"):
                    st.success(f"✅ Supplier '{supplier_name}' created successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to create supplier: {result.get('error', 'Unknown error')}")

# Tab 2: Parts & Inventory
with tab2:
    st.subheader("📦 Parts & Inventory Management")
    
    inventory_response = make_api_call("records/parts-inventory")
    
    if inventory_response.get("success"):
        parts = inventory_response.get("parts", [])
        
        if parts:
            st.write(f"**Found {len(parts)} inventory items**")
            for part in parts[:10]:  # Show first 10
                status_color = {"In Stock": "🟢", "Quarantined": "🟡", "Expired": "🔴", "Disposed": "⚫"}.get(part.get('status', ''), "⚪")
                
                with st.expander(f"{status_color} {part['part_number']} - {part.get('description', 'N/A')[:50]}"):
                    st.write(f"**Stock:** {part.get('quantity_in_stock', 0)}")
                    st.write(f"**Location:** {part.get('location', 'N/A')}")
                    st.write(f"**Status:** {part.get('status', 'N/A')}")
        else:
            st.info("No inventory items found")
    else:
        st.error(f"Failed to load inventory: {inventory_response.get('error', 'Unknown error')}")

# Tab 3: Lab Equipment
with tab3:
    st.subheader("🔬 Lab Equipment Calibration")
    
    equipment_response = make_api_call("records/lab-equipment")
    
    if equipment_response.get("success"):
        equipment_list = equipment_response.get("equipment", [])
        
        if equipment_list:
            st.write(f"**Found {len(equipment_list)} equipment items**")
            for equipment in equipment_list[:10]:  # Show first 10
                status_color = {"Calibrated": "🟢", "Due": "🟡", "Overdue": "🔴", "Out of Service": "⚫"}.get(equipment.get('calibration_status', ''), "⚪")
                
                with st.expander(f"{status_color} {equipment['equipment_name']} ({equipment.get('calibration_status', 'N/A')})"):
                    st.write(f"**Serial:** {equipment.get('serial_number', 'N/A')}")
                    st.write(f"**Location:** {equipment.get('location', 'N/A')}")
                    st.write(f"**Next Calibration:** {equipment.get('next_calibration_date', 'N/A')}")
        else:
            st.info("No equipment found")
    else:
        st.error(f"Failed to load equipment: {equipment_response.get('error', 'Unknown error')}")

# Tab 4: Customer Complaints  
with tab4:
    st.subheader("😟 Customer Complaints")
    
    complaints_response = make_api_call("records/customer-complaints")
    
    if complaints_response.get("success"):
        complaints = complaints_response.get("complaints", [])
        
        if complaints:
            st.write(f"**Found {len(complaints)} complaints**")
            for complaint in complaints[:10]:  # Show first 10
                status_color = {"Open": "🔴", "Under Investigation": "🟡", "Closed": "🟢"}.get(complaint.get('status', ''), "⚪")
                mdr_indicator = "🚨 MDR" if complaint.get('mdr_reportable') else ""
                
                with st.expander(f"{status_color} Complaint #{complaint['complaint_id']} {mdr_indicator}"):
                    st.write(f"**From:** {complaint.get('complainant_name', 'Anonymous')}")
                    st.write(f"**Product:** {complaint.get('product_id', 'N/A')}")
                    st.write(f"**Status:** {complaint.get('status', 'N/A')}")
                    st.write(f"**Description:** {complaint.get('complaint_description', 'N/A')[:100]}...")
        else:
            st.info("No complaints found")
    else:
        st.error(f"Failed to load complaints: {complaints_response.get('error', 'Unknown error')}")

# Tab 5: Non-Conformances
with tab5:
    st.subheader("⚠️ Non-Conformances")
    
    ncs_response = make_api_call("records/non-conformances")
    
    if ncs_response.get("success"):
        ncs = ncs_response.get("non_conformances", [])
        
        if ncs:
            st.write(f"**Found {len(ncs)} non-conformances**")
            for nc in ncs[:10]:  # Show first 10
                severity_color = {"Minor": "🟡", "Major": "🟠", "Critical": "🔴"}.get(nc.get('severity', ''), "⚪")
                status_color = {"Open": "🔴", "In Progress": "🟡", "Closed": "🟢"}.get(nc.get('status', ''), "⚪")
                
                with st.expander(f"{severity_color} NC #{nc['nc_id']} - {nc.get('severity', 'N/A')} ({status_color})"):
                    st.write(f"**Detection Date:** {nc.get('detection_date', 'N/A')}")
                    st.write(f"**Product/Process:** {nc.get('product_process_involved', 'N/A')}")
                    st.write(f"**Status:** {nc.get('status', 'N/A')}")
                    st.write(f"**Description:** {nc.get('description', 'N/A')[:100]}...")
        else:
            st.info("No non-conformances found")
    else:
        st.error(f"Failed to load non-conformances: {ncs_response.get('error', 'Unknown error')}")

# Summary metrics
st.markdown("---")
st.markdown("### 📊 Records Summary")

summary_col1, summary_col2, summary_col3, summary_col4, summary_col5 = st.columns(5)

with summary_col1:
    suppliers_response = make_api_call("records/suppliers")
    supplier_count = len(suppliers_response.get("suppliers", [])) if suppliers_response.get("success") else 0
    st.metric("🏢 Suppliers", supplier_count)

with summary_col2:
    inventory_response = make_api_call("records/parts-inventory")
    inventory_count = len(inventory_response.get("parts", [])) if inventory_response.get("success") else 0
    st.metric("📦 Inventory", inventory_count)

with summary_col3:
    equipment_response = make_api_call("records/lab-equipment")
    equipment_count = len(equipment_response.get("equipment", [])) if equipment_response.get("success") else 0
    st.metric("🔬 Equipment", equipment_count)

with summary_col4:
    complaints_response = make_api_call("records/customer-complaints")
    complaint_count = len(complaints_response.get("complaints", [])) if complaints_response.get("success") else 0
    st.metric("😟 Complaints", complaint_count)

with summary_col5:
    ncs_response = make_api_call("records/non-conformances")
    nc_count = len(ncs_response.get("non_conformances", [])) if ncs_response.get("success") else 0
    st.metric("⚠️ Non-Conformances", nc_count)