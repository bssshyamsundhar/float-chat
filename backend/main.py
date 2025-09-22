#!/usr/bin/env python3
"""
FastAPI Backend for Oceanographic Data Chatbot
Integrates with the existing Python script functionality
"""
import os
import re
import time
import random
import uuid
import asyncio
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2 import pool
import pandas as pd
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from google import genai
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------
# CONFIG
# -----------------------------
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyCEMWD4n6JUClUljshs9xWKMfoEI_oM0TE")
client_gemini = genai.Client(api_key=API_KEY)
MODEL = "gemini-2.0-flash-exp"

DB_CONFIG = {
    "host": "ep-purple-hall-a1c79c5s-pooler.ap-southeast-1.aws.neon.tech",
    "database": "neondb",
    "user": "neondb_owner",
    "password": "npg_6DqyuGdMm4sU",
    "port": 5432,
    "sslmode": "require"
}

# -----------------------------
# Connection pool
# -----------------------------
try:
    pg_pool = psycopg2.pool.SimpleConnectionPool(1, 10, **DB_CONFIG)
    logger.info("✅ Database connection pool initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize database pool: {e}")
    pg_pool = None

# -----------------------------
# Qdrant Setup
# -----------------------------
QDRANT_URL = "https://d6a02d23-c6aa-4d62-8769-8cbf743f03e6.us-west-2-0.aws.cloud.qdrant.io:6333"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.ZPcwpf5JOOmZGxshXp3IGK-i21jKbSMQ7GQDIgd-sRE"

try:
    client_qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("✅ Qdrant client and embedding model initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize Qdrant: {e}")
    client_qdrant = None
    embedding_model = None

SCHEMA_COLLECTION = "schema_collection"
EXAMPLE_COLLECTION = "example_collection"

# -----------------------------
# Table columns mapping
# -----------------------------
TABLE_COLUMNS = {
    "public.profiles": [
        "profile_id", "file_name", "platform_number", "cycle_number",
        "data_mode", "profile_time", "latitude", "longitude"
    ],
    "public.measurements": [
        "measurement_id", "profile_id", "level_index", "pres", "temp",
        "psal", "pres_qc", "temp_qc", "psal_qc", "pres_error", "temp_error", "psal_error"
    ]
}

# -----------------------------
# Pydantic Models
# -----------------------------
class QueryRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None

class QueryResponse(BaseModel):
    response: str
    sql_query: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    clarification_needed: bool = False
    conversation_id: str
    message_type: str = "bot"  # bot, user, system, error

class ChatMessage(BaseModel):
    message: str
    message_type: str
    timestamp: str
    sql_query: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None

# -----------------------------
# Embedding cache
# -----------------------------
embedding_cache = {}

def embed_text(text: str):
    if not embedding_model:
        return None
    if text in embedding_cache:
        return embedding_cache[text]
    vec = embedding_model.encode(text).tolist()
    embedding_cache[text] = vec
    return vec

# -----------------------------
# Qdrant retrieval
# -----------------------------
def retrieve_context(question: str, top_k: int = 3):
    if not client_qdrant or not embedding_model:
        return "Schema retrieval unavailable - using basic context"
    
    try:
        q_vec = embed_text(question)
        if not q_vec:
            return "Embedding generation failed"

        schema_results = client_qdrant.search(
            collection_name=SCHEMA_COLLECTION,
            query_vector=q_vec,
            limit=top_k
        )
        schema_docs = [p.payload.get("text", "") for p in schema_results]

        example_results = client_qdrant.search(
            collection_name=EXAMPLE_COLLECTION,
            query_vector=q_vec,
            limit=top_k
        )
        example_docs = [f"NL: {p.payload['nl']} -> SQL: {p.payload['sql']}" for p in example_results]

        return "\n".join(schema_docs + example_docs)
    except Exception as e:
        logger.error(f"Context retrieval error: {e}")
        return f"Context retrieval error: {str(e)}"

# -----------------------------
# Clarify intent
# -----------------------------
async def clarify_intent(question: str) -> str:
    try:
        context = retrieve_context(question, top_k=2)

        prompt = f"""
You are a database assistant helping users discover oceanographic data.

Schema info:
{context}

User query: "{question}"

Tasks:
1. If the query is incomplete/ambiguous (missing year, region, platform_number, etc.), 
   suggest 1-2 clarifying questions.
2. If the query looks fine, return "CLEAR".
"""

        response = client_gemini.models.generate_content(model=MODEL, contents=prompt)
        return getattr(response, "text", str(response)).strip()
    except Exception as e:
        logger.error(f"Intent clarification error: {e}")
        return "CLEAR"  # Default to proceeding if clarification fails

# -----------------------------
# SQL Extraction Helper
# -----------------------------
def extract_sql(text: str, table_columns: dict = TABLE_COLUMNS, limit: int = 1000) -> str:
    text = re.sub(r"^```sql|```$", "", text.strip(), flags=re.I | re.M)
    sql_match = re.search(r"(SELECT|WITH|INSERT|UPDATE|DELETE|CREATE)\b.*", text, re.I | re.S)
    sql = sql_match.group(0).strip() if sql_match else text.strip()

    # Expand SELECT *
    select_star = re.search(r"SELECT\s+\*\s+FROM\s+([^\s;]+)", sql, re.I)
    if select_star:
        table_name = select_star.group(1)
        cols = table_columns.get(table_name, ["*"])
        col_list = ", ".join(cols)
        sql = re.sub(r"SELECT\s+\*\s+FROM\s+" + re.escape(table_name),
                     f"SELECT {col_list} FROM {table_name}", sql, flags=re.I)

    # Add LIMIT safeguard
    if not re.search(r"LIMIT\s+\d+", sql, re.I) and not re.search(r"GROUP BY|AVG|SUM|MAX|MIN", sql, re.I):
        sql = sql.rstrip(";") + f" LIMIT {limit};"

    return sql

