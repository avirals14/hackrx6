from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.services.parser import parse_file
from app.services.embedder import generate_embeddings
from app.services.vectorstore import store_in_chroma, get_chroma_collection
from app.services.llm import run_llm_with_priority
from app.services.model_router import choose_model
import json
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://policylensapp.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Placeholder for /upload route
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_bytes = await file.read()
    try:
        chunks = parse_file(file_bytes, file.filename)
        texts = [chunk["text"] for chunk in chunks]
        embeddings = generate_embeddings(texts)
        chunks_with_embeddings = []
        for chunk, embedding in zip(chunks, embeddings):
            chunk_with_embedding = chunk.copy()
            chunk_with_embedding["embedding"] = embedding
            chunks_with_embeddings.append(chunk_with_embedding)
        store_in_chroma(chunks_with_embeddings)
        return {"message": "File processed, embedded, and stored.", "num_chunks": len(chunks)}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

# Request model for /query
class QueryRequest(BaseModel):
    query: str

# Add a helper to safely parse and validate the LLM response

def safe_parse_llm_response(response):
    try:
        data = json.loads(response)
        # Ensure all required fields are present
        for field in ["decision", "amount", "justification", "summary", "clauses_used", "confidence"]:
            if field not in data:
                raise ValueError("Missing field")
        return data
    except Exception:
        # Fallback/default response
        return {
            "decision": "needs more info",
            "amount": 0,
            "justification": "The LLM response was incomplete or invalid. Manual review required.",
            "clauses_used": [],
            "summary": "Unable to determine decision automatically.",
            "confidence": 0.0
        }

# Placeholder for /query route
@app.post("/query")
async def process_query(request: QueryRequest):
    try:
        # 1. Parse/structure the query using LLM priority (OpenAI > Gemini > Ollama)
        parsing_prompt = (
            "Extract the following fields from the query and return as JSON: age, gender, procedure, location, policy_duration_months, policy_name, policy_id. "
            "If a field is missing, use null. Query: " + request.query + "\nRespond in JSON only."
        )
        parsing_response = run_llm_with_priority(parsing_prompt)
        try:
            structured_query = json.loads(parsing_response)
        except Exception:
            structured_query = {"raw_query": request.query, "llm_parse": parsing_response}

        # 2. Embed the query
        query_embedding = generate_embeddings([request.query])[0]

        # 3. Retrieve relevant chunks from ChromaDB
        collection = get_chroma_collection()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5,
            include=["documents", "metadatas"]
        )
        retrieved_chunks = [
            {"text": doc, "metadata": meta}
            for doc, meta in zip(results["documents"][0], results["metadatas"][0])
        ]

        # 4. Reasoning using LLM priority (OpenAI > Gemini > Ollama) with improved prompt
        from app.services.llm import build_reasoning_prompt
        reasoning_prompt = build_reasoning_prompt(structured_query, retrieved_chunks)
        llm_response = run_llm_with_priority(reasoning_prompt)
        llm_response = safe_parse_llm_response(llm_response)

        return {
            "structured_query": structured_query,
            "retrieved_chunks": retrieved_chunks,
            "llm_response": llm_response
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)}) 