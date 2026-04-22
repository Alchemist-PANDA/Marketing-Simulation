import argparse
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.simulation.ab_test_runner import ABTestRunner

def main():
    parser = argparse.ArgumentParser(description='Marketing Simulation A/B Test CLI')
    parser.add_argument('--ad1', required=True, help='Text for the first ad creative')
    parser.add_argument('--ad2', required=True, help='Text for the second ad creative')
    parser.add_argument('--agents', type=int, default=500, help='Number of simulated agents (default: 500)')
    parser.add_argument('--channel', default='facebook', help='Marketing channel (facebook, tiktok, etc.)')

    args = parser.parse_args()

    print(f"Initializing simulation with {args.agents} agents...")
    runner = ABTestRunner(num_agents=args.agents)

    print(f"Running simulated A/B test on {args.channel}...")
    result = runner.run_test(args.ad1, args.ad2, channel=args.channel)

    print("\n--- RESULTS ---")
    print(f"Ad A ('{args.ad1[:30]}...'): {result['ad_a']['likes']} likes, {result['ad_a']['conversions']} conversions")
    print(f"Ad B ('{args.ad2[:30]}...'): {result['ad_b']['likes']} likes, {result['ad_b']['conversions']} conversions")
    print(f"Winner: Ad {result['winner']}")
    print(f"Lift: {result['lift_percentage']:.2f}%")

    print("\n--- FORENSIC ANALYSIS (Ad A) ---")
    for reason in result['ad_a']['analysis']['failure_reasons']:
        print(f"⚠️  {reason}")

    print("\n--- FORENSIC ANALYSIS (Ad B) ---")
    for reason in result['ad_b']['analysis']['failure_reasons']:
        print(f"⚠️  {reason}")

if __name__ == "__main__":
    main()
