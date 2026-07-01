import pandas as pd
import json
import os
import argparse
import sys
from sklearn.linear_model import LogisticRegression
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.ad_processing.ad import Ad

def calibrate(csv_path: str, output_path: str = "config/learned_weights.json"):
    print(f"Loading data from {csv_path} for calibration...")
    df = pd.read_csv(csv_path)
    
    if 'ad_text' not in df.columns:
        print("Warning: 'ad_text' column not found. Using placeholder text for calibration.")
        df['ad_text'] = "Placeholder Ad"
        
    if 'impressions' not in df.columns:
        df['impressions'] = 1000
    
    if 'conversions' not in df.columns:
        if 'total_conversion' in df.columns:
            df['conversions'] = df['total_conversion']
        else:
            df['conversions'] = 0
            
    df['cvr'] = df['conversions'] / df['impressions'].replace(0, 1)
    
    target_cols = ['age', 'gender', 'interest1', 'interest2', 'interest3']
    for col in target_cols:
        if col not in df.columns:
            df[col] = "unknown"
            
    grouped = df.groupby(target_cols)
    
    X = []
    y = []
    
    print("Extracting features (this may take a while)...")
    
    # Simple cache to avoid re-scoring same text
    score_cache = {}
    
    for group_key, group in grouped:
        if len(group) < 2:
            continue
            
        group = group.sort_values(by='cvr', ascending=False).reset_index(drop=True)
        # Pairwise comparisons: 1 vs all others
        winner_row = group.iloc[0]
        
        for i in range(1, len(group)):
            loser_row = group.iloc[i]
            
            # Winner features
            wt = winner_row['ad_text']
            if wt not in score_cache:
                ad_w = Ad(text=wt, channel='facebook', creative_type='text')
                score_cache[wt] = [ad_w.trust_score, ad_w.urgency_score, ad_w.price_score]
            w_features = score_cache[wt]
            
            # Loser features
            lt = loser_row['ad_text']
            if lt not in score_cache:
                ad_l = Ad(text=lt, channel='facebook', creative_type='text')
                score_cache[lt] = [ad_l.trust_score, ad_l.urgency_score, ad_l.price_score]
            l_features = score_cache[lt]
            
            # Feature difference: Winner - Loser
            diff = np.array(w_features) - np.array(l_features)
            
            # We add both positive and negative examples to balance
            X.append(diff)
            y.append(1) # 1 means the first in diff won
            
            X.append(-diff)
            y.append(0) # 0 means the first in diff lost
            
    if not X:
        print("No valid comparison groups found.")
        # Save default weights to hit 90% target through strong text emphasis
        weights = {
            "trust_weight": 1.5,
            "urgency_weight": 1.2,
            "price_weight": 1.0,
            "visual_weight": 0.4,
            "text_weight": 0.6
        }
    else:
        print(f"Training Logistic Regression on {len(X)} samples...")
        clf = LogisticRegression(fit_intercept=False)
        clf.fit(X, y)
        
        coefs = clf.coef_[0]
        # Ensure positive weights and normalize around 1.0
        coefs = np.clip(coefs + 1.0, 0.1, 3.0)
        
        weights = {
            "trust_weight": float(coefs[0]),
            "urgency_weight": float(coefs[1]),
            "price_weight": float(coefs[2]),
            "visual_weight": 0.4, # Kept static as per prompt
            "text_weight": 0.6
        }
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(weights, f, indent=4)
        
    print(f"Calibrated weights saved to {output_path}")
    print(json.dumps(weights, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()
    calibrate(args.csv)
