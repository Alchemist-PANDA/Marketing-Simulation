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
    image_path: Optional[str] = None
    visual_scores: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Auto-calculate scores using Neural Scorer or Keyword Fallback"""
        try:
            from src.ad_processing.neural_scorer import predict_scores
            neural_available = True
        except ImportError:
            neural_available = False

        from src.ad_processing.scorer import extract_scores

        # Only auto-calculate if scores are at their default 0.5
        if self.price_score == 0.5 and self.trust_score == 0.5 and self.urgency_score == 0.5:
            # 1. Attempt Neural Scoring if available
            if neural_available:
                try:
                    scores = predict_scores(self.text)
                    # If neural scorer returns all 0.5, it might be in fallback mode
                    # In that case, we still try the heuristic scorer for better results
                    if all(v == 0.5 for v in scores.values()):
                        neural_available = False
                    else:
                        self.price_score = scores['price_score']
                        self.trust_score = scores['trust_score']
                        self.urgency_score = scores['urgency_score']
                except Exception:
                    neural_available = False

            # 2. Fallback to Keyword/Heuristic Scoring if neural failed or was disabled
            if not neural_available:
                data = {
                    'price': self.price,
                    'category': self.category,
                    'social_proof': self.social_proof,
                    'urgency': self.urgency,
                    'text': self.text
                }
                scores = extract_scores(data)
                self.price_score = scores.get('price_score', 0.5)
                self.trust_score = scores.get('trust_score', 0.5)
                self.urgency_score = scores.get('urgency_score', 0.5)

        # 3. Visual Scoring
        if not self.visual_scores:
            from src.ad_processing.visual_scorer import score_image
            self.visual_scores = score_image(self.image_path)
