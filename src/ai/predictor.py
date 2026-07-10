"""
AI-enhanced CTR prediction module.

Provides a unified interface for:
1. Classic mode: keyword-based simulation engine
2. AI mode: ML model trained on text features + embeddings
3. Ensemble mode: weighted combination of both

Usage:
    from src.ai.predictor import AIPredictor
    predictor = AIPredictor()
    result = predictor.predict("Flash Sale! 50% off!", mode='ensemble')
"""

import os
import pickle
import numpy as np
from typing import Dict, Optional, List

_predictor_instance = None


class AIPredictor:
    def __init__(self, model_path='models/ai_ctr_model.pkl'):
        self.model = None
        self.model_info = None
        self._embedder = None
        self._ensemble = None  # lazy-loaded EnsemblePredictor (preferred if present)

        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.model_info = {
                    'name': data.get('model_name', 'unknown'),
                    'n_keyword_features': data.get('n_keyword_features', 3),
                    'n_stat_features': data.get('n_stat_features', 9),
                }

    def _get_embedder(self):
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer('all-MiniLM-L6-v2')
            except ImportError:
                self._embedder = False
        return self._embedder if self._embedder is not False else None

    def _extract_features(self, text: str) -> np.ndarray:
        from src.ad_processing.scorer import extract_text_scores

        scores = extract_text_scores(text)
        kw_feats = [scores['price_score'], scores['trust_score'], scores['urgency_score']]

        words = text.split()
        stat_feats = [
            len(words),
            len(text),
            text.count('!'),
            text.count('?'),
            text.count('%'),
            sum(1 for c in text if c.isupper()) / max(len(text), 1),
            len([w for w in words if w[0].isupper()]) / max(len(words), 1) if words else 0,
            1 if any(c.isdigit() for c in text) else 0,
            text.count('$'),
        ]

        embedder = self._get_embedder()
        if embedder:
            emb = embedder.encode([text], show_progress_bar=False)[0]
        else:
            emb = np.zeros(384, dtype=np.float32)

        features = np.array(kw_feats + stat_feats + list(emb), dtype=np.float32)
        return features

    def predict_classic(self, text: str, num_agents: int = 10000, seed: int = 42) -> Dict:
        """Predict using the simulation engine (classic mode)."""
        from src.simulation.max_engine import MaxSimulation
        from src.ad_processing.ad import Ad
        from src.agents.agent_generator import generate_population_arrays

        pop = generate_population_arrays(num_agents, seed=seed)
        sim = MaxSimulation(seed=seed, population=pop)
        ad = Ad(text=text, channel='facebook', creative_type='text')
        res = sim.simulate_exposure(ad)

        return {
            'predicted_ctr': res['likes'] / num_agents,
            'mode': 'classic',
            'scores': {
                'price_score': ad.price_score,
                'trust_score': ad.trust_score,
                'urgency_score': ad.urgency_score,
            },
            'engagement': {
                'likes': res['likes'],
                'shares': res['shares'],
                'conversions': res['conversions'],
            }
        }

    def _get_ensemble(self):
        """Lazily load the upgraded ensemble model, if it was trained/saved."""
        if self._ensemble is None:
            try:
                from src.ai.ensemble_predictor import get_ensemble_predictor
                self._ensemble = get_ensemble_predictor()
            except Exception:
                self._ensemble = False
        return self._ensemble if self._ensemble not in (False, None) else None

    def predict_ai(self, text: str) -> Dict:
        """Predict using the trained ML model.

        Prefers the upgraded ensemble (models/ensemble_model.pkl) when present,
        and falls back to the legacy single model, then to the classic engine —
        so the app never breaks if an artifact is missing.
        """
        # Preferred path: upgraded ensemble
        ens = self._get_ensemble()
        if ens is not None and getattr(ens, "available", False):
            try:
                from src.ad_processing.scorer import extract_text_scores
                out = ens.predict(text)
                scores = extract_text_scores(text)
                return {
                    'predicted_ctr': out['predicted_ctr'],
                    'mode': 'ai',
                    'model': out['model_version'],
                    'model_version': out['model_version'],
                    'confidence': out['confidence'],
                    'scores': {
                        'price_score': scores['price_score'],
                        'trust_score': scores['trust_score'],
                        'urgency_score': scores['urgency_score'],
                    },
                }
            except Exception:
                pass  # fall through to legacy model / classic

        if self.model is None:
            return self.predict_classic(text)

        features = self._extract_features(text)
        from src.ad_processing.scorer import extract_text_scores
        scores = extract_text_scores(text)

        n_kw = self.model_info.get('n_keyword_features', 3)
        n_stats = self.model_info.get('n_stat_features', 9)
        model_name = self.model_info.get('name', '')

        if 'keyword_ridge' == model_name:
            X = features[:n_kw].reshape(1, -1)
        elif 'keyword_stats' in model_name:
            X = features[:n_kw + n_stats].reshape(1, -1)
        elif 'emb' in model_name and 'all' not in model_name:
            X = features[n_kw + n_stats:].reshape(1, -1)
        else:
            X = features.reshape(1, -1)

        pred = float(self.model.predict(X)[0])
        pred = max(0.0001, pred)

        return {
            'predicted_ctr': pred,
            'mode': 'ai',
            'model': model_name,
            'model_version': f'legacy-{model_name}',
            'scores': {
                'price_score': scores['price_score'],
                'trust_score': scores['trust_score'],
                'urgency_score': scores['urgency_score'],
            }
        }

    def predict_ensemble(self, text: str, ai_weight: float = 0.5,
                         num_agents: int = 10000, seed: int = 42) -> Dict:
        """Predict using weighted ensemble of simulation + ML."""
        classic = self.predict_classic(text, num_agents, seed)
        ai = self.predict_ai(text)

        classic_rank = classic['predicted_ctr']
        ai_rank = ai['predicted_ctr']

        from sklearn.preprocessing import minmax_scale
        ensemble_score = (1 - ai_weight) * classic_rank + ai_weight * ai_rank

        return {
            'predicted_ctr': ensemble_score,
            'mode': 'ensemble',
            'classic_ctr': classic_rank,
            'ai_ctr': ai_rank,
            'ai_weight': ai_weight,
            'scores': classic['scores'],
            'engagement': classic.get('engagement', {}),
        }

    def predict(self, text: str, mode: str = 'classic', **kwargs) -> Dict:
        """Unified prediction interface."""
        if mode == 'classic':
            return self.predict_classic(text, **kwargs)
        elif mode == 'ai':
            return self.predict_ai(text)
        elif mode == 'ensemble':
            return self.predict_ensemble(text, **kwargs)
        else:
            raise ValueError(f"Unknown mode: {mode}. Use 'classic', 'ai', or 'ensemble'.")

    def explain(self, text: str) -> Dict:
        """Generate feature-level explanation for a prediction."""
        from src.ad_processing.scorer import extract_text_scores, _count_matches
        from src.ad_processing.scorer import (
            _PRICE_POSITIVE, _PRICE_NEGATIVE,
            _TRUST_POSITIVE, _TRUST_NEGATIVE,
            _URGENCY_POSITIVE, _ACTION_VERBS
        )

        scores = extract_text_scores(text)
        text_lower = text.lower()

        price_pos = [kw for kw in _PRICE_POSITIVE if kw in text_lower]
        price_neg = [kw for kw in _PRICE_NEGATIVE if kw in text_lower]
        trust_pos = [kw for kw in _TRUST_POSITIVE if kw in text_lower]
        trust_neg = [kw for kw in _TRUST_NEGATIVE if kw in text_lower]
        urgency_pos = [kw for kw in _URGENCY_POSITIVE if kw in text_lower]
        action_verbs = [kw for kw in _ACTION_VERBS if kw in text_lower]

        explanations = []

        if price_pos:
            explanations.append({
                'factor': 'Price Appeal',
                'direction': 'positive',
                'keywords': price_pos,
                'impact': f'+{len(price_pos) * 0.15:.2f} to price score',
                'explanation': f'Keywords like "{price_pos[0]}" signal a good deal, attracting price-conscious consumers.'
            })
        if price_neg:
            explanations.append({
                'factor': 'Premium Positioning',
                'direction': 'negative',
                'keywords': price_neg,
                'impact': f'-{len(price_neg) * 0.15:.2f} to price score',
                'explanation': f'Keywords like "{price_neg[0]}" signal luxury pricing, which reduces click-through but may increase conversion quality.'
            })
        if trust_pos:
            explanations.append({
                'factor': 'Trust Signals',
                'direction': 'positive',
                'keywords': trust_pos,
                'impact': f'+{min(len(trust_pos), 1) * 0.15 + max(len(trust_pos)-1, 0) * 0.05:.2f} to trust score',
                'explanation': f'Keywords like "{trust_pos[0]}" build credibility and reduce purchase anxiety.'
            })
        if urgency_pos:
            explanations.append({
                'factor': 'Urgency/Scarcity',
                'direction': 'positive',
                'keywords': urgency_pos,
                'impact': f'+{len(urgency_pos) * 0.20:.2f} to urgency score',
                'explanation': f'Keywords like "{urgency_pos[0]}" create FOMO and drive immediate action.'
            })
        if action_verbs:
            explanations.append({
                'factor': 'Call-to-Action',
                'direction': 'positive',
                'keywords': action_verbs,
                'impact': f'Urgency +{min(len(action_verbs), 2) * 0.05:.2f}, Price +{min(len(action_verbs), 2) * 0.03:.2f}',
                'explanation': f'Action verbs like "{action_verbs[0]}" create direct-response intent.'
            })

        if not explanations:
            explanations.append({
                'factor': 'No Strong Signals',
                'direction': 'neutral',
                'keywords': [],
                'impact': 'Default scores applied',
                'explanation': 'This ad lacks strong promotional, trust, or urgency keywords. Consider adding a clear call-to-action or value proposition.'
            })

        return {
            'scores': scores,
            'explanations': explanations,
            'recommendation': self._generate_recommendation(scores, explanations),
        }

    def _generate_recommendation(self, scores: Dict, explanations: List) -> str:
        weakest = min(scores, key=scores.get)
        if weakest == 'urgency_score' and scores['urgency_score'] < 0.4:
            return "Add urgency: include time-limited language like 'today only', 'limited time', or 'hurry'."
        elif weakest == 'price_score' and scores['price_score'] < 0.4:
            return "Highlight value: mention discounts, free offers, or concrete savings."
        elif weakest == 'trust_score' and scores['trust_score'] < 0.4:
            return "Build trust: add social proof like 'trusted by thousands' or 'certified'."
        return "This ad has balanced signals across price, trust, and urgency."


def get_predictor() -> AIPredictor:
    """Get or create singleton predictor instance."""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = AIPredictor()
    return _predictor_instance
