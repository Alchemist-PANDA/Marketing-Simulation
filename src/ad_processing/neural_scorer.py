"""
Neural scoring module with embedding caching.
Uses sentence-transformers for ad text scoring with LRU cache
to avoid redundant re-encoding on UI interactions.
"""

import pickle
import os
import logging
from functools import lru_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_EMBEDDER = None
_MODELS = {}


def get_embedder():
    global _EMBEDDER
    if _EMBEDDER is None:
        try:
            from sentence_transformers import SentenceTransformer
            _EMBEDDER = SentenceTransformer('all-MiniLM-L6-v2')
        except (ImportError, Exception) as e:
            logger.warning(f"Could not load SentenceTransformer: {e}. Neural scoring disabled.")
            _EMBEDDER = False
    return _EMBEDDER


def _load_models(model_dir='models'):
    global _MODELS
    if _MODELS:
        return
    targets = ['price', 'trust', 'urgency']
    for t in targets:
        path = os.path.join(model_dir, f"{t}_scorer.pkl")
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    _MODELS[t] = pickle.load(f)
            except Exception as e:
                logger.error(f"Error loading model {path}: {e}")
                _MODELS[t] = None
        else:
            _MODELS[t] = None


@lru_cache(maxsize=256)
def _cached_encode(text: str):
    """Cache embeddings by text content to avoid re-encoding on slider changes."""
    embedder = get_embedder()
    if not embedder:
        return None
    try:
        return tuple(embedder.encode([text])[0])
    except Exception as e:
        logger.error(f"Error encoding text: {e}")
        return None


def predict_scores(ad_text: str, model_dir: str = 'models') -> dict:
    global _MODELS

    embedding_tuple = _cached_encode(ad_text)

    if embedding_tuple is None:
        return {"price_score": 0.5, "trust_score": 0.5, "urgency_score": 0.5}

    import numpy as np
    emb = np.array([list(embedding_tuple)])

    _load_models(model_dir)

    results = {}
    targets = ['price', 'trust', 'urgency']
    for t in targets:
        model = _MODELS.get(t)
        if model is not None:
            try:
                score = model.predict(emb)[0]
                results[f"{t}_score"] = max(0.0, min(1.0, float(score)))
            except Exception as e:
                logger.error(f"Error predicting with model {t}: {e}")
                results[f"{t}_score"] = 0.5
        else:
            results[f"{t}_score"] = 0.5

    return results
