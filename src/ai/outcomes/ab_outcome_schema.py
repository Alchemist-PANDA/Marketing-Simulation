"""
A/B-outcome ingestion schema + pairing — the foundation for training the
creative ranker on labels that actually depend on the CREATIVE (real A/B
test results), instead of TikTok Creative-Center CTR percentile tiers (which
are driven mostly by targeting/budget/audience — see docs/VALIDATION.md
"v7 honest reckoning" for why those cap out at ~55%).

THE CORE IDEA
-------------
Within a single A/B test, every arm (creative variant) is shown to the *same*
audience over the *same* window. So the difference in click/conversion rate
between two arms of the SAME test isolates the causal effect of the creative.
Pairs are therefore only ever formed WITHIN a test_id, never across tests.
This is what makes the label creative-dependent and leakage-resistant.

INPUT FORMAT (one row per creative arm)
---------------------------------------
Required columns:
  test_id        : groups arms tested against each other (same audience/window)
  creative_text  : the ad copy / headline shown
  impressions    : how many people saw this arm (> 0)
  clicks         : how many clicked (or `conversions` for a conversion test)

Optional columns (used if present, ignored if absent):
  conversions    : if present and objective='conversions', used instead of clicks
  creative_id    : stable id for the arm (defaults to a hash of test_id+text)
  image_path / video_path : local path to the creative asset (for visual feats)
  channel, objective, industry, brand, date : context metadata
  source         : dataset provenance tag (e.g. "upworthy", "customer_meta")

The same schema serves BOTH the public seed data (Upworthy) and a customer's
own exported A/B results — a Shopify/Meta/TikTok Ads Manager export maps onto
these columns directly.
"""

from __future__ import annotations

import csv
import hashlib
import math
from dataclasses import dataclass, field
from typing import Iterable


REQUIRED = ("test_id", "creative_text", "impressions", "clicks")


@dataclass
class Arm:
    test_id: str
    creative_text: str
    impressions: int
    clicks: int
    conversions: "int | None" = None
    creative_id: str = ""
    image_path: str = ""
    video_path: str = ""
    channel: str = ""
    objective: str = ""
    industry: str = ""
    brand: str = ""
    date: str = ""
    source: str = ""

    def rate(self, objective: str = "clicks") -> float:
        num = self.conversions if (objective == "conversions" and self.conversions is not None) else self.clicks
        return num / self.impressions if self.impressions > 0 else 0.0

    def __post_init__(self):
        if not self.creative_id:
            h = hashlib.md5(f"{self.test_id}|{self.creative_text}".encode()).hexdigest()[:16]
            self.creative_id = h


@dataclass
class OutcomePair:
    test_id: str
    a: Arm            # a is ALWAYS the better arm (higher rate) — ground truth "A"
    b: Arm
    rate_a: float
    rate_b: float
    n_a: int
    n_b: int
    source: str = ""

    @property
    def rate_gap(self) -> float:
        return abs(self.rate_a - self.rate_b)

    @property
    def significant(self) -> bool:
        """Two-proportion z-test: is the arm difference unlikely to be noise?

        Filters out pairs whose rate difference is within sampling noise, so
        the model learns from real creative effects rather than low-impression
        flukes. |z| >= 1.96 ~ p<0.05.
        """
        return abs(self._z()) >= 1.96

    def _z(self) -> float:
        x1, n1 = self.rate_a * self.n_a, self.n_a
        x2, n2 = self.rate_b * self.n_b, self.n_b
        if n1 == 0 or n2 == 0:
            return 0.0
        p = (x1 + x2) / (n1 + n2)
        se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
        if se == 0:
            return 0.0
        return (self.rate_a - self.rate_b) / se


def load_arms(path: str) -> list[Arm]:
    """Read an A/B-outcome CSV into Arm objects, validating required columns."""
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: missing required columns {missing}; "
                             f"have {reader.fieldnames}")
        arms = []
        for r in reader:
            try:
                imp = int(float(r["impressions"]))
                clk = int(float(r["clicks"]))
            except (ValueError, TypeError):
                continue
            if imp <= 0 or clk < 0 or not (r.get("creative_text") or "").strip():
                continue
            conv = None
            if r.get("conversions") not in (None, ""):
                try:
                    conv = int(float(r["conversions"]))
                except (ValueError, TypeError):
                    conv = None
            arms.append(Arm(
                test_id=str(r["test_id"]).strip(),
                creative_text=r["creative_text"].strip(),
                impressions=imp, clicks=clk, conversions=conv,
                creative_id=(r.get("creative_id") or "").strip(),
                image_path=(r.get("image_path") or "").strip(),
                video_path=(r.get("video_path") or "").strip(),
                channel=(r.get("channel") or "").strip(),
                objective=(r.get("objective") or "").strip(),
                industry=(r.get("industry") or "").strip(),
                brand=(r.get("brand") or "").strip(),
                date=(r.get("date") or "").strip(),
                source=(r.get("source") or "").strip(),
            ))
    return arms


def _norm(t: str) -> str:
    return " ".join((t or "").lower().split())


def build_pairs(arms: Iterable[Arm], objective: str = "clicks",
                min_impressions: int = 100,
                require_significant: bool = True,
                max_pairs_per_test: int = 10,
                drop_identical_text: bool = True) -> list[OutcomePair]:
    """Form WITHIN-TEST creative pairs (a = better arm). Cross-test pairs are
    never formed — that is the whole point (same audience isolates creative).

    - min_impressions: drop arms with too few impressions to trust the rate.
    - require_significant: keep only pairs whose rate gap beats a 2-proportion
      z-test (filters sampling noise; near-ties would just teach the model
      coin-flips).
    - max_pairs_per_test: cap combinatorial blow-up on many-arm tests, keeping
      the largest-gap pairs (clearest creative signal).
    - drop_identical_text: skip pairs whose creative TEXT is identical (e.g.
      same headline, different image). A text model can't learn from a pair
      where its only input is unchanged but the label flips — those pairs are
      pure contradiction/noise for text training.
    """
    by_test: dict[str, list[Arm]] = {}
    for arm in arms:
        if arm.impressions >= min_impressions:
            by_test.setdefault(arm.test_id, []).append(arm)

    pairs: list[OutcomePair] = []
    for tid, group in by_test.items():
        if len(group) < 2:
            continue
        cand = []
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                if drop_identical_text and _norm(a.creative_text) == _norm(b.creative_text):
                    continue
                ra, rb = a.rate(objective), b.rate(objective)
                if ra == rb:
                    continue
                if ra < rb:  # ensure a is the better arm
                    a, b, ra, rb = b, a, rb, ra
                p = OutcomePair(tid, a, b, ra, rb, a.impressions, b.impressions,
                                source=a.source)
                if require_significant and not p.significant:
                    continue
                cand.append(p)
        cand.sort(key=lambda p: -p.rate_gap)
        pairs.extend(cand[:max_pairs_per_test])
    return pairs


def summarize(arms: list[Arm], pairs: list[OutcomePair]) -> dict:
    tests = {a.test_id for a in arms}
    return {
        "arms": len(arms),
        "tests": len(tests),
        "pairs": len(pairs),
        "sources": sorted({a.source for a in arms if a.source}),
        "median_gap": (sorted(p.rate_gap for p in pairs)[len(pairs) // 2]
                       if pairs else 0.0),
    }
