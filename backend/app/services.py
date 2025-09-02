# backend/app/services.py
# This file contains the business logic for interacting with AI models and the vector DB.
from .settings import settings
import ollama
import qdrant_client
from qdrant_client.http.models import PointStruct, UpdateStatus, VectorParams, Distance
import uuid

# Initialize clients
ollama_client = ollama.Client(host=settings.OLLAMA_BASE_URL)
qdrant_client = qdrant_client.QdrantClient(url=settings.QDRANT_URL)

# Mock database for projects
mock_projects_db = [
    {"name": "Project Alpha", "description": "AI-driven data analysis platform."},
    {"name": "Project Beta", "description": "Compliance and audit automation tool."}
]

def get_projects_from_db():
    return mock_projects_db

def create_project_in_db(project):
    mock_projects_db.append(project.dict())
    return {"status": "success", "project": project}

def add_document_to_kb(doc):
    try:
        embedding = ollama_client.embeddings(
            model=settings.EMBEDDING_MODEL,
            prompt=doc.content
        )['embedding']

        qdrant_client.recreate_collection(
            collection_name=doc.collection_name,
            vectors_config=VectorParams(size=len(embedding), distance=Distance.COSINE)
        )

        operation_info = qdrant_client.upsert(
            collection_name=doc.collection_name,
            wait=True,
            points=[
                PointStruct(id=str(uuid.uuid4()), vector=embedding, payload={"content": doc.content})
            ]
        )
        return {"status": "success", "info": str(operation_info)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def query_knowledge_base(query):
    try:
        query_embedding = ollama_client.embeddings(
            model=settings.EMBEDDING_MODEL,
            prompt=query.query
        )['embedding']

        search_result = qdrant_client.search(
            collection_name="default_collection",
            query_vector=query_embedding,
            limit=3
        )
        
        context = " ".join([hit.payload['content'] for hit in search_result]) if search_result else "No context found."

        prompt = f"Using the following context, answer the question.\n\nContext: {context}\n\nQuestion: {query.query}"
        
        response = ollama_client.chat(
            model=settings.GENERAL_PURPOSE_LLM,
            messages=[{'role': 'user', 'content': prompt}]
        )
        
        return response['message']['content']
    except Exception as e:
        return f"An error occurred: {str(e)}"

