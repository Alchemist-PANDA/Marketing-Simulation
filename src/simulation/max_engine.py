"""
Primary Simulation Engine (MaxCap)
Integrates psychology, market dynamics, and ad engagement modeling.
Zero API cost design. Pure NumPy structured-array core for 100k-1M agent scale.

No per-agent Python objects, no per-agent Python loops. Population state lives
entirely in float32 NumPy arrays; purchase/like/share outcomes are computed and
applied via vectorized boolean masking.
"""

import json
import os
from typing import Dict, List, Any, Optional
import numpy as np

from src.agents.agent_generator import generate_population_arrays, ARCHETYPES
from src.psychology.prospect_theory import ProspectTheoryEngine
from src.ad_processing.ad import Ad

try:
    from numba import njit
    _NUMBA_AVAILABLE = True
except ImportError:
    _NUMBA_AVAILABLE = False


def _compute_probs_numpy(emotional_mod, archetype_score, price_disutility,
                          urgency_score, like_base_terms, share_base_terms):
    """Pure NumPy core: utility -> purchase probability. No Python loops."""
    fomo_impact = urgency_score * 0.5
    perceived_value = 10.0 * (1.0 + emotional_mod + archetype_score + fomo_impact)
    utility = perceived_value + price_disutility
    prob_buy = 1.0 / (1.0 + np.exp(np.clip(-utility / 10.0, -50, 50)))
    return prob_buy.astype(np.float32)


if _NUMBA_AVAILABLE:
    @njit(fastmath=True, cache=True)
    def _compute_probs_numba(emotional_mod, archetype_score, price_disutility, urgency_score):
        # Vectorized array expression compiled to machine code by Numba —
        # no explicit per-agent loop, just JIT-compiled SIMD-friendly ops.
        fomo_impact = urgency_score * 0.5
        perceived_value = 10.0 * (1.0 + emotional_mod + archetype_score + fomo_impact)
        utility = perceived_value + price_disutility
        z = np.clip(-utility / 10.0, -50.0, 50.0)
        return 1.0 / (1.0 + np.exp(z))


def generate_recommendations(ad_scores, emotional_valence, economic_utility):
    recs = []
    if ad_scores.get("trust", 0.5) < 0.4:
        recs.append({"priority": "high", "category": "trust", "message": "Low trust score – add social proof (e.g., 'Trusted by 10,000+ customers')"})
    if ad_scores.get("urgency", 0.5) < 0.3:
        recs.append({"priority": "high", "category": "urgency", "message": "Low urgency – add scarcity messaging (e.g., 'Only 3 left in stock!')"})
    if ad_scores.get("persuasion", 0.5) < 0.4:
        recs.append({"priority": "medium", "category": "persuasion", "message": "Weak persuasion – use stronger CTAs (e.g., 'Buy now and save!')"})
    if ad_scores.get("emotional_appeal", 0.5) < 0.3:
        recs.append({"priority": "medium", "category": "emotion", "message": "Low emotional appeal – use storytelling or vivid imagery"})
    if np.mean(economic_utility) < 0.3:
        recs.append({"priority": "high", "category": "price", "message": "High price sensitivity – consider lowering price or emphasizing value"})
    return recs


