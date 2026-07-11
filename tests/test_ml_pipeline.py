"""
Fast, deterministic tests for the ML pipeline that do NOT load the MiniLM model
(so they stay quick in CI). Embedding-dependent behavior is covered by the
training run itself.
"""
import numpy as np

from src.ai import synth_data
from src.ai.feature_extractor import EMBED_DIM, STAT_COLUMNS, feature_names, text_stats


def test_synth_data_is_deterministic():
    a = synth_data.generate(n=300, seed=42)
    b = synth_data.generate(n=300, seed=42)
    assert a["ad_text"].tolist() == b["ad_text"].tolist()
    assert np.allclose(a["actual_ctr"].values, b["actual_ctr"].values)


def test_synth_ctr_is_positive_and_bounded():
    df = synth_data.generate(n=500, seed=1)
    assert (df["actual_ctr"] > 0).all()
    assert df["actual_ctr"].max() < 0.2  # sane CTR ceiling


def test_split_is_disjoint_and_complete():
    df = synth_data.generate(n=400, seed=7)
    tr, val, hold = synth_data.split(df, seed=7)
    assert len(tr) + len(val) + len(hold) == len(df)
    # No overlap / leakage across splits (checked by unique ad text).
    texts = set(tr["ad_text"]) | set(val["ad_text"]) | set(hold["ad_text"])
    assert len(texts) == len(df)


def test_text_stats_shape_and_values():
    v = text_stats("Save 50% today only! Trusted by 10,000 buyers. Shop now.")
    assert v.shape == (len(STAT_COLUMNS),)
    assert not np.isnan(v).any()
    # word_count is first column and should be > 0
    assert v[0] > 0


def test_feature_names_length():
    assert len(feature_names()) == len(STAT_COLUMNS) + EMBED_DIM
