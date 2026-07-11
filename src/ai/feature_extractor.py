"""
Feature extraction for ad-CTR prediction.

Produces a single feature vector per ad by concatenating:
  1. Sentence embedding  (all-MiniLM-L6-v2, 384 dims) — semantic meaning
  2. Text statistics      (length, punctuation, capitalization, readability)
  3. Sentiment            (lightweight lexicon polarity + subjectivity proxy)

The embedder is loaded lazily and cached, so importing this module is cheap and
inference stays within Streamlit Cloud's memory budget (MiniLM is ~90 MB).
"""
from __future__ import annotations

import re

import numpy as np

EMBED_MODEL = "all-MiniLM-L6-v2"
EMBED_DIM = 384

# Column order for the non-embedding features (kept stable for the scaler).
STAT_COLUMNS = [
    "word_count", "char_count", "avg_word_len", "sentence_count",
    "excl_count", "question_count", "pct_count", "dollar_count",
    "digit_count", "upper_ratio", "cap_word_ratio", "unique_word_ratio",
    "flesch_reading_ease", "avg_sentence_len",
    "sentiment_pos", "sentiment_neg", "sentiment_polarity",
]

_POS_WORDS = {
    "save", "free", "best", "love", "loved", "trusted", "guarantee", "guaranteed",
    "easy", "new", "exclusive", "premium", "quality", "happy", "win", "bonus",
    "unbeatable", "favorite", "rated", "top", "proven", "instantly", "now",
    "discount", "deal", "offer", "gift", "reward", "boost", "smart",
}
_NEG_WORDS = {
    "miss", "last", "expire", "expires", "hurry", "limited", "only", "risk",
    "warning", "problem", "hard", "difficult", "stop", "lose", "losing", "fail",
}

_embedder = None


def _get_embedder():
    """Lazily load and cache the sentence-transformer model."""
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(EMBED_MODEL)
    return _embedder


def _count_syllables(word: str) -> int:
    word = word.lower()
    groups = re.findall(r"[aeiouy]+", word)
    n = len(groups)
    if word.endswith("e") and n > 1:
        n -= 1
    return max(1, n)


def _flesch_reading_ease(text: str, words: list[str], n_sentences: int) -> float:
    n_words = len(words)
    if n_words == 0 or n_sentences == 0:
        return 0.0
    n_syll = sum(_count_syllables(w) for w in words)
    return 206.835 - 1.015 * (n_words / n_sentences) - 84.6 * (n_syll / n_words)


def text_stats(text: str) -> np.ndarray:
    """Compute the STAT_COLUMNS features for one ad (order matches STAT_COLUMNS)."""
    words = re.findall(r"[A-Za-z']+", text)
    tokens = text.split()
    n_words = len(words)
    n_chars = len(text)
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    n_sent = max(1, len(sentences))

    lower = [w.lower() for w in words]
    pos = sum(1 for w in lower if w in _POS_WORDS)
    neg = sum(1 for w in lower if w in _NEG_WORDS)
    polarity = (pos - neg) / max(1, n_words)

    stats = [
        n_words,
        n_chars,
        (sum(len(w) for w in words) / n_words) if n_words else 0.0,
        n_sent,
        text.count("!"),
        text.count("?"),
        text.count("%"),
        text.count("$"),
        sum(1 for c in text if c.isdigit()),
        sum(1 for c in text if c.isupper()) / max(1, n_chars),
        (sum(1 for w in tokens if w[:1].isupper()) / len(tokens)) if tokens else 0.0,
        (len(set(lower)) / n_words) if n_words else 0.0,
        _flesch_reading_ease(text, words, n_sent),
        (n_words / n_sent),
        pos / max(1, n_words),
        neg / max(1, n_words),
        polarity,
    ]
    return np.array(stats, dtype=np.float32)


def embed(texts: list[str], batch_size: int = 64) -> np.ndarray:
    """Return the (n, EMBED_DIM) embedding matrix for a list of texts."""
    model = _get_embedder()
    return np.asarray(
        model.encode(list(texts), batch_size=batch_size, show_progress_bar=False,
                     normalize_embeddings=True),
        dtype=np.float32,
    )


def build_features(texts: list[str]) -> np.ndarray:
    """Full feature matrix: [stats | embeddings], shape (n, len(STAT_COLUMNS)+EMBED_DIM)."""
    texts = list(texts)
    stats = np.vstack([text_stats(t) for t in texts])
    embs = embed(texts)
    return np.hstack([stats, embs]).astype(np.float32)


def feature_names() -> list[str]:
    return list(STAT_COLUMNS) + [f"emb_{i}" for i in range(EMBED_DIM)]
