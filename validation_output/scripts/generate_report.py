#!/usr/bin/env python3
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

def main():
    print("Generating performance report...")
    # Mock data for demonstration
    report_data = {
        "timestamp": "2026-04-22",
        "total_spend": 4500.20,
        "total_conversions": 120,
        "average_roi": 1.4
    }

    report_path = os.path.join(os.path.dirname(__file__), "../report.json")
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=4)
    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    main()
