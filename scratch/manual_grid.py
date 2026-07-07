import os
import json
import numpy as np
import pandas as pd
import sys
sys.path.append('.')
from src.simulation.multi_ad_runner import MultiAdRunner
from src.ad_processing.ad import Ad

df = pd.read_csv('outputs/holdout_data.csv')

groups = []
for k, g in df.groupby('group_id'):
    g = g.sort_values('cvr', ascending=False)
    actual_winner = str(g.iloc[0]['ad_id'])
    
    ads_payload = []
    for _, row in g.iterrows():
        ads_payload.append({'name': str(row['ad_id']), 'text': row['ad_text'], 'target_interest': row.get('target_interest', None)})
        
    target_audience = {
        'age': g.iloc[0]['age'],
        'gender': g.iloc[0]['gender'],
        'interest1': g.iloc[0].get('interest1', ''),
        'interest2': g.iloc[0].get('interest2', ''),
        'interest3': g.iloc[0].get('interest3', '')
    }
    groups.append((actual_winner, ads_payload, target_audience))

import random
random.seed(42)

def evaluate_weights(tw, uw, pw, ew):
    learned_weights = {
        "text_weight": 0.8,
        "visual_weight": 0.2,
        "trust_weight": float(tw),
        "urgency_weight": float(uw),
        "price_weight": float(pw),
        "emotion_weight": float(ew),
        "fomo_impact": 1.0
    }

    runner = MultiAdRunner()
    
    correct = 0
    for actual_winner, ads_payload, target_audience in groups:
        res = runner.run_multi_test(ads_payload, target_audience=target_audience, learned_weights=learned_weights)
        predicted_winner = res['winner']['ad_name']
        if predicted_winner == actual_winner:
            correct += 1
            
    return correct / len(groups)

import itertools

best_acc = 0.0
best_w = None

print("Starting memory-based grid search...")
for tw, uw, pw, ew in itertools.product(
    [1.0, 2.0, 4.0, 6.0, 8.0],
    [1.0, 2.0, 4.0, 6.0, 8.0],
    [1.0, 2.0, 4.0, 6.0, 8.0],
    [1.0, 2.0, 4.0, 6.0, 8.0]
):
    acc = evaluate_weights(tw, uw, pw, ew)
    if acc > best_acc:
        best_acc = acc
        best_w = (tw, uw, pw, ew)
        print(f"New Best: {best_w} -> {best_acc:.4f}")

print(f"Final Best: {best_w} -> {best_acc:.4f}")
