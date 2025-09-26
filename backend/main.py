"""
FastAPI Backend for Oceanographic Data Chatbot
Integrated with frontend logic for Run Anyway / Refine
"""
import os
import re
import time
import uuid
import random
import asyncio
from typing import List, Dict, Any, Optional
import json
import psycopg2
from psycopg2 import pool
import pandas as pd
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from google import genai

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import datetime

# -----------------------------
# Logging
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------
# Config
# -----------------------------
API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_DEFAULT_KEY_HERE")
client_gemini = genai.Client(api_key="AIzaSyCEMWD4n6JUClUljshs9xWKMfoEI_oM0TE")
MODEL = "gemini-2.5-flash"

DB_CONFIG = {
    "host": "ep-purple-hall-a1c79c5s-pooler.ap-southeast-1.aws.neon.tech",
    "database": "neondb",
    "user": "neondb_owner",
    "password": "npg_6DqyuGdMm4sU",
    "port": 5432,
    "sslmode": "require"
}

# -----------------------------
# PostgreSQL connection pool
# -----------------------------
try:
    pg_pool = psycopg2.pool.SimpleConnectionPool(1, 10, **DB_CONFIG)
    logger.info("✅ Database connection pool initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize DB pool: {e}")
    pg_pool = None

# -----------------------------
# Qdrant + embeddings
# -----------------------------
QDRANT_URL = "https://d6a02d23-c6aa-4d62-8769-8cbf743f03e6.us-west-2-0.aws.cloud.qdrant.io:6333"
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")

