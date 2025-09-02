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
                status_placeholder.write(f"Processing {uploaded_file.name}...")
                
                try:
                    # Prepare file for upload
                    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                    data = {"collection_name": collection_name}
                    
                    response = requests.post(
                        f"{BACKEND_URL}/kb/upload",
                        files=files,
                        data=data,
                        headers=get_auth_headers()
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
                
                except Exception as e:
                    results.append({
                        "filename": uploaded_file.name,
                        "status": f"❌ Error: {str(e)}",
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
        if available_collections and st.button("💾 Set Default", type="primary"):
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
    
    st.markdown("---")
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        
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
    
    with col2:
        st.subheader("📋 Existing Collections")
        
        if collections:
            for collection in collections:
                with st.expander(f"🗂️ **{collection['name']}**" + (" (Default)" if collection.get('is_default') else "")):
                    col_info1, col_info2 = st.columns(2)
                    
                    with col_info1:
                        st.write(f"**Description:** {collection.get('description', 'No description')}")
                        st.write(f"**Created by:** {collection.get('created_by', 'Unknown')}")
                        st.write(f"**Created:** {collection.get('created_date', 'Unknown')[:10] if collection.get('created_date') else 'Unknown'}")
                    
                    with col_info2:
                        st.write(f"**Documents:** {collection.get('document_count', 0)}")
                        st.write(f"**Size:** {collection.get('total_size_mb', 0)} MB")
                        st.write(f"**Tags:** {', '.join(collection.get('tags', [])) if collection.get('tags') else 'None'}")
                    
                    # Action buttons
                    action_col1, action_col2, action_col3 = st.columns(3)
                    
                    with action_col1:
                        if st.button(f"📄 View Documents", key=f"view_{collection['name']}"):
                            # Fetch and display documents in this collection
                            try:
                                response = requests.get(f"{BACKEND_URL}/kb/collections/{collection['name']}", headers=get_auth_headers())
                                if response.status_code == 200:
                                    collection_data = response.json()
                                    documents = collection_data.get('documents', [])
                                    
                                    if documents:
                                        st.write(f"**Documents in '{collection['name']}':**")
                                        for i, doc in enumerate(documents, 1):
                                            st.write(f"{i}. **{doc['filename']}** ({doc.get('size_bytes', 0)} bytes, {doc.get('chunk_count', 0)} chunks)")
                                            st.write(f"   - Status: {doc.get('status', 'unknown')}")
                                            st.write(f"   - Uploaded: {doc.get('upload_date', 'unknown')[:19] if doc.get('upload_date') else 'unknown'}")
                                    else:
                                        st.info(f"No documents found in collection '{collection['name']}'")
                                else:
                                    st.error(f"Failed to fetch documents: {response.status_code}")
                            except Exception as e:
                                st.error(f"Error fetching documents: {str(e)}")
                    
                    with action_col2:
                        if st.button(f"🗑️ Delete", key=f"delete_{collection['name']}", type="secondary"):
                            if st.session_state.get(f"confirm_delete_{collection['name']}", False):
                                success, result = delete_collection(collection['name'], force=True)
                                if success:
                                    st.success(f"Collection '{collection['name']}' deleted!")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to delete: {result}")
                            else:
                                st.session_state[f"confirm_delete_{collection['name']}"] = True
                                st.warning("Click again to confirm deletion!")
                    
                    with action_col3:
                        if collection.get('document_count', 0) > 0:
                            if st.button(f"🔄 Reset", key=f"reset_{collection['name']}"):
                                try:
                                    response = requests.post(
                                        f"{BACKEND_URL}/kb/reset",
                                        params={"collection_name": collection['name']},
                                        headers=get_auth_headers()
                                    )
                                    if response.status_code == 200:
                                        st.success(f"Collection '{collection['name']}' reset!")
                                        st.rerun()
                                    else:
                                        st.error("Reset failed")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
        else:
            st.info("No collections found. Create your first collection using the form on the left.")


