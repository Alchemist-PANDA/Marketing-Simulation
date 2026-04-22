"""
Customer Lifetime Value prediction and churn modeling.
No API calls. Survival analysis and probabilistic modeling.
"""

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


@dataclass
class CLVPrediction:
    """Predicted customer lifetime value"""
    expected_ltv: float
    confidence_interval: Tuple[float, float]
    expected_tenure_days: float
    churn_probability_30d: float
    churn_probability_90d: float
    optimal_intervention: str
    intervention_roi: float


class SurvivalModel:
    """
    Non-parametric survival analysis (Kaplan-Meier style).
    Estimates time until churn without assuming distribution.
    """

    def __init__(self):
        self.customer_histories: Dict[str, List[Dict]] = defaultdict(list)
        self.churn_events: List[Tuple[int, bool]] = []  # (days_active, churned)

    def record_activity(self, customer_id: str, day: int, event: str,
                      purchase_amount: float = 0):
        self.customer_histories[customer_id].append({
            'day': day,
            'event': event,
            'amount': purchase_amount
        })

    def detect_churn(self, customer_id: str, current_day: int,
                     churn_threshold_days: int = 14) -> bool:
        """
        Churn = no purchase for N days
        """
        history = self.customer_histories[customer_id]
        purchases = [h for h in history if h['event'] == 'purchase']

        if not purchases:
            return True  # Never purchased = churned immediately

        last_purchase = max(p['day'] for p in purchases)
        days_since = current_day - last_purchase

        return days_since > churn_threshold_days

    def calculate_survival_curve(self) -> List[Tuple[int, float]]:
        """
        Returns: [(day, survival_probability), ...]
        """
        if not self.churn_events:
            return []

        # Sort by days active
        events = sorted(self.churn_events, key=lambda x: x[0])

        survival = []
        n_at_risk = len(events)
        n_survived = n_at_risk

        current_day = 0
        for day, churned in events:
            if day > current_day:
                survival.append((current_day, n_survived / n_at_risk))
                current_day = day

            if churned:
                n_survived -= 1

        survival.append((current_day, n_survived / n_at_risk))
        return survival

    def predict_survival(self, customer_id: str, current_day: int) -> Dict:
        """
        Predict survival metrics for specific customer
        """
        history = self.customer_histories[customer_id]
        purchases = [h for h in history if h['event'] == 'purchase']

        if not purchases:
            return {
                'days_active': 0,
                'churn_risk': 'critical',
                'expected_remaining_days': 0,
                'recommendation': 'Win-back campaign immediately'
            }

        # RFM features
        days_active = current_day - purchases[0]['day']
        frequency = len(purchases) / max(days_active, 1)
        recency = current_day - max(p['day'] for p in purchases)
        monetary = sum(p['amount'] for p in purchases) / len(purchases)

        # Simple hazard model: risk increases with recency, decreases with frequency
        base_hazard = 0.02  # 2% daily churn baseline

        recency_factor = 1 + (recency / 7) ** 2  # Quadratic increase
        frequency_factor = 1 / (1 + frequency * 10)  # More purchases = lower risk
        monetary_factor = 1 / (1 + monetary / 50)  # Higher spenders more loyal

        daily_hazard = base_hazard * recency_factor * frequency_factor * monetary_factor

        # Survival probabilities
        survival_30 = (1 - daily_hazard) ** 30
        survival_90 = (1 - daily_hazard) ** 90

        risk_level = 'low'
        if daily_hazard > 0.1:
            risk_level = 'critical'
        elif daily_hazard > 0.05:
            risk_level = 'high'
        elif daily_hazard > 0.03:
            risk_level = 'medium'

        return {
            'days_active': days_active,
            'rfm_score': {
                'recency': recency,
                'frequency': frequency,
                'monetary': monetary
            },
            'daily_churn_hazard': daily_hazard,
            'survival_probability_30d': survival_30,
            'survival_probability_90d': survival_90,
            'churn_risk': risk_level,
            'expected_remaining_days': 1 / daily_hazard if daily_hazard > 0 else 999,
            'recommendation': {
                'critical': 'Immediate intervention: personal call + 50% discount',
                'high': 'Urgent: email with exclusive offer + free shipping',
                'medium': 'Standard: retargeting campaign',
                'low': 'Maintain: loyalty program engagement'
            }[risk_level]
        }


