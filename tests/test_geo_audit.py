"""Tests for GEO audit agent."""

import pytest
from geo_audit_agent.audit import run_audit, detect_sentiment, extract_competitors
from geo_audit_agent.measurement import measure_lift, calculate_visibility_score
from geo_audit_agent.remediation import generate_remediation
from geo_audit_agent.industry_templates import get_template


class TestSentimentDetection:
    """Test sentiment detection logic."""

    def test_positive_sentiment_with_stands_out(self):
        """Test positive sentiment when brand stands out."""
        raw_response = "Capital Arena Fitness Club stands out for its commitment to customer satisfaction."
        sentiment = detect_sentiment(raw_response, "Capital Arena Fitness Club")
        assert sentiment == "positive"

    def test_positive_sentiment_with_excellent(self):
        """Test positive sentiment with excellent keyword."""
        raw_response = "Capital Arena Fitness Club offers excellent facilities and top-notch service."
        sentiment = detect_sentiment(raw_response, "Capital Arena Fitness Club")
        assert sentiment == "positive"

    def test_neutral_sentiment_brand_mentioned_no_signal(self):
        """Test neutral sentiment when brand mentioned but no positive/negative signal."""
        raw_response = "Capital Arena Fitness Club is located in Islamabad."
        sentiment = detect_sentiment(raw_response, "Capital Arena Fitness Club")
        assert sentiment == "neutral"

    def test_none_sentiment_brand_not_mentioned(self):
        """Test none sentiment when brand not mentioned."""
        raw_response = "There are many gyms in Islamabad with great facilities."
        sentiment = detect_sentiment(raw_response, "Capital Arena Fitness Club")
        assert sentiment == "none"

    def test_positive_sentiment_multiple_keywords(self):
        """Test positive sentiment with multiple positive keywords."""
        raw_response = "Capital Arena Fitness Club is a premium, well-maintained facility with supportive trainers."
        sentiment = detect_sentiment(raw_response, "Capital Arena Fitness Club")
        assert sentiment == "positive"


class TestCompetitorExtraction:
    """Test competitor extraction logic."""

    def test_extract_numbered_list_competitors(self):
        """Test extraction of numbered list competitors."""
        raw_response = """
        1. Capital Arena Fitness Club
        2. Gold's Gym Islamabad
        3. Fitness First
        """
        competitors = extract_competitors(raw_response, "Capital Arena Fitness Club")
        assert "Gold's Gym Islamabad" in competitors
        assert "Fitness First" in competitors
        assert "Capital Arena Fitness Club" not in competitors

    def test_exclude_target_brand(self):
        """Test that target brand is excluded from competitors."""
        raw_response = """
        1. Capital Arena Fitness Club
        2. Other Gym
        """
        competitors = extract_competitors(raw_response, "Capital Arena Fitness Club")
        assert "Capital Arena Fitness Club" not in competitors
        assert "Other Gym" in competitors

    def test_exclude_generic_placeholders(self):
        """Test that generic placeholders are excluded."""
        raw_response = """
        1. Capital Arena Fitness Club
        2. Local Favorite
        3. Established Brand
        4. Premium Choice
        5. Real Competitor Gym
        """
        competitors = extract_competitors(raw_response, "Capital Arena Fitness Club")
        assert "Local Favorite" not in competitors
        assert "Established Brand" not in competitors
        assert "Premium Choice" not in competitors
        assert "Real Competitor Gym" in competitors

    def test_no_competitors_found(self):
        """Test when no competitors are found."""
        raw_response = "This is just some text without a numbered list."
        competitors = extract_competitors(raw_response, "Capital Arena Fitness Club")
        assert len(competitors) == 0


class TestLiftMeasurement:
    """Test lift measurement logic."""

    def test_positive_lift(self):
        """Test positive lift calculation."""
        result = measure_lift(0.50, 0.75)
        assert result['absolute_lift'] == 0.25
        assert result['percentage_lift'] == 50.0
        assert result['status'] == 'positive'
        assert 'improved' in result['explanation'].lower()

    def test_negative_lift(self):
        """Test negative lift detection."""
        result = measure_lift(1.00, 0.85)
        assert abs(result['absolute_lift'] - (-0.15)) < 0.001
        assert abs(result['percentage_lift'] - (-15.0)) < 0.001
        assert result['status'] == 'negative'
        assert result['message'] == 'Visibility decreased'
        assert 'no lift detected' in result['explanation'].lower()

    def test_baseline_strong(self):
        """Test baseline strong detection."""
        result = measure_lift(0.90, 0.92)
        assert result['status'] == 'baseline_strong'
        assert 'already strong' in result['message'].lower()

    def test_marginal_lift(self):
        """Test marginal lift detection."""
        result = measure_lift(0.50, 0.52)
        assert abs(result['absolute_lift'] - 0.02) < 0.001
        assert result['status'] == 'marginal'


