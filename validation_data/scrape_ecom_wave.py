"""
Scrape additional TikTok Creative Center top-ads data, varied across as many
axes as possible (period, orderBy, country set, startDate) to minimize
overlap with the existing 2,774-ad corpus and maximize new unique ecommerce
ads -- especially new same-brand pairs, the identified weak spot.

Budget-aware: checks account usage before/after each call and stops early
if the monthly cap is being approached.
"""
import json
import os
import time
import urllib.request
import ssl

APIFY_TOKEN = os.environ["APIFY_TOKEN"]
ACTOR = "rFFzT2mRuOd1K4iTM"
OUT_DIR = "/home/user/Marketing-Simulation/validation_data/wave3_raw"
os.makedirs(OUT_DIR, exist_ok=True)

ctx = ssl.create_default_context()
ca_bundle = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
if ca_bundle and os.path.exists(ca_bundle):
    ctx.load_verify_locations(ca_bundle)


def usage_usd():
    url = f"https://api.apify.com/v2/users/me/limits?token={APIFY_TOKEN}"
    with urllib.request.urlopen(urllib.request.Request(url), context=ctx, timeout=30) as r:
        d = json.loads(r.read().decode())
    return d["data"]["current"]["monthlyUsageUsd"], d["data"]["limits"]["maxMonthlyUsageUsd"]


def run_query(name, body):
    url = f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items?token={APIFY_TOKEN}"
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=280) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        print(f"  [{name}] ERROR: {e}")
        return 0
    if isinstance(data, dict) and "error" in data:
        print(f"  [{name}] API ERROR: {data['error'].get('message','')[:200]}")
        return 0
    n = len(data) if isinstance(data, list) else 0
    outpath = os.path.join(OUT_DIR, f"{name}.json")
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"  [{name}] {n} items -> {outpath}")
    return n


COUNTRY_SETS = [
    ["US", "GB", "IE", "NZ", "CA", "AU"],
    ["US", "GB", "CA", "AU", "SG", "PH"],
    ["US", "IN", "ZA", "MY", "PK"],
]

QUERIES = []
for period, order_by in [("7", "ctr"), ("7", "like"), ("7", "cvr"), ("7", "impression"),
                         ("30", "ctr"), ("30", "cvr"), ("180", "ctr"), ("180", "impression")]:
    for ci, countries in enumerate(COUNTRY_SETS):
        QUERIES.append({
            "name": f"p{period}_{order_by}_c{ci}",
            "body": {
                "mode": "top_ads",
                "topAdsKeyword": "",
                "topAdsCountryCode": countries,
                "topAdsPeriod": period,
                "topAdsOrderBy": order_by,
                "topAdsIndustry": [],
                "topAdsLanguage": "en",
                "topAdsMaxItems": 400,
                "region": "all",
                "startDate": "2025-01-01" if period != "7" else "2025-09-01",
                "endDate": "",
                "queryType": "2",
                "query": "",
                "advertiserBizId": "",
                "maxAds": 100,
                "fetchDetails": False,
                "topAdsLikeRange": "",
                "proxyConfiguration": {"useApifyProxy": True},
            },
        })

print(f"Planned queries: {len(QUERIES)}")
used, cap = usage_usd()
print(f"Starting usage: ${used:.4f} / ${cap} cap")

STOP_AT_USD = cap * 0.85  # leave a buffer

total_items = 0
for q in QUERIES:
    used, cap = usage_usd()
    if used >= STOP_AT_USD:
        print(f"\nStopping: usage ${used:.4f} reached {STOP_AT_USD:.2f} buffer threshold")
        break
    n = run_query(q["name"], q["body"])
    total_items += n
    time.sleep(1)

used, cap = usage_usd()
print(f"\nDone. Total raw items fetched: {total_items}")
print(f"Final usage: ${used:.4f} / ${cap} cap")
