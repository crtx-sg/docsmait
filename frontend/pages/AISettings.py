# frontend/pages/AISettings.py
import streamlit as st
import requests
import json
import time
import os
from typing import Dict, Any, Optional

# Page config
st.set_page_config(page_title="AI Settings", page_icon="🤖", layout="wide")

from config import BACKEND_URL

def get_auth_headers():
    """Get authentication headers"""
    token = st.session_state.get("access_token")
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}

def fetch_ai_settings() -> Optional[Dict[str, Any]]:
    """Fetch current AI settings"""
    headers = get_auth_headers()
    if not headers:
        return None
    
    try:
        response = requests.get(f"{BACKEND_URL}/ai/config/settings", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch AI settings: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching AI settings: {str(e)}")
        return None

def fetch_ai_prompts() -> Optional[Dict[str, Any]]:
    """Fetch current AI prompts"""
    headers = get_auth_headers()
    if not headers:
        return None
    
    try:
        response = requests.get(f"{BACKEND_URL}/ai/config/prompts", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch AI prompts: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching AI prompts: {str(e)}")
        return None

def fetch_available_models() -> Optional[Dict[str, Any]]:
    """Fetch available AI models"""
    headers = get_auth_headers()
    if not headers:
        return None
    
    try:
        response = requests.get(f"{BACKEND_URL}/ai/models", headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch available models: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching available models: {str(e)}")
        return None

def check_ai_health() -> Optional[Dict[str, Any]]:
    """Check AI service health"""
    headers = get_auth_headers()
    if not headers:
        return None
    
    try:
        response = requests.get(f"{BACKEND_URL}/ai/health", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"healthy": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"healthy": False, "error": str(e)}

def update_ai_settings(settings: Dict[str, Any]) -> bool:
    """Update AI settings"""
    headers = get_auth_headers()
    if not headers:
        return False
    
    try:
        response = requests.put(
            f"{BACKEND_URL}/ai/config/settings",
            headers=headers,
            json=settings,
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error updating AI settings: {str(e)}")
        return False

def update_prompt(document_type: str, category: str, prompt: str) -> bool:
    """Update document prompt"""
    headers = get_auth_headers()
    if not headers:
        return False
    
    try:
        response = requests.put(
            f"{BACKEND_URL}/ai/config/prompts",
            headers=headers,
            json={
                "document_type": document_type,
                "category": category,
                "prompt": prompt
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error updating prompt: {str(e)}")
        return False

# Main app
def main():
    # Check authentication
    if "access_token" not in st.session_state:
        st.error("🔒 Please log in to access AI Settings")
        st.stop()
    
    st.title("🤖 AI Configuration")
    st.markdown("Configure AI settings and document prompts for the AI assistant")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["⚙️ AI Settings", "📝 Document Prompts", "🔧 System Status"])
    
    with tab1:
        
        # Fetch current settings
        current_settings = fetch_ai_settings()
        if not current_settings:
            st.error("Unable to load AI settings")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Model Settings")
            
            # Fetch available models
            models_info = fetch_available_models()
            if models_info and models_info.get("success"):
                available_models = models_info.get("models", [])
            else:
                available_models = current_settings.get("available_models", ["qwen2:7b"])
            
            current_model = current_settings.get("default_model", "qwen2:7b")
            selected_model = st.selectbox(
                "Default AI Model",
                options=available_models,
                index=available_models.index(current_model) if current_model in available_models else 0,
                help="Select the default AI model for document assistance"
            )
            
            ai_timeout = st.number_input(
                "AI Request Timeout (seconds)",
                min_value=10,
                max_value=300,
                value=current_settings.get("ai_timeout", 120),
                help="Maximum time to wait for AI responses"
            )
        
        with col2:
            st.subheader("Response Settings")
            
            max_response_length = st.number_input(
                "Maximum Response Length",
                min_value=100,
                max_value=10000,
                value=current_settings.get("max_response_length", 2000),
                help="Maximum length of AI responses"
            )
            
            ai_context_window = st.number_input(
                "Context Window Size",
                min_value=1000,
                max_value=20000,
                value=current_settings.get("ai_context_window", 4000),
                help="Maximum amount of document content to send to AI"
            )
            
            show_prompt = st.checkbox(
                "Show/Allow Prompt Editing",
                value=current_settings.get("show_prompt", True),
                help="Allow users to see and edit prompts before AI requests"
            )
        
        # Update settings button
        if st.button("💾 Update AI Settings", type="primary"):
            new_settings = {
                "default_model": selected_model,
                "ai_timeout": ai_timeout,
                "max_response_length": max_response_length,
                "ai_context_window": ai_context_window,
                "show_prompt": show_prompt
            }
            
            if update_ai_settings(new_settings):
                st.success("✅ AI settings updated successfully!")
                time.sleep(2)
                st.rerun()
            else:
                st.error("❌ Failed to update AI settings")
    
    with tab2:
        st.markdown("Configure AI prompts for different document types")
        
        # Fetch current prompts
        current_prompts = fetch_ai_prompts()
        if not current_prompts:
            st.error("Unable to load AI prompts")
            return
        
        # Create expandable sections for each category
        for category, doc_types in current_prompts.items():
            category_display = category.replace("_", " ").title()
            
            with st.expander(f"📁 {category_display}", expanded=False):
                for doc_type, prompt in doc_types.items():
                    doc_type_display = doc_type.replace("_", " ").title()
                    
                    st.subheader(f"📄 {doc_type_display}")
                    
                    # Create unique key for each text area
                    prompt_key = f"prompt_{category}_{doc_type}"
                    
                    edited_prompt = st.text_area(
                        f"Prompt for {doc_type_display}",
                        value=prompt,
                        height=100,
                        key=prompt_key,
                        help="Use [configurable_item] as placeholder for user input"
                    )
                    
                    col1, col2, col3 = st.columns([1, 1, 2])
                    
                    with col1:
                        if st.button(f"💾 Save", key=f"save_{category}_{doc_type}"):
                            if update_prompt(doc_type, category, edited_prompt):
                                st.success(f"✅ Updated {doc_type_display} prompt")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to update {doc_type_display} prompt")
                    
                    with col2:
                        if st.button(f"🔄 Reset", key=f"reset_{category}_{doc_type}"):
                            st.info("Reset functionality coming soon")
                    
                    st.divider()
    
    with tab3:
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("AI Service Health")
            
            if st.button("🔄 Check AI Health", key="health_check"):
                with st.spinner("Checking AI service..."):
                    health_info = check_ai_health()
                    
                    if health_info and health_info.get("healthy"):
                        st.success("✅ AI Service is healthy")
                        st.info(f"Service: {health_info.get('service', 'Unknown')}")
                    else:
                        st.error("❌ AI Service is not available")
                        if "error" in health_info:
                            st.error(f"Error: {health_info['error']}")
        
        with col2:
            st.subheader("Available Models")
            
            if st.button("🔄 Refresh Models", key="refresh_models"):
                with st.spinner("Fetching available models..."):
                    models_info = fetch_available_models()
                    
                    if models_info:
                        if models_info.get("success"):
                            st.success("✅ Models fetched from AI service")
                            models = models_info.get("models", [])
                        else:
                            st.warning("⚠️ Using fallback model list")
                            models = models_info.get("models", [])
                        
                        st.write("**Available Models:**")
                        for model in models:
                            st.write(f"• {model}")
                    else:
                        st.error("❌ Unable to fetch models")
        
        st.divider()
        
        st.subheader("Usage Statistics")
        st.info("📊 Usage analytics and prompt effectiveness metrics coming soon")

if __name__ == "__main__":
    main()