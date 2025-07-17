from typing import List

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

_model = None

def get_model():
    global _model
    if _model is None:
        if not SentenceTransformer:
            raise ImportError("sentence-transformers is not installed.")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    model = get_model()
    return model.encode(texts, convert_to_numpy=True).tolist()
