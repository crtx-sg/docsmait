# frontend/auth_utils.py
import streamlit as st
import requests
from config import BACKEND_URL

def get_auth_headers():
    """Get authentication headers for API requests"""
    if "access_token" in st.session_state and st.session_state.access_token:
        return {"Authorization": f"Bearer {st.session_state.access_token}"}
    return {}

def is_logged_in():
    return "access_token" in st.session_state and st.session_state.access_token is not None

def get_current_user():
    if not is_logged_in():
        return None
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/auth/me",
            headers={"Authorization": f"Bearer {st.session_state.access_token}"}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.session_state.access_token = None
            return None
    except:
        st.session_state.access_token = None
        return None

def login_user(email, password):
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            token_data = response.json()
            st.session_state.access_token = token_data["access_token"]
            return True, "Login successful!"
        else:
            error_data = response.json()
            return False, error_data.get("detail", "Login failed")
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def signup_user(username, email, password, confirm_password):
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/signup",
            json={
                "username": username,
                "email": email,
                "password": password,
                "confirm_password": confirm_password
            }
        )
        if response.status_code == 200:
            token_data = response.json()
            st.session_state.access_token = token_data["access_token"]
            return True, "Signup successful!"
        else:
            error_data = response.json()
            return False, error_data.get("detail", "Signup failed")
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def logout_user():
    st.session_state.access_token = None

def require_auth():
    """Decorator function to require authentication for a page"""
    if not is_logged_in():
        st.warning("Please login to access this page")
        st.stop()

def setup_authenticated_sidebar():
    """Setup sidebar with navigation for authenticated users"""
    if not is_logged_in():
        return
    
    # Hide Streamlit's default page navigation
    st.markdown(
        """
        <style>
        ul[data-testid="stSidebarNavItems"] {display: none !important;}
        .css-1d391kg ul {display: none !important;}
        section[data-testid="stSidebarNav"] {display: none !important;}
        .css-1y4p8pa {display: none !important;}
        div[data-testid="stSidebarNav"] {display: none !important;}
        </style>
        """,
        unsafe_allow_html=True
    )
    
    current_user = get_current_user()
    if current_user:
        # Display username at top of sidebar
        st.sidebar.markdown(f"### 👤 {current_user['username']}")
        if current_user.get('is_super_admin'):
            st.sidebar.markdown("👑 **Super Admin**")
        elif current_user['is_admin']:
            st.sidebar.markdown("🔑 **Admin**")
        
        st.sidebar.markdown("---")
        
        # Navigation menu in specified order
        st.sidebar.page_link("app.py", label="🏠 Home")
        st.sidebar.page_link("pages/_Projects.py", label="📋 Projects")
        st.sidebar.page_link("pages/Templates.py", label="📄 Templates")
        st.sidebar.page_link("pages/Documents.py", label="📁 Documents")
        st.sidebar.page_link("pages/Code.py", label="💻 Code")
        st.sidebar.page_link("pages/Issues.py", label="🐛 Issues")
# Reviews page removed - functionality available in Documents → My Reviews tab
        st.sidebar.page_link("pages/DesignRecord.py", label="🔬 Design Record")
        st.sidebar.page_link("pages/Audit.py", label="📊 Audit")
        st.sidebar.page_link("pages/Records.py", label="📋 Records")
        st.sidebar.page_link("pages/Activity_Logs.py", label="📊 Activity Logs")
        st.sidebar.page_link("pages/Training.py", label="🎓 Training")
        st.sidebar.page_link("pages/_Knowledge_Base.py", label="📚 Knowledge Base")
        st.sidebar.page_link("pages/Help.py", label="❓ Help")
        
        # Settings menu only for super admin
        if current_user.get('is_super_admin'):
            st.sidebar.page_link("pages/Settings.py", label="⚙️ Settings")
        
        st.sidebar.markdown("---")
        
        # Logout button
        if st.sidebar.button("🚪 Logout", type="secondary"):
            logout_user()
            st.rerun()
        
        # Add Coherentix Labs link at the bottom
        st.sidebar.markdown("---")
        st.sidebar.markdown(
            """
            <div style="text-align: center; margin-top: 20px; padding: 10px; font-size: 12px; color: #666;">
                <a href="https://www.coherentix.com" target="_blank" style="text-decoration: none; color: #0066cc;">
                    <strong>Coherentix Labs</strong>
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )