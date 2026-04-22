#!/usr/bin/env python3
"""
Campaign Performance Prediction Script

Predicts campaign performance metrics using trained models.
"""

import sys
import os
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from analytics.predictive import (
    CampaignPredictor,
    TimeSeriesForecaster,
    BudgetOptimizer,
    generate_sample_predictions
)
import pandas as pd
import numpy as np


def load_historical_data(data_path: str) -> pd.DataFrame:
    """Load historical campaign data for training."""
    if not os.path.exists(data_path):
        print(f"Warning: {data_path} not found, generating sample data")
        return generate_training_data()

    if data_path.endswith('.csv'):
        return pd.read_csv(data_path)
    elif data_path.endswith('.json'):
        return pd.read_json(data_path)
    else:
        raise ValueError("Unsupported file format. Use CSV or JSON.")


def generate_training_data(n_samples: int = 100) -> pd.DataFrame:
    """Generate synthetic training data for demonstration."""
    np.random.seed(42)

    channels = ['social_media', 'search', 'email', 'display', 'video']
    data = []

    for i in range(n_samples):
        budget = np.random.uniform(1000, 100000)
        channel = np.random.choice(channels)
        duration = np.random.randint(7, 90)
        audience_size = np.random.randint(5000, 500000)

        # Simulate realistic performance metrics
        channel_effectiveness = {
            'social_media': 1.2,
            'search': 1.5,
            'email': 1.8,
            'display': 0.9,
            'video': 1.3
        }

        effectiveness = channel_effectiveness[channel]
        base_conversion_rate = 0.02 * effectiveness

        conversions = budget * base_conversion_rate * (1 + np.random.normal(0, 0.2))
        revenue = conversions * np.random.uniform(50, 200)
        engagement = audience_size * np.random.uniform(0.05, 0.15) * effectiveness

        data.append({
            'campaign_id': f'HIST_{i+1:03d}',
            'budget': budget,
            'channel': channel,
            'duration_days': duration,
            'audience_size': audience_size,
            'start_date': f'2025-{np.random.randint(1, 13):02d}-{np.random.randint(1, 28):02d}',
            'conversions': max(0, conversions),
            'revenue': max(0, revenue),
            'engagement': max(0, engagement),
            'previous_conversions': np.random.uniform(0, 100),
            'previous_conversion_rate': np.random.uniform(0.01, 0.05)
        })

    return pd.DataFrame(data)


def predict_campaign(predictor: CampaignPredictor, config: dict) -> dict:
    """Predict performance for a single campaign configuration."""
    print("\nCampaign Configuration:")
    print("-" * 50)
    for key, value in config.items():
        print(f"  {key}: {value}")

    print("\nPredictions:")
    print("-" * 50)

    # Basic prediction
    predictions = predictor.predict(config)

    for metric, value in predictions.items():
        print(f"  {metric}: {value:.2f}")

    # Prediction with confidence intervals
    print("\nConfidence Intervals:")
    print("-" * 50)

    confidence_predictions = predictor.predict_with_confidence(config)

    for metric, (pred, lower, upper) in confidence_predictions.items():
        print(f"  {metric}: {pred:.2f} (95% CI: {lower:.2f} - {upper:.2f})")

    # Calculate ROI
    if 'revenue' in predictions and 'budget' in config:
        roi = (predictions['revenue'] - config['budget']) / config['budget'] * 100
        print(f"\n  Predicted ROI: {roi:.2f}%")

    return predictions


def optimize_budget(predictor: CampaignPredictor,
                   total_budget: float,
                   channels: list) -> dict:
    """Optimize budget allocation across channels."""
    print(f"\nOptimizing budget allocation for ${total_budget:,.2f}")
    print(f"Channels: {', '.join(channels)}")
    print("-" * 50)

    optimizer = BudgetOptimizer(predictor)
    allocation = optimizer.optimize_allocation(total_budget, channels)

    print("\nOptimal Allocation:")
    for channel, budget in allocation.items():
        percentage = (budget / total_budget) * 100
        print(f"  {channel}: ${budget:,.2f} ({percentage:.1f}%)")

    # Predict performance for each channel
    print("\nExpected Performance by Channel:")
    print("-" * 50)

    total_conversions = 0
    total_revenue = 0

    for channel, budget in allocation.items():
        config = {
            'budget': budget,
            'channel': channel,
            'duration_days': 30,
            'audience_size': 10000
        }

        predictions = predictor.predict(config)
        conversions = predictions.get('conversions', 0)
        revenue = predictions.get('revenue', 0)

        total_conversions += conversions
        total_revenue += revenue

        print(f"  {channel}:")
        print(f"    Conversions: {conversions:.0f}")
        print(f"    Revenue: ${revenue:,.2f}")

    print(f"\nTotal Expected:")
    print(f"  Conversions: {total_conversions:.0f}")
    print(f"  Revenue: ${total_revenue:,.2f}")
    print(f"  ROI: {((total_revenue - total_budget) / total_budget * 100):.2f}%")

    return allocation


