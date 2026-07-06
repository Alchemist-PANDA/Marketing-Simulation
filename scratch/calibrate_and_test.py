import os
import json
import numpy as np
import pandas as pd
import sys
sys.path.append('.')
from src.simulation.multi_ad_runner import MultiAdRunner
from src.ad_processing.ad import Ad

# Load datasets
train_df = pd.read_csv('outputs/train_data.csv')
holdout_df = pd.read_csv('outputs/holdout_data.csv')

def parse_df(df):
    groups = []
    for k, g in df.groupby('group_id'):
        g = g.sort_values('cvr', ascending=False)
        actual_winner = str(g.iloc[0]['ad_id'])
        
        ads_payload = []
        for _, row in g.iterrows():
            ads_payload.append({
                'name': str(row['ad_id']), 
                'text': row['ad_text'], 
                'target_interest': row.get('target_interest', None)
            })
            
        target_audience = {
            'age': g.iloc[0]['age'],
            'gender': g.iloc[0]['gender'],
            'interest1': g.iloc[0].get('interest1', ''),
            'interest2': g.iloc[0].get('interest2', ''),
            'interest3': g.iloc[0].get('interest3', '')
        }
        groups.append((actual_winner, ads_payload, target_audience))
    return groups

train_groups = parse_df(train_df)
holdout_groups = parse_df(holdout_df)

print(f"Loaded {len(train_groups)} train groups and {len(holdout_groups)} holdout groups.")

runner = MultiAdRunner()

def evaluate(weights, groups_data):
    correct = 0
    for actual_winner, ads_payload, target_audience in groups_data:
        # Shuffle payload to avoid order bias (seeded)
        import random
        random.seed(42)
        random.shuffle(ads_payload)
        
        res = runner.run_multi_test(ads_payload, target_audience=target_audience, learned_weights=weights)
        predicted_winner = res['winner']['ad_name']
        if predicted_winner == actual_winner:
            correct += 1
    return correct / len(groups_data)

# Let's perform coordinate descent to find the optimal weights
# Weights to optimize: text_weight, visual_weight, trust_weight, urgency_weight, price_weight, emotion_weight
# We search text_weight in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0], and set visual_weight = 1.0 - text_weight
# We search other weights in [0.0, 1.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 15.0]

best_weights = {
    "text_weight": 0.8,
    "visual_weight": 0.2,
    "trust_weight": 8.0,
    "urgency_weight": 1.0,
    "price_weight": 2.0,
    "emotion_weight": 8.0
}

best_train_acc = evaluate(best_weights, train_groups)
print(f"Initial Train Acc: {best_train_acc:.4f}")

improved = True
step = 0
while improved and step < 10:
    improved = False
    step += 1
    print(f"\n--- Coordinate Descent Step {step} ---")
    
    # 1. Optimize text_weight and visual_weight
    best_tw = best_weights["text_weight"]
    for tw in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        if tw == best_tw:
            continue
        test_w = best_weights.copy()
        test_w["text_weight"] = tw
        test_w["visual_weight"] = round(1.0 - tw, 1)
        acc = evaluate(test_w, train_groups)
        if acc > best_train_acc:
            best_train_acc = acc
            best_weights = test_w
            improved = True
            print(f"Improved TW/VW to ({tw}, {test_w['visual_weight']}) -> Train Acc: {best_train_acc:.4f}")
            
    # 2. Optimize other weights
    for weight_key in ["trust_weight", "urgency_weight", "price_weight", "emotion_weight"]:
        current_val = best_weights[weight_key]
        for val in [0.0, 1.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 15.0]:
            if val == current_val:
                continue
            test_w = best_weights.copy()
            test_w[weight_key] = val
            acc = evaluate(test_w, train_groups)
            if acc > best_train_acc:
                best_train_acc = acc
                best_weights = test_w
                improved = True
                print(f"Improved {weight_key} to {val} -> Train Acc: {best_train_acc:.4f}")

print("\n--- Calibration Complete ---")
print("Best weights:", best_weights)
print(f"Best Train Accuracy: {best_train_acc:.4f}")

# Evaluate on Holdout
holdout_acc = evaluate(best_weights, holdout_groups)
print(f"Holdout Accuracy: {holdout_acc:.4f}")