class MaxSimulation:
    def __init__(self, num_agents: int = 100, seed: int = None,
                 population: Optional[Dict[str, np.ndarray]] = None,
                 use_numba: bool = True):
        self.seed = seed
        self.np_rng = np.random.RandomState(seed)
        self.prospect = ProspectTheoryEngine()
        self.tick = 0
        self.use_numba = use_numba and _NUMBA_AVAILABLE

        if population is not None:
            self.population = population
        else:
            self.population = generate_population_arrays(num_agents, seed=seed)

        self.num_agents = len(self.population['money'])

        self.archetype_calibration = {}
        config_path = 'config/archetype_calibration.json'
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    self.archetype_calibration = json.load(f)
            except Exception:
                pass

        self._cal_factors = np.array(
            [self.archetype_calibration.get(a, 1.0) for a in ARCHETYPES],
            dtype=np.float32
        )[self.population['archetype_idx']]

        self.learned_weights = {
            "trust_weight": 1.0,
            "urgency_weight": 1.0,
            "price_weight": 1.0,
            "visual_weight": 0.4,
            "text_weight": 0.6
        }
        weights_path = 'config/learned_weights.json'
        if os.path.exists(weights_path):
            try:
                with open(weights_path, 'r') as f:
                    self.learned_weights.update(json.load(f))
            except Exception:
                pass

    def simulate_exposure(self, ad: Ad, progress_callback=None) -> Dict[str, Any]:
        """Simulates one round of ad exposure to the entire population. Zero Python agent loops."""
        pop = self.population
        n = self.num_agents

        emotional_mod = np.zeros(n, dtype=np.float32)
        if ad.channel in ('facebook', 'tiktok', 'instagram'):
            emotional_mod += pop['extraversion'] * 0.3
        if ad.channel in ('google', 'search', 'email'):
            emotional_mod += pop['conscientiousness'] * 0.4
        if ad.creative_type in ('video', 'flashy'):
            emotional_mod -= pop['neuroticism'] * 0.5
        if ad.creative_type in ('video', 'interactive'):
            emotional_mod += pop['openness'] * 0.4
        # Get learned weights
        tw = self.learned_weights['text_weight']
        vw = self.learned_weights['visual_weight']
        trust_w = self.learned_weights['trust_weight']
        urgency_w = self.learned_weights['urgency_weight']
        price_w = self.learned_weights['price_weight']

        # Combine text and visual scores
        combined_trust = tw * ad.trust_score + vw * ad.visual_scores.get('visual_trust', 0.5)
        combined_urgency = tw * ad.urgency_score + vw * ad.visual_scores.get('visual_urgency', 0.5)
        visual_premium = ad.visual_scores.get('visual_premium', 0.5)
        visual_excitement = ad.visual_scores.get('visual_excitement', 0.5)

        # Add visual excitement boost to emotional mod
        emotional_mod += (visual_excitement - 0.5) * vw * 2.0
        np.clip(emotional_mod, -1.0, 1.0, out=emotional_mod)

        if progress_callback:
            progress_callback(0.2, "Emotional analysis complete")

        archetype_score = (
            (ad.price_score * price_w + visual_premium * vw) * pop['price_sensitivity']
            + (combined_trust * trust_w) * pop['trust_sensitivity']
            + (combined_urgency * urgency_w) * pop['urgency_sensitivity']
            - pop['skepticism']
        ).astype(np.float32)

        price_disutility = float(self.prospect.apply(-ad.price, reference=0))

        if progress_callback:
            progress_callback(0.4, "Utility calculation complete")

        urgency_arr = np.full(n, combined_urgency, dtype=np.float32)
        if self.use_numba:
            prob_buy = _compute_probs_numba(emotional_mod, archetype_score, price_disutility, urgency_arr)
        else:
            prob_buy = _compute_probs_numpy(emotional_mod, archetype_score, price_disutility,
                                             urgency_arr, None, None)

        can_afford = pop['money'] >= ad.price
        prob_buy = prob_buy * can_afford

        like_prob = (
            0.1
            + pop['extraversion'] * 0.2
            + pop['openness'] * 0.1
            - pop['neuroticism'] * 0.05
            + ad.price_score * 0.1
            + ad.trust_score * 0.25
            + ad.urgency_score * 0.4
        ).astype(np.float32)
        if ad.channel in ('tiktok', 'instagram'):
            like_prob *= 1.5
        like_prob *= self._cal_factors
        np.clip(like_prob, 0, 1, out=like_prob)

        share_prob = np.clip(
            0.05 + 0.5 * pop['extraversion'] + 0.1 * pop['agreeableness'],
            0, 1
        ).astype(np.float32)

        if progress_callback:
            progress_callback(0.6, "Probability models complete")

        rand_buy = self.np_rng.random(n).astype(np.float32)
        rand_like = self.np_rng.random(n).astype(np.float32)
        rand_share = self.np_rng.random(n).astype(np.float32)

        bought = rand_buy < prob_buy
        liked = rand_like < like_prob
        shared = rand_share < share_prob

        if progress_callback:
            progress_callback(0.8, "Agent decisions sampled")

        # Zero-loop state update via boolean masking
        pop['purchased'] = pop['purchased'] | bought
        pop['money_spent'] = np.where(bought, pop['money_spent'] + ad.price, pop['money_spent'])
        pop['money'] = np.where(bought, pop['money'] - ad.price, pop['money'])

        if progress_callback:
            progress_callback(1.0, "Simulation complete")

        self.tick += 1

        # Extract features for dashboard
        income = pop['money']
        new_purchases = bought
        engagements = liked | shared
        
        perceived_value = float(np.mean(10.0 * (1.0 + emotional_mod + archetype_score + ad.urgency_score * 0.5)))
        loss_aversion_impact = float(np.mean(np.clip(ad.price / (income + 1e-6), 0.0, 1.0)))
        
        ad_scores = {
            "trust": ad.trust_score,
            "urgency": ad.urgency_score,
            "persuasion": ad.trust_score * 0.5 + ad.urgency_score * 0.5,
            "emotional_appeal": np.mean(emotional_mod) + 0.5
        }
        economic_utility = archetype_score + price_disutility
        recs = generate_recommendations(ad_scores, emotional_mod, economic_utility)
        
        high_income = income > 1200
        med_income = (income >= 600) & (income <= 1200)
        low_income = income < 600

        segment_analysis = {
            "high_income": {
                "conversion_rate": float(np.mean(new_purchases[high_income]) * 100) if np.any(high_income) else 0.0,
                "engagement_rate": float(np.mean(engagements[high_income]) * 100) if np.any(high_income) else 0.0,
                "count": int(np.sum(high_income))
            },
            "medium_income": {
                "conversion_rate": float(np.mean(new_purchases[med_income]) * 100) if np.any(med_income) else 0.0,
                "engagement_rate": float(np.mean(engagements[med_income]) * 100) if np.any(med_income) else 0.0,
                "count": int(np.sum(med_income))
            },
            "low_income": {
                "conversion_rate": float(np.mean(new_purchases[low_income]) * 100) if np.any(low_income) else 0.0,
                "engagement_rate": float(np.mean(engagements[low_income]) * 100) if np.any(low_income) else 0.0,
                "count": int(np.sum(low_income))
            }
        }
        
        personality_performance = {
            "openness": float(np.mean(emotional_mod[pop['openness'] > 0.6])) if np.any(pop['openness'] > 0.6) else 0.0,
            "conscientiousness": float(np.mean(emotional_mod[pop['conscientiousness'] > 0.6])) if np.any(pop['conscientiousness'] > 0.6) else 0.0,
            "extraversion": float(np.mean(emotional_mod[pop['extraversion'] > 0.6])) if np.any(pop['extraversion'] > 0.6) else 0.0,
            "agreeableness": float(np.mean(emotional_mod[pop['agreeableness'] > 0.6])) if np.any(pop['agreeableness'] > 0.6) else 0.0,
            "neuroticism": float(np.mean(emotional_mod[pop['neuroticism'] > 0.6])) if np.any(pop['neuroticism'] > 0.6) else 0.0
        }
        
        prospect_insights = {
            "loss_aversion_impact": loss_aversion_impact,
            "perceived_value": perceived_value,
            "price_sensitivity": {
                "high": float(np.mean(new_purchases[low_income]) * 100) if np.any(low_income) else 0.0,
                "medium": float(np.mean(new_purchases[med_income]) * 100) if np.any(med_income) else 0.0,
                "low": float(np.mean(new_purchases[high_income]) * 100) if np.any(high_income) else 0.0
            },
            "price_elasticity": float(((np.mean(new_purchases[low_income]) if np.any(low_income) else 0) - (np.mean(new_purchases[high_income]) if np.any(high_income) else 0)) * 100)
        }

        conversion_rate = (bought.sum() / n) * 100 if n > 0 else 0
        engagement_rate = ((liked | shared).sum() / n) * 100 if n > 0 else 0

        return {
            'likes': int(liked.sum()),
            'shares': int(shared.sum()),
            'conversions': int(bought.sum()),
            'details': [],
            
            "conversion_rate": float(conversion_rate),
            "engagement_rate": float(engagement_rate),
            "purchase_count": int(bought.sum()),
            "engaged_count": int((liked | shared).sum()),
            "avg_emotional_valence": float(np.mean(emotional_mod)),
            "avg_economic_utility": float(np.mean(economic_utility)),
            "high_emotion_percent": float(np.mean(emotional_mod > 0.7) * 100),
            "total_agents": n,
            
            "scores": ad_scores,
            "segment_analysis": segment_analysis,
            "personality_performance": personality_performance,
            "prospect_insights": prospect_insights,
            "recommendations": recs
        }


