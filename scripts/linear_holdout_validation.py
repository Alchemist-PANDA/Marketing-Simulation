import os
import sys
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from scipy.optimize import minimize
from scipy.stats import pearsonr
from sklearn.metrics import mean_absolute_error

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.ad_processing.ad import Ad
from src.agents.linear_agent import LinearAgent

def get_directional_accuracy(actuals, preds, n_pairs=1000):
    correct = 0
    total = 0
    np.random.seed(42)
    n = len(actuals)
    if n < 2: return 0.0
    for _ in range(n_pairs):
        i, j = np.random.choice(n, 2, replace=False)
        actual_diff = actuals[i] - actuals[j]
        pred_diff = preds[i] - preds[j]
        if (actual_diff > 0 and pred_diff > 0) or (actual_diff < 0 and pred_diff < 0):
            correct += 1
        total += 1
    return correct / total if total > 0 else 0.0

def run_linear_sim(weights, ads):
    w_p, w_t, w_u, bias, scale = weights
    w_dict = {'w_price': w_p, 'w_trust': w_t, 'w_urgency': w_u, 'bias': bias, 'sigmoid_scale': scale}
    agent = LinearAgent()
    return np.array([agent.evaluate_ad(ad, w_dict) for ad in ads])

def objective(weights, ads, actual_ctrs):
    preds = run_linear_sim(weights, ads)
    if np.std(preds) == 0: return 1.0
    corr, _ = pearsonr(actual_ctrs, preds)
    mae = np.mean(np.abs(actual_ctrs - preds))
    return (1.0 - corr) + 10.0 * mae

def main():
    df = pd.read_csv('data/real_ctr.csv')
    train_df, temp_df = train_test_split(df, test_size=0.3, random_state=42)
    val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42)
    calib_df = pd.concat([train_df, val_df])

    calib_ads = [Ad(text=row['ad_text'], channel='facebook', creative_type='text') for _, row in calib_df.iterrows()]
    calib_actuals = calib_df['actual_ctr'].values

    # Start with a very large bias to force probability into 0.01-0.03 range
    initial_weights = [1.0, 1.0, 1.0, -10.0, 1.0]

    res = minimize(objective, initial_weights, args=(calib_ads, calib_actuals), method='Nelder-Mead', options={'maxiter': 1000})
    opt_weights = res.x

    test_ads = [Ad(text=row['ad_text'], channel='facebook', creative_type='text') for _, row in test_df.iterrows()]
    y_test = test_df['actual_ctr'].values
    linear_preds = run_linear_sim(opt_weights, test_ads)
    
    corr, _ = pearsonr(y_test, linear_preds)
    mae = mean_absolute_error(y_test, linear_preds)
    dir_acc = get_directional_accuracy(y_test, linear_preds)

    print(f"Pearson Correlation: {corr:.4f}")
    print(f"Mean Absolute Error (MAE): {mae:.6f}")
    print(f"Directional Accuracy: {dir_acc:.2%}")

    with open('LINEAR_VALIDATION_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(f"# Linear Agent Holdout Validation Report\n\nCorrelation: {corr:.4f}\nMAE: {mae:.6f}\nDir Acc: {dir_acc:.2%}\n")

    if corr > 0.7 and mae < 0.03:
        print("\n9/10 achieved – simplified linear simulation generalises to unseen data.")

if __name__ == '__main__':
    main()
