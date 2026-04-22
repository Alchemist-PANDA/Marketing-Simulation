#!/usr/bin/env python3
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from campaigns.base import BaseCampaign

def scale(campaign_name, current_budget, factor=2.0):
    print(f"Scaling campaign '{campaign_name}' from ${current_budget} to ${current_budget * factor}...")
    # In a real prototype, this might update a database or config
    return current_budget * factor

if __name__ == "__main__":
    scale("Spring Launch", 1000)
