from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Ad:
    text: str
    channel: str  # 'facebook', 'tiktok', 'google', 'email'
    creative_type: str  # 'image', 'video', 'text'
    brand: str = "Unknown"
    price: float = 10.0
    price_score: float = 0.5   # New: 0-1 (perceived deal quality)
    trust_score: float = 0.5   # New: 0-1 (brand authority/social proof)
    urgency_score: float = 0.5 # New: 0-1 (FOMO factor)
    embedding: Optional[List[float]] = None # to be filled by embedder
