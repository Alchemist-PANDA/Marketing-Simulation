"""
Advanced market dynamics: network effects, seasonality, trends, bubbles.
No API calls. Differential equations and agent-based emergence.
"""

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import deque


@dataclass
class MarketTrend:
    """Emergent market trend tracked across simulation"""
    name: str
    start_day: int
    peak_day: Optional[int] = None
    end_day: Optional[int] = None
    adoption_curve: List[float] = field(default_factory=list)
    total_adopters: int = 0

    def is_active(self, day: int) -> bool:
        return self.start_day <= day <= (self.end_day or float('inf'))


class NetworkEffects:
    """
    Metcalfe's Law: value of network = n²
    Reed's Law: value of group-forming networks = 2^n
    """

    def __init__(self, agents: Dict[str, 'Agent']):
        self.agents = agents
        self.network_value_history: List[Dict] = []

    def calculate_metcalfe_value(self, brand: str) -> float:
        """n² value of user base"""
        users = sum(
            1 for a in self.agents.values()
            if a.state.brand_affinity.get(brand, 0) > 0.3
        )
        return users ** 2

    def calculate_reed_value(self, brand: str) -> float:
        """2^n potential subgroups"""
        users = [
            a for a in self.agents.values()
            if a.state.brand_affinity.get(brand, 0) > 0.3
        ]
        if len(users) < 2:
            return 0.0

        # Simplified: number of potential friend-pairs
        n = len(users)
        return n * (n - 1) / 2

    def calculate_critical_mass(self, brand: str) -> float:
        """
        Critical mass = 16% of market (Rogers' Diffusion of Innovations)
        After this, growth becomes self-sustaining
        """
        total = len(self.agents)
        adopters = sum(
            1 for a in self.agents.values()
            if a.state.brand_affinity.get(brand, 0) > 0.5
        )

        ratio = adopters / total if total > 0 else 0

        # S-curve: slow start, explosive middle, saturation
        if ratio < 0.16:
            # Below critical mass: linear, effortful growth
            growth_rate = ratio * 0.5
        elif ratio < 0.5:
            # Above critical mass: exponential viral growth
            growth_rate = ratio * (1 + ratio) * 2
        else:
            # Saturation: diminishing returns
            growth_rate = (1 - ratio) * 0.3

        return growth_rate

    def detect_tipping_point(self, brand: str, history: List[float]) -> Optional[int]:
        """
        Detect when brand crossed critical mass (16%)
        Returns day number or None
        """
        for i, ratio in enumerate(history):
            if ratio >= 0.16:
                # Confirm: must stay above 16% for 2+ days
                if i + 1 < len(history) and history[i + 1] >= 0.14:
                    return i
        return None


