from fastapi import FastAPI, HTTPException
import os
from langchain_groq import ChatGroq
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

from rag_service import RagService
from structures import *
from ingest import ingest_data

load_dotenv()

qdrant_url = os.getenv("QDRANT_URL")
qdrant_client = QdrantClient(url=qdrant_url)

patch_collection = os.getenv("PATCH_COLLECTION", 'lol_knowledge')
encoder = SentenceTransformer(model_name_or_path=os.getenv('EMBEDDING_MODEL','all-MiniLM-L6-v2'))

groq_api_key = os.getenv('GROQ_API_KEY')
llm_model = ChatGroq(
            temperature=0, 
            groq_api_key=groq_api_key, 
            model_name=os.getenv('LLM_MODEL', 'llama-3.3-70b-versatile')
        )

agent = RagService(qdrant_client, patch_collection, encoder, llm_model)

app = FastAPI(title='lol-agent-api', version='1.0')

@app.get("/")
def read_root():
    return {"status": "LoL RAG System is online"}

@app.post('/add_patch_to_db')
async def add_patch_to_db(request: IngestQuery):
    try:
        results = await ingest_data(qdrant_client, patch_collection, encoder, request.file)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/chat')
def chat_endpoint(request: QueryRequest):
    try:
        # Appel du service
        answer_text, sources = agent.get_answer(request.question)
        
        return QueryResponse(
            answer=answer_text,
            sources=sources
        )
    except Exception as e:
        # Gestion d'erreur propre
        raise HTTPException(status_code=500, detail=str(e))
