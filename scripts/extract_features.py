"""
Feature extraction pipeline for the AI-enhanced simulation engine.

Extracts three feature types:
1. Keyword-based scores (price, trust, urgency) — from scorer.py
2. Sentence embeddings (384-dim) — from all-MiniLM-L6-v2
3. Handcrafted text features (length, punctuation, readability)

Outputs a feature matrix ready for model training.
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ad_processing.scorer import extract_text_scores


def extract_keyword_features(texts):
    """Extract keyword-based price/trust/urgency scores."""
    features = []
    for text in texts:
        scores = extract_text_scores(text)
        features.append([
            scores['price_score'],
            scores['trust_score'],
            scores['urgency_score'],
        ])
    return np.array(features, dtype=np.float32)


def extract_text_stats(texts):
    """Extract handcrafted text statistics."""
    features = []
    for text in texts:
        words = text.split()
        features.append([
            len(words),
            len(text),
            text.count('!'),
            text.count('?'),
            text.count('%'),
            sum(1 for c in text if c.isupper()) / max(len(text), 1),
            len([w for w in words if w[0].isupper()]) / max(len(words), 1) if words else 0,
            1 if any(c.isdigit() for c in text) else 0,
            text.count('$'),
        ])
    return np.array(features, dtype=np.float32)


def extract_embeddings(texts):
    """Extract sentence-transformer embeddings."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(texts, show_progress_bar=False)
        return embeddings.astype(np.float32)
    except ImportError:
        print("WARNING: sentence-transformers not installed, using zeros")
        return np.zeros((len(texts), 384), dtype=np.float32)


def extract_all_features(texts, include_embeddings=True):
    """Extract complete feature matrix."""
    keyword_feats = extract_keyword_features(texts)
    text_stats = extract_text_stats(texts)

    feature_names = [
        'kw_price', 'kw_trust', 'kw_urgency',
        'word_count', 'char_count', 'excl_count', 'question_count',
        'pct_count', 'upper_ratio', 'cap_word_ratio', 'has_number', 'dollar_count',
    ]

    features = np.hstack([keyword_feats, text_stats])

    if include_embeddings:
        embeddings = extract_embeddings(texts)
        emb_names = [f'emb_{i}' for i in range(embeddings.shape[1])]
        features = np.hstack([features, embeddings])
        feature_names.extend(emb_names)

    return features, feature_names


def process_dataset(csv_path, output_path=None, include_embeddings=True):
    """Process a CSV dataset and save features."""
    df = pd.read_csv(csv_path)
    texts = df['ad_text'].tolist()

    text_df = df.groupby('ad_text')['actual_ctr'].mean().reset_index()
    unique_texts = text_df['ad_text'].tolist()
    ctrs = text_df['actual_ctr'].values

    features, feature_names = extract_all_features(unique_texts, include_embeddings)

    result = pd.DataFrame(features, columns=feature_names)
    result['ad_text'] = unique_texts
    result['actual_ctr'] = ctrs

    if output_path:
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        result.to_csv(output_path, index=False)
        print(f"Saved {len(result)} rows x {len(feature_names)} features to {output_path}")

    return result, feature_names


if __name__ == '__main__':
    for split in ['train', 'val', 'holdout']:
        path = f'data/{split}.csv'
        if os.path.exists(path):
            process_dataset(path, f'data/features_{split}.csv')
