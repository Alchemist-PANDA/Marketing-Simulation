"""
Synthetic ad-performance dataset generator — DEVELOPMENT BENCHMARK ONLY.

⚠️  IMPORTANT — READ BEFORE INTERPRETING ANY ACCURACY NUMBER
------------------------------------------------------------
No public dataset pairs English ad *creative text* with real CTR at the scale
this project needs (the datasets with real CTR — Avazu/Criteo — are anonymized
categorical features with no text; the datasets with real ad copy have no
performance labels). This module therefore generates a **synthetic** dataset so
the ML pipeline can be built, tuned, and regression-tested end to end.

Directional accuracy measured on this data reflects the pipeline's ability to
recover a *known generative function* from text — it is a software benchmark,
NOT a claim about real-world ad performance. Any report that quotes a number
from this data must say so explicitly.

Design goals that make the benchmark non-trivial (not keyword-circular):
  * CTR is driven by latent "quality" factors (urgency, social proof,
    specificity, clarity, price framing, CTA strength, curiosity), each
    expressed through *families* of interchangeable phrases — so a model must
    generalize semantically (via embeddings), not memorize exact tokens.
  * Factors combine non-linearly with a couple of interaction terms.
  * Industry sets a realistic base CTR level.
  * Gaussian noise is added so the achievable accuracy has a ceiling < 100%.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SEED = 42

# 20 industries, each with (base CTR, representative product noun). The product
# noun is written into the ad text, so a text model CAN infer the industry (and
# thus its base CTR) from the copy — this is what makes CTR genuinely a function
# of the text rather than of a hidden column.
INDUSTRY_PRODUCTS = {
    "E-commerce Fashion": (0.021, "sneakers"), "Consumer Electronics": (0.018, "wireless headphones"),
    "SaaS / B2B": (0.009, "software suite"), "Finance / Fintech": (0.011, "credit card"),
    "Health & Wellness": (0.016, "daily supplements"), "Beauty & Cosmetics": (0.024, "skincare set"),
    "Food & Beverage": (0.019, "coffee subscription"), "Travel & Hospitality": (0.014, "getaway package"),
    "Automotive": (0.008, "family sedan"), "Real Estate": (0.007, "downtown condo"),
    "Education / e-Learning": (0.013, "online course"), "Gaming": (0.028, "game pass"),
    "Home & Garden": (0.015, "garden kit"), "Fitness": (0.020, "training program"),
    "Pet Care": (0.022, "grain-free pet food"), "Insurance": (0.006, "insurance plan"),
    "Telecom": (0.010, "unlimited data plan"), "Nonprofit": (0.012, "monthly donation"),
    "Entertainment / Streaming": (0.026, "streaming plan"), "Luxury Goods": (0.009, "designer watch"),
}
INDUSTRIES = {k: v[0] for k, v in INDUSTRY_PRODUCTS.items()}

# Phrase families. Index 0 = weak/absent, higher index = stronger signal.
# Multiple surface forms per level force the model to learn meaning, not tokens.
URGENCY = [
    ["", "available now", "shop the collection"],
    ["ends soon", "don't miss out", "while supplies last"],
    ["only 24 hours left", "today only", "final hours", "last chance"],
    ["ends at midnight tonight", "48-hour flash sale", "offer expires today — act now"],
]
SOCIAL_PROOF = [
    ["", "for everyone"],
    ["loved by customers", "highly rated", "a customer favorite"],
    ["trusted by 10,000+ buyers", "rated 4.8/5 by thousands", "join 50,000 happy customers"],
    ["#1 rated in its category, backed by 25,000 five-star reviews"],
]
SPECIFICITY = [
    ["great value", "a smarter choice"],
    ["save on your order", "real savings inside"],
    ["save 30% today", "get 40% off", "cut your bill by half"],
    ["save $75 instantly and get free shipping over $50"],
]
CTA = [
    ["", "learn more"],
    ["shop now", "get started", "try it today"],
    ["claim your discount", "start your free trial", "grab yours now"],
    ["start your free trial — no credit card, cancel anytime"],
]
CURIOSITY = [
    ["", "a new product"],
    ["you'll want to see this", "here's why it works"],
    ["the secret pros use", "what nobody tells you about"],
    ["the counterintuitive trick that doubled our results"],
]
PRICE_FRAMING = [  # affects CTR up (deal) or down (luxury)
    ["premium craftsmanship", "the luxury standard"],       # low CTR framing
    ["quality you can trust"],
    ["affordable for everyone", "budget-friendly"],
    ["lowest price guaranteed", "unbeatable price"],
]

# Products are tied 1:1 to industries (see INDUSTRY_PRODUCTS) so the text carries
# the category signal.


def _pick(rng, family):
    """Choose a phrase-family level (0..3) and a surface form for it."""
    level = rng.integers(0, 4)
    options = family[level]
    return level, rng.choice(options)


def _compose(rng, product):
    """Assemble an ad from sampled phrase families; return (text, factor_levels)."""
    u_lv, u = _pick(rng, URGENCY)
    s_lv, s = _pick(rng, SOCIAL_PROOF)
    sp_lv, sp = _pick(rng, SPECIFICITY)
    c_lv, c = _pick(rng, CTA)
    cu_lv, cu = _pick(rng, CURIOSITY)
    pf_lv, pf = _pick(rng, PRICE_FRAMING)

    parts = [p for p in [
        f"The {product} you've been waiting for",
        pf, sp, s, cu, u, c,
    ] if p]
    # Light shuffle of the middle clauses for phrasing variety
    head, tail = parts[0], parts[1:]
    rng.shuffle(tail)
    text = head + ". " + ". ".join(w.capitalize() for w in tail) + "."
    return text, dict(urgency=u_lv, social=s_lv, spec=sp_lv, cta=c_lv, curiosity=cu_lv, price=pf_lv)


def _latent_ctr(rng, base, f):
    """Map factor levels -> CTR via a documented non-linear function + noise."""
    # Normalize levels to 0..1
    u, s, sp, c, cu = f["urgency"]/3, f["social"]/3, f["spec"]/3, f["cta"]/3, f["curiosity"]/3
    # Price framing: level 0 = luxury (dampens CTR), level 3 = deal (lifts CTR)
    price_effect = (f["price"] - 1.5) / 1.5  # in [-1, 1]

    # Weighted quality with two interaction terms:
    #  - urgency amplifies CTA (a strong CTA matters more under time pressure)
    #  - specificity amplifies social proof (concrete numbers + reviews compound)
    quality = (
        0.28 * u + 0.22 * s + 0.20 * sp + 0.16 * c + 0.10 * cu
        + 0.12 * (u * c) + 0.10 * (sp * s)
        + 0.18 * price_effect
    )
    # Multiplier in ~[0.5, 1.9] around the industry base
    mult = 0.5 + 1.4 * (quality - (-0.18)) / (1.36 + 0.18)
    mult = float(np.clip(mult, 0.35, 2.1))
    ctr = base * mult
    # Modest multiplicative noise so achievable accuracy has a realistic ceiling
    # (< 100%) without drowning the text signal.
    ctr *= float(np.exp(rng.normal(0.0, 0.07)))
    return max(0.0005, ctr)


def generate(n: int = 2600, seed: int = SEED) -> pd.DataFrame:
    """Generate `n` synthetic ads with text, industry, latent factors, and CTR."""
    rng = np.random.default_rng(seed)
    items = list(INDUSTRY_PRODUCTS.items())
    rows = []
    for _ in range(n):
        ind_name, (base, product) = items[rng.integers(0, len(items))]
        text, f = _compose(rng, product)
        ctr = _latent_ctr(rng, base, f)
        rows.append({
            "ad_text": text,
            "industry": ind_name,
            "actual_ctr": round(ctr, 6),
            "impressions": int(rng.integers(500, 200_000)),
            **{f"factor_{k}": v for k, v in f.items()},
        })
    df = pd.DataFrame(rows).drop_duplicates(subset=["ad_text"]).reset_index(drop=True)
    return df


def split(df: pd.DataFrame, seed: int = SEED):
    """Deterministic 70/15/15 train/val/holdout split."""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(df))
    n_tr = int(0.70 * len(df))
    n_val = int(0.15 * len(df))
    tr = df.iloc[idx[:n_tr]].reset_index(drop=True)
    val = df.iloc[idx[n_tr:n_tr + n_val]].reset_index(drop=True)
    hold = df.iloc[idx[n_tr + n_val:]].reset_index(drop=True)
    return tr, val, hold


if __name__ == "__main__":
    import os
    os.makedirs("data", exist_ok=True)
    df = generate()
    tr, val, hold = split(df)
    df.to_csv("data/expanded_real_dataset.csv", index=False)
    tr.to_csv("data/synth_train.csv", index=False)
    val.to_csv("data/synth_val.csv", index=False)
    hold.to_csv("data/synth_holdout.csv", index=False)
    print(f"Generated {len(df)} ads  ->  train={len(tr)} val={len(val)} holdout={len(hold)}")
    print(f"CTR range: {df.actual_ctr.min():.4f} .. {df.actual_ctr.max():.4f}  mean={df.actual_ctr.mean():.4f}")
