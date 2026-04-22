import os
import pandas as pd
import numpy as np

def generate_synthetic_data(n=1000):
    """Generates synthetic ad performance data."""
    print("Generating synthetic ad performance data...")
    data = []
    for i in range(n):
        price_score = np.random.uniform(0, 1)
        trust_score = np.random.uniform(0, 1)
        urgency_score = np.random.uniform(0, 1)

        # Simple linear model with some noise
        # CTR: Base 0.02 + weights
        true_ctr = 0.02 + 0.03 * price_score + 0.02 * trust_score + 0.01 * urgency_score + np.random.normal(0, 0.005)
        true_ctr = max(0.001, min(0.1, true_ctr))

        # CVR: Base 0.05 + weights
        true_cvr = 0.05 + 0.1 * price_score + 0.05 * trust_score + 0.03 * urgency_score + np.random.normal(0, 0.01)
        true_cvr = max(0.005, min(0.3, true_cvr))

        data.append({
            'ad_id': i,
            'text': f"Ad copy {i} with scores P:{price_score:.2f} T:{trust_score:.2f} U:{urgency_score:.2f}",
            'price_score': price_score,
            'trust_score': trust_score,
            'urgency_score': urgency_score,
            'actual_ctr': true_ctr,
            'actual_cvr': true_cvr
        })

    df = pd.DataFrame(data)
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/facebook_ads.csv', index=False)
    print(f"Synthetic data saved to data/facebook_ads.csv. Generated {n} rows.")
    return df

if __name__ == "__main__":
    df = generate_synthetic_data()
    print("\nFirst 5 rows of generated data:")
    print(df.head())
