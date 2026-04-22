import pandas as pd
import numpy as np
import os
import pickle
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, cross_validate
from sklearn.metrics import mean_absolute_error, r2_score
from sentence_transformers import SentenceTransformer
from scipy.stats import pearsonr

def train_direct_predictor(input_path='data/real_ctr.csv', model_path='models/direct_ctr_predictor.pkl'):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    os.makedirs('models', exist_ok=True)
    df = pd.read_csv(input_path)

    print("Loading all-MiniLM-L6-v2...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print(f"Embedding {len(df)} ads...")
    embeddings = model.encode(df['ad_text'].tolist(), show_progress_bar=True)
    y = df['actual_ctr'].values

    # 5-fold CV
    print("Running 5-fold Cross-Validation...")
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    mae_scores = []
    correlations = []

    for train_index, test_index in kf.split(embeddings):
        X_train, X_test = embeddings[train_index], embeddings[test_index]
        y_train, y_test = y[train_index], y[test_index]

        regressor = Ridge(alpha=1.0)
        regressor.fit(X_train, y_train)
        y_pred = regressor.predict(X_test)

        mae_scores.append(mean_absolute_error(y_test, y_pred))
        corr, _ = pearsonr(y_test, y_pred)
        correlations.append(corr)

    avg_mae = np.mean(mae_scores)
    avg_corr = np.mean(correlations)

    print(f"\n--- Direct Predictor Performance ---")
    print(f"Mean Absolute Error (MAE): {avg_mae:.6f}")
    print(f"Pearson Correlation: {avg_corr:.4f}")

    # Final fit and save
    final_regressor = Ridge(alpha=1.0)
    final_regressor.fit(embeddings, y)

    with open(model_path, 'wb') as f:
        pickle.dump(final_regressor, f)
    print(f"Model saved to {model_path}")

    return avg_mae, avg_corr

if __name__ == "__main__":
    train_direct_predictor()
