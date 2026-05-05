from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ChannelType(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    GOOGLE = "google"
    EMAIL = "email"

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

class AdRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Ad creative text")
    price: float = Field(default=20.0, ge=0, description="Product price")
    category: str = Field(default="general", description="Product category")
    social_proof: float = Field(default=2.5, ge=0, le=5, description="Social proof rating (0-5)")
    urgency: float = Field(default=2.5, ge=0, le=5, description="Urgency/Scarcity level (0-5)")
    channel: ChannelType = Field(default=ChannelType.FACEBOOK, description="Marketing channel")
    agents: int = Field(default=1000, ge=100, le=10000, description="Number of agents to simulate")
    seed: Optional[int] = Field(default=None, description="Optional seed for deterministic simulation")

class SimulateResponse(BaseModel):
    predicted_ctr: float
    predicted_cvr: float
    confidence_score: float
    raw_metrics: Dict[str, int]
    failure_reasons: List[str]

class CalibrationRecord(BaseModel):
    predicted_ctr: float
    actual_ctr: float
    predicted_cvr: float
    actual_cvr: float

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
