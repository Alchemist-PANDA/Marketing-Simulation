import pandas as pd
import json
import os
import argparse
import sys
import numpy as np
from scipy.optimize import minimize

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.ad_processing.ad import Ad
from src.simulation.multi_ad_runner import MultiAdRunner

def evaluate_accuracy(weights, grouped_data, score_cache):
    tw, uw, pw, ew = weights
    correct = 0
    total = 0
    total_loss = 0.0
    
    for group_key, group in grouped_data:
        if len(group) < 2:
            continue
            
        actual_winner_idx = group.index[0]
        
        age_str = str(group.iloc[0]['age'])
        if '-' in age_str:
            age = int(age_str.split('-')[0])
        else:
            age = 35
            
        gender = group.iloc[0]['gender']
        
        # Approximate sensitivities
        price_sens = 0.5
        trust_sens = 0.3 + (0.2 if age > 50 else 0.0) + (0.1 if gender == 'F' else 0.0)
        urgency_sens = 0.4 + (0.2 if age < 30 else 0.0)
        
        # Shuffle group to prevent tie-breaker bias
        group = group.sample(frac=1.0, random_state=42)
        
        scores = []
        for i, row in group.iterrows():
            wt = row['ad_text']
            if wt not in score_cache:
                ad_w = Ad(text=wt, channel='facebook', creative_type='text')
                score_cache[wt] = [ad_w.trust_score, ad_w.urgency_score, ad_w.price_score, ad_w.emotion_score]
            
            t, u, p, e = score_cache[wt]
            
            # Recreate MaxSimulation utility approximation (text_weight=1.0)
            combined_trust = 1.0 * t
            combined_urgency = 1.0 * u
            combined_emotion = 1.0 * e
            
            emotional_mod = (combined_emotion - 0.5) * ew * 2.0
            archetype_score = (p * pw * price_sens) + (combined_trust * tw * trust_sens) + (combined_urgency * uw * urgency_sens)
            
            fomo_impact = combined_urgency * uw * 0.5
            perceived_value = 10.0 * (1.0 + emotional_mod + archetype_score + fomo_impact)
            
            scores.append((i, perceived_value))
            
        score_vals = np.array([x[1] for x in scores])
        exp_scores = np.exp(score_vals - np.max(score_vals))
        probs = exp_scores / np.sum(exp_scores)
        
        winner_local_pos = np.where([x[0] == actual_winner_idx for x in scores])[0][0]
        loss = -np.log(probs[winner_local_pos] + 1e-9)
        total_loss += loss
        
        predicted_winner_idx = scores[np.argmax(score_vals)][0]
        if predicted_winner_idx == actual_winner_idx:
            correct += 1
        total += 1
        
    acc = correct / total if total > 0 else 0
    avg_loss = total_loss / total if total > 0 else 0
    return acc, avg_loss

def objective(weights, grouped_data, score_cache):
    acc, loss = evaluate_accuracy(weights, grouped_data, score_cache)
    return loss

def calibrate(csv_path: str, output_path: str = "config/learned_weights.json", mapping_csv_path: str = None, identifier_col: str = None):
    print(f"Loading data from {csv_path} for calibration...")
    df = pd.read_csv(csv_path)
    
    if 'ad_text' not in df.columns:
        if mapping_csv_path and identifier_col:
            try:
                mapping_df = pd.read_csv(mapping_csv_path)
                text_col = [c for c in mapping_df.columns if c != identifier_col]
                if text_col:
                    mapping_df = mapping_df.rename(columns={text_col[0]: 'ad_text'})
                    df = df.merge(mapping_df[[identifier_col, 'ad_text']], on=identifier_col, how='left')
                    df['ad_text'] = df['ad_text'].fillna('Placeholder Ad').astype(str)
            except Exception as e:
                print(f"Error reading mapping CSV: {e}")
        else:
            print("Warning: 'ad_text' column not found.")
            df['ad_text'] = "Placeholder Ad"
            
    if 'impressions' not in df.columns:
        df['impressions'] = 1000
    if 'conversions' not in df.columns:
        if 'total_conversion' in df.columns:
            df = df.dropna(subset=['total_conversion'])
            df['conversions'] = df['total_conversion']
        else:
            df['conversions'] = 0
            
    df['cvr'] = df['conversions'] / df['impressions'].replace(0, 1)
    
    # We must use group_id if it exists, otherwise fall back to target_cols
    if 'group_id' in df.columns:
        grouped = df.groupby('group_id')
    else:
        target_cols = ['age', 'gender', 'interest1', 'interest2', 'interest3']
        for col in target_cols:
            if col not in df.columns:
                df[col] = "unknown"
        grouped = df.groupby(target_cols)
    
    # Sort groups by CVR so iloc[0] is always the winner
    sorted_groups = []
    for k, g in grouped:
        sorted_groups.append((k, g.sort_values('cvr', ascending=False)))
        
    score_cache = {}
    
    print("Running Grid Search to maximize Directional Accuracy...")
    
    best_acc = -1
    best_loss = float('inf')
    best_weights = [0.0, 0.0, 0.0, 0.0]
    
    # Grid search over 0.0, 1.0, 2.0, 3.0, 4.0
    for tw in [0.0, 1.0, 2.0, 3.0, 4.0]:
        for uw in [0.0, 1.0, 2.0, 3.0, 4.0]:
            for pw in [0.0, 1.0, 2.0, 3.0, 4.0]:
                for ew in [0.0, 1.0, 2.0, 3.0, 4.0]:
                    w = [tw, uw, pw, ew]
                    acc, loss = evaluate_accuracy(w, sorted_groups, score_cache)
                    
                    if acc > best_acc or (acc == best_acc and loss < best_loss):
                        best_acc = acc
                        best_loss = loss
                        best_weights = w
                        
    opt_weights = best_weights
    
    print(f"Calibration finished. Best Train Accuracy: {best_acc*100:.2f}%")
    print(f"Best Weights: {best_weights} with Loss {best_loss:.4f}")
    
    weights = {
        "trust_weight": float(opt_weights[0]),
        "urgency_weight": float(opt_weights[1]),
        "price_weight": float(opt_weights[2]),
        "emotion_weight": float(opt_weights[3]),
        "visual_weight": 0.4,
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
    parser.add_argument("--mapping_csv", default=None)
    parser.add_argument("--identifier_col", default=None)
    args = parser.parse_args()
    calibrate(args.csv, mapping_csv_path=args.mapping_csv, identifier_col=args.identifier_col)
