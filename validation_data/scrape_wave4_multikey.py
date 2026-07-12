"""
Wave-4 large diversified ecommerce scrape across 8 Apify keys in parallel.
Each key processes a slice of the 275-keyword ecommerce bank via keyword
search (the anti-saturation axis: leaderboards are saturated, keyword search
returns mostly-new ads). Per-key budget guard stops at $4.60 of the $5 cap.

Usage: python3 scrape_wave4_multikey.py <key_index 0-7>
Launch all 8 in background, one per key.
"""
import json
import os
import ssl
import sys
import time
import urllib.request

sys.path.insert(0, "/tmp/claude-0/-home-user-Marketing-Simulation/a6a16d5d-152a-5a09-8ed4-0ec5de802d49/scratchpad")
from keywords import KEYWORDS

# API keys are read from the APIFY_KEYS env var (comma-separated) so no
# credentials are ever committed. Example:
#   export APIFY_KEYS="key1,key2,...,key8"
KEYS = [k.strip() for k in os.environ.get("APIFY_KEYS", "").split(",") if k.strip()]
ACTOR = "rFFzT2mRuOd1K4iTM"
OUT_DIR = "/home/user/Marketing-Simulation/validation_data/wave4_raw"
os.makedirs(OUT_DIR, exist_ok=True)
BUDGET_STOP = 4.60

COUNTRY_SETS = [
    ["US", "GB", "CA", "AU"],
    ["US", "SG", "PH", "MY"],
    ["GB", "IE", "NZ", "ZA"],
    ["US", "CA", "NG", "PK"],
]
PERIODS = ["180", "30"]
ORDERS = ["ctr", "like"]

ctx = ssl.create_default_context()
ca = os.environ.get("SSL_CERT_FILE") or "/root/.ccr/ca-bundle.crt"
if os.path.exists(ca):
    ctx.load_verify_locations(ca)


def usage(token):
    url = f"https://api.apify.com/v2/users/me/limits?token={token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url), context=ctx, timeout=30) as r:
            return json.loads(r.read().decode())["data"]["current"]["monthlyUsageUsd"]
    except Exception:
        return 0.0


def run(token, body, retries=2):
    url = f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items?token={token}"
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=240) as r:
                d = json.loads(r.read().decode())
            if isinstance(d, dict) and "error" in d:
                return None, d["error"].get("message", "")[:100]
            return d, None
        except urllib.error.HTTPError as e:
            if e.code == 400:
                return None, "HTTP400"
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            return None, f"HTTP{e.code}"
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            return None, str(e)[:80]
    return None, "exhausted"


def slug(s):
    return "".join(c if c.isalnum() else "_" for c in s)[:40]


def main(kidx):
    token = KEYS[kidx]
    flat = [(cat, kw) for cat, kws in KEYWORDS.items() for kw in kws]
    # round-robin partition so each key gets a spread of categories
    my_kws = [flat[i] for i in range(len(flat)) if i % len(KEYS) == kidx]
    print(f"[key{kidx}] assigned {len(my_kws)} keywords", flush=True)

    total_items = 0
    for n, (cat, kw) in enumerate(my_kws):
        u = usage(token)
        if u >= BUDGET_STOP:
            print(f"[key{kidx}] BUDGET STOP at ${u:.3f} after {n} keywords", flush=True)
            break
        cs = COUNTRY_SETS[n % len(COUNTRY_SETS)]
        period = PERIODS[n % len(PERIODS)]
        order = ORDERS[(n // 2) % len(ORDERS)]
        body = {
            "mode": "top_ads",
            "topAdsKeyword": kw,
            "topAdsCountryCode": cs,
            "topAdsPeriod": period,
            "topAdsOrderBy": order,
            "topAdsLanguage": "en",
            "topAdsMaxItems": 300,
            "region": "all",
            "startDate": "2025-01-01",
            "queryType": "2",
            "maxAds": 100,
            "fetchDetails": False,
            "proxyConfiguration": {"useApifyProxy": True},
        }
        d, err = run(token, body)
        if err:
            print(f"[key{kidx}] {kw!r} ({cat}) ERR {err}", flush=True)
            continue
        outpath = os.path.join(OUT_DIR, f"k{kidx}_{slug(cat)}_{slug(kw)}.json")
        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(d, f)
        total_items += len(d)
        print(f"[key{kidx}] {n+1}/{len(my_kws)} {kw!r} -> {len(d)} items "
              f"(cum {total_items}, ${u:.3f})", flush=True)
        time.sleep(0.5)

    final = usage(token)
    print(f"[key{kidx}] DONE: {total_items} items, spent ${final:.3f}", flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]))
