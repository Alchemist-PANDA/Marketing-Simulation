"""
Filter the merged (both-wave) TikTok corpus down to ecommerce-only industries,
keeping the existing brand-hash train/val/holdout split intact (no re-splitting
needed since splits were assigned by brand, not by industry — filtering doesn't
leak brands across splits).

Output feeds train_ranker_ecom.py, which trains a model with weights specialized
to ecommerce ad copy instead of diluted across Insurance/Gaming/Travel/etc.
"""
import csv

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

IN_DIR = "/home/user/Marketing-Simulation/validation_data"

with open(f"{IN_DIR}/merged_ads_clean.csv", encoding="utf-8") as f:
    ads = list(csv.DictReader(f))
with open(f"{IN_DIR}/merged_validation_pairs.csv", encoding="utf-8") as f:
    pairs = list(csv.DictReader(f))
with open(f"{IN_DIR}/merged_visual_features.csv", encoding="utf-8") as f:
    vf_rows = list(csv.DictReader(f))

ecom_ads = [a for a in ads if a["industry"] in ECOM_INDUSTRIES]
ecom_ids = {a["id"] for a in ecom_ads}
ecom_pairs = [p for p in pairs if p["ad_a_id"] in ecom_ids and p["ad_b_id"] in ecom_ids]
ecom_vf = [r for r in vf_rows if r["id"] in ecom_ids]

print(f"Ecommerce ads: {len(ecom_ads)} / {len(ads)}")
print(f"Ecommerce pairs: {len(ecom_pairs)} / {len(pairs)}")
print(f"Ecommerce visual features: {len(ecom_vf)}")

by_split = {}
for a in ecom_ads:
    by_split[a["split"]] = by_split.get(a["split"], 0) + 1
print("Ads by split:", by_split)

pair_split = {}
for p in ecom_pairs:
    pair_split[p["split"]] = pair_split.get(p["split"], 0) + 1
print("Pairs by split:", pair_split)

decisive = sum(1 for p in ecom_pairs if p["is_decisive"] == "True")
print(f"Decisive pairs: {decisive} / {len(ecom_pairs)}")

with open(f"{IN_DIR}/ecommerce_ads_clean.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=ads[0].keys())
    w.writeheader()
    w.writerows(ecom_ads)

with open(f"{IN_DIR}/ecommerce_validation_pairs.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=pairs[0].keys())
    w.writeheader()
    w.writerows(ecom_pairs)

with open(f"{IN_DIR}/ecommerce_visual_features.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=vf_rows[0].keys())
    w.writeheader()
    w.writerows(ecom_vf)

print(f"\nSaved -> ecommerce_ads_clean.csv, ecommerce_validation_pairs.csv, ecommerce_visual_features.csv")
