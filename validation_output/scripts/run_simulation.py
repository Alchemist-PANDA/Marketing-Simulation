#!/usr/bin/env python3
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from campaigns.base import BaseCampaign
from analytics.reports import generate_summary

def main():
    print("Starting Marketing Simulation...")
    campaign = BaseCampaign("Spring Launch", budget=1000, strategy="optimized")
    results = campaign.run(iterations=500)
    summary = generate_summary(campaign.name, results)

    print("\n--- Simulation Results ---")
    for key, value in summary.items():
        print(f"{key.upper()}: {value}")

if __name__ == "__main__":
    main()
