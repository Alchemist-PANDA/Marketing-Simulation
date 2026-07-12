"""
Merge the wave-3 raw scrape (validation_data/wave3_raw/*.json) into the
existing two-wave corpus, dedupe, filter to English + valid CTR, and report
how much NEW ecommerce signal (esp. same-brand pairs) this actually added
before committing to a full rebuild + retrain.
"""
import csv
import glob
import json
import os
from collections import Counter

OUT_DIR = "/home/user/Marketing-Simulation/validation_data"
RAW_DIR = f"{OUT_DIR}/wave3_raw"

with open(f"{OUT_DIR}/merged_ads_clean.csv", encoding="utf-8") as f:
    existing = list(csv.DictReader(f))
existing_ids = {a["id"] for a in existing}
print(f"Existing corpus: {len(existing)} ads")

raw_items = []
for fpath in sorted(glob.glob(f"{RAW_DIR}/*.json")):
    with open(fpath, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        raw_items.extend(data)
print(f"Raw wave-3 items: {len(raw_items)}")


def is_english_text(text):
    ascii_count = sum(1 for c in text if ord(c) < 128)
    return ascii_count / max(1, len(text)) > 0.7


new_ads = {}
for item in raw_items:
    ad_id = item.get("id", "")
    title = (item.get("ad_title") or "").strip()
    if not ad_id or not title or len(title) < 10:
        continue
    if ad_id in existing_ids or ad_id in new_ads:
        continue
    if not is_english_text(title):
        continue
    ctr = item.get("ctr", 0)
    if not ctr or ctr <= 0:
        continue
    new_ads[ad_id] = {
        "id": ad_id,
        "ad_title": title,
        "brand_name": (item.get("brand_name") or "").strip(),
        "likes": item.get("like", 0),
        "ctr_percentile": ctr,
        "ctr_readable": item.get("ctr_readable", ""),
        "industry": item.get("industry", ""),
        "objective": item.get("objective", ""),
        "video_duration": item.get("video_duration", 0),
        "video_cover": item.get("video_cover", ""),
        "video_url_720p": item.get("video_url_720p", ""),
        "split": None,  # assigned in build_merged_dataset step
        "wave": "wave3_20260712",
    }

new_ads = list(new_ads.values())
print(f"New unique English ads with valid CTR: {len(new_ads)}")

ECOM_INDUSTRIES = {
    "Skincare", "Cosmetics", "Haircare", "Wig & Hair Styling",
    "Women's Clothing", "Men's Clothing", "Apparel & Accessories",
    "Clothing Accessories", "Fragrances & Perfumes", "Online Shopping",
    "Ordinary Jewelry", "High-end Jewelry", "Toys", "Home Decor", "Oral Care",
    "Bags", "Watches", "Men's Shoes", "Women's Shoes", "Furniture",
    "Kitchen Accessories", "Petfood", "Gifts & Flowers",
    "Large E-commerce Platforms", "Small & Medium-sized E-commerce Platforms",
    "Feminine Care", "Beauty & Personal Care", "Health & Fitness",
    "Personal Care Appliances", "Daily Essentials", "Glasses & Drinkware",
    "Home Appliances", "Cleaning Appliances", "Cleaning Supplies",
    "Storage Products", "Sports & Outdoor", "Computer Accessories",
    "Tissues & Wet Wipes", "Office Equipment", "Office Equipment & Supplies",
    "Pet Household Products", "Pet Grooming", "Pet Healthcare",
    "Sports & Fitness", "Gaming Devices", "Digital Devices",
    "Tech & Electronics", "Cell Phones", "Computers", "Audio & Video Players",
}

new_ecom = [a for a in new_ads if a["industry"] in ECOM_INDUSTRIES]
print(f"New ecommerce ads: {len(new_ecom)} / {len(new_ads)}")

ind_dist = Counter(a["industry"] for a in new_ecom)
print("\nNew ecommerce ads by industry:")
for k, v in ind_dist.most_common(30):
    print(f"  {v:4d}  {k}")

# Same-brand potential: brands that now have >=2 ads INCLUDING existing corpus
existing_ecom_by_brand = {}
for a in existing:
    if a["industry"] in ECOM_INDUSTRIES and a["brand_name"]:
        existing_ecom_by_brand.setdefault(a["brand_name"], []).append(a)

new_by_brand = {}
for a in new_ecom:
    if a["brand_name"]:
        new_by_brand.setdefault(a["brand_name"], []).append(a)

brands_with_new_pairs_possible = 0
new_same_brand_pair_estimate = 0
for brand, items in new_by_brand.items():
    total_for_brand = len(items) + len(existing_ecom_by_brand.get(brand, []))
    if total_for_brand >= 2:
        brands_with_new_pairs_possible += 1
        # rough combinatorial estimate capped
        new_same_brand_pair_estimate += min(len(items) * max(1, total_for_brand - len(items)), 20)

print(f"\nEcommerce brands touched by new same-brand-eligible ads: {brands_with_new_pairs_possible}")
print(f"Rough new same-brand pair potential: ~{new_same_brand_pair_estimate}")
print(f"(new ecom ads with a brand_name at all: {sum(1 for a in new_ecom if a['brand_name'])})")

# Save new_ads (all industries, for merging into the 3-wave corpus)
with open(f"{OUT_DIR}/wave3_ads_clean.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=[
        "id", "ad_title", "brand_name", "likes", "ctr_percentile",
        "ctr_readable", "industry", "objective", "video_duration",
        "video_cover", "video_url_720p", "split", "wave",
    ])
    w.writeheader()
    w.writerows(new_ads)
print(f"\nSaved {len(new_ads)} new ads (all industries) -> wave3_ads_clean.csv")
