import pandas as pd
import re

import sys
sys.path.append('.')
from scripts.holdout_validation_real import fix_data_columns
df = pd.read_csv('data/data.csv')
df = fix_data_columns(df)
df['cvr'] = df['total_conversion'] / df['impressions'].replace(0, 1)

df_map = pd.read_csv('data/mapping.csv')
df = df.merge(df_map[['ad_id', 'ad_text']], on='ad_id', how='left')

unique_groups = df['group_id'].unique()
import random
random.seed(42)
random.shuffle(unique_groups)

split_idx = int(len(unique_groups) * 0.7)
train_groups = set(unique_groups[:split_idx])
holdout_groups = set(unique_groups[split_idx:])

train_matches = 0
train_tot = 0
holdout_matches = 0
holdout_tot = 0

for k, g in df.groupby('group_id'):
    g = g.sort_values('cvr', ascending=False)
    winner_text = g.iloc[0]['ad_text']
    
    m = re.search(r'interest (\d+)', str(winner_text))
    matched = False
    if m:
        ad_interest = int(m.group(1))
        group_interests = [g.iloc[0]['interest1'], g.iloc[0]['interest2'], g.iloc[0]['interest3']]
        if ad_interest in group_interests:
            matched = True
            
    if k in train_groups:
        if matched: train_matches += 1
        train_tot += 1
    else:
        if matched: holdout_matches += 1
        holdout_tot += 1

print(f"Train Match: {train_matches}/{train_tot}")
print(f"Holdout Match: {holdout_matches}/{holdout_tot}")


