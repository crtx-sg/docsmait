# frontend/pages/Settings.py
import streamlit as st
import requests
import json
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers, BACKEND_URL
from config import MIN_PASSWORD_LENGTH, TEXT_AREA_MEDIUM_HEIGHT

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

# Check if user is admin or super admin
def check_admin_or_super_admin():
    """Check if current user is admin or super admin"""
    try:
        response = requests.get(f"{BACKEND_URL}/auth/me", headers=get_auth_headers())
        if response.status_code == 200:
            user_data = response.json()
            return user_data.get('is_admin', False) or user_data.get('is_super_admin', False)
        return False
    except Exception as e:
        st.error(f"Error checking user permissions: {e}")
        return False

# Get current user information
def get_current_user_info():
    """Get current user information"""
    try:
        response = requests.get(f"{BACKEND_URL}/auth/me", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error getting user information: {e}")
        return None

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

# Test SMTP connection
def test_smtp_connection(smtp_settings):
    """Test SMTP connection and display logs"""
    st.markdown("### 🧪 SMTP Connection Test")
    
    # Create a container for logs
    log_container = st.container()
    
    with log_container:
        st.write("**📝 Connection Test Log:**")
        log_placeholder = st.empty()
        
        logs = []
        
        try:
            # Import required modules
            import smtplib
            import ssl
            from datetime import datetime
            
            # Log start
            logs.append(f"🚀 {datetime.now().strftime('%H:%M:%S')} - Starting SMTP connection test")
            logs.append(f"📧 {datetime.now().strftime('%H:%M:%S')} - Server: {smtp_settings.get('server_name', 'Not set')}")
            logs.append(f"🚪 {datetime.now().strftime('%H:%M:%S')} - Port: {smtp_settings.get('port', 'Not set')}")
            logs.append(f"🔒 {datetime.now().strftime('%H:%M:%S')} - Security: {smtp_settings.get('connection_security', 'Not set')}")
            log_placeholder.text_area("", value="\n".join(logs), height=150, key="smtp_logs")
            
            # Check if settings are complete
            if not smtp_settings.get('server_name') or not smtp_settings.get('username'):
                logs.append(f"❌ {datetime.now().strftime('%H:%M:%S')} - Error: Server name and username are required")
                log_placeholder.text_area("", value="\n".join(logs), height=150, key="smtp_logs_error")
                st.error("❌ SMTP configuration incomplete. Please configure server name and username.")
                return
            
            logs.append(f"🔄 {datetime.now().strftime('%H:%M:%S')} - Attempting to connect...")
            log_placeholder.text_area("", value="\n".join(logs), height=150, key="smtp_logs_connecting")
            
            # Create SMTP connection based on security setting
            server = None
            if smtp_settings.get('connection_security') == 'SSL/TLS':
                logs.append(f"🔐 {datetime.now().strftime('%H:%M:%S')} - Using SSL/TLS connection")
                log_placeholder.text_area("", value="\n".join(logs), height=150, key="smtp_logs_ssl")
                
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    smtp_settings.get('server_name'),
                    int(smtp_settings.get('port', 465)),
                    context=context
                )
            else:
                logs.append(f"📡 {datetime.now().strftime('%H:%M:%S')} - Using plain SMTP connection")
                log_placeholder.text_area("", value="\n".join(logs), height=150, key="smtp_logs_plain")
                
                server = smtplib.SMTP(
                    smtp_settings.get('server_name'),
                    int(smtp_settings.get('port', 587))
                )
                
                if smtp_settings.get('connection_security') == 'STARTTLS':
                    logs.append(f"🔒 {datetime.now().strftime('%H:%M:%S')} - Upgrading to STARTTLS")
                    log_placeholder.text_area("", value="\n".join(logs), height=150, key="smtp_logs_starttls")
                    server.starttls(context=ssl.create_default_context())
            
            logs.append(f"✅ {datetime.now().strftime('%H:%M:%S')} - Connection established successfully")
            log_placeholder.text_area("", value="\n".join(logs), height=150, key="smtp_logs_connected")
            
            # Test authentication if credentials are provided
            if smtp_settings.get('username') and smtp_settings.get('password'):
                logs.append(f"🔑 {datetime.now().strftime('%H:%M:%S')} - Testing authentication...")
                log_placeholder.text_area("", value="\n".join(logs), height=150, key="smtp_logs_auth")
                
                server.login(smtp_settings.get('username'), smtp_settings.get('password'))
                
                logs.append(f"✅ {datetime.now().strftime('%H:%M:%S')} - Authentication successful")
                log_placeholder.text_area("", value="\n".join(logs), height=150, key="smtp_logs_auth_success")
            else:
                logs.append(f"⚠️ {datetime.now().strftime('%H:%M:%S')} - Skipping authentication test (no password provided)")
                log_placeholder.text_area("", value="\n".join(logs), height=150, key="smtp_logs_no_auth")
            
            # Close connection
            server.quit()
            logs.append(f"🔚 {datetime.now().strftime('%H:%M:%S')} - Connection closed")
            logs.append(f"🎉 {datetime.now().strftime('%H:%M:%S')} - SMTP test completed successfully!")
            log_placeholder.text_area("", value="\n".join(logs), height=150, key="smtp_logs_final")
            
            st.success("🎉 **SMTP Connection Test Successful!** Your email configuration is working correctly.")
            
        except smtplib.SMTPAuthenticationError as e:
            logs.append(f"❌ {datetime.now().strftime('%H:%M:%S')} - Authentication failed: {str(e)}")
            log_placeholder.text_area("", value="\n".join(logs), height=150, key="smtp_logs_auth_error")
            st.error(f"❌ **Authentication Failed**: {str(e)}")
            
        except smtplib.SMTPConnectError as e:
            logs.append(f"❌ {datetime.now().strftime('%H:%M:%S')} - Connection failed: {str(e)}")
            log_placeholder.text_area("", value="\n".join(logs), height=150, key="smtp_logs_conn_error")
            st.error(f"❌ **Connection Failed**: {str(e)}")
            
        except smtplib.SMTPServerDisconnected as e:
            logs.append(f"❌ {datetime.now().strftime('%H:%M:%S')} - Server disconnected: {str(e)}")
            log_placeholder.text_area("", value="\n".join(logs), height=150, key="smtp_logs_disconn_error")
            st.error(f"❌ **Server Disconnected**: {str(e)}")
            
        except Exception as e:
            logs.append(f"❌ {datetime.now().strftime('%H:%M:%S')} - Unexpected error: {str(e)}")
            log_placeholder.text_area("", value="\n".join(logs), height=150, key="smtp_logs_gen_error")
            st.error(f"❌ **Connection Test Failed**: {str(e)}")
            
        finally:
            if server:
                try:
                    server.quit()
                except:
                    pass

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
            return {"error": f"Server error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection error: {e}"}

