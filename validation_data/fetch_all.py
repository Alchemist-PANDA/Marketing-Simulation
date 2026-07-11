"""Fetch all scraped TikTok ads from Apify datasets and merge into one CSV."""
import json
import csv
import urllib.request
import ssl
import os

DATASETS = {
    "impression_main": "hySqRSE8Jt8NDB7IM",
    "likes_main": "i3MX6Mdsr7xIOYN7j",
    "ctr_main": "hkCes2Mdc7wQaak6V",
    "cvr_secondary": "jSbvVS2hU4vZC4sN7",
    "impression_secondary": "tUuf6yeldOgLq3rhs",
    "test_beauty": "prlWP9FvGQqvh6X3I",
}

FIELDS = [
    "id", "ad_title", "brand_name", "like", "ctr", "ctr_readable",
    "industry", "objective", "video_duration", "creative_center_url"
]

API_TOKEN = os.environ.get("APIFY_TOKEN", "")

ctx = ssl.create_default_context()
ca_bundle = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
if ca_bundle and os.path.exists(ca_bundle):
    ctx.load_verify_locations(ca_bundle)

all_items = []
seen_ids = set()

for label, dataset_id in DATASETS.items():
    offset = 0
    limit = 250
    while True:
        fields_param = ",".join(FIELDS)
        url = (
            f"https://api.apify.com/v2/datasets/{dataset_id}/items"
            f"?format=json&clean=true&limit={limit}&offset={offset}"
            f"&fields={fields_param}"
        )
        if API_TOKEN:
            url += f"&token={API_TOKEN}"

        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                items = json.loads(resp.read().decode())
        except Exception as e:
            print(f"  Error fetching {label} offset={offset}: {e}")
            break

        if not items:
            break

        for item in items:
            ad_id = item.get("id", "")
            if ad_id and ad_id not in seen_ids:
                seen_ids.add(ad_id)
                item["source_sort"] = label
                all_items.append(item)

        print(f"  {label}: fetched {len(items)} at offset={offset} (total unique: {len(all_items)})")
        if len(items) < limit:
            break
        offset += limit

print(f"\nTotal unique ads: {len(all_items)}")

# Write CSV
outpath = "/home/user/Marketing-Simulation/validation_data/tiktok_ads_raw.csv"
fieldnames = FIELDS + ["source_sort"]
with open(outpath, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for item in all_items:
        writer.writerow(item)

print(f"Saved to {outpath}")

# Quick stats
from collections import Counter
ctr_dist = Counter(item.get("ctr_readable", "unknown") for item in all_items)
industry_dist = Counter(item.get("industry", "unknown") for item in all_items)
brand_dist = Counter(item.get("brand_name", "") for item in all_items)
brands_with_ads = {k: v for k, v in brand_dist.items() if k and v >= 2}

print(f"\nCTR tier distribution:")
for tier, count in ctr_dist.most_common():
    print(f"  {tier}: {count}")

print(f"\nIndustry distribution (top 15):")
for ind, count in industry_dist.most_common(15):
    print(f"  {ind}: {count}")

print(f"\nBrands with 2+ ads: {len(brands_with_ads)}")
for brand, count in sorted(brands_with_ads.items(), key=lambda x: -x[1])[:20]:
    print(f"  {brand}: {count} ads")
