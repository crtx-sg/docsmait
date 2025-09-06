# frontend/pages/_Knowledge_Base.py
import streamlit as st
import requests
import json
from datetime import datetime
from auth_utils import require_auth, setup_authenticated_sidebar, get_auth_headers, BACKEND_URL
from config import DEFAULT_COLLECTION_NAME

require_auth()

st.set_page_config(page_title="Knowledge Base", page_icon="📚")

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

st.title("📚 Knowledge Base Management")

setup_authenticated_sidebar()

# Helper function to check if current user is admin or super admin
def is_user_admin():
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

# Create tabs for different functionality
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📤 Upload Documents", "💬 Chat with KB", "🗂️ Collections"])

with tab1:
    
    # Fetch and display statistics
    try:
        response = requests.get(f"{BACKEND_URL}/kb/stats", headers=get_auth_headers())
        if response.status_code == 200:
            stats = response.json()
            
            # Display stats in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Documents Indexed", stats.get("documents_indexed", 0))
                st.metric("Total Documents", stats.get("total_documents", 0))
            
            with col2:
                st.metric("Queries Today", stats.get("queries_today", 0))
                st.metric("Search Queries Today", stats.get("search_queries_today", 0))
            
            with col3:
                st.metric("Index Size (MB)", f"{stats.get('index_size_mb', 0):.2f}")
                if stats.get("last_updated"):
                    st.metric("Last Updated", stats["last_updated"][:10])
                else:
                    st.metric("Last Updated", "Never")
        else:
            st.error("Failed to fetch statistics")
    except requests.ConnectionError:
        st.error("Connection to backend failed")

with tab2:
    st.write("Upload documents to add to your Knowledge Base. Supported formats: PDF, DOCX, TXT, MD, HTML")
    
    # Collection selection - get from backend
    try:
        collections_response = requests.get(f"{BACKEND_URL}/kb/collections", headers=get_auth_headers())
        if collections_response.status_code == 200:
            collections_data = collections_response.json()
            collection_options = [c["name"] for c in collections_data]
            default_collection = next((c["name"] for c in collections_data if c.get("is_default")), DEFAULT_COLLECTION_NAME)
        else:
            collection_options = [DEFAULT_COLLECTION_NAME]
            default_collection = DEFAULT_COLLECTION_NAME
    except:
        collection_options = [DEFAULT_COLLECTION_NAME]
        default_collection = DEFAULT_COLLECTION_NAME
    
    collection_name = st.selectbox("Collection", collection_options, 
                                  index=collection_options.index(default_collection) if default_collection in collection_options else 0,
                                  help="Select which collection to upload documents to")
    
    # Create two columns for file upload and website scraping
    upload_col1, upload_col2 = st.columns(2)
    
    with upload_col1:
        # File upload
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'txt', 'md', 'html'],
            help="Maximum file size: 10MB per file"
        )
        
        if uploaded_files:
            st.write(f"Selected {len(uploaded_files)} file(s):")
            for file in uploaded_files:
                st.write(f"- {file.name} ({file.size} bytes)")
    
    with upload_col2:
        website_urls = st.text_area(
            "Website URLs to scrape",
            placeholder="Enter URLs, one per line:\nhttps://example.com/page1\nhttps://example.com/page2",
            height=120,
            help="Enter website URLs to scrape content from. Each URL should be on a separate line."
        )
        
        if website_urls:
            urls_list = [url.strip() for url in website_urls.split('\n') if url.strip()]
            st.write(f"Found {len(urls_list)} URL(s) to scrape:")
            for url in urls_list[:3]:  # Show first 3
                st.write(f"- {url}")
            if len(urls_list) > 3:
                st.write(f"... and {len(urls_list) - 3} more")
    
    # Process buttons
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        upload_button = st.button("📁 Upload Files", type="primary", disabled=not uploaded_files)
    
    with col_btn2:
        scrape_button = st.button("🌐 Scrape Websites", type="primary", disabled=not website_urls)
    
    # File upload processing
    if upload_button and uploaded_files:
        progress_bar = st.progress(0)
        status_placeholder = st.empty()
        results = []
        
        for i, uploaded_file in enumerate(uploaded_files):
            file_size_kb = uploaded_file.size / 1024 if uploaded_file.size else 0
            status_placeholder.write(f"Processing {uploaded_file.name} ({file_size_kb:.1f} KB)...")
            
            try:
                # Prepare file for upload
                files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                data = {"collection_name": collection_name}
                
                # Use longer timeout for large files (5 minutes base + 1 minute per MB)
                timeout_seconds = 300 + (file_size_kb / 1024 * 60)  # 5 min + 1 min/MB
                
                response = requests.post(
                    f"{BACKEND_URL}/kb/upload",
                    files=files,
                    data=data,
                    headers=get_auth_headers(),
                    timeout=timeout_seconds
                )
                
                if response.status_code == 200:
                    result = response.json()
                    results.append({
                        "filename": uploaded_file.name,
                        "status": "✅ Success",
                        "chunks": result.get("chunks_created", 0),
                        "time": result.get("processing_time", 0)
                    })
                else:
                    error_msg = response.json().get("detail", "Unknown error")
                    results.append({
                        "filename": uploaded_file.name,
                        "status": f"❌ Failed: {error_msg}",
                        "chunks": 0,
                        "time": 0
                    })
            
            except requests.exceptions.Timeout:
                results.append({
                    "filename": uploaded_file.name,
                    "status": f"⏱️ Timeout: File processing took longer than {timeout_seconds/60:.1f} minutes",
                    "chunks": 0,
                    "time": 0
                })
            except Exception as e:
                error_msg = str(e)
                if "timeout" in error_msg.lower():
                    error_msg = f"Processing timeout - file may be too large or system busy"
                results.append({
                    "filename": uploaded_file.name,
                    "status": f"❌ Error: {error_msg}",
                    "chunks": 0,
                    "time": 0
                })
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        # Display results
        status_placeholder.empty()
        progress_bar.empty()
        
        st.subheader("Upload Results")
        success_count = sum(1 for r in results if "✅" in r['status'])
        
        for result in results:
            with st.expander(f"{result['filename']} - {result['status']}"):
                if result['chunks'] > 0:
                    st.write(f"Chunks created: {result['chunks']}")
                    st.write(f"Processing time: {result['time']}s")
        
        # Clear the file uploader if all uploads were successful
        if success_count == len(results) and success_count > 0:
            st.success(f"🎉 All {success_count} documents uploaded successfully! You can now upload more documents.")
            # Add a rerun to clear the uploaded files from UI
            if st.button("📝 Upload More Documents", type="primary"):
                st.rerun()
    
    # Website scraping processing
    if scrape_button and website_urls:
        urls_list = [url.strip() for url in website_urls.split('\n') if url.strip()]
        if urls_list:
            st.info("🚧 Website scraping feature will be implemented in Phase 2")
            st.write("URLs ready for scraping:")
            for url in urls_list:
                st.write(f"- {url}")