def generate_reasoning(ad_a_data: Dict[str, Any], ad_b_data: Dict[str, Any], benchmarks: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Rule-based marketing intelligence engine that produces deterministic insights.
    """
    cvr_a = ad_a_data.get("conversion_rate", 0)
    cvr_b = ad_b_data.get("conversion_rate", 0)
    winner = "A" if cvr_a >= cvr_b else "B"
    
    def analyze_ad(data, name):
        strengths = []
        weaknesses = []
        
        cvr = data.get("conversion_rate", 0)
        eng = data.get("engagement_rate", 0)
        
        if cvr > 3.0: strengths.append(f"Strong conversion rate ({cvr:.1f}%)")
        elif cvr < 1.0: weaknesses.append(f"Low conversion rate ({cvr:.1f}%)")
            
        if eng > 15.0: strengths.append(f"High engagement ({eng:.1f}%) suggests good creative resonance")
        elif eng < 5.0: weaknesses.append(f"Low engagement ({eng:.1f}%)")
            
        scores = data.get("scores", {})
        if scores.get("trust", 0.5) < 0.4: weaknesses.append("Low trust score")
        if scores.get("urgency", 0.5) < 0.3: weaknesses.append("Low urgency")
        if scores.get("persuasion", 0.5) < 0.4: weaknesses.append("Weak persuasion")
        if scores.get("emotional_appeal", 0.5) < 0.3: weaknesses.append("Low emotional appeal")
            
        pros = data.get("prospect_insights", {})
        if pros.get("loss_aversion_impact", 0.0) > 0.4: weaknesses.append("High price sensitivity")
        if pros.get("perceived_value", 0.0) < 0.5: weaknesses.append("Low perceived value")
        
        pers = data.get("personality_performance", {})
        best_trait = max(pers.items(), key=lambda x: x[1]) if pers else ("unknown", 0)
        personality_insight = f"Resonates strongest with High {best_trait[0].title()} audiences."
        
        prospect_insight = f"Perceived value is {pros.get('perceived_value', 0):.2f}, price elasticity is {pros.get('price_elasticity', 0):.1f}%."
        
        return {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "personality_insight": personality_insight,
            "prospect_insight": prospect_insight
        }

    ad_a_breakdown = analyze_ad(ad_a_data, "A")
    ad_b_breakdown = analyze_ad(ad_b_data, "B")
    
    gap = abs(cvr_a - cvr_b)
    overall_summary = f"Ad {winner} won the test with a {gap:.2f}% higher conversion rate."
    if gap < 0.5:
        overall_summary += " The results are close, indicating both ads perform similarly overall."
    else:
        overall_summary += f" Ad {winner} significantly outperformed the alternative."

    key_drivers = []
    if ad_a_data.get("scores", {}).get("trust", 0) != ad_b_data.get("scores", {}).get("trust", 0):
        better = "A" if ad_a_data.get("scores", {}).get("trust", 0) > ad_b_data.get("scores", {}).get("trust", 0) else "B"
        key_drivers.append(f"Trust & Social Proof (Ad {better} leads)")
    if ad_a_data.get("prospect_insights", {}).get("perceived_value", 0) != ad_b_data.get("prospect_insights", {}).get("perceived_value", 0):
        better = "A" if ad_a_data.get("prospect_insights", {}).get("perceived_value", 0) > ad_b_data.get("prospect_insights", {}).get("perceived_value", 0) else "B"
        key_drivers.append(f"Perceived Value (Ad {better} conveys higher value)")
    if not key_drivers:
        key_drivers = ["Overall Conversion Rate", "Engagement Rate"]
        
    actionable_recs = []
    for rec in ad_a_data.get("recommendations", []):
        actionable_recs.append({"ad": "A", **rec})
    for rec in ad_b_data.get("recommendations", []):
        actionable_recs.append({"ad": "B", **rec})
        
    benchmark_comparison = "No external benchmarks provided."
    if benchmarks:
        ind_cvr = benchmarks.get("industry_avg_conversion", 0)
        if ind_cvr:
            diff = max(cvr_a, cvr_b) - ind_cvr
            if diff > 0:
                benchmark_comparison = f"The winning ad's conversion rate is {diff:.1f}% above the industry average ({ind_cvr}%)."
            else:
                benchmark_comparison = f"The winning ad is {-diff:.1f}% below the industry average ({ind_cvr}%)."
        if "seasonality_factor" in benchmarks:
            benchmark_comparison += f" Seasonality note: {benchmarks['seasonality_factor']}."

    return {
        "winner": winner,
        "overall_summary": overall_summary,
        "ad_a_breakdown": ad_a_breakdown,
        "ad_b_breakdown": ad_b_breakdown,
        "key_drivers": key_drivers[:3],
        "actionable_recommendations": actionable_recs,
        "benchmark_comparison": benchmark_comparison
    }
