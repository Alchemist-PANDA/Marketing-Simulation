"""
Competitive dynamics and market share simulation.
"""

import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class Competitor:
    """Represents a competitor in the market."""
    name: str
    market_share: float
    budget: float
    quality_score: float
    brand_strength: float
    price_index: float  # 1.0 = market average


class CompetitiveMarket:
    """Simulates competitive market dynamics with multiple players."""

    def __init__(self, total_market_size: float = 1000000):
        self.total_market_size = total_market_size
        self.competitors: Dict[str, Competitor] = {}
        self.time_step = 0
        self.history = []

    def add_competitor(self, competitor: Competitor):
        """Add a competitor to the market."""
        self.competitors[competitor.name] = competitor

    def normalize_market_shares(self):
        """Ensure market shares sum to 1.0."""
        total_share = sum(c.market_share for c in self.competitors.values())
        if total_share > 0:
            for competitor in self.competitors.values():
                competitor.market_share /= total_share

    def calculate_competitive_pressure(self, competitor_name: str) -> float:
        """Calculate competitive pressure on a specific competitor."""
        if competitor_name not in self.competitors:
            return 0.0

        target = self.competitors[competitor_name]
        pressure = 0.0

        for name, competitor in self.competitors.items():
            if name == competitor_name:
                continue

            # Pressure based on relative spending
            spend_ratio = competitor.budget / max(target.budget, 1)

            # Pressure based on quality advantage
            quality_diff = competitor.quality_score - target.quality_score

            # Pressure based on price advantage
            price_advantage = target.price_index - competitor.price_index

            # Combined pressure weighted by competitor's market share
            competitor_pressure = (
                0.4 * spend_ratio +
                0.3 * (1 + quality_diff / 10) +
                0.3 * (1 + price_advantage / 2)
            ) * competitor.market_share

            pressure += competitor_pressure

        return pressure

    def simulate_market_share_shift(self, marketing_actions: Dict[str, float]) -> Dict[str, float]:
        """
        Simulate market share changes based on marketing actions.

        Args:
            marketing_actions: Dict mapping competitor names to their marketing spend

        Returns:
            Dict of new market shares
        """
        new_shares = {}
        attraction_scores = {}

        # Calculate attraction score for each competitor
        for name, competitor in self.competitors.items():
            marketing_spend = marketing_actions.get(name, 0)

            # Attraction based on multiple factors
            spend_effect = np.log1p(marketing_spend) / 10
            quality_effect = competitor.quality_score / 10
            brand_effect = competitor.brand_strength / 10
            price_effect = (2.0 - competitor.price_index) / 2  # Lower price = higher attraction

            # Current market share provides inertia
            inertia_effect = competitor.market_share * 2

            attraction = (
                0.25 * spend_effect +
                0.20 * quality_effect +
                0.20 * brand_effect +
                0.15 * price_effect +
                0.20 * inertia_effect
            )

            attraction_scores[name] = max(attraction, 0.01)

        # Convert attraction scores to market shares
        total_attraction = sum(attraction_scores.values())
        for name in self.competitors.keys():
            new_shares[name] = attraction_scores[name] / total_attraction

        return new_shares

    def update_brand_strength(self, competitor_name: str, marketing_spend: float):
        """Update brand strength based on sustained marketing investment."""
        if competitor_name not in self.competitors:
            return

        competitor = self.competitors[competitor_name]

        # Brand strength increases with consistent spending
        spend_impact = np.log1p(marketing_spend) / 100

        # Brand strength decays slowly without investment
        decay = 0.02 if marketing_spend < competitor.budget * 0.5 else 0

        competitor.brand_strength = min(
            10.0,
            max(0.0, competitor.brand_strength + spend_impact - decay)
        )

    def simulate_step(self, marketing_actions: Dict[str, float]) -> Dict[str, Dict]:
        """
        Simulate one time step of competitive dynamics.

        Args:
            marketing_actions: Dict mapping competitor names to marketing spend

        Returns:
            Dict with results for each competitor
        """
        self.time_step += 1

        # Calculate new market shares
        new_shares = self.simulate_market_share_shift(marketing_actions)

        # Update competitors
        results = {}
        for name, competitor in self.competitors.items():
            old_share = competitor.market_share
            new_share = new_shares[name]

            # Update market share
            competitor.market_share = new_share

            # Update brand strength
            marketing_spend = marketing_actions.get(name, 0)
            self.update_brand_strength(name, marketing_spend)

            # Calculate metrics
            revenue = new_share * self.total_market_size * competitor.price_index
            profit = revenue - marketing_spend
            share_change = new_share - old_share
            competitive_pressure = self.calculate_competitive_pressure(name)

            results[name] = {
                'market_share': new_share,
                'share_change': share_change,
                'revenue': revenue,
                'profit': profit,
                'brand_strength': competitor.brand_strength,
                'competitive_pressure': competitive_pressure,
                'marketing_spend': marketing_spend
            }

        # Store history
        self.history.append({
            'time_step': self.time_step,
            'results': results.copy()
        })

        return results

    def get_market_leader(self) -> Tuple[str, float]:
        """Return the name and market share of the market leader."""
        if not self.competitors:
            return None, 0.0

        leader = max(self.competitors.items(), key=lambda x: x[1].market_share)
        return leader[0], leader[1].market_share

    def get_market_concentration(self) -> float:
        """Calculate Herfindahl-Hirschman Index (HHI) for market concentration."""
        hhi = sum(c.market_share ** 2 for c in self.competitors.values())
        return hhi * 10000  # Scale to 0-10000

    def get_competitive_intensity(self) -> float:
        """Calculate overall competitive intensity in the market."""
        if len(self.competitors) < 2:
            return 0.0

        # Based on number of competitors and market share distribution
        n_competitors = len(self.competitors)
        hhi = self.get_market_concentration()

        # Lower HHI = more competition
        # More competitors = more competition
        intensity = (1 - hhi / 10000) * min(n_competitors / 5, 1.0)

        return intensity

    def get_summary(self) -> Dict:
        """Get summary statistics of the market."""
        leader_name, leader_share = self.get_market_leader()

        return {
            'time_step': self.time_step,
            'n_competitors': len(self.competitors),
            'market_leader': leader_name,
            'leader_share': leader_share,
            'market_concentration_hhi': self.get_market_concentration(),
            'competitive_intensity': self.get_competitive_intensity(),
            'total_market_size': self.total_market_size,
            'competitors': {
                name: {
                    'market_share': c.market_share,
                    'brand_strength': c.brand_strength,
                    'quality_score': c.quality_score,
                    'price_index': c.price_index
                }
                for name, c in self.competitors.items()
            }
        }


def create_sample_market() -> CompetitiveMarket:
    """Create a sample competitive market with realistic competitors."""
    market = CompetitiveMarket(total_market_size=10_000_000)

    # Add competitors with different profiles
    competitors = [
        Competitor(
            name="Market Leader",
            market_share=0.35,
            budget=500_000,
            quality_score=8.5,
            brand_strength=9.0,
            price_index=1.1
        ),
        Competitor(
            name="Strong Challenger",
            market_share=0.25,
            budget=400_000,
            quality_score=8.0,
            brand_strength=7.5,
            price_index=1.0
        ),
        Competitor(
            name="Value Player",
            market_share=0.20,
            budget=250_000,
            quality_score=6.5,
            brand_strength=6.0,
            price_index=0.8
        ),
        Competitor(
            name="Niche Premium",
            market_share=0.12,
            budget=200_000,
            quality_score=9.0,
            brand_strength=7.0,
            price_index=1.4
        ),
        Competitor(
            name="New Entrant",
            market_share=0.08,
            budget=150_000,
            quality_score=7.0,
            brand_strength=4.0,
            price_index=0.9
        )
    ]

    for competitor in competitors:
        market.add_competitor(competitor)

    market.normalize_market_shares()

    return market
