from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class Ad:
    text: str
    channel: str  # 'facebook', 'tiktok', 'google', 'email'
    creative_type: str  # 'image', 'video', 'text'
    brand: str = "Unknown"
    price: float = 10.0
    category: str = "general"
    social_proof: float = 2.5 # 0-5
    urgency: float = 2.5      # 0-5
    price_score: float = 0.5   # 0-1 (perceived deal quality)
    trust_score: float = 0.5   # 0-1 (brand authority/social proof)
    urgency_score: float = 0.5 # 0-1 (FOMO factor)
    embedding: Optional[List[float]] = None # to be filled by embedder

    def __post_init__(self):
        """Auto-calculate scores using Neural Scorer or Keyword Fallback"""
        from src.ad_processing.neural_scorer import predict_scores
        from src.ad_processing.scorer import extract_scores

        # Only auto-calculate if scores are at their default 0.5
        if self.price_score == 0.5 and self.trust_score == 0.5 and self.urgency_score == 0.5:
            # 1. Attempt Neural Scoring (Weeks 1-2 Fix)
            try:
                scores = predict_scores(self.text)
                self.price_score = scores['price_score']
                self.trust_score = scores['trust_score']
                self.urgency_score = scores['urgency_score']
            except Exception as e:
                # 2. Fallback to Keyword/Heuristic Scoring
                data = {
                    'price': self.price,
                    'category': self.category,
                    'social_proof': self.social_proof,
                    'urgency': self.urgency
                }
                scores = extract_scores(data)
                self.price_score = scores['price_score']
                self.trust_score = scores['trust_score']
                self.urgency_score = scores['urgency_score']

        # Ensure embedding is filled if not present
        if self.embedding is None:
             from src.ad_processing.neural_scorer import get_embedder
             embedder = get_embedder()
             self.embedding = embedder.encode([self.text])[0].tolist()
