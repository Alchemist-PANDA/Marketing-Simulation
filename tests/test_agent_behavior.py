import pytest
import sys
import os
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.base_agent import Personality, Agent, AgentState
from src.ad_processing.ad import Ad

@pytest.fixture
def setup_seed():
    random.seed(42)

def test_price_sensitive_sensitivity(setup_seed):
    """Test that increasing price_score increases evaluation for PriceSensitiveAgent traits."""
    p = Personality(openness=0.4, conscientiousness=0.9, extraversion=0.3, agreeableness=0.5, neuroticism=0.2)
    agent = Agent("PriceSensitive", p, AgentState(money=1000))

    ad_low = Ad(text="Low price score", channel="facebook", creative_type="text", price_score=0.1, trust_score=0.5, urgency_score=0.5)
    ad_high = Ad(text="High price score", channel="facebook", creative_type="text", price_score=0.9, trust_score=0.5, urgency_score=0.5)

    score_low = agent.evaluate_ad(ad_low)
    score_high = agent.evaluate_ad(ad_high)

    assert score_high - score_low > 0.05, f"PriceSensitive should be sensitive to price_score, diff: {score_high - score_low}"

def test_social_proof_sensitivity(setup_seed):
    """Test that increasing trust_score increases evaluation for SocialProofAgent traits."""
    p = Personality(openness=0.6, conscientiousness=0.5, extraversion=0.8, agreeableness=0.9, neuroticism=0.3)
    agent = Agent("SocialProof", p, AgentState(money=1000))

    ad_low = Ad(text="Low trust", channel="facebook", creative_type="text", price_score=0.5, trust_score=0.1, urgency_score=0.5)
    ad_high = Ad(text="High trust", channel="facebook", creative_type="text", price_score=0.5, trust_score=0.9, urgency_score=0.5)

    score_low = agent.evaluate_ad(ad_low)
    score_high = agent.evaluate_ad(ad_high)

    assert score_high - score_low > 0.05, f"SocialProof should be sensitive to trust_score, diff: {score_high - score_low}"

def test_impulsive_sensitivity(setup_seed):
    """Test that increasing urgency_score increases evaluation for ImpulsiveAgent traits."""
    # Note: urgency_sensitivity is derived from extraversion and neuroticism
    p = Personality(openness=0.7, conscientiousness=0.2, extraversion=0.9, agreeableness=0.5, neuroticism=0.8)
    agent = Agent("Impulsive", p, AgentState(money=1000))

    ad_low = Ad(text="Low urgency", channel="facebook", creative_type="text", price_score=0.5, trust_score=0.5, urgency_score=0.1)
    ad_high = Ad(text="High urgency", channel="facebook", creative_type="text", price_score=0.5, trust_score=0.5, urgency_score=0.9)

    score_low = agent.evaluate_ad(ad_low)
    score_high = agent.evaluate_ad(ad_high)

    assert score_high - score_low > 0.05, f"Impulsive should be sensitive to urgency_score, diff: {score_high - score_low}"

def test_skeptical_sensitivity(setup_seed):
    """Test that SkepticalAgent (high neuroticism) has muted or lower overall responses."""
    p = Personality(openness=0.2, conscientiousness=0.6, extraversion=0.2, agreeableness=0.2, neuroticism=0.9)
    agent = Agent("Skeptical", p, AgentState(money=1000))

    # Skeptical agents have high skepticism (0.9 * 0.3 = 0.27) which subtracts from score
    ad_base = Ad(text="Base", channel="facebook", creative_type="text", price_score=0.5, trust_score=0.5, urgency_score=0.5)
    score_base = agent.evaluate_ad(ad_base)

    ad_vary = Ad(text="Vary", channel="facebook", creative_type="text", price_score=0.9, trust_score=0.9, urgency_score=0.9)
    score_vary = agent.evaluate_ad(ad_vary)

    # Change should still be positive but the total score should be relatively low due to skepticism
    # And the individual weights for skeptical archetypes (low A, low E) are smaller
    diff = score_vary - score_base
    # Adjusted threshold for skeptical sensitivity
    assert diff < 0.5, f"Skeptical agent should have muted sensitivity, diff: {diff}"
