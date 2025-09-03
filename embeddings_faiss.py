import os, json
from typing import List, Dict, Tuple
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np

DATA_DIR = os.getenv("DATA_DIR", "data")
INDEX_DIR = os.path.join(DATA_DIR, "indexes")
os.makedirs(INDEX_DIR, exist_ok=True)

EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

_model = None
def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    return _model

def embed_texts(texts: List[str]) -> np.ndarray:
    model = get_model()
    embs = model.encode(texts, batch_size=64, show_progress_bar=False, normalize_embeddings=True)
    return np.array(embs, dtype="float32")

def _index_paths(insurer_key: str) -> Tuple[str, str]:
    base = os.path.join(INDEX_DIR, insurer_key)
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "faiss.index"), os.path.join(base, "meta.json")

def save_index(insurer_key: str, texts: List[str], embeddings: np.ndarray):
    index_path, meta_path = _index_paths(insurer_key)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine (with normalized embeddings)
    index.add(embeddings)
    faiss.write_index(index, index_path)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"texts": texts}, f, ensure_ascii=False)

def load_index(insurer_key: str):
    index_path, meta_path = _index_paths(insurer_key)
    if not (os.path.exists(index_path) and os.path.exists(meta_path)):
        return None, None
    index = faiss.read_index(index_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    return index, meta["texts"]

def ensure_index(insurer_key: str, passages: List[str]):
    index, texts = load_index(insurer_key)
    if index is not None and texts and len(texts) == len(passages):
        return index, texts
    # (Re)build index
    embeddings = embed_texts(passages)
    save_index(insurer_key, passages, embeddings)
    index, texts = load_index(insurer_key)
    return index, texts

def search(index, texts: List[str], query: str, k: int = 8) -> List[Tuple[float, str]]:
    q_emb = embed_texts([query])  # 1 x d
    scores, ids = index.search(q_emb, k)
    out = []
    for s, i in zip(scores[0], ids[0]):
        if i == -1: continue
        out.append((float(s), texts[i]))
    return out
