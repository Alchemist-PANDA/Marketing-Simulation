"""Fitness gym industry template for GEO audit recommendations."""

class FitnessGymTemplate:
    """Industry-specific template for fitness gyms and health clubs."""

    def __init__(self):
        self.category_triggers = [
            'fitness', 'gym', 'health club', 'training', 'personal training'
        ]

        self.recommendation_signals = [
            'google_rating',
            'review_count',
            'trainer_credibility',
            'equipment_quality',
            'cleanliness',
            'facility_depth',
            'swimming_pool',
            'sauna',
            'steam',
            'personal_training',
            'physiotherapy',
            'membership_pricing',
            'class_schedule',
            'transformation_stories',
            'social_proof',
            'location_convenience',
            'opening_hours',
        ]

        self.schema_recommendations = [
            'LocalBusiness',
            'SportsActivityLocation',
            'HealthClub',
            'Review',
            'FAQPage',
            'Service',
        ]

        self.review_keywords = [
            'trainers',
            'cleanliness',
            'equipment',
            'results',
            'weight loss',
            'personal training',
            'sauna',
            'pool',
            'atmosphere',
            'hygiene',
            'supportive',
            'clean',
            'transformation',
        ]

        self.remediation_playbook = {
            'schema': {
                'priority': 'high',
                'actions': [
                    'Add SportsActivityLocation schema',
                    'Add HealthClub schema',
                    'Add LocalBusiness schema with facility details',
                ],
            },
            'content': {
                'priority': 'high',
                'actions': [
                    'Create service pages for personal training',
                    'Create service pages for swimming pool',
                    'Create service pages for sauna/steam',
                    'Create service pages for weight loss programs',
                    'Create service pages for strength training',
                    'Add trainer credential sections',
                    'Add membership/pricing page',
                    'Add class schedule page',
                ],
            },
            'reviews': {
                'priority': 'medium',
                'actions': [
                    'Collect reviews mentioning trainers',
                    'Collect reviews mentioning cleanliness',
                    'Collect reviews mentioning equipment',
                    'Collect reviews mentioning results',
                    'Collect reviews mentioning sauna/pool',
                    'Add transformation stories or case studies',
                ],
            },
            'local_seo': {
                'priority': 'high',
                'actions': [
                    'Improve Google Business Profile with facility photos',
                    'Add class posts to Google Business Profile',
                    'Update service list on Google Business Profile',
                    'Create "best gym with swimming pool in [city]" content',
                    'Create "best premium gym in [city]" content',
                    'Create "best gym for personal training in [city]" content',
                ],
            },
        }

    def get_gaps(self, business_data: dict) -> list:
        """Generate fitness-specific gaps based on business data."""
        gaps = []

        # Check for schema
        if not business_data.get('has_schema'):
            gaps.append({
                'type': 'schema',
                'severity': 'high',
                'title': 'Missing structured data',
                'description': 'No SportsActivityLocation or HealthClub schema detected',
            })

        # Check for service pages
        services = business_data.get('services', [])
        expected_services = ['personal training', 'swimming pool', 'sauna', 'weight loss']
        missing_services = [s for s in expected_services if not any(s in str(srv).lower() for srv in services)]

        if missing_services:
            gaps.append({
                'type': 'content',
                'severity': 'medium',
                'title': 'Missing service pages',
                'description': f'No dedicated pages for: {", ".join(missing_services)}',
            })

        # Check for trainer credentials
        if not business_data.get('has_trainer_info'):
            gaps.append({
                'type': 'content',
                'severity': 'medium',
                'title': 'Missing trainer credentials',
                'description': 'No trainer credential or bio sections found',
            })

        # Check for pricing/membership info
        if not business_data.get('has_pricing'):
            gaps.append({
                'type': 'content',
                'severity': 'low',
                'title': 'Missing pricing information',
                'description': 'No membership or pricing details found',
            })

        # Check for class schedule
        if not business_data.get('has_schedule'):
            gaps.append({
                'type': 'content',
                'severity': 'low',
                'title': 'Missing class schedule',
                'description': 'No class schedule or timetable found',
            })

        # Check for local intent content
        city = business_data.get('city', '')
        if city and not business_data.get('has_local_content'):
            gaps.append({
                'type': 'local_seo',
                'severity': 'high',
                'title': 'Missing local intent content',
                'description': f'No "best gym in {city}" style content found',
            })

        return gaps

    def get_strengths(self, business_data: dict) -> list:
        """Identify fitness-specific strengths."""
        strengths = []

        # Strong review base
        review_count = business_data.get('review_count', 0)
        rating = business_data.get('rating', 0)

        if review_count >= 100 and rating >= 4.0:
            strengths.append({
                'type': 'social_proof',
                'title': 'Strong review base',
                'description': f'{rating} rating with {review_count} reviews',
            })

        # Premium facilities
        services = business_data.get('services', [])
        premium_services = ['swimming pool', 'sauna', 'spa', 'physiotherapy', 'steam']
        has_premium = [s for s in premium_services if any(s in str(srv).lower() for srv in services)]

        if len(has_premium) >= 2:
            strengths.append({
                'type': 'facility_depth',
                'title': 'Premium facility depth',
                'description': f'Offers: {", ".join(has_premium)}',
            })

        # Active social presence
        instagram_followers = business_data.get('instagram_followers', 0)
        facebook_followers = business_data.get('facebook_followers', 0)

        if instagram_followers >= 10000 or facebook_followers >= 10000:
            strengths.append({
                'type': 'social_proof',
                'title': 'Active social presence',
                'description': f'Instagram: {instagram_followers:,}+, Facebook: {facebook_followers:,}+',
            })

        # Central location
        if business_data.get('is_central_location'):
            strengths.append({
                'type': 'location',
                'title': 'Central location',
                'description': business_data.get('location_description', 'Convenient central location'),
            })

        return strengths
