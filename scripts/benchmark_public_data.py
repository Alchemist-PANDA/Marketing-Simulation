import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.simulation.max_engine import MaxSimulation
from src.ad_processing.ad import Ad

def infer_scores(text):
    text = text.lower()
    price_score = 0.5
    trust_score = 0.5
    urgency_score = 0.5

    # Heuristic price score
    if any(w in text for w in ["discount", "cheap", "sale", "low price", "off", "save"]):
        price_score = 0.8
    elif any(w in text for w in ["premium", "luxury", "expensive", "exclusive"]):
        price_score = 0.3

    # Heuristic trust score
    if any(w in text for w in ["trusted", "review", "guarantee", "award", "certified", "verified", "authentic"]):
        trust_score = 0.8
    elif any(w in text for w in ["new", "unknown", "hidden"]):
        trust_score = 0.4

    # Heuristic urgency score
    if any(w in text for w in ["limited time", "today only", "last chance", "hurry", "now", "quick"]):
        urgency_score = 0.8

    return price_score, trust_score, urgency_score

def benchmark_public_data(num_agents=2000):
    if not os.path.exists('data/facebook_ads.csv'):
        print("Data file not found. Skipping benchmark.")
        return

    print(f"Benchmarking against data/facebook_ads.csv with {num_agents} agents...")
    df = pd.read_csv('data/facebook_ads.csv')
    sim = MaxSimulation(num_agents=num_agents)

    predicted_ctrs = []
    predicted_cvrs = []

    # Limit to 50 rows for speed
    test_df = df.head(50).copy()

    for idx, row in tqdm(test_df.iterrows(), total=len(test_df)):
        # Infer scores from text (or use the ones we generated if synthetic)
        p_s, t_s, u_s = infer_scores(row['text'])

        ad = Ad(text=row['text'], channel="facebook", creative_type="text", price=10.0,
                price_score=p_s, trust_score=t_s, urgency_score=u_s)

        res = sim.simulate_exposure(ad)
        predicted_ctrs.append(res['likes'] / num_agents)
        predicted_cvrs.append(res['conversions'] / max(1, res['likes']))

    test_df['predicted_ctr'] = predicted_ctrs
    test_df['predicted_cvr'] = predicted_cvrs

    # Compute correlation
    corr_ctr = test_df['actual_ctr'].corr(test_df['predicted_ctr'])
    corr_cvr = test_df['actual_cvr'].corr(test_df['predicted_cvr'])

    print(f"\n--- Public Benchmark Metrics ---")
    print(f"CTR Correlation: {corr_ctr:.4f}")
    print(f"CVR Correlation: {corr_cvr:.4f}")

    # Plot
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    sns.scatterplot(data=test_df, x='actual_ctr', y='predicted_ctr')
    plt.title('Actual vs Predicted CTR')

    plt.subplot(1, 2, 2)
    sns.scatterplot(data=test_df, x='actual_cvr', y='predicted_cvr')
    plt.title('Actual vs Predicted CVR')

    plt.tight_layout()
    plt.savefig('outputs/public_benchmark.png')
    print("Benchmark plots saved to outputs/public_benchmark.png")

if __name__ == "__main__":
    benchmark_public_data()
