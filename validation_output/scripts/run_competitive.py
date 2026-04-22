#!/usr/bin/env python3
"""
Script to run and analyze competitive market simulations.
"""

import sys
import os

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.competitive import create_sample_market, CompetitiveMarket, Competitor


def run_simulation(steps: int = 12):
    """Run a competitive market simulation for multiple steps."""
    market = create_sample_market()

    print(f"--- INITIAL MARKET SUMMARY ---")
    summary = market.get_summary()
    print(f"Competitors: {summary['n_competitors']}")
    print(f"Leader: {summary['market_leader']} ({summary['leader_share']:.1%})")
    print(f"Concentration (HHI): {summary['market_concentration_hhi']:.0f}")
    print(f"Competitive Intensity: {summary['competitive_intensity']:.2f}")
    print("-" * 30)

    # Simulation loop
    for step in range(1, steps + 1):
        # Define marketing actions for this step
        # Simulate different scenarios:
        # 1. Market Leader maintains budget
        # 2. Strong Challenger increases budget by 50%
        # 3. New Entrant doubles budget

        actions = {
            "Market Leader": 500_000,
            "Strong Challenger": 600_000,
            "Value Player": 250_000,
            "Niche Premium": 200_000,
            "New Entrant": 300_000
        }

        # In later steps, adjust actions based on performance
        if step > 6:
            # Market Leader reacts to Challenger's growth
            actions["Market Leader"] = 750_000
            # Value Player tries to regain share
            actions["Value Player"] = 400_000

        results = market.simulate_step(actions)

        if step % 3 == 0 or step == 1 or step == steps:
            print(f"\n--- STEP {step} RESULTS ---")
            leader, share = market.get_market_leader()
            print(f"Leader: {leader} ({share:.1%})")

            # Print highlights
            for name, data in results.items():
                change = data['share_change']
                sign = "+" if change >= 0 else ""
                print(f"{name:18} | Share: {data['market_share']:.1%} ({sign}{change:.2%}) | Brand: {data['brand_strength']:.1f}")

    print("\n" + "=" * 50)
    print("FINAL MARKET SUMMARY")
    print("=" * 50)
    final_summary = market.get_summary()
    print(f"Leader: {final_summary['market_leader']} ({final_summary['leader_share']:.1%})")
    print(f"Concentration (HHI): {final_summary['market_concentration_hhi']:.0f}")

    # Analysis of winners and losers
    initial = market.history[0]['results']
    final = market.history[-1]['results']

    print("\nMarket Performance Analysis:")
    for name in final:
        initial_share = initial[name]['market_share']
        final_share = final[name]['market_share']
        share_change = (final_share - initial_share) / initial_share

        status = "WINNER" if share_change > 0.05 else "LOSER" if share_change < -0.05 else "STABLE"
        print(f"{name:18}: {initial_share:.1%} -> {final_share:.1%} ({share_change:+.1%}) [{status}]")


if __name__ == "__main__":
    print("Starting Competitive Market Simulation...")
    run_simulation(steps=12)
    print("\nSimulation complete.")