class TestFitnessTemplate:
    """Test fitness gym industry template."""

    def test_fitness_category_detection(self):
        """Test that fitness category triggers template."""
        template = get_template('fitness gym')
        assert template is not None
        assert template.__class__.__name__ == 'FitnessGymTemplate'

    def test_gym_category_detection(self):
        """Test that gym category triggers template."""
        template = get_template('gym')
        assert template is not None

    def test_health_club_category_detection(self):
        """Test that health club category triggers template."""
        template = get_template('health club')
        assert template is not None

    def test_fitness_template_gaps(self):
        """Test fitness template generates gym-specific gaps."""
        template = get_template('fitness gym')
        business_data = {
            'has_schema': False,
            'services': [],
            'has_trainer_info': False,
            'has_pricing': False,
            'has_schedule': False,
            'city': 'Islamabad',
            'has_local_content': False,
        }
        gaps = template.get_gaps(business_data)
        assert len(gaps) > 0
        assert any('schema' in gap['type'] for gap in gaps)
        assert any('trainer' in gap['title'].lower() for gap in gaps)

    def test_fitness_template_strengths(self):
        """Test fitness template identifies strengths."""
        template = get_template('fitness gym')
        business_data = {
            'review_count': 231,
            'rating': 4.5,
            'services': ['swimming pool', 'sauna', 'spa', 'physiotherapy'],
            'instagram_followers': 18300,
            'facebook_followers': 12200,
            'is_central_location': True,
            'location_description': 'F-9 Park, Islamabad',
        }
        strengths = template.get_strengths(business_data)
        assert len(strengths) > 0
        assert any('review' in strength['title'].lower() for strength in strengths)
        assert any('facility' in strength['title'].lower() or 'premium' in strength['title'].lower() for strength in strengths)


class TestCapitalArenaScenario:
    """Test Capital Arena Fitness Club scenario."""

    def test_capital_arena_audit(self):
        """Test full audit for Capital Arena."""
        business_data = {
            'review_count': 231,
            'rating': 4.5,
            'services': ['online classes', 'sauna', 'swimming pool', 'gym', 'spa', 'steam', 'protein bar', 'physiotherapy'],
            'instagram_followers': 18300,
            'facebook_followers': 12200,
            'location_description': 'F-9 Park / Megazone, Islamabad',
            'is_central_location': True,
            'raw_response': 'Capital Arena Fitness Club stands out for its commitment to customer satisfaction.\n1. Capital Arena Fitness Club\n2. Local Favorite\n3. Established Brand',
            'has_schema': False,
            'has_trainer_info': False,
            'has_pricing': False,
            'has_schedule': False,
            'has_local_content': False,
        }

        results = run_audit('Capital Arena Fitness Club', 'fitness gym', 'Islamabad', business_data)

        # Should use fitness template
        assert results['template_used'] == 'FitnessGymTemplate'

        # Should detect positive sentiment
        assert results['sentiment'] == 'positive'

        # Should not include generic placeholders in competitors
        assert 'Local Favorite' not in results['competitors']
        assert 'Established Brand' not in results['competitors']

        # Should identify strengths (not say "no recent reviews found")
        assert len(results['strengths']) > 0

        # Should identify gaps
        assert len(results['gaps']) > 0

    def test_capital_arena_remediation(self):
        """Test remediation generation for Capital Arena."""
        gaps = [
            {'type': 'schema', 'severity': 'high', 'title': 'Missing structured data'},
            {'type': 'content', 'severity': 'medium', 'title': 'Missing service pages'},
            {'type': 'local_seo', 'severity': 'high', 'title': 'Missing local intent content'},
        ]

        remediation = generate_remediation(gaps, 'fitness gym', 'Islamabad', 'Capital Arena Fitness Club')

        # Should always generate remediation when gaps exist
        assert len(remediation) > 0

        # Should include gym-specific recommendations
        assert any('schema' in rem['type'] for rem in remediation)
        assert any('service' in rem['title'].lower() for rem in remediation)
        assert any('islamabad' in rem['action'].lower() for rem in remediation)

    def test_capital_arena_no_false_gaps(self):
        """Test that Capital Arena doesn't get false 'no recent reviews' gap."""
        business_data = {
            'review_count': 231,
            'rating': 4.5,
        }

        # Calculate visibility score - should not penalize for missing reviews
        score = calculate_visibility_score(business_data, [])
        assert score > 0.8  # Should have high score with good reviews


class TestRemediation:
    """Test remediation generation."""

    def test_remediation_always_generated_when_gaps_exist(self):
        """Test that remediation is always generated when gaps exist."""
        gaps = [
            {'type': 'schema', 'severity': 'high', 'title': 'Missing schema'},
        ]
        remediation = generate_remediation(gaps, 'fitness gym', 'Islamabad', 'Test Gym')
        assert len(remediation) > 0

    def test_no_remediation_when_no_gaps(self):
        """Test that no remediation is generated when no gaps exist."""
        gaps = []
        remediation = generate_remediation(gaps, 'fitness gym', 'Islamabad', 'Test Gym')
        assert len(remediation) == 0

    def test_remediation_includes_required_fields(self):
        """Test that remediation includes all required fields."""
        gaps = [
            {'type': 'schema', 'severity': 'high', 'title': 'Missing schema'},
        ]
        remediation = generate_remediation(gaps, 'fitness gym', 'Islamabad', 'Test Gym')

        for rem in remediation:
            assert 'priority' in rem
            assert 'type' in rem
            assert 'title' in rem
            assert 'reason' in rem
            assert 'why_this_works' in rem
            assert 'action' in rem
            assert 'effort' in rem
            assert 'impact' in rem
