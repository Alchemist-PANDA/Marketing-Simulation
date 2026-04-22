"""
Calibration layer for marketing simulation outputs.

Uses historical data (predicted vs actual) to adjust new predictions
via scaling factors, with confidence increasing with dataset size.
"""

import math
from typing import List, Dict, Tuple, Optional

class Calibrator:
    """
    Calibrates CTR and CVR predictions using historical data.

    Approach:
    - Compute scaling factors from historical data: factor = mean(actual) / mean(predicted)
    - Apply factor to new predictions
    - Confidence score = 1 - exp(-n / reference_n) where n = number of historical samples
    """

    def __init__(self, reference_n: int = 100):
        """
        Args:
            reference_n: Number of historical samples needed for ~63% confidence
                         (1 - 1/e). Confidence grows with more data.
        """
        self.reference_n = reference_n
        self.ctr_factor = 1.0
        self.cvr_factor = 1.0
        self.fitted = False
        self.num_samples = 0

    def fit(self, historical_data: List[Dict[str, float]]):
        """
        Fit calibrator on historical data.

        Args:
            historical_data: List of dicts with keys:
                - predicted_ctr (float)
                - actual_ctr (float)
                - predicted_cvr (float)
                - actual_cvr (float)
        """
        if not historical_data:
            self.fitted = False
            self.num_samples = 0
            self.ctr_factor = 1.0
            self.cvr_factor = 1.0
            return

        n = len(historical_data)
        self.num_samples = n

        # Compute means
        pred_ctr_sum = 0.0
        actual_ctr_sum = 0.0
        pred_cvr_sum = 0.0
        actual_cvr_sum = 0.0

        for record in historical_data:
            pred_ctr_sum += record.get('predicted_ctr', 0.0)
            actual_ctr_sum += record.get('actual_ctr', 0.0)
            pred_cvr_sum += record.get('predicted_cvr', 0.0)
            actual_cvr_sum += record.get('actual_cvr', 0.0)

        mean_pred_ctr = pred_ctr_sum / n
        mean_actual_ctr = actual_ctr_sum / n
        mean_pred_cvr = pred_cvr_sum / n
        mean_actual_cvr = actual_cvr_sum / n

        # Compute scaling factors (avoid division by zero)
        self.ctr_factor = mean_actual_ctr / mean_pred_ctr if mean_pred_ctr > 1e-6 else 1.0
        self.cvr_factor = mean_actual_cvr / mean_pred_cvr if mean_pred_cvr > 1e-6 else 1.0

        # Clamp factors to reasonable range [0.2, 5.0] to avoid extreme adjustments
        self.ctr_factor = max(0.2, min(5.0, self.ctr_factor))
        self.cvr_factor = max(0.2, min(5.0, self.cvr_factor))

        self.fitted = True

    def calibrate(self, predicted_ctr: float, predicted_cvr: float) -> Tuple[float, float, float]:
        """
        Apply calibration to new predictions.

        Returns:
            (adjusted_ctr, adjusted_cvr, confidence_score) where confidence in [0,1]
        """
        if not self.fitted or self.num_samples == 0:
            # No calibration data: return original with zero confidence
            return predicted_ctr, predicted_cvr, 0.0

        # Apply scaling factors
        adjusted_ctr = predicted_ctr * self.ctr_factor
        adjusted_cvr = predicted_cvr * self.cvr_factor

        # Clamp to [0,1]
        adjusted_ctr = max(0.0, min(1.0, adjusted_ctr))
        adjusted_cvr = max(0.0, min(1.0, adjusted_cvr))

        # Confidence based on sample size: 1 - exp(-n / reference_n)
        confidence = 1.0 - math.exp(-self.num_samples / self.reference_n)

        return adjusted_ctr, adjusted_cvr, confidence

    def get_calibration_summary(self) -> Dict:
        """Return summary of calibration state."""
        return {
            "fitted": self.fitted,
            "num_samples": self.num_samples,
            "ctr_factor": self.ctr_factor,
            "cvr_factor": self.cvr_factor,
            "reference_n": self.reference_n
        }

def calibrate_predictions(predicted_ctr: float,
                          predicted_cvr: float,
                          historical_data: List[Dict[str, float]],
                          reference_n: int = 100) -> Dict:
    """
    One-shot calibration: fit on historical_data and calibrate predictions.

    Returns:
        Dict with keys: adjusted_ctr, adjusted_cvr, confidence_score
    """
    calibrator = Calibrator(reference_n=reference_n)
    calibrator.fit(historical_data)
    adj_ctr, adj_cvr, conf = calibrator.calibrate(predicted_ctr, predicted_cvr)
    return {
        "adjusted_ctr": adj_ctr,
        "adjusted_cvr": adj_cvr,
        "confidence_score": conf,
        "calibration_summary": calibrator.get_calibration_summary()
    }

if __name__ == "__main__":
    # Example usage
    historical = [
        {"predicted_ctr": 0.05, "actual_ctr": 0.04, "predicted_cvr": 0.10, "actual_cvr": 0.08},
        {"predicted_ctr": 0.08, "actual_ctr": 0.07, "predicted_cvr": 0.12, "actual_cvr": 0.10},
    ]

    pred_ctr, pred_cvr = 0.06, 0.11
    result = calibrate_predictions(pred_ctr, pred_cvr, historical, reference_n=10)
    print(f"Original: CTR={pred_ctr}, CVR={pred_cvr}")
    print(f"Adjusted: CTR={result['adjusted_ctr']:.4f}, CVR={result['adjusted_cvr']:.4f}")
    print(f"Confidence: {result['confidence_score']:.2f}")
