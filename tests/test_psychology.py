import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.psychology.prospect_theory import ProspectTheoryEngine
from src.psychology.engagement_predictor import EngagementPredictor
from src.agents.base_agent import Personality
from src.ad_processing.ad import Ad

def test_prospect_theory_loss_aversion():
    """Test that losses hurt more than equivalent gains"""
    engine = ProspectTheoryEngine()

    gain_util = engine.apply(0.2, reference=0)
    loss_util = engine.apply(-0.2, reference=0)

    # Loss aversion: absolute value of loss utility should be greater
    assert abs(loss_util) > abs(gain_util), "Loss aversion not working correctly"

def test_engagement_predictor_extraversion():
    """Test that extraverts are more likely to like and share"""
    pred = EngagementPredictor()

    high_extra = Personality(openness=0.5, conscientiousness=0.5, extraversion=0.9,
                             agreeableness=0.5, neuroticism=0.2, values={})
    low_extra = Personality(openness=0.5, conscientiousness=0.5, extraversion=0.1,
                            agreeableness=0.5, neuroticism=0.8, values={})

    ad = Ad(text="Test ad", channel="facebook", creative_type="text")

    like_high = pred.predict_like_probability(high_extra, ad)
    like_low = pred.predict_like_probability(low_extra, ad)

    assert like_high > like_low, "Extraverts should be more likely to like"

    share_high = pred.predict_share_probability(high_extra, ad)
    share_low = pred.predict_share_probability(low_extra, ad)

    assert share_high > share_low, "Extraverts should be more likely to share"

def test_probability_weight():
    """Test probability weighting function"""
    engine = ProspectTheoryEngine()

    # Small probabilities should be overweighted
    w_small = engine.probability_weight(0.01)
    assert w_small > 0.01, "Small probabilities should be overweighted"

    # Large probabilities should be underweighted
    w_large = engine.probability_weight(0.99)
    assert w_large < 0.99, "Large probabilities should be underweighted"
