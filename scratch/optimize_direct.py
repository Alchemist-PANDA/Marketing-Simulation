import os
import json
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import sys
sys.path.append('.')
from src.simulation.multi_ad_runner import MultiAdRunner
# Load training data
df = pd.read_csv('outputs/train_data.csv')
mask = df['impressions'].astype(str).str.contains('-', na=False)
shifted = df[mask].copy()
cols = shifted.columns.tolist()
shifted[cols[2:]] = shifted[cols[1:-1]]
shifted['age'] = '35-39'
df.update(shifted)
df['cvr'] = df['total_conversion'] / df['impressions'].replace(0, 1)

groups = []
for k, g in df.groupby('group_id'):
    g = g.sort_values('cvr', ascending=False)
    actual_winner = str(g.iloc[0]['ad_id'])
    
    ads_payload = []
    for _, row in g.iterrows():
        ads_payload.append({'name': str(row['ad_id']), 'text': row['ad_text']})
        
    target_audience = {
        'age': g.iloc[0]['age'],
        'gender': g.iloc[0]['gender']
    }
    groups.append((actual_winner, ads_payload, target_audience))

runner = MultiAdRunner(num_agents=1000)

def evaluate_weights(w):
    tw, uw, pw, ew = w
    # Update config
    cfg = {
        "trust_weight": float(tw),
        "urgency_weight": float(uw),
        "price_weight": float(pw),
        "emotion_weight": float(ew),
        "visual_weight": 0.4,
        "text_weight": 0.6
    }
    with open('config/learned_weights.json', 'w') as f:
        json.dump(cfg, f)
        
    correct = 0
    for actual_winner, ads_payload, target_audience in groups:
        res = runner.run_multi_test(ads_payload, target_audience=target_audience)
        predicted_winner = res['winner']['ad_name']
        if predicted_winner == actual_winner:
            correct += 1
            
    accuracy = correct / len(groups)
    print(f"Weights {w} -> Acc: {accuracy:.4f}")
    return -accuracy

print("Starting Nelder-Mead optimization directly on MaxSimulation...")
w0 = np.array([2.0, 2.0, 2.0, 2.0])
res = minimize(evaluate_weights, w0, method='Nelder-Mead', options={'maxiter': 50})
print("Best weights:", res.x)
evaluate_weights(res.x)
