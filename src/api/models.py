from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SegmentType(str, Enum):
    BUDGET = "budget"
    PREMIUM = "premium"
    TECH_SAVVY = "tech_savvy"
    TRADITIONAL = "traditional"
    IMPULSIVE = "impulsive"

class AgentProfile(BaseModel):
    id: str
    name: str
    segment: SegmentType
    traits: List[str]
    base_conversion_prob: float = Field(..., ge=0, le=1)
    preferred_channels: List[str]
    sensitivity_to_price: float = Field(..., ge=0, le=1)
    last_interaction: Optional[datetime] = None

class CampaignRequest(BaseModel):
    id: str
    name: str
    channel: str
    budget: float
    target_segments: List[SegmentType]
    parameters: Dict[str, Any] = {}

class SimulationResult(BaseModel):
    campaign_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    total_agents: int
    conversions: int
    conversion_rate: float
    total_spend: float
    estimated_roi: float
    segment_performance: Dict[str, Dict[str, float]]
