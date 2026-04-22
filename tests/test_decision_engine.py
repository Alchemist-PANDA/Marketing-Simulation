import pytest
from src.simulation.decision_engine import DecisionEngine

def test_decision_engine_initialization():
    engine = DecisionEngine()
    assert engine is not None

def test_response_logic_positive():
    engine = DecisionEngine()
    # Mocking agent data
    agent = {
        "id": 1,
        "persona": "Early Adopter Gen Z",
        "price_sensitivity": 0.40,
        "brand_loyalty": 0.20,
        "digital_savviness": 0.98,
        "preferred_channel": "Social Media"
    }
    # Mocking campaign data
    campaign = {
        "type": "Social Influencer Post",
        "channel": "Social Media",
        "base_cost": 2.50,
        "effectiveness_modifier": 1.2,
        "trait_target": "digital_savviness"
    }

    response_prob = engine.calculate_response_probability(agent, campaign)
    assert response_prob > 0.5

def test_response_logic_negative():
    engine = DecisionEngine()
    # Mocking agent data
    agent = {
        "id": 2,
        "persona": "Budget-Conscious Senior",
        "price_sensitivity": 0.95,
        "brand_loyalty": 0.80,
        "digital_savviness": 0.20,
        "preferred_channel": "Direct Mail"
    }
    # Mocking campaign data
    campaign = {
        "type": "Social Influencer Post",
        "channel": "Social Media",
        "base_cost": 2.50,
        "effectiveness_modifier": 1.2,
        "trait_target": "digital_savviness"
    }

    response_prob = engine.calculate_response_probability(agent, campaign)
    assert response_prob < 0.5