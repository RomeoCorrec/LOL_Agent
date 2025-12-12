from pydantic import BaseModel
from typing import List, Optional
from qdrant_client import QdrantClient

class IngestQuery(BaseModel):
    file: str
    patch_collection: str = 'lol_knowledge'

class Source(BaseModel):
    entity: str
    patch: str
    content: str

class QueryRequest(BaseModel):
    question: str
    role: Optional[str] = "general" # ex: "jungle", "top", ou "general"

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source] = []