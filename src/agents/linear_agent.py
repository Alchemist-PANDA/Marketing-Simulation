from dataclasses import dataclass
import math
import numpy as np

@dataclass
class LinearAgent:
    """A simplified agent that uses a linear utility function for decisions."""

    def evaluate_ad(self, ad, weights):
        """
        Calculates click probability based on linear weights.
        weights: {'w_price': float, 'w_trust': float, 'w_urgency': float, 'bias': float, 'sigmoid_scale': float}
        """
        # Linear combination of ad scores
        utility = (
            weights.get('w_price', 0.0) * ad.price_score +
            weights.get('w_trust', 0.0) * ad.trust_score +
            weights.get('w_urgency', 0.0) * ad.urgency_score +
            weights.get('bias', 0.0)
        )

        # Logistic activation
        scale = weights.get('sigmoid_scale', 1.0)
        prob = 1.0 / (1.0 + math.exp(-utility / scale))
        return prob
