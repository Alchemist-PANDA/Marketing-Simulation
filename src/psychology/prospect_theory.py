"""
Pure math implementation of Prospect Theory (Kahneman & Tversky).
No API calls.
"""

import math

class ProspectTheoryEngine:
    def __init__(self, lambda_loss: float = 2.25):
        self.lambda_loss = lambda_loss # Loss aversion coefficient

    def apply(self, value: float, reference: float = 0.0) -> float:
        """
        Calculates subjective utility based on prospect theory.
        Losses hurt more than gains feel good.
        """
        x = value - reference

        if x >= 0:
            # Value function for gains: v(x) = x^alpha
            return math.pow(x, 0.88)
        else:
            # Value function for losses: v(x) = -lambda * (-x)^beta
            return -self.lambda_loss * math.pow(-x, 0.88)

    def probability_weight(self, p: float) -> float:
        """Overweight small probabilities, underweight large ones"""
        delta = 0.65
        num = math.pow(p, delta)
        den = math.pow(num + math.pow(1 - p, delta), 1 / delta)
        return num / den