# -----------------------------
# NL → SQL
# -----------------------------
async def nl_to_sql(question: str, retries: int = 3, limit: int = 1000) -> str:
    context = retrieve_context(question, top_k=3)
    prompt = f"""
You are an AI that converts natural-language questions into SQL queries.

Schema & Examples (retrieved from Qdrant Cloud):
{context}

Guidelines:
- Use only valid PostgreSQL syntax.
- Avoid SELECT * on large tables, select only key columns.
- Add LIMIT {limit} to large queries unless aggregation is used.
- Return only the SQL query, no explanation.
- Use fully-qualified table names (public.profiles, public.measurements).
- Use only the column names exactly as given in the schema. Do not invent or guess new columns.
- If the question cannot be answered with the available schema, respond with: "NO_VALID_SQL".
- Do not create new columns or tables that are not present in the schema.
- `platform_number` is the identifier for floats.
- `profile_id` links `profiles` and `measurements`.

Q: {question}
SQL:
"""

    for attempt in range(retries):
        try:
            response = client_gemini.models.generate_content(model=MODEL, contents=prompt)
            raw = getattr(response, "text", str(response))
            return extract_sql(raw, table_columns=TABLE_COLUMNS, limit=limit)
        except Exception as e:
            if "503" in str(e) and attempt < retries - 1:
                wait = (2 ** attempt) + random.random()
                logger.warning(f"Gemini overloaded, retrying in {wait:.1f}s...")
                await asyncio.sleep(wait)
                continue
            logger.error(f"SQL generation error: {e}")
            raise e

# -----------------------------
# Run SQL
# -----------------------------
def run_sql(sql: str):
    if not pg_pool:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    conn = pg_pool.getconn()
    try:
        df = pd.read_sql(sql, conn)
        return df.to_dict('records')
    finally:
        pg_pool.putconn(conn)

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(
    title="Oceanographic Data Chatbot API",
    description="API for querying oceanographic data using natural language",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:3000", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store conversations in memory (in production, use a proper database)
conversations: Dict[str, List[ChatMessage]] = {}

# -----------------------------
# Routes
# -----------------------------
@app.get("/")
async def root():
    return {
        "message": "Oceanographic Data Chatbot API",
        "status": "online",
        "endpoints": ["/query", "/health", "/conversations"]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected" if pg_pool else "disconnected",
        "qdrant": "connected" if client_qdrant else "disconnected",
        "embedding_model": "loaded" if embedding_model else "not loaded"
    }

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    try:
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Initialize conversation if new
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        
        # Add user message to conversation
        user_message = ChatMessage(
            message=request.question,
            message_type="user",
            timestamp=str(int(time.time()))
        )
        conversations[conversation_id].append(user_message)
        
        # Check for clarification
        clarification = await clarify_intent(request.question)
        
        if clarification != "CLEAR":
            bot_message = ChatMessage(
                message=f"🤔 Your query might need clarification:\n\n{clarification}",
                message_type="system",
                timestamp=str(int(time.time()))
            )
            conversations[conversation_id].append(bot_message)
            
            return QueryResponse(
                response=bot_message.message,
                clarification_needed=True,
                conversation_id=conversation_id,
                message_type="system"
            )
        
        # Generate SQL
        sql_query = await nl_to_sql(request.question, limit=500)
        
        if sql_query == "NO_VALID_SQL":
            error_message = "❌ I couldn't generate a valid SQL query for your question. Please try rephrasing or check if you're asking about available data."
            bot_message = ChatMessage(
                message=error_message,
                message_type="error",
                timestamp=str(int(time.time()))
            )
            conversations[conversation_id].append(bot_message)
            
            return QueryResponse(
                response=error_message,
                conversation_id=conversation_id,
                message_type="error"
            )
        
        # Execute SQL
        try:
            data = run_sql(sql_query)
            
            response_text = f"✅ **Query executed successfully!**\n\n**Generated SQL:**\n```sql\n{sql_query}\n```\n\n**Results:** Found {len(data)} records"
            
            if len(data) > 0:
                # Add a sample of the data to the response
                sample_size = min(5, len(data))
                response_text += f" (showing first {sample_size}):"
            
            bot_message = ChatMessage(
                message=response_text,
                message_type="bot",
                timestamp=str(int(time.time())),
                sql_query=sql_query,
                data=data
            )
            conversations[conversation_id].append(bot_message)
            
            return QueryResponse(
                response=response_text,
                sql_query=sql_query,
                data=data,
                conversation_id=conversation_id,
                message_type="bot"
            )
            
        except Exception as e:
            error_message = f"❌ **SQL Execution Error:**\n\n```sql\n{sql_query}\n```\n\n**Error:** {str(e)}"
            bot_message = ChatMessage(
                message=error_message,
                message_type="error",
                timestamp=str(int(time.time())),
                sql_query=sql_query
            )
            conversations[conversation_id].append(bot_message)
            
            return QueryResponse(
                response=error_message,
                sql_query=sql_query,
                conversation_id=conversation_id,
                message_type="error"
            )
            
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        error_message = f"❌ **System Error:** {str(e)}"
        return QueryResponse(
            response=error_message,
            conversation_id=conversation_id or str(uuid.uuid4()),
            message_type="error"
        )

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation_id": conversation_id, "messages": conversations[conversation_id]}

@app.get("/conversations")
async def list_conversations():
    return {"conversations": list(conversations.keys())}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)