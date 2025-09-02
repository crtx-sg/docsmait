# frontend/pages/Activity_Log_Test.py
import streamlit as st
from auth_utils import require_auth, setup_authenticated_sidebar

require_auth()

st.set_page_config(page_title="Activity Log Test", page_icon="📋")

st.title("📋 Activity Log (Test)")
setup_authenticated_sidebar()

st.success("✅ Activity Log page is working!")
st.info("This is a test version to verify the page shows up in the sidebar.")