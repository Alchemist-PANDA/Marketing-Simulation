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
    emotion_score: float = 0.5 # 0-1 (Emotional appeal)
    target_interest: Optional[int] = None # Interest ID match
    embedding: Optional[List[float]] = None # to be filled by embedder
    image_path: Optional[str] = None
    visual_scores: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Auto-calculate scores using Heuristic Keyword Fallback"""
        from src.ad_processing.scorer import extract_scores

        # Only auto-calculate if scores are at their default 0.5
        if self.price_score == 0.5 and self.trust_score == 0.5 and self.urgency_score == 0.5:
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
            self.emotion_score = scores.get('emotion_score', 0.5)
            self.target_interest = scores.get('target_interest', None)

        # 3. Visual Scoring
        if not self.visual_scores:
            from src.ad_processing.visual_scorer import score_image
            self.visual_scores = score_image(self.image_path)
