import json
import os
import sys
sys.path.append('.')
from scripts.calibrate_weights import evaluate_accuracy, calibrate
import pandas as pd

df = pd.read_csv('outputs/train_data.csv')
if 'group_id' in df.columns:
    grouped = df.groupby('group_id')
else:
    grouped = df.groupby(['age', 'gender', 'interest1', 'interest2', 'interest3'])

sorted_groups = []
for k, g in grouped:
    sorted_groups.append((k, g.sort_values('cvr', ascending=False)))

score_cache = {}

winners = []
for k, g in grouped:
    # First row is winner
    winners.append(g.iloc[0]['ad_text'])

from collections import Counter
print(Counter(winners))
