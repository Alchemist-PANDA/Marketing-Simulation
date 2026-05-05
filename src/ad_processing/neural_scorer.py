import pickle
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Singleton to avoid reloading model
_EMBEDDER = None
_MODELS = {}

def get_embedder():
    global _EMBEDDER
    if _EMBEDDER is None:
        try:
            from sentence_transformers import SentenceTransformer
            _EMBEDDER = SentenceTransformer('all-MiniLM-L6-v2')
        except (ImportError, Exception) as e:
            logger.warning(f"Could not load SentenceTransformer: {e}. Neural scoring will be disabled.")
            _EMBEDDER = False
    return _EMBEDDER

def load_models(model_dir='models'):
    global _MODELS
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

def predict_scores(ad_text, model_dir='models'):
    global _MODELS
    embedder = get_embedder()

    # Fallback if embedder is not available
    if not embedder:
        return {
            "price_score": 0.5,
            "trust_score": 0.5,
            "urgency_score": 0.5
        }

    try:
        emb = embedder.encode([ad_text])
    except Exception as e:
        logger.error(f"Error encoding text: {e}")
        return {
            "price_score": 0.5,
            "trust_score": 0.5,
            "urgency_score": 0.5
        }

    results = {}
    targets = ['price', 'trust', 'urgency']
    for t in targets:
        # Load model if not already in memory
        if t not in _MODELS or _MODELS[t] is None:
            path = os.path.join(model_dir, f"{t}_scorer.pkl")
            if os.path.exists(path):
                try:
                    with open(path, 'rb') as f:
                        _MODELS[t] = pickle.load(f)
                except Exception as e:
                    logger.error(f"Error loading model {path} during prediction: {e}")
                    _MODELS[t] = None
            else:
                _MODELS[t] = None

        # Predict if model exists, else fallback
        if _MODELS[t] is not None:
            try:
                score = _MODELS[t].predict(emb)[0]
                results[f"{t}_score"] = max(0.0, min(1.0, float(score)))
            except Exception as e:
                logger.error(f"Error predicting with model {t}: {e}")
                results[f"{t}_score"] = 0.5
        else:
            results[f"{t}_score"] = 0.5

    return results
