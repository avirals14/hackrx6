from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.services.parser import parse_file
from app.services.embedder import generate_embeddings
from app.services.vectorstore import store_in_chroma, get_chroma_collection
from app.services.llm import run_llm_reasoning
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

# Placeholder for /query route
@app.post("/query")
async def process_query(request: QueryRequest):
    try:
        # 1. Parse/structure the query using Gemma (LLM)
        from app.services.llm import run_llm_with_fallback, run_llm_reasoning
        parsing_model = choose_model("parsing")
        parsing_prompt = (
            "Extract the following fields from the query and return as JSON: age, procedure, location, policy_duration_months. "
            "If a field is missing, use null. Query: " + request.query + "\nRespond in JSON only."
        )
        parsing_response = run_llm_with_fallback(parsing_prompt, parsing_model)
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

        # 4. LLM reasoning using LLaMA 3, fallback to Gemma
        reasoning_model = choose_model("reasoning")
        fallback_model = choose_model("parsing")
        llm_response = run_llm_reasoning(structured_query, retrieved_chunks, primary_model=reasoning_model, fallback_model=fallback_model)

        return {
            "structured_query": structured_query,
            "retrieved_chunks": retrieved_chunks,
            "llm_response": llm_response
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)}) 