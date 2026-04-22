"""
Predictive Analytics Module

Provides forecasting and predictive modeling capabilities for marketing campaigns.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
import warnings

warnings.filterwarnings('ignore')


class CampaignPredictor:
    """Predicts campaign performance metrics using historical data."""

    def __init__(self):
        self.models = {
            'conversions': None,
            'revenue': None,
            'engagement': None
        }
        self.scalers = {
            'conversions': StandardScaler(),
            'revenue': StandardScaler(),
            'engagement': StandardScaler()
        }
        self.feature_names = []
        self.is_trained = False

    def prepare_features(self, campaign_data: pd.DataFrame) -> pd.DataFrame:
        """Extract and engineer features from campaign data."""
        features = pd.DataFrame()

        # Budget features
        features['budget'] = campaign_data['budget']
        features['budget_log'] = np.log1p(campaign_data['budget'])

        # Channel encoding (one-hot)
        if 'channel' in campaign_data.columns:
            channel_dummies = pd.get_dummies(campaign_data['channel'], prefix='channel')
            features = pd.concat([features, channel_dummies], axis=1)

        # Temporal features
        if 'start_date' in campaign_data.columns:
            dates = pd.to_datetime(campaign_data['start_date'])
            features['day_of_week'] = dates.dt.dayofweek
            features['month'] = dates.dt.month
            features['quarter'] = dates.dt.quarter
            features['is_weekend'] = (dates.dt.dayofweek >= 5).astype(int)

        # Duration features
        if 'duration_days' in campaign_data.columns:
            features['duration'] = campaign_data['duration_days']
            features['duration_log'] = np.log1p(campaign_data['duration_days'])

        # Target audience size
        if 'audience_size' in campaign_data.columns:
            features['audience_size'] = campaign_data['audience_size']
            features['audience_size_log'] = np.log1p(campaign_data['audience_size'])

        # Historical performance features
        if 'previous_conversions' in campaign_data.columns:
            features['prev_conversions'] = campaign_data['previous_conversions']
            features['prev_conversion_rate'] = campaign_data.get('previous_conversion_rate', 0)

        # Interaction features
        features['budget_per_day'] = features['budget'] / features.get('duration', 1)
        features['budget_per_audience'] = features['budget'] / features.get('audience_size', 1)

        self.feature_names = features.columns.tolist()
        return features

    def train(self, historical_data: pd.DataFrame, target_metrics: List[str] = None):
        """Train predictive models on historical campaign data."""
        if target_metrics is None:
            target_metrics = ['conversions', 'revenue', 'engagement']

        X = self.prepare_features(historical_data)

        for metric in target_metrics:
            if metric not in historical_data.columns:
                print(f"Warning: {metric} not found in historical data, skipping")
                continue

            y = historical_data[metric].values

            # Handle missing values
            valid_idx = ~(np.isnan(X.values).any(axis=1) | np.isnan(y))
            X_clean = X[valid_idx]
            y_clean = y[valid_idx]

            if len(X_clean) < 10:
                print(f"Warning: Insufficient data for {metric} model")
                continue

            # Scale features
            X_scaled = self.scalers[metric].fit_transform(X_clean)

            # Train ensemble model
            model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=4,
                random_state=42
            )

            model.fit(X_scaled, y_clean)
            self.models[metric] = model

            # Evaluate model
            scores = cross_val_score(model, X_scaled, y_clean, cv=5,
                                    scoring='neg_mean_squared_error')
            rmse = np.sqrt(-scores.mean())
            print(f"{metric} model trained - RMSE: {rmse:.2f}")

        self.is_trained = True

    def predict(self, campaign_config: Dict) -> Dict[str, float]:
        """Predict performance metrics for a new campaign configuration."""
        if not self.is_trained:
            raise ValueError("Models must be trained before prediction")

        # Convert config to DataFrame
        config_df = pd.DataFrame([campaign_config])
        X = self.prepare_features(config_df)

        # Ensure all features are present
        for feature in self.feature_names:
            if feature not in X.columns:
                X[feature] = 0

        X = X[self.feature_names]

        predictions = {}
        for metric, model in self.models.items():
            if model is not None:
                X_scaled = self.scalers[metric].transform(X)
                pred = model.predict(X_scaled)[0]
                predictions[metric] = max(0, pred)  # Ensure non-negative

        return predictions

    def predict_with_confidence(self, campaign_config: Dict) -> Dict[str, Tuple[float, float, float]]:
        """Predict with confidence intervals using bootstrap."""
        base_predictions = self.predict(campaign_config)

        results = {}
        for metric, pred in base_predictions.items():
            # Simple confidence interval estimation (±20%)
            lower = pred * 0.8
            upper = pred * 1.2
            results[metric] = (pred, lower, upper)

        return results

    def feature_importance(self, metric: str = 'conversions') -> Dict[str, float]:
        """Get feature importance for a specific metric."""
        if not self.is_trained or self.models[metric] is None:
            return {}

        model = self.models[metric]
        importances = model.feature_importances_

        return dict(zip(self.feature_names, importances))


class TimeSeriesForecaster:
    """Forecasts time-series metrics like daily conversions or revenue."""

    def __init__(self, window_size: int = 7):
        self.window_size = window_size
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False

    def create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create sliding window sequences for time series prediction."""
        X, y = [], []
        for i in range(len(data) - self.window_size):
            X.append(data[i:i + self.window_size])
            y.append(data[i + self.window_size])
        return np.array(X), np.array(y)

    def train(self, time_series_data: pd.Series):
        """Train forecasting model on time series data."""
        data = time_series_data.values.reshape(-1, 1)
        data_scaled = self.scaler.fit_transform(data).flatten()

        X, y = self.create_sequences(data_scaled)

        if len(X) < 10:
            raise ValueError("Insufficient data for time series forecasting")

        # Use Random Forest for time series
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )

        self.model.fit(X, y)
        self.is_trained = True

        # Evaluate
        train_score = self.model.score(X, y)
        print(f"Time series model trained - R² score: {train_score:.3f}")

    def forecast(self, steps: int = 7) -> np.ndarray:
        """Forecast future values."""
        if not self.is_trained:
            raise ValueError("Model must be trained before forecasting")

        # This is a simplified forecast - in production, use proper recursive forecasting
        predictions = []
        current_window = self.scaler.transform([[0]] * self.window_size).flatten()

        for _ in range(steps):
            pred = self.model.predict([current_window])[0]
            predictions.append(pred)
            current_window = np.roll(current_window, -1)
            current_window[-1] = pred

        # Inverse transform
        predictions_array = np.array(predictions).reshape(-1, 1)
        return self.scaler.inverse_transform(predictions_array).flatten()