def scenario_analysis(predictor: CampaignPredictor,
                     channel: str,
                     budget_range: tuple) -> pd.DataFrame:
    """Perform scenario analysis across budget range."""
    print(f"\nScenario Analysis: {channel}")
    print(f"Budget Range: ${budget_range[0]:,.2f} - ${budget_range[1]:,.2f}")
    print("-" * 50)

    optimizer = BudgetOptimizer(predictor)
    scenarios = optimizer.simulate_scenarios(budget_range, channel, steps=10)

    print("\nScenario Results:")
    print(scenarios.to_string(index=False))

    # Find optimal budget
    optimal_idx = scenarios['predicted_roi'].idxmax()
    optimal_budget = scenarios.loc[optimal_idx, 'budget']
    optimal_roi = scenarios.loc[optimal_idx, 'predicted_roi']

    print(f"\nOptimal Budget: ${optimal_budget:,.2f}")
    print(f"Expected ROI: {optimal_roi * 100:.2f}%")

    return scenarios


def main():
    parser = argparse.ArgumentParser(
        description='Predict campaign performance using trained models'
    )

    parser.add_argument(
        '--mode',
        choices=['predict', 'optimize', 'scenario', 'train'],
        default='predict',
        help='Prediction mode'
    )

    parser.add_argument(
        '--data',
        type=str,
        help='Path to historical data (CSV or JSON)'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Campaign configuration (JSON string or file path)'
    )

    parser.add_argument(
        '--budget',
        type=float,
        help='Total budget for optimization'
    )

    parser.add_argument(
        '--channels',
        type=str,
        nargs='+',
        default=['social_media', 'search', 'email'],
        help='Channels for optimization'
    )

    parser.add_argument(
        '--channel',
        type=str,
        default='social_media',
        help='Channel for scenario analysis'
    )

    parser.add_argument(
        '--budget-range',
        type=float,
        nargs=2,
        default=[5000, 50000],
        help='Budget range for scenario analysis'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Output file path for results'
    )

    args = parser.parse_args()

    print("Campaign Performance Predictor")
    print("=" * 50)

    # Load or generate training data
    if args.data:
        historical_data = load_historical_data(args.data)
    else:
        print("\nGenerating synthetic training data...")
        historical_data = generate_training_data(n_samples=200)

    print(f"\nTraining data: {len(historical_data)} campaigns")

    # Train predictor
    print("\nTraining predictive models...")
    predictor = CampaignPredictor()
    predictor.train(historical_data)

    # Execute based on mode
    results = None

    if args.mode == 'train':
        print("\nModel training complete!")

        # Show feature importance
        print("\nFeature Importance (Conversions):")
        importance = predictor.feature_importance('conversions')
        for feature, score in sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {feature}: {score:.4f}")

    elif args.mode == 'predict':
        # Load campaign config
        if args.config:
            if os.path.exists(args.config):
                with open(args.config, 'r') as f:
                    config = json.load(f)
            else:
                config = json.loads(args.config)
        else:
            # Default config
            config = {
                'budget': 25000,
                'channel': 'social_media',
                'duration_days': 30,
                'audience_size': 50000,
                'start_date': '2026-05-01'
            }

        results = predict_campaign(predictor, config)

    elif args.mode == 'optimize':
        if not args.budget:
            print("Error: --budget required for optimization mode")
            sys.exit(1)

        results = optimize_budget(predictor, args.budget, args.channels)

    elif args.mode == 'scenario':
        results = scenario_analysis(
            predictor,
            args.channel,
            tuple(args.budget_range)
        )

    # Save results if output path provided
    if args.output and results is not None:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(results, pd.DataFrame):
            results.to_csv(output_path, index=False)
        else:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)

        print(f"\nResults saved to: {output_path}")

    print("\nPrediction complete!")


if __name__ == '__main__':
    main()
