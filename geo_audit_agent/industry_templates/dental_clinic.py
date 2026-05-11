"""Dental clinic industry template for GEO audit recommendations."""

class DentalClinicTemplate:
    """Industry-specific template for dental clinics and orthodontists."""

    def __init__(self):
        self.category_triggers = [
            'dental clinic', 'dentist', 'dental care', 'orthodontist', 'braces',
            'dental implants', 'cosmetic dentistry', 'emergency dentist',
            'teeth whitening', 'root canal', 'pediatric dentist'
        ]

        self.recommendation_signals = [
            'google_rating',
            'review_count',
            'dentist_credentials',
            'years_of_experience',
            'specializations',
            'services_offered',
            'emergency_availability',
            'hygiene_cleanliness',
            'painless_treatment_mentions',
            'before_after_proof',
            'insurance_payment_options',
            'location_convenience',
            'appointment_booking_clarity',
            'website_service_pages',
            'faq_content',
            'patient_testimonials',
            'schema_markup',
        ]

        self.schema_recommendations = [
            'Dentist',
            'MedicalClinic',
            'LocalBusiness',
            'Service',
            'Review',
            'AggregateRating',
            'FAQPage',
        ]

        self.review_keywords = [
            'painless',
            'hygienic',
            'clean clinic',
            'professional doctor',
            'friendly staff',
            'braces',
            'implants',
            'whitening',
            'root canal',
            'emergency',
            'appointment',
            'affordable',
            'insurance',
            'children',
            'patient care',
        ]

        self.remediation_playbook = {
            'schema': {
                'priority': 'high',
                'actions': [
                    'Add Dentist schema',
                    'Add MedicalClinic schema',
                    'Add LocalBusiness schema with specialized medical fields',
                ],
            },
            'content': {
                'priority': 'high',
                'actions': [
                    'Add treatment pages for braces',
                    'Add treatment pages for implants',
                    'Add treatment pages for whitening',
                    'Add treatment pages for root canal',
                    'Add treatment pages for emergency dentistry',
                    'Add dentist bio/credential pages',
                    'Add hygiene/safety section',
                    'Add insurance/payment info',
                    'Add emergency appointment info',
                    'Add treatment FAQs',
                    'Add before/after cases where compliant',
                ],
            },
            'reviews': {
                'priority': 'medium',
                'actions': [
                    'Collect patient reviews mentioning painless treatment',
                    'Collect patient reviews mentioning hygiene',
                    'Collect patient reviews mentioning professionalism',
                    'Collect patient reviews mentioning results',
                    'Add patient testimonials/reviews to service pages',
                ],
            },
            'local_seo': {
                'priority': 'high',
                'actions': [
                    'Improve Google Business Profile with clinic photos',
                    'Update service list on Google Business Profile',
                    'Create "Best dental clinic in [city]" content',
                    'Create local comparison content',
                ],
            },
        }

    def get_gaps(self, business_data: dict) -> list:
        """Generate dental-specific gaps based on business data."""
        gaps = []

        # Check for schema
        if not business_data.get('has_schema'):
            gaps.append({
                'type': 'schema',
                'severity': 'high',
                'title': 'Missing structured data',
                'description': 'No Dentist or MedicalClinic schema detected',
            })

        # Check for service pages
        services = business_data.get('services', [])
        expected_treatments = ['braces', 'implants', 'whitening', 'root canal', 'emergency dentistry']
        missing_treatments = [t for t in expected_treatments if not any(t in str(srv).lower() for srv in services)]

        if missing_treatments:
            gaps.append({
                'type': 'content',
                'severity': 'medium',
                'title': 'Missing treatment-specific pages',
                'description': f'No dedicated pages for: {", ".join(missing_treatments)}',
            })

        # Check for credentials
        if not business_data.get('has_credentials'):
            gaps.append({
                'type': 'content',
                'severity': 'medium',
                'title': 'Missing dentist credentials',
                'description': 'No dentist bio or credential pages found',
            })

        # Check for emergency info
        if not business_data.get('has_emergency_info'):
            gaps.append({
                'type': 'content',
                'severity': 'high',
                'title': 'Missing emergency availability',
                'description': 'No information about emergency dentistry or availability',
            })

        # Check for insurance/payment
        if not business_data.get('has_insurance_info'):
            gaps.append({
                'type': 'content',
                'severity': 'medium',
                'title': 'Missing insurance/payment info',
                'description': 'No insurance or payment option details found',
            })

        # Check for hygiene/safety
        if not business_data.get('has_hygiene_info'):
            gaps.append({
                'type': 'content',
                'severity': 'medium',
                'title': 'Missing hygiene/safety information',
                'description': 'No information about clinic hygiene or safety protocols',
            })

        # Check for FAQ
        if not business_data.get('has_faq'):
            gaps.append({
                'type': 'content',
                'severity': 'low',
                'title': 'Missing FAQ content',
                'description': 'No treatment FAQs found on the website',
            })

        # Check for local comparison
        city = business_data.get('city', '')
        if city and not business_data.get('has_local_comparison'):
            gaps.append({
                'type': 'local_seo',
                'severity': 'high',
                'title': 'Missing local comparison content',
                'description': f'No "best dental clinic in {city}" style content found',
            })

        return gaps

    def get_strengths(self, business_data: dict) -> list:
        """Identify dental-specific strengths."""
        strengths = []

        # Strong review base
        review_count = business_data.get('review_count', 0)
        rating = business_data.get('rating', 0)

        if review_count >= 50 and rating >= 4.5:
            strengths.append({
                'type': 'social_proof',
                'title': 'Strong review base',
                'description': f'{rating} rating with {review_count} reviews',
            })

        # Specialized services
        services = business_data.get('services', [])
        specialized_services = ['braces', 'implants', 'whitening', 'root canal', 'cosmetic dentistry']
        has_specialized = [s for s in specialized_services if any(s in str(srv).lower() for srv in services)]

        if len(has_specialized) >= 3:
            strengths.append({
                'type': 'service_depth',
                'title': 'Specialized treatment depth',
                'description': f'Offers: {", ".join(has_specialized)}',
            })

        # Dentist credentials
        if business_data.get('has_credentials'):
            strengths.append({
                'type': 'content',
                'title': 'Documented dentist credentials',
                'description': 'Clear bio and credential pages for the dental team',
            })

        # Emergency availability
        if business_data.get('has_emergency_info'):
            strengths.append({
                'type': 'service',
                'title': 'Emergency availability',
                'description': 'Provides emergency dental services and clear contact information',
            })

        # Hygiene mentions in reviews
        hygiene_mentions = business_data.get('hygiene_review_mentions', 0)
        if hygiene_mentions >= 10:
            strengths.append({
                'type': 'social_proof',
                'title': 'Hygiene/Cleanliness reputation',
                'description': f'{hygiene_mentions} patients mentioned clinic hygiene in reviews',
            })

        # Central location
        if business_data.get('is_central_location'):
            strengths.append({
                'type': 'location',
                'title': 'Central location',
                'description': business_data.get('location_description', 'Convenient central location'),
            })

        return strengths
