"""
Expanded Ad Dataset Generator — v2 (325+ unique ads)
=====================================================

Adds 210 new ads to the existing 125, covering:
  - 12 industries: SaaS, e-commerce, education, health, finance, travel,
    food, real estate, automotive, beauty, gaming, non-profit
  - 8 writing styles: urgency, social proof, question hook, pain point,
    benefit-led, data-driven, aspirational, humorous
  - CTR tiers specifically designed to fill gaps in v1:
    4-5%  (extreme flash + scarcity)
    3-4%  (strong flash + urgency)
    2.5-3% (solid offer + limited time)
    1.5-2.5% (clear value, some urgency)
    1-1.5% (educational / feature-focused)
    0.5-1% (professional / service)
    0.1-0.5% (brand / aspirational / generic)

CTR assignments follow WordStream / Databox / Meta Ads benchmarks
  by vertical and persuasion pattern. All values are synthetic estimates.

Run:
    python scripts/generate_v2_dataset.py
"""

import os
import csv
import random
import numpy as np
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# NEW ADS (210 entries)
# Format: (ad_text, base_ctr)
# ─────────────────────────────────────────────────────────────────────────────

NEW_ADS = [

    # =========================================================================
    # TIER 1A — Extreme flash + scarcity (CTR 4.0–5.0%)
    # Target gap: currently 0 ads at this level
    # =========================================================================
    ("⚡ 90% OFF TODAY ONLY. Everything must go. Shop now — while stocks last!", 0.047),
    ("INSANE DEAL: Buy 2 Get 3 FREE on ALL orders. 4 hours only. Go!", 0.045),
    ("$1 FLASH SALE — First 500 orders ship today. Grab yours NOW.", 0.048),
    ("Biggest sale of the year: 85% off sitewide. No code needed. Ends midnight!", 0.044),
    ("LAST HOUR: 80% off + free next-day delivery. Don't miss this!", 0.046),
    ("Today only: spend $30 get $60 FREE. Auto-applied at checkout.", 0.043),
    ("SHOCK DEAL: Premium headphones $19 (was $199). Only 38 left!", 0.049),
    ("Black Friday prices in July — 75% off everything. 6 hours left.", 0.042),

    # =========================================================================
    # TIER 1B — Strong flash + urgency (CTR 3.0–4.0%)
    # =========================================================================

    # SaaS
    ("DEAL: Get 6 months of our Pro plan for the price of 1. Today only!", 0.038),
    ("Limited: 70% off annual plan + onboarding call. 12 spots left.", 0.036),

    # E-commerce fashion
    ("Summer blowout: all dresses under $15. Ships free. Ends Sunday!", 0.035),
    ("Clearance sale: designer bags from $29. Limited sizes. Shop fast!", 0.034),
    ("Buy any 3 items, get the cheapest FREE. Today only + free shipping.", 0.033),
    ("Last chance! 60% off all outerwear. Winter is coming — be ready.", 0.031),

    # E-commerce electronics
    ("Flash deal: MacBook accessories 65% off. Add to cart before they're gone!", 0.037),
    ("PS5 bundle: controller + 2 games for $89. Only 20 bundles available.", 0.036),
    ("AirPods Pro — $79 today only (usually $249). Verified stock. Grab now!", 0.039),

    # E-commerce home
    ("Robot vacuum sale: $99 today only (was $399). Limited stock!", 0.034),
    ("Mattress flash sale: $199 queen (reg. $799). Free same-day delivery!", 0.032),

    # Food / delivery
    ("BOGO FREE pizza today! No code. First 1,000 orders only. Order now!", 0.038),
    ("Free delivery + $10 off your next 3 orders. Offer ends in 2 hours.", 0.034),

    # Fitness
    ("Gym membership for $1 — seriously. First month $1, cancel anytime!", 0.033),
    ("Protein powder: buy 2 tubs, get 1 FREE + shaker bottle. Today only!", 0.031),

    # Travel
    ("✈ Flight sale: NYC → London from $199. Book by midnight. 40 seats left!", 0.036),
    ("Hotel deal: 5-star resort from $59/night. Flash sale ends in 3 hours.", 0.033),

    # =========================================================================
    # TIER 2A — Strong value + urgency (CTR 2.5–3.0%)
    # Filling the 2.5-3% gap (only 6 ads existed)
    # =========================================================================

    # E-commerce
    ("Summer sale: 50% off all swimwear + free shipping over $40. Ends Friday!", 0.028),
    ("New arrivals 30% off this weekend only. Free returns. Shop the look.", 0.026),
    ("Back-to-school savings: 40% off backpacks, stationery, and more!", 0.027),
    ("Flash deal: $50 off any order over $150. Use code SAVE50. Today only!", 0.029),
    ("Sneaker drop: limited colourways — 40% off retail. Ships tomorrow.", 0.027),

    # SaaS / software
    ("Start free for 30 days. No credit card required. Cancel anytime.", 0.025),
    ("Switch from [Competitor]. We'll migrate your data free. 50% off Year 1.", 0.026),
    ("New: AI-powered analytics. Try free — see your data like never before.", 0.025),
    ("Cut your team's reporting time by 80%. Start your free trial today!", 0.028),
    ("2,000+ integrations. Setup in 5 minutes. Free forever plan available.", 0.026),

    # Health & wellness
    ("Lose 10 lbs in 30 days — guaranteed or your money back. Start today!", 0.029),
    ("Doctor-formulated supplements. 3rd-party tested. Buy 2, get 1 free.", 0.027),
    ("Finally: a meal plan that actually works. Free first week. No strings.", 0.026),
    ("Therapy from $40/session. Match with a licensed therapist in 24 hours.", 0.028),

    # Education
    ("Harvard professors. MIT curriculum. Online. $29/month. Start today.", 0.027),
    ("Get Google-certified in data analytics — in 6 months. Enroll now!", 0.025),
    ("Become a web developer in 3 months. Job guarantee or full refund.", 0.029),

    # Finance
    ("High-yield savings: 5.2% APY. No fees. Open in 3 minutes!", 0.028),
    ("Get your credit score to 750+. Free personalised action plan inside.", 0.026),
    ("Earn 5% cashback on everything. $200 welcome bonus. Apply now!", 0.027),
    ("Invest in the S&P 500 with no fees. Start with $1 today.", 0.025),

    # Travel
    ("All-inclusive Caribbean: 7 nights from $599/person. Limited rooms!", 0.028),
    ("Weekend getaway: 2 nights, spa & breakfast from $149. Book today.", 0.026),

    # Automotive
    ("0% APR for 60 months. Drive home today. Limited inventory.", 0.027),
    ("Car insurance from $29/month. Compare 50+ providers in 2 minutes.", 0.025),

    # =========================================================================
    # TIER 2B — Good value, moderate urgency (CTR 1.5–2.5%)
    # =========================================================================

    # E-commerce
    ("Free shipping on orders over $35. 30-day free returns. Shop now.", 0.019),
    ("Handmade jewellery starting at $12. Gift-wrapped. Free engraving.", 0.016),
    ("Sustainable fashion: organic cotton basics from $15. Plant 1 tree per order.", 0.017),
    ("Customise your own sneakers. Ships in 2 weeks. 100s of combos.", 0.018),
    ("Curated gift boxes for every budget. Same-day delivery available.", 0.021),
    ("New season arrivals: 20% off your first order with code WELCOME20.", 0.022),
    ("Furniture that arrives in a box and assembles in minutes. From $89.", 0.018),

    # SaaS / B2B
    ("Automate your invoicing. Save 5 hours/week. Start free for 14 days.", 0.020),
    ("Your CRM shouldn't cost more than your product. Free up to 5 users.", 0.019),
    ("Project management, simplified. Trusted by 150,000 teams worldwide.", 0.017),
    ("Never miss a follow-up again. AI reminders built in. Free trial.", 0.021),
    ("Close more deals with AI-powered sales coaching. Free 21-day trial.", 0.022),
    ("HR software that pays for itself in month 1. Book a free demo today.", 0.018),
    ("Hiring? Post a job free. 10 million+ candidates ready to apply.", 0.017),

    # Health & fitness
    ("Running plan built around YOUR schedule. First month on us.", 0.019),
    ("Sleep tracker + smart alarm. Wake up refreshed every morning. $49.", 0.018),
    ("Online yoga classes: 500+ sessions, 7 instructors. $12/month.", 0.021),
    ("Personalized nutrition plan. DNA-based. 90-day money-back guarantee.", 0.020),
    ("Mental health app: CBT exercises + mood tracking. Free for 7 days.", 0.019),
    ("Home gym starter pack: $149 (dumbells, mat, resistance bands). Ships free.", 0.022),

    # Finance
    ("Fee-free current account. Apply in 5 minutes. No branch needed.", 0.018),
    ("Automatic savings: round up your purchases and save without thinking.", 0.021),
    ("Budget tracker that actually motivates you. Join 800,000+ users.", 0.019),
    ("Tax filing made easy. Guaranteed maximum refund or it's free.", 0.023),
    ("Freelancer? Invoice, track expenses, pay taxes — in one app. Free.", 0.020),

    # Education
    ("Short courses from 50+ universities. Earn a certificate in 6 weeks.", 0.018),
    ("Speak a new language in 30 minutes a day. Proven by 25M+ learners.", 0.021),
    ("IELTS prep: average score increase of 1.5 bands. Money-back if not.", 0.019),
    ("Kids' maths tutoring: 30-minute weekly sessions from $19. First free.", 0.022),
    ("Coding for kids age 8–16. Project-based. Small groups. Try free.", 0.020),
    ("Become an Excel power user in 4 hours. 47,000 students enrolled.", 0.018),

    # Travel
    ("Travel insurance from £1.30/day. Covers cancellations, medical, theft.", 0.017),
    ("Airbnb alternative: private villas at hotel prices. No service fee.", 0.019),
    ("City breaks from £99pp. Flights + hotel. Flexible cancellation.", 0.021),
    ("Hidden gem destinations. Expert curation. 12,000+ happy travellers.", 0.018),

    # Food & delivery
    ("Cook restaurant-quality meals at home. Ingredients delivered weekly.", 0.020),
    ("Organic veg box: seasonal, local, plastic-free. From £15/week.", 0.018),
    ("Coffee subscription: freshly roasted, delivered to your door. From $12.", 0.021),
    ("Vegan meal prep for the whole week. Ready in 15 min. From $8/meal.", 0.019),

    # Beauty
    ("Dermatologist-tested skincare. Zero parabens, zero BS. Try for $5.", 0.022),
    ("Custom foundation: matched to your exact skin tone in 30 seconds.", 0.020),
    ("Cruelty-free makeup from $4. Join 2M+ ethical beauty enthusiasts.", 0.018),

    # Real estate / renting
    ("List your property free for 30 days. 2.3M buyers waiting. Sign up.", 0.017),
    ("Find your flat in 48 hours. AI matching to your exact requirements.", 0.019),

    # Automotive
    ("Used cars with 12-month warranty. Fully inspected. Prices from £3,999.", 0.018),
    ("Electric car: 0–60 in 3.9s. £0 road tax. Test drive this weekend.", 0.021),

    # Non-profit / cause
    ("Your £2 gives a child clean water for life. Donate today.", 0.022),
    ("Adopt a dog remotely. $25/month funds food, vet care, and love.", 0.019),

    # =========================================================================
    # TIER 3 — Educational / feature-focused (CTR 1.0–1.5%)
    # Diverse industries
    # =========================================================================

    # SaaS
    ("How 500 companies cut costs 40% with smarter procurement. Read the guide.", 0.011),
    ("The complete guide to remote team management. Free download.", 0.012),
    ("Webinar: How to 10x your email open rate. Free. Thursday 2pm EST.", 0.013),
    ("Case study: how TechCorp reduced churn by 60% in 90 days.", 0.011),
    ("Security compliance made easy. SOC2 in 3 weeks, not 3 months.", 0.012),
    ("AI writing assistant: from brief to blog in 90 seconds. Try now.", 0.014),
    ("API-first infrastructure. Built for scale. Free up to 1M requests/month.", 0.012),

    # Education
    ("Introduction to machine learning: free 4-week course starts Monday.", 0.013),
    ("Unlock a career in UX design. No prior experience needed. Start free.", 0.011),
    ("Online accounting certificate. Recognised by ACCA. Self-paced.", 0.012),
    ("How to start investing. Free masterclass for complete beginners.", 0.013),
    ("Public speaking course: go from nervous to confident in 8 sessions.", 0.011),
    ("Creative writing workshop with published authors. Limited places.", 0.010),

    # Health
    ("Understanding your gut microbiome. Free educational guide inside.", 0.011),
    ("At-home blood test: 70+ health markers analysed. Results in 48 hrs.", 0.013),
    ("Online physio consultation. Skip the waiting room. From £30.", 0.012),
    ("CBT-based app for anxiety. 10 minutes a day. Evidence-based.", 0.013),
    ("Dental care without the dentist anxiety. Meet our calming team.", 0.011),

    # Finance
    ("Your complete guide to buying your first home. Download free.", 0.012),
    ("How to build a 6-month emergency fund in 12 months. Free PDF.", 0.011),
    ("Learn technical stock analysis in 3 hours. Beginner-friendly.", 0.013),
    ("Compare business bank accounts. Unbiased. Free. Takes 2 minutes.", 0.012),
    ("Retirement planning calculator. See if you're on track — free.", 0.011),

    # Travel
    ("Travel smarter: 9 hacks to halve your flight costs. Free guide.", 0.012),
    ("How to travel Southeast Asia for $30/day. Free 40-page itinerary.", 0.013),
    ("Slow travel: work remotely and explore the world. Guide + toolkit.", 0.011),

    # Food
    ("5-ingredient weeknight dinners: free recipe e-book. Download now.", 0.012),
    ("Sourdough starter guide: from flour to loaf in 5 days. Free PDF.", 0.011),
    ("The science of coffee. Free deep-dive guide for true enthusiasts.", 0.012),

    # Real estate
    ("First-time buyer guide: the 12 things no one tells you. Free.", 0.012),
    ("Renting vs. buying in 2025: independent analysis. Read free.", 0.011),

    # Beauty
    ("Your 3-step AM skincare routine for sensitive skin. Free guide.", 0.012),
    ("Hair care routine for colour-treated hair. Expert tips. Free.", 0.011),

    # Gaming
    ("Level up faster: 7 pro tips for [Game]. Free strategy guide.", 0.013),
    ("Cloud gaming: stream AAA titles on any device. Free 14-day trial.", 0.012),

    # =========================================================================
    # TIER 4 — Product / service with moderate appeal (CTR 0.5–1.0%)
    # =========================================================================

    # SaaS / B2B
    ("Enterprise security monitoring. 24/7 alerts. GDPR compliant.", 0.008),
    ("E-signature software. Legally binding in 180 countries. Free plan.", 0.009),
    ("Video conferencing with AI transcription. Secure. Free for teams.", 0.008),
    ("Customer feedback platform. Close the loop automatically. Demo today.", 0.007),
    ("Employee engagement surveys. Anonymous. Actionable insights. Try free.", 0.008),

    # Health
    ("Private GP appointments from £45. Same-day availability. Book now.", 0.009),
    ("Online hearing test. Clinically validated. Free. Takes 5 minutes.", 0.007),
    ("Posture corrector: clinically tested, doctor recommended. $39.", 0.008),
    ("Prescription skincare delivered. Dermatologist reviewed. From $19/month.", 0.009),

    # Finance
    ("Business insurance from £10/month. Instant quotes. Buy online.", 0.007),
    ("International money transfers: 8x cheaper than the bank. Send now.", 0.009),
    ("Expense management software. Automates 90% of your finance admin.", 0.008),
    ("Equity release: access your home's value without moving. Free advice.", 0.006),

    # Real estate
    ("Commercial real estate analytics: rental yield, ROI, vacancy rates.", 0.006),
    ("Property management software: tenants, maintenance, finance. All-in-one.", 0.007),
    ("Mortgage broker: whole-of-market access. No broker fee. Free advice.", 0.008),
    ("Holiday let management. We handle everything. From 15% commission.", 0.007),

    # Automotive
    ("Fleet management: GPS, fuel tracking, maintenance alerts. From $8/vehicle.", 0.006),
    ("Car finance with no credit check required. Instant decision. Apply now.", 0.008),
    ("Vehicle wrap advertising: earn money from your car. Apply to drive.", 0.007),

    # Food / hospitality
    ("Restaurant POS system: orders, payments, inventory. From $49/month.", 0.007),
    ("Catering for corporate events: 50–500 guests. Get a free quote.", 0.006),
    ("Commercial coffee machine rental: from £1/day. Includes maintenance.", 0.007),

    # Gaming / entertainment
    ("Game server hosting: 1-click launch, 99.9% uptime. From $5/month.", 0.008),
    ("Streaming setup consultation. Lighting, audio, scene build. 1-hour.", 0.007),

    # =========================================================================
    # TIER 5 — Professional / brand awareness (CTR 0.2–0.5%)
    # =========================================================================

    # B2B services
    ("Your supply chain, optimised. Enterprise logistics consulting.", 0.004),
    ("Bespoke software development. Agile. Fixed-price delivery. Let's talk.", 0.004),
    ("ISO 27001 certification support. We handle the paperwork. You ship.", 0.003),
    ("Business continuity planning: protect what you've built. Free assessment.", 0.004),
    ("Executive coaching for C-suite leaders. 100% confidential. Apply.", 0.003),

    # Luxury / aspirational
    ("Private members' club. Where London's business community connects.", 0.003),
    ("Bespoke jewellery: designed around your story. By appointment only.", 0.003),
    ("Michelin-starred dining. Seasonal tasting menu. Reserve your table.", 0.004),
    ("Architectural design: homes that are truly one of a kind. Enquire.", 0.003),
    ("Classic car restoration. 40 years of expertise. Commission yours.", 0.002),
    ("Charter a private yacht in the Maldives. Experiences from $8,000.", 0.002),
    ("Investment-grade whisky. Starting at £1,000. Free portfolio guide.", 0.003),
    ("Contemporary art acquisition advisory. Curated for serious collectors.", 0.002),

    # Brand / awareness
    ("We're B Corp certified. Because business can be a force for good.", 0.003),
    ("Net zero by 2030. Our roadmap. See how we're getting there.", 0.002),
    ("People-first culture. 96% employee satisfaction. We're hiring.", 0.003),
    ("20 years of innovation in clean energy. Our story continues.", 0.002),
    ("We don't just build software. We build what's next.", 0.002),

    # =========================================================================
    # TIER 6 — Generic / vague / low signal (CTR 0.1–0.2%)
    # =========================================================================

    ("Solutions for modern challenges. Find out what we do.", 0.001),
    ("Connecting people with possibilities. Learn more.", 0.002),
    ("Where great ideas become great products. Discover more.", 0.001),
    ("Your success is our mission.", 0.001),
    ("Innovating the future of mobility.", 0.002),
    ("Built for the way you work today.", 0.001),
    ("A new standard in customer experience.", 0.002),
    ("Transforming data into decisions.", 0.001),
    ("The platform built for tomorrow's teams.", 0.002),
    ("Excellence, delivered.", 0.001),

    # =========================================================================
    # BONUS — Diverse writing styles (mixed tiers)
    # =========================================================================

    # Question hooks
    ("Tired of overpaying for software? Switch to us — same features, 60% less.", 0.024),
    ("What if you could automate your taxes in 10 minutes? Now you can.", 0.021),
    ("Still using spreadsheets in 2025? There's a better way. Free trial.", 0.018),
    ("Can't sleep? Our clinically-backed programme fixes insomnia in 6 weeks.", 0.022),
    ("What would you do with an extra $500/month? We'll show you how.", 0.025),
    ("Is your business protected against cyber attacks? Free audit inside.", 0.015),
    ("Could your marketing be converting 3x more? Our audit shows you how.", 0.016),
    ("Why are your competitors outranking you? Free SEO analysis.", 0.014),

    # Pain-point led
    ("Stop losing money to hidden bank fees. Switch in 3 minutes.", 0.023),
    ("Never scramble for a parking spot again. Reserve ahead. From $3.", 0.019),
    ("Sick of the commute? Remote jobs at top companies. Browse 12,000+.", 0.021),
    ("Your old mattress is wrecking your sleep. Ours won't. Try 100 nights.", 0.018),
    ("That lower-back pain won't fix itself. Online physio, from £25.", 0.019),
    ("Drowning in admin? Hire a virtual assistant for $8/hour.", 0.017),
    ("No one should struggle alone with their finances. Free advice here.", 0.016),

    # Social proof
    ("Rated #1 by Forbes. Loved by 4.2M users. Try it free.", 0.022),
    ("98% of our students would recommend us. Join 120,000+ learners.", 0.020),
    ("5-star rated by 28,000+ customers on Trustpilot. Shop now.", 0.021),
    ("Used by Nike, Apple, and NASA. Now available for your team.", 0.019),
    ("'Best investment I made this year' — Forbes, Inc, TechCrunch.", 0.020),
    ("94% of users see results in 30 days. Join 500,000+ success stories.", 0.022),
    ("The app that 3M people use to manage their money. Now free to join.", 0.021),

    # Emotional / storytelling
    ("From struggling freelancer to $8k/month. Here's exactly what I did.", 0.023),
    ("She lost 32kg without giving up carbs. Her plan, inside.", 0.024),
    ("This single tool saved our agency 20 hours a week. See how.", 0.021),
    ("After 10 years of anxiety, this app finally helped. Read her story.", 0.019),
    ("I quit my 9-5 at 31. Here's the income stream that made it possible.", 0.025),

    # Data-driven
    ("87% of B2B leads are wasted. Fix that with our lead scoring tool.", 0.018),
    ("Companies using our platform see 43% higher revenue in year 1.", 0.020),
    ("Reduce customer churn by 35% in 60 days. Proven. See the data.", 0.019),
    ("4.7M hours of productivity saved by our users in 2024 alone.", 0.017),
    ("Independent study: our users save $3,200/year on average. Read it.", 0.018),
    ("Our algorithm beats inflation 94% of the time. 10-year track record.", 0.017),

    # Humorous / witty
    ("Netflix for learning. Except useful. Try it free.", 0.020),
    ("Adulting is hard. We make the money part easier. Free app.", 0.019),
    ("Your accountant charges £250/hour. Ours is $20/month. Same output.", 0.021),
    ("Faster than your current tools. Cheaper too. Sorry, not sorry.", 0.018),
    ("We didn't disrupt the industry. We just made it bearable.", 0.015),
    ("Finally, HR software that HR actually likes. Wild, right?", 0.017),
    ("Your inbox called. It wants fewer meetings. We can help.", 0.016),

    # Seasonal / event-based
    ("Back to school: 35% off laptops, tablets, and accessories. Shop now.", 0.026),
    ("Father's Day gift ideas under $50. Free next-day delivery this week.", 0.023),
    ("Valentine's Day sale: free gift wrapping + 20% off jewellery. Today!", 0.028),
    ("New Year offer: 3 months free on any annual plan. Start fresh!", 0.025),
    ("Black Friday early access: sign up now for 48-hour exclusive deals.", 0.030),
    ("Summer sale starts NOW. Up to 50% off travel, fashion, and home.", 0.027),
    ("End-of-financial-year deals: save on software before the deadline!", 0.024),
]