class CLVEngine:
    """
    Customer Lifetime Value calculations.
    Probabilistic models for future value prediction.
    """

    def __init__(self, survival_model: SurvivalModel):
        self.survival = survival_model
        self.discount_rate = 0.001  # Daily discount rate (~30% annual)

    def calculate_clv(self, customer_id: str, current_day: int) -> CLVPrediction:
        """
        CLV = Σ (Expected_Revenue_t × Survival_t) / (1 + r)^t
        """
        history = self.survival.customer_histories[customer_id]
        purchases = [h for h in history if h['event'] == 'purchase']

        if not purchases:
            return CLVPrediction(
                expected_ltv=0,
                confidence_interval=(0, 0),
                expected_tenure_days=0,
                churn_probability_30d=1.0,
                churn_probability_90d=1.0,
                optimal_intervention='acquisition',
                intervention_roi=0
            )

        # Historical metrics
        avg_order_value = sum(p['amount'] for p in purchases) / len(purchases)
        purchase_frequency = len(purchases) / max(current_day - purchases[0]['day'], 1)

        # Survival prediction
        survival_pred = self.survival.predict_survival(customer_id, current_day)
        daily_hazard = survival_pred['daily_churn_hazard']

        # Calculate CLV: sum over expected lifetime
        clv = 0.0
        survival_prob = 1.0

        for day in range(1, 365):  # 1-year horizon
            survival_prob *= (1 - daily_hazard)

            if survival_prob < 0.01:  # Negligible
                break

            expected_revenue = avg_order_value * purchase_frequency * survival_prob
            discounted = expected_revenue / ((1 + self.discount_rate) ** day)
            clv += discounted

        # Confidence interval via bootstrapping (simplified)
        std_dev = clv * 0.3  # 30% uncertainty
        ci_lower = max(0, clv - 1.96 * std_dev)
        ci_upper = clv + 1.96 * std_dev

        # Optimal intervention
        interventions = {
            'none': (0, 0),
            'email_discount_10': (5, 0.15),
            'email_discount_20': (8, 0.25),
            'personal_call': (25, 0.40),
            'free_product': (15, 0.35),
            'loyalty_tier_upgrade': (0, 0.20)
        }

        best_roi = -float('inf')
        best_intervention = 'none'

        for intervention, (cost, retention_boost) in interventions.items():
            boosted_clv = clv * (1 + retention_boost)
            roi = (boosted_clv - clv - cost) / max(cost, 1)
            if roi > best_roi:
                best_roi = roi
                best_intervention = intervention

        return CLVPrediction(
            expected_ltv=clv,
            confidence_interval=(ci_lower, ci_upper),
            expected_tenure_days=survival_pred['expected_remaining_days'],
            churn_probability_30d=1 - survival_pred['survival_probability_30d'],
            churn_probability_90d=1 - survival_pred['survival_probability_90d'],
            optimal_intervention=best_intervention,
            intervention_roi=best_roi
        )

    def segment_by_clv(self, agents: Dict[str, 'Agent']) -> Dict[str, List[str]]:
        """
        Segment customers by predicted CLV
        """
        segments = {
            'champions': [],      # High CLV, high frequency
            'loyal': [],          # High CLV, moderate frequency
            'potential': [],      # Moderate CLV, can grow
            'at_risk': [],        # High CLV but churn risk
            'hibernating': [],    # Were good, now inactive
            'new': [],            # Recent, low data
            'lost': []            # Churned
        }

        # This would integrate with simulation data
        # Simplified version based on agent traits

        for name, agent in agents.items():
            if hasattr(agent.state, 'money') and agent.state.money > agent.income * 0.3 and len(agent.state.purchases) > 3:
                segments['champions'].append(name)
            elif agent.personality.brand_loyalty > 0.7:
                segments['loyal'].append(name)
            elif agent.personality.price_sensitivity < 0.4:
                segments['potential'].append(name)
            elif agent.personality.neuroticism > 0.7:
                segments['at_risk'].append(name)
            elif len(agent.state.purchases) == 0:
                segments['new'].append(name)
            else:
                segments['hibernating'].append(name)

        return segments


