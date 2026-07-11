"""
Phase 1 experiment: quantify the tie problem and the sign problem
using the already-computed backtest results (no re-simulation needed).

Questions:
1. If we INVERT the simulator's picks, what accuracy do we get? (sign audit)
2. How many ties come from identical keyword scores?
"""

import csv

RESULTS = "/home/user/Marketing-Simulation/validation_data/backtest_results.csv"

with open(RESULTS, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

total = len(rows)
ties = sum(1 for r in rows if r["sim_winner"] == "TIE")
correct = sum(1 for r in rows if r["correct"] == "True")

# Inverted decision: pick B whenever sim picked A and vice versa; ties stay ties
inv_correct = sum(1 for r in rows if r["sim_winner"] == "B")

# Non-tie subset
non_tie = [r for r in rows if r["sim_winner"] != "TIE"]
nt_correct = sum(1 for r in non_tie if r["correct"] == "True")

print(f"Total pairs:              {total}")
print(f"Ties:                     {ties} ({ties/total*100:.1f}%)")
print(f"Baseline accuracy:        {correct}/{total} = {correct/total*100:.1f}%")
print(f"INVERTED picks accuracy:  {inv_correct}/{total} = {inv_correct/total*100:.1f}%")
print(f"Non-tie subset:           {nt_correct}/{len(non_tie)} = {nt_correct/len(non_tie)*100:.1f}%")
print(f"Non-tie INVERTED:         {len(non_tie)-nt_correct}/{len(non_tie)} = {(len(non_tie)-nt_correct)/len(non_tie)*100:.1f}%")
