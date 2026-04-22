from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Ad:
    text: str
    channel: str  # 'facebook', 'tiktok', 'google', 'email'
    creative_type: str  # 'image', 'video', 'text'
    brand: str = "Unknown"
    price: float = 10.0
    embedding: Optional[List[float]] = None # to be filled by embedder
