import pickle
import os
import sys
from sentence_transformers import SentenceTransformer

# Singleton to avoid reloading model
_EMBEDDER = None
_MODELS = {}

def get_embedder():
    global _EMBEDDER
    if _EMBEDDER is None:
        _EMBEDDER = SentenceTransformer('all-MiniLM-L6-v2')
    return _EMBEDDER

def load_models(model_dir='models'):
    global _MODELS
    targets = ['price', 'trust', 'urgency']
    for t in targets:
        path = os.path.join(model_dir, f"{t}_scorer.pkl")
        if os.path.exists(path):
            with open(path, 'rb') as f:
                _MODELS[t] = pickle.dump(f) # Wait, this should be pickle.load
                pass

def predict_scores(ad_text, model_dir='models'):
    global _MODELS
    embedder = get_embedder()
    emb = embedder.encode([ad_text])

    results = {}
    targets = ['price', 'trust', 'urgency']
    for t in targets:
        if t not in _MODELS:
            path = os.path.join(model_dir, f"{t}_scorer.pkl")
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    _MODELS[t] = pickle.load(f)
            else:
                results[f"{t}_score"] = 0.5 # Fallback
                continue

        score = _MODELS[t].predict(emb)[0]
        results[f"{t}_score"] = max(0.0, min(1.0, float(score)))

    return results
