"""
Prediction accuracy evaluation module for marketing simulation.

Metrics:
- Mean Absolute Error (MAE)
- Mean Absolute Percentage Error (MAPE)

Calculates the precision of simulation outputs compared to real-world ground truth.
"""

from typing import List, Dict

def evaluate_accuracy(predicted_ctr: List[float],
                      actual_ctr: List[float],
                      predicted_cvr: List[float],
                      actual_cvr: List[float]) -> Dict[str, float]:
    """
    Evaluate prediction accuracy for CTR and CVR.

    Args:
        predicted_ctr: List of predicted CTR values
        actual_ctr: List of actual CTR values
        predicted_cvr: List of predicted CVR values
        actual_cvr: List of actual CVR values

    Returns:
        Dictionary with MAE for both metrics and an average percentage error.
    """

    def calculate_mae(pred: List[float], actual: List[float]) -> float:
        if not pred or len(pred) == 0:
            return 0.0
        return sum(abs(p - a) for p, a in zip(pred, actual)) / len(pred)

    def calculate_mape(pred: List[float], actual: List[float]) -> float:
        if not pred or len(pred) == 0:
            return 0.0
        errors = []
        for p, a in zip(pred, actual):
            if a == 0:
                # Handle edge case where actual is zero
                errors.append(0.0 if p == 0 else 100.0)
            else:
                errors.append(abs(p - a) / a * 100.0)
        return sum(errors) / len(pred)

    mae_ctr = calculate_mae(predicted_ctr, actual_ctr)
    mae_cvr = calculate_mae(predicted_cvr, actual_cvr)

    mape_ctr = calculate_mape(predicted_ctr, actual_ctr)
    mape_cvr = calculate_mape(predicted_cvr, actual_cvr)

    # Average percentage error across both metrics for a single "Accuracy" score
    avg_percentage_error = (mape_ctr + mape_cvr) / 2.0

    return {
        "mae_ctr": round(mae_ctr, 6),
        "mae_cvr": round(mae_cvr, 6),
        "avg_percentage_error": round(avg_percentage_error, 2)
    }

if __name__ == "__main__":
    # Test sample data
    p_ctr = [0.05, 0.08, 0.03, 0.10]
    a_ctr = [0.04, 0.07, 0.03, 0.09]

    p_cvr = [0.10, 0.12, 0.09, 0.15]
    a_cvr = [0.08, 0.10, 0.09, 0.13]

    result = evaluate_accuracy(p_ctr, a_ctr, p_cvr, a_cvr)
    print(f"Accuracy Evaluation:")
    print(f" - MAE (CTR): {result['mae_ctr']}")
    print(f" - MAE (CVR): {result['mae_cvr']}")
    print(f" - Avg % Error: {result['avg_percentage_error']}%")
