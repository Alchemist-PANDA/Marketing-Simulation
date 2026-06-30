import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from scipy.stats import pearsonr
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.ad_processing.ad import Ad

df = pd.read_csv('data/real_ctr.csv')
ads = [Ad(text=row['ad_text'], channel='facebook', creative_type='text') for _, row in df.iterrows()]

X = np.array([[ad.price_score, ad.trust_score, ad.urgency_score] for ad in ads])
y = df['actual_ctr'].values

model = Ridge()
model.fit(X, y)
preds = model.predict(X)
corr, _ = pearsonr(y, preds)
print(f"Max possible linear correlation with these 3 scores: {corr:.4f}")
