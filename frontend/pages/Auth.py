# frontend/pages/Auth.py
import streamlit as st
from auth_utils import login_user, signup_user, logout_user, is_logged_in, get_current_user

# Hide sidebar on authentication page
st.set_page_config(
    page_title="Authentication", 
    page_icon="🔐",
    initial_sidebar_state="collapsed"
)

# Additional CSS to completely hide sidebar
st.markdown(
    """
    <style>
    .css-1d391kg {display: none;}
    .css-1f4c4qu {display: none;}
    section[data-testid="stSidebar"] {display: none !important;}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🔐 Authentication")

if is_logged_in():
    # If already logged in, redirect to main page
    st.success("You are already logged in!")
    st.info("Redirecting to main page...")
    st.switch_page("app.py")
else:
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="user@example.com")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login", type="primary")
            
            if submit_login:
                if email and password:
                    success, message = login_user(email, password)
                    if success:
                        st.success(message)
                        st.info("Redirecting to main page...")
                        st.switch_page("app.py")
                    else:
                        st.error(message)
                else:
                    st.error("Please fill in all fields")
    
    with tab2:
        st.subheader("Sign Up")
        with st.form("signup_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            email = st.text_input("Email", placeholder="user@example.com")
            password = st.text_input("Password", type="password", help="Minimum 8 characters")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit_signup = st.form_submit_button("Sign Up", type="primary")
            
            if submit_signup:
                if username and email and password and confirm_password:
                    if password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(password) < 8:
                        st.error("Password must be at least 8 characters long")
                    elif len(username) < 3:
                        st.error("Username must be at least 3 characters long")
                    else:
                        success, message = signup_user(username, email, password, confirm_password)
                        if success:
                            st.success(message)
                            st.info("🎉 As the first user, you have been granted admin privileges!")
                            st.info("Redirecting to main page...")
                            st.switch_page("app.py")
                        else:
                            st.error(message)
                else:
                    st.error("Please fill in all fields")

st.markdown("---")
st.markdown("### 📝 Notes")
st.info("""
- The **first user** to sign up will automatically receive **admin privileges**
- Use a valid email address for your account
- Passwords must be at least 8 characters long
- Usernames must be at least 3 characters long and unique
""")