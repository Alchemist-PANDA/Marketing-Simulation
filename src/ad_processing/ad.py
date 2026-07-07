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
        """Auto-calculate scores from ad text.

        Scoring priority:
        1. Text-aware keyword analysis (always available, no ML deps)
        2. Neural scorer via sentence-transformers (when installed and
           the keyword scorer found no signal in the text)
        3. Attribute-based fallback (price/social_proof/urgency numbers)
        """
        from src.ad_processing.scorer import extract_scores, extract_text_scores

        if self.price_score == 0.5 and self.trust_score == 0.5 and self.urgency_score == 0.5:
            # Try text-aware keyword scoring first
            text_scores = extract_text_scores(self.text)
            has_keyword_signal = (
                text_scores['price_score'] != 0.5
                or text_scores['trust_score'] != 0.45
                or text_scores['urgency_score'] != 0.3
            )

            if has_keyword_signal:
                self.price_score = text_scores['price_score']
                self.trust_score = text_scores['trust_score']
                self.urgency_score = text_scores['urgency_score']
            else:
                # No keyword signal — try neural scorer for semantic analysis
                try:
                    from src.ad_processing.neural_scorer import predict_scores
                    scores = predict_scores(self.text)
                    if not all(v == 0.5 for v in scores.values()):
                        self.price_score = scores['price_score']
                        self.trust_score = scores['trust_score']
                        self.urgency_score = scores['urgency_score']
                        return
                except (ImportError, Exception):
                    pass

                # Final fallback: attribute-based scoring
                data = {
                    'price': self.price,
                    'category': self.category,
                    'social_proof': self.social_proof,
                    'urgency': self.urgency,
                    'text': self.text,
                }
                scores = extract_scores(data)
                self.price_score = scores.get('price_score', 0.5)
                self.trust_score = scores.get('trust_score', 0.5)
                self.urgency_score = scores.get('urgency_score', 0.5)
                self.price_score = scores.get('price_score', 0.5)
                self.trust_score = scores.get('trust_score', 0.5)
                self.urgency_score = scores.get('urgency_score', 0.5)

        # Ensure embedding is filled if not present
        if self.embedding is None:
             from src.ad_processing.neural_scorer import get_embedder
             embedder = get_embedder()
             self.embedding = embedder.encode([self.text])[0].tolist()
