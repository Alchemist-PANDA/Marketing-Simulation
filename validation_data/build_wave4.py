"""
Clean wave-4 raw keyword-search scrape -> wave4_ads_clean.csv.
Dedupe against the existing 3-wave corpus, English + valid-CTR filter, and
blank generic platform-campaign "brand" labels (same bug class as the
Shopee labels caught in wave-3) so same-brand pairing stays honest.
"""
import csv
import glob
import json
from collections import Counter

OUT_DIR = "/home/user/Marketing-Simulation/validation_data"

existing = set()
for fn in ["tiktok_ads_clean.csv", "fresh_ads_clean.csv", "wave3_ads_clean.csv"]:
    for r in csv.DictReader(open(f"{OUT_DIR}/{fn}", encoding="utf-8")):
        existing.add(r["id"])
print(f"Existing corpus ids: {len(existing)}")

raw = []
for fp in glob.glob(f"{OUT_DIR}/wave4_raw/*.json"):
    try:
        d = json.load(open(fp, encoding="utf-8"))
    except Exception:
        continue
    if isinstance(d, list):
        raw.extend(d)
print(f"Raw wave-4 items: {len(raw)}")


def is_english(t):
    return t and sum(c < 128 for c in map(ord, t)) / max(1, len(t)) > 0.7


new = {}
for it in raw:
    i = it.get("id", "")
    t = (it.get("ad_title") or "").strip()
    if not i or not t or len(t) < 10 or i in existing or i in new:
        continue
    if not is_english(t):
        continue
    c = it.get("ctr", 0)
    if not c or c <= 0:
        continue
    new[i] = {
        "id": i, "ad_title": t,
        "brand_name": (it.get("brand_name") or "").strip(),
        "likes": it.get("like", 0), "ctr_percentile": c,
        "ctr_readable": it.get("ctr_readable", ""),
        "industry": it.get("industry", ""), "objective": it.get("objective", ""),
        "video_duration": it.get("video_duration", 0),
        "video_cover": it.get("video_cover", ""),
        "video_url_720p": it.get("video_url_720p", ""),
        "split": None, "wave": "wave4_20260712",
    }
new = list(new.values())
print(f"New unique English valid-CTR ads: {len(new)}")

# Generic-brand detection: a real single advertiser rarely has a huge number
# of distinct ads in one keyword scrape; platform-promo campaign labels do.
# Flag brand names with >=20 ads AND whose name looks campaign-like, plus a
# manual blocklist of patterns. Blank them so they only form same-industry
# pairs, never same-brand.
brand_counts = Counter(a["brand_name"] for a in new if a["brand_name"])
CAMPAIGN_PATTERNS = ["festival", "celebrate", "sale", "% off", "shopee", "lazada",
                     "11.11", "12.12", "black friday", "flash", "deal", "official store",
                     "brands", "super brand", "mega", "payday"]
generic = set()
for b, n in brand_counts.items():
    bl = b.lower()
    if any(p in bl for p in CAMPAIGN_PATTERNS):
        generic.add(b)
    elif n >= 25:  # implausibly many distinct ads for one real advertiser here
        generic.add(b)
print(f"Generic/campaign brand labels blanked: {len(generic)}")
for b in sorted(generic, key=lambda x: -brand_counts[x])[:15]:
    print(f"  {brand_counts[b]:4d}  {b!r}")

blanked = 0
for a in new:
    if a["brand_name"] in generic:
        a["brand_name"] = ""
        blanked += 1
print(f"Ads blanked: {blanked}")

with open(f"{OUT_DIR}/wave4_ads_clean.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=[
        "id", "ad_title", "brand_name", "likes", "ctr_percentile",
        "ctr_readable", "industry", "objective", "video_duration",
        "video_cover", "video_url_720p", "split", "wave"])
    w.writeheader()
    w.writerows(new)
print(f"Saved {len(new)} ads -> wave4_ads_clean.csv")
