# frontend/pages/Settings.py
import streamlit as st
import requests
import json
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers, BACKEND_URL

require_auth()

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
st.title("⚙️ System Settings")

setup_authenticated_sidebar()

# Check if user is super admin
def check_super_admin():
    """Check if current user is super admin"""
    try:
        response = requests.get(f"{BACKEND_URL}/auth/me", headers=get_auth_headers())
        if response.status_code == 200:
            user_data = response.json()
            return user_data.get('is_super_admin', False)
        return False
    except Exception as e:
        st.error(f"Error checking user permissions: {e}")
        return False

# Get SMTP settings
def get_smtp_settings():
    """Get current SMTP settings"""
    try:
        response = requests.get(f"{BACKEND_URL}/settings/smtp", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            return {"error": "Access denied"}
        else:
            return {"error": f"Server error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection error: {e}"}

# Update SMTP settings
def update_smtp_settings(smtp_config):
    """Update SMTP settings"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/settings/smtp",
            json=smtp_config,
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            return {"success": False, "error": error_data.get("detail", f"Server error: {response.status_code}")}
    except Exception as e:
        return {"success": False, "error": f"Connection error: {e}"}

# Get all users for admin management
def get_all_users():
    """Get all users for admin management"""
    try:
        response = requests.get(f"{BACKEND_URL}/admin/users", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            return {"error": "Access denied"}
        else:
            return {"error": f"Server error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection error: {e}"}

# Create admin user
def create_admin_user(user_data):
    """Create new admin user"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/admin/users",
            json=user_data,
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            return {"error": error_data.get("detail", f"Server error: {response.status_code}")}
    except Exception as e:
        return {"error": f"Connection error: {e}"}

# Check if user is super admin
if not check_super_admin():
    st.error("🚫 Access Denied")
    st.warning("Only the super admin can access system settings.")
    st.stop()

# Main settings interface
st.markdown("---")

# Settings tabs
settings_tabs = st.tabs(["Email Notifications", "User Management"])

# === EMAIL NOTIFICATIONS TAB ===
with settings_tabs[0]:
    
    st.subheader("📧 SMTP Configuration")
    st.markdown("Configure email notification settings for the system.")
    
    # Get current SMTP settings
    smtp_settings = get_smtp_settings()
    
    if "error" in smtp_settings:
        st.error(f"Error loading SMTP settings: {smtp_settings['error']}")
    else:
        # SMTP configuration form
        with st.form("smtp_config_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                server_name = st.text_input(
                    "Server Name", 
                    value=smtp_settings.get('server_name', ''),
                    help="SMTP server hostname (e.g., smtp.gmail.com)"
                )
                port = st.number_input(
                    "Port", 
                    value=smtp_settings.get('port', 25),
                    min_value=1,
                    max_value=65535,
                    help="SMTP server port (common: 25, 587, 465)"
                )
                username = st.text_input(
                    "Username", 
                    value=smtp_settings.get('username', ''),
                    help="SMTP username (usually your email address)"
                )
                
            with col2:
                password = st.text_input(
                    "Password", 
                    type="password",
                    help="SMTP password or app-specific password"
                )
                auth_method = st.selectbox(
                    "Authentication Method",
                    options=["normal_password", "oauth2", "plain", "login"],
                    index=0,
                    help="Authentication method for SMTP server"
                )
                connection_security = st.selectbox(
                    "Connection Security",
                    options=["STARTTLS", "SSL/TLS", "None"],
                    index=0,
                    help="Security protocol for SMTP connection"
                )
            
            enabled = st.checkbox(
                "Enable Email Notifications", 
                value=smtp_settings.get('enabled', False),
                help="Enable or disable email notifications system-wide"
            )
            
            submitted = st.form_submit_button("Save SMTP Settings", type="primary")
            
            if submitted:
                # Validate required fields
                if not server_name or not username:
                    st.error("Server Name and Username are required fields.")
                elif not password:
                    st.warning("Password field is empty. SMTP may not work without proper authentication.")
                else:
                    # Prepare SMTP configuration
                    smtp_config = {
                        "server_name": server_name,
                        "port": port,
                        "username": username,
                        "password": password,
                        "auth_method": auth_method,
                        "connection_security": connection_security,
                        "enabled": enabled
                    }
                    
                    # Update SMTP settings
                    result = update_smtp_settings(smtp_config)
                    
                    if result.get("success"):
                        st.success("✅ SMTP settings updated successfully!")
                        st.balloons()
                        st.experimental_rerun()
                    else:
                        st.error(f"❌ Failed to update SMTP settings: {result.get('error', 'Unknown error')}")

# === USER MANAGEMENT TAB ===
with settings_tabs[1]:
    
    st.subheader("👥 User Management")
    st.markdown("Manage system users and admin privileges.")
    
    # Create new admin user section
    st.markdown("#### Create New Admin User")
    
    with st.form("create_admin_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input("Username", help="Username for the new admin user")
            new_email = st.text_input("Email", help="Email address for the new admin user")
            
        with col2:
            new_password = st.text_input("Password", type="password", help="Password for the new admin user")
            confirm_password = st.text_input("Confirm Password", type="password", help="Confirm the password")
        
        create_admin_submitted = st.form_submit_button("Create Admin User", type="primary")
        
        if create_admin_submitted:
            if not all([new_username, new_email, new_password, confirm_password]):
                st.error("All fields are required.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters long.")
            else:
                # Create admin user
                user_data = {
                    "username": new_username,
                    "email": new_email,
                    "password": new_password,
                    "confirm_password": confirm_password
                }
                
                result = create_admin_user(user_data)
                
                if "error" in result:
                    st.error(f"❌ Failed to create admin user: {result['error']}")
                else:
                    st.success(f"✅ Admin user '{new_username}' created successfully!")
                    st.balloons()
                    st.experimental_rerun()
    
    # List existing users
    st.markdown("#### Current Users")
    
    users_data = get_all_users()
    
    if "error" in users_data:
        st.error(f"Error loading users: {users_data['error']}")
    else:
        if users_data:
            # Display users in a table
            user_display = []
            for user in users_data:
                user_display.append({
                    "ID": user["id"],
                    "Username": user["username"],
                    "Email": user["email"],
                    "Admin": "✅" if user["is_admin"] else "❌",
                    "Super Admin": "👑" if user["is_super_admin"] else "❌",
                    "Created": user["created_at"][:10] if user["created_at"] else "N/A"
                })
            
            st.dataframe(user_display, use_container_width=True)
            
            # Admin status management
            st.markdown("#### Manage Admin Status")
            
            # Filter out super admin users from the list (cannot change super admin status)
            regular_users = [u for u in users_data if not u["is_super_admin"]]
            
            if regular_users:
                selected_user = st.selectbox(
                    "Select User to Modify",
                    options=regular_users,
                    format_func=lambda u: f"{u['username']} ({u['email']}) - {'Admin' if u['is_admin'] else 'Regular User'}"
                )
                
                if selected_user:
                    current_status = selected_user["is_admin"]
                    new_status = st.checkbox(
                        f"Admin privileges for {selected_user['username']}",
                        value=current_status,
                        help="Grant or revoke admin privileges for this user"
                    )
                    
                    if st.button(f"Update Admin Status for {selected_user['username']}", type="secondary"):
                        if new_status != current_status:
                            # Update admin status
                            status_data = {
                                "user_id": selected_user["id"],
                                "is_admin": new_status
                            }
                            
                            # Note: This would need an API endpoint implementation
                            st.info("Admin status update functionality will be implemented in the next update.")
                        else:
                            st.info("No changes made to admin status.")
            else:
                st.info("No regular users to manage. Only super admin users exist.")
        else:
            st.info("No users found in the system.")

# Footer with help information
st.markdown("---")
st.markdown("### 💡 Help & Information")

with st.expander("SMTP Configuration Help"):
    st.markdown("""
    **Common SMTP Settings:**
    
    - **Gmail**: smtp.gmail.com, Port 587, STARTTLS
    - **Outlook**: smtp-mail.outlook.com, Port 587, STARTTLS  
    - **Yahoo**: smtp.mail.yahoo.com, Port 587, STARTTLS
    - **Custom**: Contact your email provider for specific settings
    
    **Security Notes:**
    - Use app-specific passwords for Gmail/Outlook
    - STARTTLS is recommended for secure connections
    - Test email functionality after configuration
    """)

with st.expander("User Management Help"):
    st.markdown("""
    **User Roles:**
    
    - **Super Admin**: Full system access, can create admin users, access settings
    - **Admin**: Administrative privileges, can manage content and users  
    - **Regular User**: Basic user access to application features
    
    **Important Notes:**
    - Only the first user created becomes super admin
    - Super admin status cannot be changed or transferred
    - Admin users can be promoted/demoted by super admin
    """)