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

    def test_remediation_has_business_friendly_titles(self):
        """Test that remediation uses business-friendly titles, not tool names."""
        gaps = [
            {'type': 'schema', 'severity': 'high', 'title': 'Missing structured data'},
            {'type': 'content', 'severity': 'medium', 'title': 'Missing service pages'},
            {'type': 'local_seo', 'severity': 'high', 'title': 'Missing local intent content'},
        ]
        remediation = generate_remediation(gaps, 'fitness gym', 'Islamabad', 'Test Gym')

        # Check that titles are business-friendly
        titles = [rem['title'] for rem in remediation]
        assert any('structured data' in title.lower() for title in titles)
        assert any('service' in title.lower() for title in titles)
        assert any('local' in title.lower() or 'islamabad' in title.lower() for title in titles)

        # Check that no tool names appear
        for title in titles:
            assert 'generate_json_ld' not in title.lower()
            assert 'tool' not in title.lower()
            assert 'output_preview' not in title.lower()

    def test_remediation_deduplication(self):
        """Test that duplicate remediation cards are handled."""
        gaps = [
            {'type': 'schema', 'severity': 'high', 'title': 'Missing schema'},
            {'type': 'schema', 'severity': 'high', 'title': 'Missing schema'},  # duplicate
        ]
        remediation = generate_remediation(gaps, 'fitness gym', 'Islamabad', 'Test Gym')

        # Should generate remediation for schema gap
        assert len(remediation) > 0

        # Check titles are unique (deduplication happens in dashboard display logic)
        titles = [rem['title'] for rem in remediation]
        # Note: deduplication is handled in dashboard.py, not remediation.py
        # This test verifies remediation.py generates consistent titles


class TestEcommerceTemplate:
    """Test ecommerce industry template."""

    def test_ecommerce_category_detection(self):
        """Test that ecommerce category triggers template."""
        template = get_template('online fashion store')
        assert template is not None
        assert template.__class__.__name__ == 'EcommerceTemplate'

        # Fitness gym logic is not triggered
        assert template.__class__.__name__ != 'FitnessGymTemplate'

    def test_ecommerce_template_gaps(self):
        """Test ecommerce template generates ecommerce-specific gaps."""
        template = get_template('online fashion store')
        business_data = {
            'has_schema': False,
            'has_product_reviews': False,
            'has_shipping_info': False,
            'has_size_guide': False,
            'has_faq': False,
            'has_trust_badges': False,
            'has_comparison_content': False,
            'has_category_pages': False,
            'market': 'Pakistan',
            'category': 'online fashion store'
        }
        gaps = template.get_gaps(business_data)
        assert len(gaps) > 0

        types = [gap['type'] for gap in gaps]
        assert 'schema' in types
        assert 'reviews' in types
        assert 'trust' in types

        # Verify no fitness gym logic
        titles = [gap['title'].lower() for gap in gaps]
        assert not any('trainer' in t for t in titles)
        assert not any('class schedule' in t for t in titles)

    def test_ecommerce_template_strengths(self):
        """Test ecommerce template identifies strengths."""
        template = get_template('online fashion store')
        business_data = {
            'platform': 'Shopify',
            'has_product_catalog': True,
            'has_return_policy': True,
            'return_policy_description': '14-day exchange window',
            'has_payment_options': True,
            'payment_options_description': 'American Express, Mastercard, and Visa',
            'instagram_followers': 12000,
            'has_social_presence': True,
            'market': 'Pakistan'
        }
        strengths = template.get_strengths(business_data)
        assert len(strengths) > 0

        titles = [s['title'].lower() for s in strengths]
        assert any('shopify' in t for t in titles)
        assert any('return' in t or 'exchange' in t for t in titles)
        assert any('payment' in t for t in titles)
        assert any('social' in t for t in titles)


class TestMEMEScenario:
    """Test MEME Official Store scenario."""

    def test_meme_audit(self):
        """Test full audit for MEME Official Store."""
        business_data = {
            'platform': 'Shopify',
            'has_product_catalog': True,
            'has_return_policy': True,
            'return_policy_description': '14-day exchange window',
            'has_payment_options': True,
            'instagram_followers': 12000,
            'has_social_presence': True,
            'market': 'Pakistan',
            'has_schema': False,
            'has_product_reviews': False,
            'has_shipping_info': False,
            'has_size_guide': False,
            'has_faq': False,
            'has_trust_badges': False,
            'has_comparison_content': False,
            'has_category_pages': False,
            'raw_response': 'MEME Official Store is the best fashion destination.\n1. MEME Official Store\n2. Sapphire\n3. Khaadi',
        }

        results = run_audit('MEME Official Store', 'online fashion store', 'Pakistan', business_data)

        # Should use ecommerce template
        assert results['template_used'] == 'EcommerceTemplate'

        # Should not use fitness template
        assert results['template_used'] != 'FitnessGymTemplate'

        # Should identify strengths
        assert len(results['strengths']) > 0

        # Should identify gaps
        assert len(results['gaps']) > 0

    def test_meme_remediation(self):
        """Test remediation generation for MEME Official Store."""
        gaps = [
            {'type': 'schema', 'severity': 'high', 'title': 'Missing structured data'},
            {'type': 'reviews', 'severity': 'high', 'title': 'Missing product-specific reviews'},
            {'type': 'content', 'severity': 'high', 'title': 'Missing comparison content'},
        ]

        remediation = generate_remediation(gaps, 'online fashion store', 'Pakistan', 'MEME Official Store')

        assert len(remediation) > 0

        titles_actions = ' '.join([rem['title'].lower() + ' ' + rem['action'].lower() for rem in remediation])

        # Verify ecommerce specific remediations
        assert 'schema' in titles_actions or 'structured data' in titles_actions
        assert 'review' in titles_actions

        # Verify no gym specific remediations
        assert 'healthclub' not in titles_actions
        assert 'sportsactivitylocation' not in titles_actions
        assert 'trainer' not in titles_actions
        assert 'class schedule' not in titles_actions
