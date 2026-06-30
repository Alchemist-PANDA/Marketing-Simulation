import pandas as pd
from scipy.stats import pearsonr
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.ad_processing.ad import Ad

def check_scores():
    df = pd.read_csv('data/real_ctr.csv').head(100)
    data = []
    for _, row in df.iterrows():
        ad = Ad(text=row['ad_text'], channel='facebook', creative_type='text')
        data.append({
            'actual_ctr': row['actual_ctr'],
            'price_score': ad.price_score,
            'trust_score': ad.trust_score,
            'urgency_score': ad.urgency_score
        })

    score_df = pd.DataFrame(data)
    for col in ['price_score', 'trust_score', 'urgency_score']:
        corr, _ = pearsonr(score_df['actual_ctr'], score_df[col])
        print(f"Correlation of {col} with actual_ctr: {corr:.4f}")

if __name__ == "__main__":
    check_scores()
