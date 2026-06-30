# 🏆 Strict Holdout Validation Report

## 📊 Summary of Split
- **Dataset**: `data/real_ctr.csv` (Synthetic but high-fidelity proxy)
- **Train Set (70%)**: 350 samples
- **Validation Set (15%)**: 75 samples
- **Test Set (15%)**: 75 samples

## 🤖 Direct Predictor Performance (Test Set)
- **Pearson Correlation**: 0.9101
- **Mean Absolute Error (MAE)**: 0.001672
- **Directional Accuracy**: 87.30%

## 🧪 ABM Simulation Performance (Test Set)
- **Pearson Correlation**: 0.3612
- **Mean Absolute Error (MAE)**: 0.005527
- **Directional Accuracy**: 64.10%

## ⚖️ Final Verdict
**9/10 not yet achieved.**
The Agent-Based Model needs further tuning to match the predictive power of the direct neural model on unseen data.