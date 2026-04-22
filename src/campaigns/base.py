import random

class BaseCampaign:
    def __init__(self, name, budget, strategy="default"):
        self.name = name
        self.budget = budget
        self.strategy = strategy
        self.results = {
            "impressions": 0,
            "clicks": 0,
            "conversions": 0,
            "spend": 0
        }

    def run(self, iterations=100):
        """Simulate the campaign performance."""
        for _ in range(iterations):
            if self.results["spend"] >= self.budget:
                break

            # Simulated performance based on strategy
            cost_per_imp = random.uniform(0.01, 0.05)
            self.results["impressions"] += 100
            self.results["spend"] += cost_per_imp * 100

            ctr = 0.02 if self.strategy == "aggressive" else 0.01
            clicks = int(100 * ctr * random.uniform(0.8, 1.2))
            self.results["clicks"] += clicks

            conv_rate = 0.05 if self.strategy == "optimized" else 0.03
            self.results["conversions"] += int(clicks * conv_rate)

        return self.results
