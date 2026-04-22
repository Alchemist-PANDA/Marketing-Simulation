#!/usr/bin/env python3
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from campaigns.base import BaseCampaign
from analytics.reports import generate_summary

def compare():
    c1 = BaseCampaign("A/B Test - Standard", budget=500, strategy="default")
    c2 = BaseCampaign("A/B Test - Aggressive", budget=500, strategy="aggressive")

    r1 = generate_summary(c1.name, c1.run())
    r2 = generate_summary(c2.name, c2.run())

    print(f"{'Metric':<15} | {'Standard':<15} | {'Aggressive':<15}")
    print("-" * 50)
    for key in r1.keys():
        if key == "campaign": continue
        print(f"{key:<15} | {str(r1[key]):<15} | {str(r2[key]):<15}")

if __name__ == "__main__":
    compare()