with tab3:
    st.write("Ask questions about your uploaded documents using AI-powered search and retrieval.")
    
    # Collection selection - get from backend
    try:
        collections_response = requests.get(f"{BACKEND_URL}/kb/collections", headers=get_auth_headers())
        if collections_response.status_code == 200:
            collections_data = collections_response.json()
            collection_options = [c["name"] for c in collections_data]
        else:
            collection_options = [DEFAULT_COLLECTION_NAME]
    except:
        collection_options = [DEFAULT_COLLECTION_NAME]
    
    chat_collection = st.selectbox("Select Collection", collection_options, help="Choose which collection to query")
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for chat in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(chat["query"])
        with st.chat_message("assistant"):
            st.write(chat["response"])
            if chat.get("sources"):
                with st.expander(f"📚 Sources ({len(chat['sources'])})"):
                    for i, source in enumerate(chat["sources"], 1):
                        st.write(f"**{i}. {source['filename']}** (Score: {source['score']})")
                        st.write(f"_{source['text_preview']}_")
                        st.divider()
    
    # Chat input
    query = st.chat_input("Ask a question about your documents...")
    
    if query:
        # Add user message to chat
        with st.chat_message("user"):
            st.write(query)
        
        # Process query
        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/kb/chat",
                        json={"message": query, "collection_name": chat_collection},
                        headers=get_auth_headers()
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.write(result["response"])
                        
                        # Show performance metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.caption(f"🔍 Embedding: {result['query_embedding_time']:.0f}ms")
                        with col2:
                            st.caption(f"📖 Retrieval: {result['retrieval_time']:.0f}ms")
                        with col3:
                            st.caption(f"🤖 LLM: {result['llm_response_time']:.0f}ms")
                        
                        # Show sources
                        if result.get("sources"):
                            with st.expander(f"📚 Sources ({len(result['sources'])})"):
                                for i, source in enumerate(result["sources"], 1):
                                    st.write(f"**{i}. {source['filename']}** (Relevance: {source['score']:.3f})")
                                    st.write(f"_{source['text_preview']}_")
                                    st.divider()
                        
                        # Add to chat history
                        st.session_state.chat_history.append({
                            "query": query,
                            "response": result["response"],
                            "sources": result.get("sources", [])
                        })
                    else:
                        error_msg = response.json().get("detail", "Unknown error")
                        st.error(f"Query failed: {error_msg}")
                
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
    
    # Clear chat history
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

