import os
import sys
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.simulation.ab_test_runner import ABTestRunner

def run_public_ab_validation():
    print("--- Public A/B Test Case Study Validation ---")
    print("Hypothesis: Ad B (Urgency/FOMO) should outperform Ad A (Generic Value) in a social context.")

    # Ad A: Generic Value (Benefit-oriented)
    ad_a_text = "Get our premium software and improve your team's productivity today. Great value for the price."

    # Ad B: Urgency/FOMO (Loss-aversion oriented)
    ad_b_text = "HURRY! Limited time offer ends at midnight. Don't miss your chance to save 50% on premium software!"

    num_agents = 10000
    runner = ABTestRunner(num_agents=num_agents)

    print(f"Simulating exposure to {num_agents} psychographic agents...")
    result = runner.run_test(ad_a_text, ad_b_text, channel='facebook')

    ctr_a = result['ad_a']['likes'] / num_agents
    ctr_b = result['ad_b']['likes'] / num_agents

    lift = result['lift_percentage']
    winner = result['winner']

    print(f"\n--- Simulation Results ---")
    print(f"Ad A (Generic): CTR {ctr_a:.4%}")
    print(f"Ad B (Urgent) : CTR {ctr_b:.4%}")
    print(f"Predicted Winner: Ad {winner}")
    print(f"Predicted Lift: {lift:.2f}%")

    # Benchmarking against public marketing data (e.g., CXL/WordStream benchmarks)
    # Most A/B tests for urgency see a 10% - 40% lift.
    if winner == 'B' and lift > 5:
        print("\nVERDICT: [SUCCESS] Simulation correctly predicted the psychological winner (Urgency).")
        print("Fidelity Score: High (Aligned with Prospect Theory & Market Benchmarks)")
    else:
        print("\nVERDICT: [FAILURE] Simulation did not detect the psychological lift of urgency.")

if __name__ == "__main__":
    run_public_ab_validation()
