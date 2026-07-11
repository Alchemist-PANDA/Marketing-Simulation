"""
Creative Ranker — learned pairwise model trained on real TikTok Creative
Center outcomes (CTR percentile tiers).

This replaces hand-tuned keyword weights as the decision signal for
"which creative wins". The agent simulation stays as the explanation and
population-texture layer; this model supplies the calibrated ranking.

Features (all available in-app at prediction time):
- MiniLM sentence embedding, PCA-reduced (components stored in artifact)
- 22 engineered copy features
- campaign objective one-hot (user selects objective in the app)
- industry hash one-hot (from brand profile / user input)
- log video duration

Public API:
    score_ad(text, objective="", industry="", duration=0.0,
             visual_quality=None) -> quality in [0,1]
    compare(text_a, text_b, ...)  -> dict(winner, prob_a, confidence, called)
    is_available()                -> bool

Trainer (validation_data/train_ranker.py) imports the feature functions from
here so app and training can never drift apart.
"""

import os
import re
from functools import lru_cache

import numpy as np

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "models", "creative_ranker.joblib",
)

EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF"
    "\U00002190-\U000021FF\U00002B00-\U00002BFF]"
)

URGENCY_TERMS = ["limited", "now", "today", "last chance", "hurry", "ends",
                 "don't miss", "final", "sale", "deadline", "expires"]
SOCIAL_TERMS = ["review", "rated", "trusted", "millions", "customers",
                "viral", "everyone", "tiktokmademebuyit", "best"]
PRICE_TERMS = ["% off", "discount", "free", "deal", "save", "$", "price",
               "cheap", "sale", "off"]
CTA_TERMS = ["shop now", "buy now", "order", "get yours", "link in bio",
             "download", "sign up", "book", "grab", "claim", "try"]

FEATURE_NAMES = [
    "char_len", "word_count", "avg_word_len", "hashtag_count", "mention_count",
    "emoji_count", "emoji_density", "exclaim_count", "question_count",
    "digit_count", "pct_count", "caps_ratio", "urgency_hits", "social_hits",
    "price_hits", "cta_hits", "first_person", "second_person",
    "starts_engaging", "sentence_count", "all_caps_words", "ellipsis",
]

OBJECTIVE_VOCAB = ["Traffic", "App Installs", "Conversions", "Video Views",
                   "Reach", "Lead Generation", "Product Sales"]
N_INDUSTRY_HASH = 16

# app objective names -> TikTok Creative Center vocabulary
APP_OBJECTIVE_MAP = {
    "conversions": "Conversions",
    "conversion_rate": "Conversions",
    "engagement": "Video Views",
    "likes": "Video Views",
    "shares": "Reach",
    "ctr": "Traffic",
    "traffic": "Traffic",
    "leads": "Lead Generation",
    "sales": "Product Sales",
}


class ProbaEnsemble:
    """Average predicted probabilities of several fitted classifiers.

    Lives here (not in the training script) so joblib artifacts that pickle
    an ensemble can always be loaded by the app.
    """

    def __init__(self, models):
        self.models = models

    def predict_proba(self, X):
        ps = [m.predict_proba(X) for m in self.models]
        return np.mean(ps, axis=0)

    def score(self, X, y):
        pred = (self.predict_proba(X)[:, 1] >= 0.5).astype(int)
        return float((pred == np.asarray(y)).mean())


