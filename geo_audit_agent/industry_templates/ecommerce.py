"""E-commerce industry template for GEO audit recommendations."""

class EcommerceTemplate:
    """Industry-specific template for e-commerce and online retail stores."""

    def __init__(self):
        self.category_triggers = [
            'ecommerce', 'e-commerce', 'online store', 'online shop', 'fashion store',
            'clothing store', 'shopify', 'retail', 'marketplace', 'skincare store',
            'electronics store', 'furniture store'
        ]

        self.recommendation_signals = [
            'product range',
            'product quality',
            'pricing clarity',
            'shipping speed',
            'return/exchange policy',
            'product reviews',
            'product-specific reviews',
            'product page quality',
            'product images/video',
            'size guide if fashion',
            'trust badges',
            'secure payments',
            'COD/payment options',
            'warranty/guarantee',
            'marketplace presence',
            'social proof',
            'category authority',
            'FAQ content',
            'comparison/listicle visibility',
        ]

        self.schema_recommendations = [
            'Organization',
            'OnlineStore',
            'Product',
            'Offer',
            'Review',
            'AggregateRating',
            'FAQPage',
            'BreadcrumbList',
        ]

        self.review_keywords = [
            'quality',
            'delivery',
            'packaging',
            'fit',
            'size',
            'original',
            'authentic',
            'customer service',
            'return',
            'exchange',
            'price',
            'value',
            'fast shipping',
        ]

        self.remediation_playbook = {
            'schema': {
                'priority': 'high',
                'actions': [
                    'Add Product, Offer, AggregateRating, Review schema',
                ],
            },
            'content': {
                'priority': 'high',
                'actions': [
                    'Add FAQ sections to product and category pages',
                    'Create high-intent category pages',
                    'Add shipping and return/exchange policy clearly on product pages',
                    'Add size guide and fit details',
                    'Improve product page images/videos',
                ],
            },
            'reviews': {
                'priority': 'medium',
                'actions': [
                    'Collect product-specific reviews mentioning quality, fit, delivery, packaging',
                ],
            },
            'local_seo': {
                'priority': 'high',
                'actions': [
                    'Create comparison content like "Best online fashion stores in [market]"',
                    'Add trust badges and secure payment indicators',
                    'Add marketplace/social proof',
                ],
            },
        }

    def get_gaps(self, business_data: dict) -> list:
        """Generate ecommerce-specific gaps based on business data."""
        gaps = []

        # Check for schema
        if not business_data.get('has_schema'):
            gaps.append({
                'type': 'schema',
                'severity': 'high',
                'title': 'Missing structured data',
                'description': 'No Product, Offer, or Review schema detected',
            })

        # Check for reviews/product reviews
        if not business_data.get('has_product_reviews'):
            gaps.append({
                'type': 'reviews',
                'severity': 'high',
                'title': 'Missing product-specific reviews',
                'description': 'No product-specific reviews detailing quality, fit, and delivery',
            })

        # Check for shipping info
        if not business_data.get('has_shipping_info'):
            gaps.append({
                'type': 'content',
                'severity': 'medium',
                'title': 'Missing shipping information',
                'description': 'Shipping and delivery information is not clearly visible on product pages',
            })

        # Check for size guide
        # Assuming fashion if category is not provided to be safe based on instructions
        cat = business_data.get('category', '').lower()
        if not business_data.get('has_size_guide') and ('fashion' in cat or 'clothing' in cat or cat == ''):
            gaps.append({
                'type': 'content',
                'severity': 'medium',
                'title': 'Missing size guide',
                'description': 'No sizing or fit guidance available for apparel products',
            })

        # Check for FAQ
        if not business_data.get('has_faq'):
            gaps.append({
                'type': 'content',
                'severity': 'low',
                'title': 'Missing FAQ content',
                'description': 'No FAQ sections on product or category pages',
            })

        # Check for trust badges
        if not business_data.get('has_trust_badges'):
            gaps.append({
                'type': 'trust',
                'severity': 'medium',
                'title': 'Missing trust signals',
                'description': 'Missing trust badges and secure payment messaging',
            })

        # Check for comparison content
        if not business_data.get('has_comparison_content'):
            market = business_data.get('market', 'Pakistan')
            gaps.append({
                'type': 'content',
                'severity': 'high',
                'title': 'Missing comparison content',
                'description': f'No high-intent listicles or "Best online fashion stores in {market}" style content',
            })

        # Check for high intent category pages
        if not business_data.get('has_category_pages'):
            gaps.append({
                'type': 'content',
                'severity': 'high',
                'title': 'Missing category pages',
                'description': 'No high-intent category landing pages identified',
            })

        return gaps

    def get_strengths(self, business_data: dict) -> list:
        """Identify ecommerce-specific strengths."""
        strengths = []

        # Platform check
        platform = business_data.get('platform', '')
        if platform:
            strengths.append({
                'type': 'platform',
                'title': f'{platform.title()} storefront',
                'description': f'Built on robust {platform.title()} e-commerce infrastructure',
            })

        # Product catalog
        if business_data.get('has_product_catalog'):
            strengths.append({
                'type': 'catalog',
                'title': 'Clear product catalog',
                'description': 'Well-defined product categories and offerings',
            })

        # Return policy
        if business_data.get('has_return_policy'):
            strengths.append({
                'type': 'trust',
                'title': 'Clear return/exchange policy',
                'description': business_data.get('return_policy_description', 'Customer-friendly return policy available'),
            })

        # Payment options
        if business_data.get('has_payment_options'):
            strengths.append({
                'type': 'payments',
                'title': 'Multiple payment options',
                'description': business_data.get('payment_options_description', 'Secure payment methods offered'),
            })

        # Social presence
        instagram_followers = business_data.get('instagram_followers', 0)
        social_presence = business_data.get('has_social_presence')

        if instagram_followers >= 10000 or social_presence:
            desc = f'Active social presence with {instagram_followers:,}+ Instagram followers' if instagram_followers >= 10000 else 'Active Instagram/social presence'
            strengths.append({
                'type': 'social_proof',
                'title': 'Active social presence',
                'description': desc,
            })

        # Market focus
        market = business_data.get('market', '')
        if market:
            strengths.append({
                'type': 'market',
                'title': f'{market} market focus',
                'description': f'Clear targeting and visibility for the {market} market',
            })

        return strengths