with tab4:
    
    # Helper functions for collections
    def fetch_collections():
        """Fetch all collections from the backend"""
        try:
            response = requests.get(f"{BACKEND_URL}/kb/collections", headers=get_auth_headers())
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to fetch collections: {response.status_code}")
                return []
        except Exception as e:
            st.error(f"Error fetching collections: {str(e)}")
            return []

    def create_collection(name, description, tags):
        """Create a new collection"""
        try:
            payload = {"name": name, "description": description, "tags": tags}
            response = requests.post(f"{BACKEND_URL}/kb/collections", json=payload, headers=get_auth_headers())
            return response.status_code == 200, response.json() if response.status_code == 200 else response.text
        except Exception as e:
            return False, str(e)

    def delete_collection(name, force=False):
        """Delete a collection"""
        try:
            params = {"force": force} if force else {}
            response = requests.delete(f"{BACKEND_URL}/kb/collections/{name}", params=params, headers=get_auth_headers())
            return response.status_code == 200, response.json() if response.status_code == 200 else response.text
        except Exception as e:
            return False, str(e)

    # Fetch collections
    collections = fetch_collections()
    
    # Add default collection management at the top
    st.info("💡 Set which collection should be used as default for new document uploads")
    
    default_col1, default_col2, default_col3 = st.columns([2, 1, 1])
    
    with default_col1:
        available_collections = [c["name"] for c in collections] if collections else []
        current_default = next((c["name"] for c in collections if c.get("is_default")), None)
        
        if available_collections:
            selected_default = st.selectbox(
                "Default Collection",
                options=available_collections,
                index=available_collections.index(current_default) if current_default in available_collections else 0,
                help="Choose which collection should be the default for new uploads"
            )
        else:
            st.warning("No collections available. Create a collection first.")
            selected_default = None
    
    with default_col2:
        if available_collections and is_user_admin():
            if st.button("💾 Set Default", type="primary"):
                # Update default collection via new API endpoint
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/kb/collections/{selected_default}/set-default",
                        headers=get_auth_headers()
                    )
                    if response.status_code == 200:
                        st.success(f"'{selected_default}' set as default!")
                        st.rerun()
                    else:
                        st.error("Failed to update default collection")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        elif available_collections:
            st.button("💾 Set Default", disabled=True, type="primary", help="Admin access required")
    
    st.markdown("---")
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Collection creation - Admin only
        if is_user_admin():
            st.subheader("🔨 Create New Collection")
            with st.form("create_collection_form"):
                new_name = st.text_input("Collection Name", placeholder="e.g., my_documents")
                new_description = st.text_area("Description", placeholder="Brief description of this collection...")
                new_tags_input = st.text_input("Tags (comma-separated)", placeholder="tag1, tag2, tag3")
                new_tags = [tag.strip() for tag in new_tags_input.split(",") if tag.strip()]
                
                if st.form_submit_button("🔨 Create Collection", type="primary"):
                    if new_name:
                        success, result = create_collection(new_name, new_description, new_tags)
                        if success:
                            st.success(f"Collection '{new_name}' created successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to create collection: {result}")
                    else:
                        st.warning("Please enter a collection name")
        else:
            st.subheader("🔒 Admin Access Required")
            st.info("Only Admin or Super Admin users can create new collections. Please contact your administrator if you need to create a collection.")
            st.text_input("Collection Name", disabled=True, placeholder="Admin access required")
            st.text_area("Description", disabled=True, placeholder="Admin access required")
            st.text_input("Tags", disabled=True, placeholder="Admin access required")
            st.button("🔨 Create Collection", disabled=True, type="primary", help="Admin access required")
    
    with col2:
        st.subheader("📋 Existing Collections")
        
        if collections:
            # Convert collections to DataFrame format
            import pandas as pd
            
            # Prepare data for display
            display_data = []
            for collection in collections:
                display_data.append({
                    "Collection": collection['name'] + (" ⭐" if collection.get('is_default') else ""),
                    "Description": collection.get('description', 'No description')[:50] + ("..." if len(collection.get('description', '')) > 50 else ""),
                    "Documents": collection.get('document_count', 0),
                    "Size (MB)": round(collection.get('total_size_mb', 0), 2),
                    "Tags": ', '.join(collection.get('tags', [])[:2]) + (f" +{len(collection.get('tags', [])) - 2}" if len(collection.get('tags', [])) > 2 else ""),
                    "Created By": collection.get('created_by', 'Unknown'),
                    "Created Date": collection.get('created_date', 'Unknown')[:10] if collection.get('created_date') else 'Unknown'
                })
            
            df_collections = pd.DataFrame(display_data)
            
            # Display dataframe with selection
            selected_indices = st.dataframe(
                df_collections,
                use_container_width=True,
                selection_mode="single-row",
                on_select="rerun",
                key="collections_dataframe"
            ).selection.rows
            
            # Handle selection and show collection management
            if selected_indices:
                selected_idx = selected_indices[0]
                selected_collection = collections[selected_idx]
                
                st.markdown("---")
                st.subheader(f"🗂️ Collection Actions: {selected_collection['name']}")
                
                # Action buttons in four columns
                action_col1, action_col2, action_col3, action_col4 = st.columns(4)
                
                with action_col1:
                    # View Documents
                    if st.button("📄 View", key="view_documents", use_container_width=True):
                        st.session_state["show_documents"] = True
                        st.session_state["selected_collection_name"] = selected_collection['name']
                
                with action_col2:
                    # Edit Collection - Admin only
                    if is_user_admin():
                        if st.button("✏️ Edit", key="edit_collection", use_container_width=True):
                            st.session_state["show_edit"] = True
                            st.session_state["selected_collection_name"] = selected_collection['name']
                    else:
                        st.button("✏️ Edit", disabled=True, use_container_width=True, help="Admin access required")
                
                with action_col3:
                    # Reset Collection with double confirmation (only if has documents) - Admin only
                    if is_user_admin() and selected_collection.get('document_count', 0) > 0:
                        reset_confirm_key = f"reset_confirm_{selected_collection['name']}"
                        reset_double_confirm_key = f"reset_double_confirm_{selected_collection['name']}"
                        
                        if st.session_state.get(reset_double_confirm_key, False):
                            if st.button("🔄 CONFIRM", key="final_reset", use_container_width=True):
                                try:
                                    response = requests.post(
                                        f"{BACKEND_URL}/kb/reset",
                                        params={"collection_name": selected_collection['name']},
                                        headers=get_auth_headers()
                                    )
                                    if response.status_code == 200:
                                        st.success(f"Collection '{selected_collection['name']}' reset!")
                                        # Clear all confirmation states
                                        for key in [reset_confirm_key, reset_double_confirm_key]:
                                            if key in st.session_state:
                                                del st.session_state[key]
                                        st.rerun()
                                    else:
                                        st.error("Reset failed")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                        elif st.session_state.get(reset_confirm_key, False):
                            if st.button("🔄 Reset?", key="reset_second", use_container_width=True):
                                st.session_state[reset_double_confirm_key] = True
                                st.warning("⚠️ FINAL CONFIRMATION: Click 'CONFIRM' to clear all documents!")
                                st.rerun()
                        else:
                            if st.button("🔄 Reset", key="reset_first", use_container_width=True):
                                st.session_state[reset_confirm_key] = True
                                st.warning("⚠️ This will delete all documents! Click again to proceed.")
                                st.rerun()
                    elif not is_user_admin():
                        st.button("🔄 Reset", disabled=True, use_container_width=True, help="Admin access required")
                    else:
                        st.button("🔄 Reset", disabled=True, use_container_width=True, help="No documents to reset")
                
                with action_col4:
                    # Delete Collection with double confirmation - Admin only
                    if is_user_admin():
                        delete_confirm_key = f"delete_confirm_{selected_collection['name']}"
                        delete_double_confirm_key = f"delete_double_confirm_{selected_collection['name']}"
                        
                        if st.session_state.get(delete_double_confirm_key, False):
                            if st.button("🗑️ CONFIRM", key="final_delete", type="secondary", use_container_width=True):
                                success, result = delete_collection(selected_collection['name'], force=True)
                                if success:
                                    st.success(f"Collection '{selected_collection['name']}' deleted!")
                                    # Clear all confirmation states
                                    for key in [delete_confirm_key, delete_double_confirm_key]:
                                        if key in st.session_state:
                                            del st.session_state[key]
                                    st.rerun()
                                else:
                                    st.error(f"Failed to delete: {result}")
                    elif st.session_state.get(delete_confirm_key, False):
                        if st.button("🗑️ Delete?", key="delete_second", type="secondary", use_container_width=True):
                            st.session_state[delete_double_confirm_key] = True
                            st.warning("⚠️ FINAL CONFIRMATION: Click 'CONFIRM' to permanently delete!")
                            st.rerun()
                        else:
                            if st.button("🗑️ Delete", key="delete_first", type="secondary", use_container_width=True):
                                st.session_state[delete_confirm_key] = True
                                st.warning("⚠️ This will permanently delete the collection! Click again to proceed.")
                                st.rerun()
                    else:
                        st.button("🗑️ Delete", disabled=True, type="secondary", use_container_width=True, help="Admin access required")
                
                # Show documents if requested
                if st.session_state.get("show_documents", False) and st.session_state.get("selected_collection_name") == selected_collection['name']:
                    st.markdown("---")
                    st.subheader(f"📄 Documents in '{selected_collection['name']}'")
                    
                    try:
                        response = requests.get(f"{BACKEND_URL}/kb/collections/{selected_collection['name']}", headers=get_auth_headers())
                        if response.status_code == 200:
                            collection_data = response.json()
                            documents = collection_data.get('documents', [])
                            
                            if documents:
                                doc_data = []
                                for doc in documents:
                                    doc_data.append({
                                        "Filename": doc['filename'],
                                        "Size (bytes)": f"{doc.get('size_bytes', 0):,}",
                                        "Chunks": doc.get('chunk_count', 0),
                                        "Status": doc.get('status', 'unknown').title(),
                                        "Uploaded": doc.get('upload_date', 'unknown')[:19] if doc.get('upload_date') else 'Unknown'
                                    })
                                
                                df_documents = pd.DataFrame(doc_data)
                                st.dataframe(df_documents, use_container_width=True)
                                
                                # Close button
                                if st.button("✖️ Close Documents View", key="close_documents"):
                                    st.session_state["show_documents"] = False
                                    st.rerun()
                            else:
                                st.info(f"No documents found in collection '{selected_collection['name']}'")
                                if st.button("✖️ Close", key="close_no_documents"):
                                    st.session_state["show_documents"] = False
                                    st.rerun()
                        else:
                            st.error(f"Failed to fetch documents: {response.status_code}")
                            if st.button("✖️ Close", key="close_error"):
                                st.session_state["show_documents"] = False
                                st.rerun()
                    except Exception as e:
                        st.error(f"Error fetching documents: {str(e)}")
                        if st.button("✖️ Close", key="close_exception"):
                            st.session_state["show_documents"] = False
                            st.rerun()
                
                # Show edit form if requested
                if st.session_state.get("show_edit", False) and st.session_state.get("selected_collection_name") == selected_collection['name']:
                    st.markdown("---")
                    st.subheader(f"✏️ Edit Collection: '{selected_collection['name']}'")
                    
                    with st.form("edit_collection_form"):
                        edit_description = st.text_area(
                            "Description", 
                            value=selected_collection.get('description', ''),
                            help="Update collection description"
                        )
                        edit_tags_input = st.text_input(
                            "Tags (comma-separated)", 
                            value=', '.join(selected_collection.get('tags', [])),
                            help="Update collection tags"
                        )
                        edit_tags = [tag.strip() for tag in edit_tags_input.split(",") if tag.strip()]
                        
                        form_col1, form_col2 = st.columns(2)
                        
                        with form_col1:
                            if st.form_submit_button("💾 Update Collection", type="primary", use_container_width=True):
                                try:
                                    payload = {"description": edit_description, "tags": edit_tags}
                                    response = requests.put(
                                        f"{BACKEND_URL}/kb/collections/{selected_collection['name']}", 
                                        json=payload, 
                                        headers=get_auth_headers()
                                    )
                                    if response.status_code == 200:
                                        st.success(f"Collection '{selected_collection['name']}' updated!")
                                        st.session_state["show_edit"] = False
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to update collection: {response.text}")
                                except Exception as e:
                                    st.error(f"Error updating collection: {str(e)}")
                        
                        with form_col2:
                            if st.form_submit_button("✖️ Cancel", use_container_width=True):
                                st.session_state["show_edit"] = False
                                st.rerun()
        else:
            st.info("No collections found. Create your first collection using the form on the left.")