def engineered_features(text: str) -> np.ndarray:
    t = (text or "").strip()
    tl = t.lower()
    words = t.split()
    n_words = max(1, len(words))
    hashtags = tl.count("#")
    mentions = tl.count("@")
    emojis = len(EMOJI_RE.findall(t))
    caps_words = sum(1 for w in words if len(w) > 2 and w.isupper())
    first_word_engaging = 1.0 if words and (
        words[0].lower() in {"pov", "when", "this", "how", "why", "stop",
                             "wait", "imagine", "warning"}
        or "?" in words[0]
    ) else 0.0
    return np.array([
        len(t),
        len(words),
        sum(len(w) for w in words) / n_words,
        hashtags,
        mentions,
        emojis,
        emojis / n_words,
        t.count("!"),
        t.count("?"),
        sum(c.isdigit() for c in t),
        len(re.findall(r"\d+%", t)),
        sum(c.isupper() for c in t) / max(1, len(t)),
        sum(1 for k in URGENCY_TERMS if k in tl),
        sum(1 for k in SOCIAL_TERMS if k in tl),
        sum(1 for k in PRICE_TERMS if k in tl),
        sum(1 for k in CTA_TERMS if k in tl),
        len(re.findall(r"\b(i|my|me|we|our)\b", tl)),
        len(re.findall(r"\b(you|your)\b", tl)),
        first_word_engaging,
        max(1, len(re.split(r"[.!?]+", t))),
        caps_words,
        1.0 if "..." in t or "…" in t else 0.0,
    ], dtype=np.float32)


def context_features(objective: str = "", industry: str = "",
                     duration: float = 0.0) -> np.ndarray:
    """Objective one-hot + industry hash one-hot + log duration.

    NOTE: not used by the deployable model — when a user compares two
    creatives for the same campaign, objective/industry are identical on
    both sides and cancel out of the pairwise diff. Kept for research use.
    """
    import hashlib
    obj = APP_OBJECTIVE_MAP.get((objective or "").lower(), objective)
    obj_vec = np.zeros(len(OBJECTIVE_VOCAB) + 1, dtype=np.float32)
    if obj in OBJECTIVE_VOCAB:
        obj_vec[OBJECTIVE_VOCAB.index(obj)] = 1.0
    else:
        obj_vec[-1] = 1.0
    ind_vec = np.zeros(N_INDUSTRY_HASH, dtype=np.float32)
    if industry:
        h = int(hashlib.md5(industry.strip().lower().encode()).hexdigest(), 16)
        ind_vec[h % N_INDUSTRY_HASH] = 1.0
    dur = np.array([np.log1p(max(0.0, float(duration or 0.0)))],
                   dtype=np.float32)
    return np.concatenate([obj_vec, ind_vec, dur])


VISUAL_KEYS = ["vf_brightness", "vf_contrast", "vf_colorfulness",
               "vf_edge_density", "vf_aspect", "vf_quality"]


def visual_vector(report: "dict | None", artifact: "dict | None" = None) -> np.ndarray:
    """7-dim visual vector: 6 features + availability flag.

    ``report`` is the dict produced by visual_features.image_features /
    video_features (or a row of visual_features.csv). Missing/unavailable
    -> artifact's stored training means with flag 0, so absent visuals are
    neutral rather than misleading.
    """
    if report and (report.get("available", True)):
        vals = []
        key_alias = {
            "vf_brightness": "brightness", "vf_contrast": "contrast",
            "vf_colorfulness": "colorfulness", "vf_edge_density": "edge_density",
            "vf_aspect": "aspect_ratio", "vf_quality": "visual_quality",
        }
        ok = True
        for k in VISUAL_KEYS:
            v = report.get(k, report.get(key_alias[k]))
            if v is None:
                ok = False
                break
            vals.append(float(v))
        if ok:
            return np.array(vals + [1.0], dtype=np.float32)
    if artifact is not None and "visual_mean" in artifact:
        return np.concatenate([artifact["visual_mean"],
                               np.array([0.0], dtype=np.float32)])
    return np.array([0.5, 0.35, 0.35, 0.25, 1.4, 0.6, 0.0], dtype=np.float32)


def reduce_embedding(emb: np.ndarray, artifact: dict) -> np.ndarray:
    """Apply the artifact's stored PCA projection to a raw embedding."""
    mean = artifact["pca_mean"]
    comps = artifact["pca_components"]
    return ((emb - mean) @ comps.T).astype(np.float32)


@lru_cache(maxsize=1)
def _load_artifact():
    try:
        import joblib
        if not os.path.exists(MODEL_PATH):
            return None
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


