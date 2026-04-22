import pandas as pd
import numpy as np
import os
import pickle
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, cross_val_score
from sentence_transformers import SentenceTransformer

def train_scorer(input_path='data/labeled_ads.csv', model_dir='models'):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    os.makedirs(model_dir, exist_ok=True)
    df = pd.read_csv(input_path)

    print(f"Loading sentence-transformers/all-MiniLM-L6-v2...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print(f"Embedding {len(df)} ad texts...")
    embeddings = model.encode(df['text'].tolist(), show_progress_bar=True)

    targets = ['price_score', 'trust_score', 'urgency_score']
    for target in targets:
        print(f"\nTraining Ridge regression for {target}...")
        y = df[target].values

        # 5-fold CV
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        r2_scores = cross_val_score(Ridge(alpha=1.0), embeddings, y, cv=kf, scoring='r2')
        mae_scores = cross_val_score(Ridge(alpha=1.0), embeddings, y, cv=kf, scoring='neg_mean_absolute_error')

        print(f"R²: {np.mean(r2_scores):.4f} (±{np.std(r2_scores):.4f})")
        print(f"MAE: {-np.mean(mae_scores):.4f} (±{np.std(mae_scores):.4f})")

        # Final fit on all data
        regressor = Ridge(alpha=1.0)
        regressor.fit(embeddings, y)

        model_path = os.path.join(model_dir, f"{target.split('_')[0]}_scorer.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(regressor, f)
        print(f"Model saved to {model_path}")

    print("\nTraining complete.")

if __name__ == "__main__":
    train_scorer()