class SeasonalityEngine:
    """
    Models seasonal patterns, holidays, economic cycles.
    """

    def __init__(self):
        # Monthly seasonality multipliers (retail patterns)
        self.monthly_patterns = {
            1: 0.8,   # Post-holiday slump
            2: 0.9,
            3: 1.0,
            4: 1.0,
            5: 1.1,   # Spring boost
            6: 1.0,
            7: 0.9,   # Summer vacation
            8: 1.0,
            9: 1.1,   # Back to school
            10: 1.0,
            11: 1.3,  # Black Friday buildup
            12: 1.5,  # Holiday peak
        }

        # Day-of-week patterns
        self.dow_patterns = {
            0: 0.9,   # Monday
            1: 0.95,
            2: 1.0,
            3: 1.0,
            4: 1.05,  # Thursday
            5: 1.2,   # Friday
            6: 1.1,   # Saturday
        }

        # Hour-of-day patterns
        self.hourly_patterns = {
            # Sleep hours
            **{h: 0.1 for h in range(0, 7)},
            # Morning commute/breakfast
            7: 0.6, 8: 0.8,
            # Work hours
            9: 0.7, 10: 0.7, 11: 0.8,
            # Lunch
            12: 1.0, 13: 1.0,
            # Afternoon
            14: 0.8, 15: 0.8, 16: 0.9,
            # Evening commute/dinner
            17: 1.1, 18: 1.2, 19: 1.1,
            # Evening leisure
            20: 1.0, 21: 0.9,
            # Late night
            22: 0.5, 23: 0.2
        }

        # Special events
        self.events = {
            'black_friday': {'month': 11, 'day': 29, 'multiplier': 3.0},
            'cyber_monday': {'month': 12, 'day': 2, 'multiplier': 2.5},
            'christmas': {'month': 12, 'day': 25, 'multiplier': 0.1},  # Closed
            'valentines': {'month': 2, 'day': 14, 'multiplier': 1.8},
            'prime_day': {'month': 7, 'day': 15, 'multiplier': 2.0},
        }

    def get_seasonal_multiplier(self, month: int, day: int, hour: int,
                                day_of_week: int) -> float:
        """Combined seasonal effect"""
        base = self.monthly_patterns.get(month, 1.0)
        dow = self.dow_patterns.get(day_of_week, 1.0)
        hod = self.hourly_patterns.get(hour, 0.5)

        # Check special events
        event_mult = 1.0
        for event, info in self.events.items():
            if info['month'] == month and abs(info['day'] - day) <= 2:
                # Ramp up/down over 3 days
                distance = abs(info['day'] - day)
                ramp = 1 - (distance / 3)
                event_mult = 1 + (info['multiplier'] - 1) * ramp

        return base * dow * hod * event_mult

    def predict_peak_sales(self, brand: str, year: int) -> List[Tuple[int, int, float]]:
        """
        Predict highest-revenue days for upcoming year
        Returns: [(month, day, expected_multiplier), ...]
        """
        peaks = []

        for month in range(1, 13):
            for day in range(1, 32):
                try:
                    # Simple day-of-week calculation (Zeller's congruence)
                    q = day
                    m = month + 12 if month < 3 else month
                    K = year % 100
                    J = year // 100
                    dow = (q + (13 * (m + 1)) // 5 + K + K // 4 + J // 4 + 5 * J) % 7

                    mult = self.get_seasonal_multiplier(month, day, 12, dow)
                    if mult > 1.5:
                        peaks.append((month, day, mult))
                except:
                    continue

        return sorted(peaks, key=lambda x: x[2], reverse=True)[:10]


class BubbleDetector:
    """
    Detects speculative bubbles in brand adoption.
    Uses price-to-earnings style metrics for brands.
    """

    def __init__(self):
        self.price_history: Dict[str, deque] = {}
        self.adoption_history: Dict[str, deque] = {}
        self.max_history = 30

    def record(self, brand: str, price: float, adopters: int):
        if brand not in self.price_history:
            self.price_history[brand] = deque(maxlen=self.max_history)
            self.adoption_history[brand] = deque(maxlen=self.max_history)

        self.price_history[brand].append(price)
        self.adoption_history[brand].append(adopters)

    def detect_bubble(self, brand: str) -> Dict:
        """
        Returns bubble metrics:
        - price_to_adoption_ratio (P/A)
        - velocity (rate of change)
        - divergence (price up, adoption flat = bubble)
        """
        if brand not in self.price_history or len(self.price_history[brand]) < 10:
            return {'status': 'insufficient_data'}

        prices = list(self.price_history[brand])
        adoptions = list(self.adoption_history[brand])

        # Price-to-adoption ratio trend
        pa_ratios = [p / max(a, 1) for p, a in zip(prices, adoptions)]

        # Recent vs. historical average
        recent_pa = sum(pa_ratios[-5:]) / 5
        historical_pa = sum(pa_ratios[:-5]) / max(len(pa_ratios) - 5, 1)

        # Velocity
        price_velocity = (prices[-1] - prices[-5]) / prices[-5] if prices[-5] > 0 else 0
        adoption_velocity = (adoptions[-1] - adoptions[-5]) / max(adoptions[-5], 1)

        # Bubble signature: price rising faster than adoption
        divergence = price_velocity - adoption_velocity

        status = 'stable'
        if divergence > 0.5 and recent_pa > historical_pa * 2:
            status = 'bubble_warning'
        elif divergence > 1.0:
            status = 'bubble_detected'
        elif divergence < -0.3:
            status = 'undervalued'

        return {
            'status': status,
            'price_velocity': price_velocity,
            'adoption_velocity': adoption_velocity,
            'divergence': divergence,
            'pa_ratio_trend': recent_pa / historical_pa if historical_pa > 0 else 1.0,
            'recommendation': {
                'bubble_detected': 'Reduce marketing spend, prepare for correction',
                'bubble_warning': 'Monitor closely, diversify channels',
                'stable': 'Maintain current strategy',
                'undervalued': 'Increase investment, opportunity for growth'
            }.get(status, 'Monitor')
        }