def reset_user_password(user_id, new_password):
    """Reset user password by admin"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/admin/users/{user_id}/reset-password",
            json={"new_password": new_password},
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            return {"error": "Access denied"}
        elif response.status_code == 404:
            return {"error": "User not found"}
        else:
            return {"error": f"Server error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection error: {e}"}

def update_user_admin_status(user_id, is_admin):
    """Update user admin status"""
    try:
        response = requests.put(
            f"{BACKEND_URL}/admin/users/{user_id}/admin-status",
            json={"user_id": user_id, "is_admin": is_admin},
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            return {"error": "Access denied - only super admin can change admin status"}
        elif response.status_code == 404:
            return {"error": "User not found"}
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            return {"error": error_data.get("detail", f"Server error: {response.status_code}")}
    except Exception as e:
        return {"error": f"Connection error: {e}"}


# Check if user is admin or super admin
if not check_admin_or_super_admin():
    st.error("🚫 Access Denied")
    st.warning("Only users with admin or super admin privileges can access system settings.")
    st.stop()

# Get current user information for role-based UI
current_user = get_current_user_info()
is_super_admin = current_user.get('is_super_admin', False) if current_user else False

# Main settings interface
st.markdown("---")

# Settings tabs - both admin and super admin can access all settings
settings_tabs = st.tabs(["📧 Email Notifications", "👥 User Management"])
show_email_tab = True
show_user_tab = True
user_tab_index = 1

# === EMAIL NOTIFICATIONS TAB === (Admin & Super Admin)
with settings_tabs[0]:
    
    st.subheader("📧 SMTP Configuration")
    st.markdown("Configure email notification settings for the system.")
    st.info("🔐 **Admin Access**: Administrators and super administrators can configure system-wide email settings.")
    
    # Get current SMTP settings
    smtp_settings = get_smtp_settings()
    
    if "error" in smtp_settings:
        st.error(f"Error loading SMTP settings: {smtp_settings['error']}")
    else:
        # Current SMTP Configuration Status
        st.markdown("### 📊 Current SMTP Configuration")
        
        if smtp_settings.get('enabled', False):
            st.success("✅ **SMTP is Configured and Enabled**")
        else:
            st.warning("⚠️ **SMTP is Not Configured or Disabled**")
            st.info("📝 Configure the settings below to enable email notifications")
        
        # Display current configuration in dataframe
        import pandas as pd
        
        config_data = [
            {"Setting": "📧 Server Name", "Value": smtp_settings.get('server_name', 'Not configured')},
            {"Setting": "🚪 Port", "Value": str(smtp_settings.get('port', 'Not configured'))},
            {"Setting": "👤 Username", "Value": smtp_settings.get('username', 'Not configured')},
            {"Setting": "🔐 Authentication Method", "Value": smtp_settings.get('auth_method', 'Not configured').title()},
            {"Setting": "🔒 Security Protocol", "Value": smtp_settings.get('connection_security', 'Not configured')},
            {"Setting": "📬 Status", "Value": "✅ Enabled" if smtp_settings.get('enabled', False) else "❌ Disabled"}
        ]
        
        df_config = pd.DataFrame(config_data)
        st.dataframe(df_config, use_container_width=True, hide_index=True)
        
        # Test connection button
        test_col1, test_col2, test_col3 = st.columns(3)
        with test_col2:
            if st.button("🧪 Test SMTP Connection", type="secondary", use_container_width=True):
                test_smtp_connection(smtp_settings)
        
        st.markdown("---")
        st.markdown("### ⚙️ SMTP Configuration")
        
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
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to update SMTP settings: {result.get('error', 'Unknown error')}")

# === USER MANAGEMENT TAB ===
with settings_tabs[user_tab_index]:
    
    st.subheader("👥 User Management")
    if is_super_admin:
        st.markdown("Manage system users and admin privileges.")
    else:
        st.markdown("View system users and manage password resets.")
    
    # Create new admin user section (Super Admin Only)
    if is_super_admin:
        st.markdown("#### Create New Admin User")
        st.info("🔐 **Super Admin Only**: Only super administrators can create new admin users.")
        
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
                elif len(new_password) < MIN_PASSWORD_LENGTH:
                    st.error(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")
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
                        st.rerun()
    
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
            
            # Admin status management (Super Admin Only)
            if is_super_admin:
                st.markdown("#### Manage Admin Status")
                st.info("🔐 **Super Admin Only**: Only super administrators can grant or revoke admin privileges.")
                
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
                                result = update_user_admin_status(selected_user["id"], new_status)
                                
                                if "error" in result:
                                    st.error(f"❌ Failed to update admin status: {result['error']}")
                                else:
                                    status_text = "granted" if new_status else "revoked"
                                    st.success(f"✅ Admin privileges {status_text} for user '{selected_user['username']}'!")
                                    st.balloons()
                                    st.rerun()
                            else:
                                st.info("No changes made to admin status.")
                else:
                    st.info("No regular users to manage. Only super admin users exist.")
                
            # Password Reset Section
            st.markdown("#### 🔐 Reset User Password")
            st.markdown("*Help users who have forgotten their passwords by resetting them.*")
            
            if users_data and len(users_data) > 1:  # More than just the current super admin
                # Filter out current user to prevent self-password reset via admin panel
                from auth_utils import get_current_user
                current_user = get_current_user()
                current_user_id = current_user.get('id') if current_user else None
                
                other_users = [u for u in users_data if u.get('id') != current_user_id]
                
                if other_users:
                    with st.form("password_reset_form"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            selected_user_reset = st.selectbox(
                                "Select User to Reset Password",
                                options=other_users,
                                format_func=lambda u: f"{u['username']} ({u['email']}) - {'Super Admin' if u['is_super_admin'] else 'Admin' if u['is_admin'] else 'Regular User'}",
                                help="Choose the user whose password you want to reset"
                            )
                            
                            new_password_reset = st.text_input(
                                "New Password",
                                type="password",
                                help=f"Enter a secure new password (minimum {MIN_PASSWORD_LENGTH} characters)",
                                placeholder="Enter new password..."
                            )
                            
                            confirm_password_reset = st.text_input(
                                "Confirm New Password",
                                type="password",
                                help="Re-enter the new password to confirm",
                                placeholder="Confirm new password..."
                            )
                        
                        with col2:
                            st.markdown("**Password Requirements:**")
                            st.markdown(f"• Minimum {MIN_PASSWORD_LENGTH} characters")
                            st.markdown("• Use strong passwords")
                            st.markdown("• Inform user of new password securely")
                            
                            st.warning("⚠️ **Important:** The user will need to use this new password to log in. Make sure to communicate it to them securely.")
                        
                        reset_submitted = st.form_submit_button("🔐 Reset Password", type="primary")
                        
                        if reset_submitted:
                            if not selected_user_reset:
                                st.error("Please select a user.")
                            elif not new_password_reset or not confirm_password_reset:
                                st.error("Please enter and confirm the new password.")
                            elif new_password_reset != confirm_password_reset:
                                st.error("Passwords do not match. Please try again.")
                            elif len(new_password_reset) < MIN_PASSWORD_LENGTH:
                                st.error(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")
                            else:
                                # Reset the password
                                result = reset_user_password(selected_user_reset["id"], new_password_reset)
                                
                                if "error" in result:
                                    st.error(f"❌ Failed to reset password: {result['error']}")
                                else:
                                    st.success(f"✅ Password successfully reset for user '{selected_user_reset['username']}'!")
                                    st.info(f"📧 **Next Steps:** Securely communicate the new password to {selected_user_reset['username']} at {selected_user_reset['email']}")
                                    st.balloons()
                                    st.rerun()
                else:
                    st.info("No other users available for password reset.")
            else:
                st.info("Password reset is available when there are multiple users in the system.")
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
    
    **Password Reset:**
    - Super admins can reset passwords for any user (except themselves)
    - Users cannot reset their own passwords through the admin panel
    - Always communicate new passwords securely (email, secure messaging, in-person)
    - Encourage users to change their password after reset
    
    **Important Notes:**
    - Only the first user created becomes super admin
    - Super admin status cannot be changed or transferred
    - Admin users can be promoted/demoted by super admin
    - Password resets are logged for security purposes
    """)