@lru_cache(maxsize=1)
def _load_embedder():
    try:
        from sentence_transformers import SentenceTransformer
        art = _load_artifact()
        name = (art or {}).get(
            "embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
        return SentenceTransformer(name)
    except Exception:
        return None


def is_available() -> bool:
    art = _load_artifact()
    return art is not None and "pca_components" in art \
        and _load_embedder() is not None


def _features(text: str, duration: float = 0.0, visual: "dict | None" = None):
    """Deployable feature vector: PCA embedding + copy features +
    log duration + visual vector. Everything here is known in-app."""
    art = _load_artifact()
    emb_model = _load_embedder()
    if art is None or emb_model is None:
        return None
    emb = _embed_cached(text)
    return np.concatenate([
        reduce_embedding(emb, art),
        engineered_features(text),
        np.array([np.log1p(max(0.0, float(duration or 0.0)))], dtype=np.float32),
        visual_vector(visual, art),
    ]).astype(np.float32)


@lru_cache(maxsize=512)
def _embed_cached(text: str):
    return _load_embedder().encode([text], normalize_embeddings=True)[0]


def _pair_prob(feat_a: np.ndarray, feat_b: np.ndarray) -> float:
    """Calibrated P(A beats B). Feature layout: [diff, |diff|]."""
    art = _load_artifact()
    d = feat_a - feat_b
    x = art["scaler"].transform(
        np.concatenate([d, np.abs(d)]).reshape(1, -1))
    p = float(art["model"].predict_proba(x)[0, 1])
    iso = art.get("iso")
    if iso is not None:
        p = float(iso.predict([p])[0])
    return min(max(p, 0.0), 1.0)


def score_ad(text: str, objective: str = "", industry: str = "",
             duration: float = 0.0,
             visual: "dict | None" = None,
             visual_quality: "float | None" = None) -> float:
    """Quality in [0,1]: calibrated P(this ad beats the average corpus ad).

    ``objective``/``industry`` are accepted for API stability but unused —
    they cancel out of same-campaign comparisons (see context_features).
    ``visual`` is a feature dict from visual_features; ``visual_quality``
    is a legacy scalar fallback."""
    if visual is None and visual_quality is not None:
        visual = {"visual_quality": float(visual_quality), "available": True,
                  "brightness": 0.5, "contrast": 0.35, "colorfulness": 0.35,
                  "edge_density": 0.25, "aspect_ratio": 1.4}
    art = _load_artifact()
    feat = _features(text, duration, visual) if text else None
    if art is None or feat is None or "mean_feat" not in art:
        return 0.5
    return _pair_prob(feat, art["mean_feat"])


def compare(text_a: str, text_b: str, objective: str = "",
            industry: str = "", duration_a: float = 0.0,
            duration_b: float = 0.0,
            visual_a: "dict | None" = None,
            visual_b: "dict | None" = None) -> dict:
    """Head-to-head verdict with calibrated confidence and abstention.

    Probability is averaged over both orderings — the trainer evaluates
    with this exact protocol so deployed behavior matches the validation."""
    art = _load_artifact()
    fa = _features(text_a, duration_a, visual_a)
    fb = _features(text_b, duration_b, visual_b)
    if art is None or fa is None or fb is None:
        return {"available": False, "winner": None, "prob_a": 0.5,
                "confidence": 0.0, "called": False, "threshold": None}
    p_ab = _pair_prob(fa, fb)
    p_ba = _pair_prob(fb, fa)
    prob_a = (p_ab + (1.0 - p_ba)) / 2.0
    threshold = float(art.get("threshold", 0.65))
    confidence = max(prob_a, 1.0 - prob_a)
    return {
        "available": True,
        "winner": "A" if prob_a >= 0.5 else "B",
        "prob_a": round(prob_a, 4),
        "confidence": round(confidence, 4),
        "called": confidence >= threshold,
        "threshold": threshold,
    }