try:
    client_qdrant = QdrantClient(url=QDRANT_URL, api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.ZPcwpf5JOOmZGxshXp3IGK-i21jKbSMQ7GQDIgd-sRE")
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("✅ Qdrant client + embeddings ready")
except Exception as e:
    logger.error(f"❌ Failed to init Qdrant: {e}")
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
# Pydantic models
# -----------------------------
class QueryRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    override: Optional[bool] = False
    sql_query: Optional[str] = None 
    
class QueryResponse(BaseModel):
    response: str
    sql_query: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    clarification_needed: bool = False
    conversation_id: str
    message_type: str = "bot"

class ChatMessage(BaseModel):
    message: str
    message_type: str
    timestamp: str
    sql_query: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None

# -----------------------------
# Embedding helper
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

def retrieve_context(question: str, top_k: int = 3) -> str:
    if not client_qdrant or not embedding_model:
        return "Schema retrieval unavailable - using basic context"
    try:
        q_vec = embed_text(question)
        if not q_vec:
            return "Embedding failed"
        schema_results = client_qdrant.search(collection_name=SCHEMA_COLLECTION, query_vector=q_vec, limit=top_k)
        schema_docs = [p.payload.get("text", "") for p in schema_results]
        example_results = client_qdrant.search(collection_name=EXAMPLE_COLLECTION, query_vector=q_vec, limit=top_k)
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
You are a database assistant.

Schema info:
{context}

User query: "{question}"

If the query is incomplete or ambiguous, suggest clarifying questions (1-2 max). 
Otherwise, return "CLEAR".
"""
        response = client_gemini.models.generate_content(model=MODEL, contents=prompt)
        return getattr(response, "text", str(response)).strip()
    except Exception as e:
        logger.error(f"Clarification error: {e}")
        return "CLEAR"

# -----------------------------
# NL → SQL
# -----------------------------
def extract_sql(text: str, table_columns: dict = TABLE_COLUMNS, limit: int = 500) -> str:
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

    # Add LIMIT
    if not re.search(r"LIMIT\s+\d+", sql, re.I) and not re.search(r"GROUP BY|AVG|SUM|MAX|MIN", sql, re.I):
        sql = sql.rstrip(";") + f" LIMIT {limit};"
    return sql

async def nl_to_sql(question: str, retries: int = 3, limit: int = 500) -> str:
    context = retrieve_context(question)
    prompt = f"""
Convert NL to SQL.

Schema & Examples:
{context}

Guidelines:
- Use valid PostgreSQL syntax.
- Avoid SELECT * on large tables; select key columns.
- Add LIMIT {limit} unless aggregation is used.
- Return only SQL, no explanation.
- Use fully-qualified table names.
- Columns exactly as in schema.
- If query cannot be answered, return "NO_VALID_SQL".
- platform_number identifies floats; profile_id links profiles and measurements.

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
                await asyncio.sleep(wait)
                continue
            raise e
    return "NO_VALID_SQL"

# -----------------------------
# Run SQL
# -----------------------------
def run_sql(sql: str):
    if not pg_pool:
        raise HTTPException(status_code=500, detail="DB connection unavailable")
    conn = pg_pool.getconn()
    try:
        df = pd.read_sql(sql, conn)
        return df.to_dict("records")
    finally:
        pg_pool.putconn(conn)

LOG_FILE = "nl_sql_log.jsonl"

LOG_FILE = "nl_sql_log.jsonl"

def log_query(nl_query, sql_query, success, error_msg=None, rows_returned=None, result=None):
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "nl_query": nl_query,
        "sql_query": sql_query,
        "success": success,
        "error": error_msg,
        "rows_returned": rows_returned,
        "result": result if result is not None else None
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(title="Oceanographic Data Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # frontend dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

conversations: Dict[str, List[ChatMessage]] = {}

# -----------------------------
# Routes
# -----------------------------
@app.get("/")
async def root():
    return {"message": "Oceanographic Data Chatbot API", "status": "online"}

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
        if conversation_id not in conversations:
            conversations[conversation_id] = []

        user_msg = ChatMessage(
            message=request.question,
            message_type="user",
            timestamp=str(int(time.time()))
        )
        conversations[conversation_id].append(user_msg)

        clarification = "CLEAR" if request.override else await clarify_intent(request.question)

        if clarification != "CLEAR":
            sql_query = await nl_to_sql(request.question, limit=500)
            bot_msg = ChatMessage(
                message=f"🤔 Your query might need clarification:\n\n{clarification}\n\n👉 You can refine OR run as-is.",
                message_type="system",
                timestamp=str(int(time.time())),
                sql_query=sql_query
            )
            conversations[conversation_id].append(bot_msg)

            # 🔹 Log clarification stage
            log_query(
                nl_query=request.question,
                sql_query=sql_query,
                success=False,
                error_msg="Clarification needed",
                result=None
            )

            return QueryResponse(
                response=bot_msg.message,
                clarification_needed=True,
                sql_query=sql_query,
                conversation_id=conversation_id,
                message_type="system"
            )

        # ✅ Respect frontend override
        if request.override and request.sql_query:
            sql_query = request.sql_query
        else:
            sql_query = await nl_to_sql(request.question, limit=500)

        if sql_query == "NO_VALID_SQL":
            # 🔹 Log invalid SQL
            log_query(
                nl_query=request.question,
                sql_query=None,
                success=False,
                error_msg="NO_VALID_SQL",
                result=None
            )
            return QueryResponse(
                response="❌ I couldn't generate a valid SQL query.",
                conversation_id=conversation_id,
                message_type="error"
            )

        data = run_sql(sql_query)

        # 🔹 Log successful query
        log_query(
            nl_query=request.question,
            sql_query=sql_query,
            success=True,
            rows_returned=len(data),
            result=data   # ✅ store actual results here
        )

        response_text = f"✅ **Query executed successfully!**\n```sql\n{sql_query}\n```\nFound {len(data)} records"

        bot_msg = ChatMessage(
            message=response_text,
            message_type="bot",
            timestamp=str(int(time.time())),
            sql_query=sql_query,
            data=data
        )
        conversations[conversation_id].append(bot_msg)

        return QueryResponse(
            response=response_text,
            sql_query=sql_query,
            data=data,
            conversation_id=conversation_id,
            message_type="bot"
        )

    except Exception as e:
        logger.error(f"Query processing error: {e}")

        # 🔹 Log error case
        log_query(
            nl_query=request.question,
            sql_query=request.sql_query,
            success=False,
            error_msg=str(e),
            result=None
        )

        return QueryResponse(
            response=f"❌ System Error: {str(e)}",
            conversation_id=request.conversation_id or str(uuid.uuid4()),
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
