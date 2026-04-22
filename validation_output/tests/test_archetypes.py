import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.base_agent import Personality, Agent, AgentState
from src.ad_processing.ad import Ad

def test_agent_archetype_evaluation():
    """Test that agents react differently based on ad scores and their traits."""

    # 1. Price Sensitive Persona (High Conscientiousness)
    price_sensitive_p = Personality(openness=0.5, conscientiousness=0.9, extraversion=0.5,
                                    agreeableness=0.5, neuroticism=0.2)
    ps_agent = Agent("PS Agent", price_sensitive_p, AgentState(money=1000))

    # 2. Impulsive Persona (High Extraversion)
    impulsive_p = Personality(openness=0.5, conscientiousness=0.2, extraversion=0.9,
                              agreeableness=0.5, neuroticism=0.2)
    imp_agent = Agent("Imp Agent", impulsive_p, AgentState(money=1000))

    # Ad with high price score (great deal) but low urgency
    ad_deal = Ad(text="Cheap ad", channel="facebook", creative_type="text", price=10.0,
                 price_score=1.0, urgency_score=0.1, trust_score=0.5)

    # Ad with low price score but high urgency
    ad_urgent = Ad(text="Urgent ad", channel="facebook", creative_type="text", price=10.0,
                   price_score=0.1, urgency_score=1.0, trust_score=0.5)

    # PS agent should prefer the deal ad
    ps_deal_score = ps_agent.evaluate_ad(ad_deal)
    ps_urgent_score = ps_agent.evaluate_ad(ad_urgent)
    assert ps_deal_score > ps_urgent_score, "Price sensitive agent should prefer high price_score"

    # Impulsive agent should prefer the urgent ad
    imp_deal_score = imp_agent.evaluate_ad(ad_deal)
    imp_urgent_score = imp_agent.evaluate_ad(ad_urgent)
    assert imp_urgent_score > imp_deal_score, "Impulsive agent should prefer high urgency_score"

def test_skeptical_agent_suppression():
    """Test that skepticism (neuroticism) reduces the overall ad evaluation."""

    trusting_p = Personality(openness=0.5, conscientiousness=0.5, extraversion=0.5,
                             agreeableness=0.5, neuroticism=0.1)
    trusting_agent = Agent("Trusting", trusting_p, AgentState(money=1000))

    skeptical_p = Personality(openness=0.5, conscientiousness=0.5, extraversion=0.5,
                              agreeableness=0.5, neuroticism=0.9)
    skeptical_agent = Agent("Skeptical", skeptical_p, AgentState(money=1000))

    ad = Ad(text="Test ad", channel="facebook", creative_type="text", price=10.0,
            price_score=0.5, trust_score=0.5, urgency_score=0.5)

    trust_score = trusting_agent.evaluate_ad(ad)
    skep_score = skeptical_agent.evaluate_ad(ad)

    # Skep agent should have a lower evaluation for the same ad due to high neuroticism
    assert trust_score > skep_score, "High neuroticism should lead to more skeptical (lower) evaluations"