class ChurnInterventionEngine:
    """
    Recommends and simulates churn prevention actions.
    """

    INTERVENTIONS = {
        'email_discount_10': {
            'cost': 0.50,
            'effectiveness': 0.15,
            'channel': 'email',
            'description': '10% discount via email'
        },
        'email_discount_20': {
            'cost': 1.00,
            'effectiveness': 0.25,
            'channel': 'email',
            'description': '20% discount via email'
        },
        'sms_personal': {
            'cost': 0.75,
            'effectiveness': 0.30,
            'channel': 'sms',
            'description': 'Personal SMS from brand rep'
        },
        'free_shipping': {
            'cost': 5.00,
            'effectiveness': 0.20,
            'channel': 'email',
            'description': 'Free shipping on next order'
        },
        'loyalty_bonus': {
            'cost': 3.00,
            'effectiveness': 0.35,
            'channel': 'app',
            'description': 'Bonus loyalty points (2x)'
        },
        'win_back_call': {
            'cost': 15.00,
            'effectiveness': 0.50,
            'channel': 'phone',
            'description': 'Personal phone call with offer'
        }
    }

    def recommend_intervention(self, clv: float, churn_risk: str,
                               days_since_purchase: int) -> Dict:
        """
        Cost-benefit analysis for churn intervention
        """
        if churn_risk == 'critical' and clv > 200:
            return {
                'intervention': 'win_back_call',
                'expected_cost': 15.00,
                'expected_retention': 0.50,
                'expected_value': clv * 0.50,
                'roi': (clv * 0.50 - 15) / 15,
                'urgency': 'immediate'
            }

        elif churn_risk in ['critical', 'high'] and clv > 100:
            return {
                'intervention': 'loyalty_bonus',
                'expected_cost': 3.00,
                'expected_retention': 0.35,
                'expected_value': clv * 0.35,
                'roi': (clv * 0.35 - 3) / 3,
                'urgency': '24_hours'
            }

        elif days_since_purchase > 10:
            return {
                'intervention': 'email_discount_20',
                'expected_cost': 1.00,
                'expected_retention': 0.25,
                'expected_value': clv * 0.25,
                'roi': (clv * 0.25 - 1) / 1,
                'urgency': '48_hours'
            }

        else:
            return {
                'intervention': 'email_discount_10',
                'expected_cost': 0.50,
                'expected_retention': 0.15,
                'expected_value': clv * 0.15,
                'roi': (clv * 0.15 - 0.50) / 0.50,
                'urgency': 'routine'
            }

    def simulate_intervention(self, agent: 'Agent', intervention: str,
                             clv_engine: CLVEngine) -> Dict:
        """
        Simulate outcome of intervention on specific agent
        """
        config = self.INTERVENTIONS.get(intervention, {})
        if not config:
            return {'success': False, 'reason': 'Unknown intervention'}

        # Agent's receptiveness
        base_prob = config['effectiveness']

        # Modifiers
        if agent.personality.ad_skepticism > 0.7:
            base_prob *= 0.6  # Skeptics harder to reach

        if agent.personality.price_sensitivity > 0.8 and 'discount' in intervention:
            base_prob *= 1.3  # Bargain hunters love discounts

        if agent.personality.agreeableness > 0.7 and 'personal' in intervention:
            base_prob *= 1.2  # Agreeable agents respond to personal touch

        # Deterministic outcome
        rng = agent.deterministic_random(f"intervention_{intervention}")
        success = rng.random() < base_prob

        if success:
            # Reset recency, boost affinity
            agent.state.brand_affinity['intervened_brand'] = min(1.0,
                agent.state.brand_affinity.get('intervened_brand', 0) + 0.2)
            if hasattr(agent.state, 'happiness'):
                agent.state.happiness = min(100, agent.state.happiness + 10)

        return {
            'success': success,
            'intervention': intervention,
            'cost': config['cost'],
            'probability': base_prob,
            'agent_receptiveness': 'high' if base_prob > 0.3 else 'medium' if base_prob > 0.15 else 'low'
        }