# ─────────────────────────────────────────────────────────────────────────────
# LOAD EXISTING ADS
# ─────────────────────────────────────────────────────────────────────────────

def load_existing_ads():
    """Load the original 125 ads from generate_expanded_dataset.py."""
    from scripts.generate_expanded_dataset import ADS as EXISTING_ADS
    return EXISTING_ADS


# ─────────────────────────────────────────────────────────────────────────────
# GENERATE COMBINED DATASET
# ─────────────────────────────────────────────────────────────────────────────

def generate_v2_dataset(seed=42):
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    from scripts.generate_expanded_dataset import ADS as EXISTING_ADS

    # Combine: 125 existing + 210 new = 335 unique ads
    ALL_ADS = EXISTING_ADS + NEW_ADS

    print(f"Total unique ads: {len(ALL_ADS)}")

    # Deduplicate on exact text match (safety check)
    seen = set()
    unique_ads = []
    for text, ctr in ALL_ADS:
        if text not in seen:
            seen.add(text)
            unique_ads.append((text, ctr))
    print(f"After dedup: {len(unique_ads)} unique ads")

    rng = np.random.RandomState(seed)

    # Generate rows with noise (3 reps per ad)
    rows = []
    for text, base_ctr in unique_ads:
        for _ in range(3):
            noise = rng.normal(0, base_ctr * 0.08)
            noisy_ctr = max(0.0005, base_ctr + noise)
            rows.append({'ad_text': text, 'actual_ctr': round(noisy_ctr, 6)})

    # Split: 70% train, 15% val, 15% holdout (by unique ad, no leakage)
    random.seed(seed)
    np.random.seed(seed)
    n = len(unique_ads)
    indices = list(range(n))
    np.random.shuffle(indices)

    n_train = int(n * 0.70)
    n_val = int(n * 0.15)
    train_idx = set(indices[:n_train])
    val_idx = set(indices[n_train:n_train + n_val])
    holdout_idx = set(indices[n_train + n_val:])

    train_rows, val_rows, holdout_rows = [], [], []
    for i, (text, _) in enumerate(unique_ads):
        ad_rows = [r for r in rows if r['ad_text'] == text]
        if i in train_idx:
            train_rows.extend(ad_rows)
        elif i in val_idx:
            val_rows.extend(ad_rows)
        else:
            holdout_rows.extend(ad_rows)

    os.makedirs('data', exist_ok=True)
    for name, data in [('train_v2', train_rows), ('val_v2', val_rows), ('holdout_v2', holdout_rows)]:
        df = pd.DataFrame(data)
        df.to_csv(f'data/{name}.csv', index=False)
        print(f'{name}.csv: {len(df)} rows, {df["ad_text"].nunique()} unique texts')

    all_df = pd.DataFrame(rows)
    all_df.to_csv('data/expanded_ads_v2.csv', index=False)
    print(f'\nexpanded_ads_v2.csv: {len(all_df)} rows, {all_df["ad_text"].nunique()} unique texts')
    print(f'CTR range: [{all_df.actual_ctr.min():.4f}, {all_df.actual_ctr.max():.4f}]')

    # CTR tier distribution
    bins = [0, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05, 1.0]
    labels = ['<0.5%', '0.5-1%', '1-1.5%', '1.5-2%', '2-2.5%', '2.5-3%', '3-4%', '4-5%', '>5%']
    dedup = all_df.drop_duplicates('ad_text').copy()
    dedup['tier'] = pd.cut(dedup['actual_ctr'], bins=bins, labels=labels)
    print('\nCTR tier distribution:')
    print(dedup['tier'].value_counts().sort_index())

    return train_rows, val_rows, holdout_rows


if __name__ == '__main__':
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    generate_v2_dataset()
