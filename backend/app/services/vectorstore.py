from typing import List, Dict, Any
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

_collection = None

def get_chroma_collection(collection_name: str = "documents"):
    global _collection
    if _collection is None:
        if not chromadb:
            raise ImportError("chromadb is not installed.")
        client = chromadb.Client(Settings(persist_directory="./chroma_db"))
        _collection = client.get_or_create_collection(collection_name)
    return _collection

def store_in_chroma(chunks_with_embeddings: List[Dict[str, Any]], collection_name: str = "documents"):
    collection = get_chroma_collection(collection_name)
    for idx, chunk in enumerate(chunks_with_embeddings):
        collection.add(
            embeddings=[chunk["embedding"]],
            documents=[chunk["text"]],
            metadatas=[chunk["metadata"]],
            ids=[f"{chunk['metadata']['filename']}_{chunk['metadata']['page']}_{chunk['metadata']['chunk_id']}"]
        )