class BudgetOptimizer:
    """Optimizes budget allocation across channels using predictive models."""

    def __init__(self, predictor: CampaignPredictor):
        self.predictor = predictor

    def optimize_allocation(self,
                          total_budget: float,
                          channels: List[str],
                          constraints: Optional[Dict] = None) -> Dict[str, float]:
        """Find optimal budget allocation across channels."""
        if constraints is None:
            constraints = {}

        # Simple grid search optimization
        best_allocation = None
        best_roi = -float('inf')

        # Generate allocation candidates
        n_channels = len(channels)
        step = total_budget / 20  # 20 steps per channel

        for _ in range(100):  # Random search
            allocation = np.random.dirichlet(np.ones(n_channels)) * total_budget

            # Apply constraints
            valid = True
            for i, channel in enumerate(channels):
                min_budget = constraints.get(f'{channel}_min', 0)
                max_budget = constraints.get(f'{channel}_max', total_budget)

                if allocation[i] < min_budget or allocation[i] > max_budget:
                    valid = False
                    break

            if not valid:
                continue

            # Calculate expected ROI
            total_revenue = 0
            for i, channel in enumerate(channels):
                config = {
                    'budget': allocation[i],
                    'channel': channel,
                    'duration_days': 30,
                    'audience_size': 10000
                }

                try:
                    predictions = self.predictor.predict(config)
                    total_revenue += predictions.get('revenue', 0)
                except:
                    continue

            roi = (total_revenue - total_budget) / total_budget if total_budget > 0 else 0

            if roi > best_roi:
                best_roi = roi
                best_allocation = allocation

        if best_allocation is None:
            # Fallback: equal allocation
            best_allocation = np.ones(n_channels) * (total_budget / n_channels)

        return {
            channel: budget
            for channel, budget in zip(channels, best_allocation)
        }

    def simulate_scenarios(self,
                          budget_range: Tuple[float, float],
                          channel: str,
                          steps: int = 10) -> pd.DataFrame:
        """Simulate campaign performance across budget range."""
        budgets = np.linspace(budget_range[0], budget_range[1], steps)
        results = []

        for budget in budgets:
            config = {
                'budget': budget,
                'channel': channel,
                'duration_days': 30,
                'audience_size': 10000
            }

            try:
                predictions = self.predictor.predict(config)
                results.append({
                    'budget': budget,
                    'predicted_conversions': predictions.get('conversions', 0),
                    'predicted_revenue': predictions.get('revenue', 0),
                    'predicted_roi': (predictions.get('revenue', 0) - budget) / budget if budget > 0 else 0
                })
            except:
                continue

        return pd.DataFrame(results)


def generate_sample_predictions(n_campaigns: int = 5) -> pd.DataFrame:
    """Generate sample prediction data for testing."""
    np.random.seed(42)

    channels = ['social_media', 'search', 'email', 'display']
    predictions = []

    for i in range(n_campaigns):
        budget = np.random.uniform(1000, 50000)
        channel = np.random.choice(channels)

        # Simulate predictions based on budget and channel
        base_conversions = budget * 0.02
        base_revenue = budget * 2.5

        channel_multipliers = {
            'social_media': 1.2,
            'search': 1.5,
            'email': 1.8,
            'display': 0.9
        }

        multiplier = channel_multipliers[channel]

        predictions.append({
            'campaign_id': f'CAMP_{i+1:03d}',
            'budget': budget,
            'channel': channel,
            'predicted_conversions': base_conversions * multiplier,
            'predicted_revenue': base_revenue * multiplier,
            'confidence_lower': base_revenue * multiplier * 0.8,
            'confidence_upper': base_revenue * multiplier * 1.2
        })

    return pd.DataFrame(predictions)


if __name__ == '__main__':
    print("Predictive Analytics Module")
    print("=" * 50)

    # Generate sample data
    sample_data = generate_sample_predictions()
    print("\nSample Predictions:")
    print(sample_data.to_string(index=False))
