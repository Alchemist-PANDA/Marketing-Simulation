import pandas as pd
import numpy as np
import os

def create_realistic_ctr_data(output_path='data/real_ctr.csv', n=500):
    os.makedirs('data', exist_ok=True)

    industries = [
        {"name": "Retail", "base_ctr": 0.015, "keywords": ["sale", "shop", "discount", "fashion", "buy", "deal"]},
        {"name": "Finance", "base_ctr": 0.006, "keywords": ["loan", "credit", "insurance", "bank", "invest", "save money"]},
        {"name": "B2B", "base_ctr": 0.008, "keywords": ["software", "saas", "team", "enterprise", "solutions", "workflow"]},
        {"name": "Real Estate", "base_ctr": 0.012, "keywords": ["home", "apartment", "house", "luxury", "listings", "property"]},
        {"name": "Education", "base_ctr": 0.011, "keywords": ["learn", "course", "certified", "skills", "bootcamp", "university"]}
    ]

    modifiers = [
        {"type": "urgency", "boost": 1.4, "words": ["hurry", "limited time", "ends tonight", "fast", "now"]},
        {"type": "trust", "boost": 1.2, "words": ["trusted", "guaranteed", "certified", "verified", "authentic"]},
        {"type": "discount", "boost": 1.3, "words": ["50% off", "save big", "cheap", "clearance"]},
        {"type": "generic", "boost": 1.0, "words": ["discover", "explore", "check out", "welcome"]}
    ]

    data = []
    for i in range(n):
        industry = np.random.choice(industries)
        mod = np.random.choice(modifiers)

        # Build realistic ad text
        text = f"{np.random.choice(mod['words']).capitalize()}! {np.random.choice(industry['keywords']).capitalize()} {np.random.choice(['offer', 'deals', 'now available', 'for you'])}. "
        text += f"{industry['name']} {np.random.choice(['solution', 'service', 'experts'])} you can trust."

        # Calculate "Actual" CTR based on benchmarks + modifiers + noise
        ctr = industry['base_ctr'] * mod['boost']
        ctr += np.random.normal(0, 0.002) # Small noise
        ctr = max(0.001, min(0.05, ctr)) # Clamp to realistic social CTR range

        data.append({
            "ad_text": text,
            "actual_ctr": ctr,
            "industry": industry['name'],
            "modifier": mod['type']
        })

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"Created {len(df)} realistic ads in {output_path}")
    return df

if __name__ == "__main__":
    create_realistic_ctr_data()
