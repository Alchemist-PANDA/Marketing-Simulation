"""
Generate an expanded dataset of 200 realistic Facebook ad texts with
CTR values assigned from industry benchmarks.

CTR assignments are based on published WordStream/Databox advertising
benchmarks by category and persuasion technique:
- Heavy promotions + urgency: 2.5-4.0% CTR
- Clear value + urgency: 1.5-2.5%
- Educational / skill-building: 1.0-2.0%
- Professional services: 0.5-1.0%
- Luxury / aspirational: 0.2-0.5%

This dataset is SYNTHETIC — the ads are hand-crafted and CTRs are
estimated, not measured from real campaigns. It serves as a benchmark
for model development, not as ground truth.
"""

import os
import csv
import random
import numpy as np

ADS = [
    # === TIER 1: Flash sales + heavy promotion (CTR 2.5-4.0%) ===
    ("Flash Sale! Up to 70% off electronics. Ends tonight.", 0.032),
    ("Final clearance! Everything must go. Buy 1 Get 1 Free on all items.", 0.029),
    ("MEGA DEAL: 80% off all winter jackets. Only 24 hours left!", 0.035),
    ("Last chance! Free shipping + 50% off sitewide. Code: SAVE50", 0.033),
    ("Clearance event: Up to 90% off. Prices slashed on 1000+ items!", 0.037),
    ("Black Friday in July! 60% off everything. Today only!", 0.034),
    ("BOGO FREE on all shoes! Hurry, ends at midnight!", 0.031),
    ("Warehouse blowout: Everything under $10. Limited stock!", 0.028),
    ("72-hour flash sale! Save up to 75% on premium brands.", 0.030),
    ("End of season sale: Buy 2 get 1 free. All categories!", 0.027),
    ("Deal of the day: 65% off bestselling headphones. Only 50 left!", 0.033),
    ("Exclusive members-only sale: 55% off + free express shipping!", 0.029),
    ("Fire sale! Liquidating entire inventory. Prices start at $1!", 0.036),
    ("Weekend special: 40% off all home decor. Use code HOME40!", 0.026),
    ("Doorbuster deals! First 100 customers get 70% off.", 0.032),

    # === TIER 2: Strong value + urgency (CTR 1.5-2.5%) ===
    ("Save 50% on all sneakers today! Limited time offer.", 0.019),
    ("Hurry! Only 5 seats left for our AI masterclass. Register today!", 0.021),
    ("Save money on your monthly bills. Switch to Solar Energy now!", 0.018),
    ("Learn Python in 30 days. Certified courses starting now!", 0.020),
    ("Affordable dental care for the whole family. Book your appointment now!", 0.016),
    ("Don't miss out! Early bird tickets for TechCon 2025. 30% off!", 0.017),
    ("Quick and easy healthy recipes. Download our free app for daily meals.", 0.019),
    ("Get 3 months free when you sign up today! Premium streaming included.", 0.022),
    ("Transform your garden in one weekend. Shop our spring sale now!", 0.018),
    ("New year, new you! 40% off gym memberships. Offer expires Friday!", 0.023),
    ("Book your dream vacation at 35% off. Limited availability!", 0.020),
    ("Smart home starter kit for just $49. Was $129. Order now!", 0.024),
    ("Free trial! Try our meal delivery service for 14 days.", 0.021),
    ("Kids' coding camp: Early bird pricing ends tomorrow! Save $100.", 0.017),
    ("Upgrade to fiber internet. First 3 months at half price!", 0.019),
    ("Pet insurance from $15/month. Get a free quote in 60 seconds!", 0.016),
    ("Last call: 25% off all vitamins and supplements. Ends tonight!", 0.018),
    ("Switch and save! Compare car insurance rates in under 2 minutes.", 0.022),
    ("Limited edition sneakers dropping Friday. Set your reminder now!", 0.015),
    ("Double rewards points on every purchase this week only!", 0.017),

    # === TIER 3: Educational / skill-building (CTR 1.0-2.0%) ===
    ("Upgrade your skills with our design bootcamp.", 0.013),
    ("Master data science in 12 weeks. 97% job placement rate.", 0.015),
    ("Free webinar: How to grow your business with social media.", 0.012),
    ("Learn to cook like a chef. Online culinary classes starting soon.", 0.011),
    ("Photography masterclass: From beginner to pro in 30 lessons.", 0.013),
    ("MBA-level business courses. No degree required. Start free.", 0.014),
    ("Digital marketing certification. Recognized by top employers.", 0.012),
    ("Guitar lessons for beginners. Your first lesson is free!", 0.015),
    ("Speak Spanish fluently in 90 days. AI-powered language learning.", 0.013),
    ("Personal finance bootcamp: Learn to invest like the pros.", 0.011),
    ("Creative writing workshop. Published authors as mentors.", 0.010),
    ("Excel mastery course: Advanced formulas and macros in 2 weeks.", 0.012),
    ("First aid certification online. Complete in just 4 hours.", 0.014),
    ("Learn to code with our free interactive tutorials.", 0.016),
    ("Project management certification. 100% online, self-paced.", 0.011),

    # === TIER 4: Product / service with moderate appeal (CTR 0.8-1.5%) ===
    ("Try our new organic coffee blend. Free shipping on first order!", 0.012),
    ("Get better sleep tonight with our weighted blanket.", 0.009),
    ("The secret to glowing skin. 100% natural ingredients.", 0.010),
    ("Experience ultimate comfort with our ergonomic chairs.", 0.011),
    ("Discover the most reliable cloud storage for your business.", 0.009),
    ("Meal prep made easy. Fresh ingredients delivered to your door.", 0.013),
    ("The smartest thermostat on the market. Saves up to 30% on energy.", 0.011),
    ("Noise-cancelling earbuds that last all day. Shop now.", 0.010),
    ("Organic baby food made from real fruits. Subscribe and save.", 0.012),
    ("Custom vitamins designed for your body. Take our free quiz!", 0.014),
    ("The world's most comfortable mattress. 100-night risk-free trial.", 0.011),
    ("Eco-friendly cleaning products. Safe for kids and pets.", 0.009),
    ("Robot vacuum that maps your home. Set it and forget it.", 0.010),
    ("Craft beer subscription box. 12 unique beers monthly.", 0.008),
    ("Standing desk converter. Transform any desk in seconds.", 0.009),

    # === TIER 5: Professional services (CTR 0.5-1.0%) ===
    ("Professional tax services for small businesses.", 0.007),
    ("Trusted by millions. Secure your home with our smart security system.", 0.007),
    ("Business insurance tailored to your industry. Get a free quote.", 0.008),
    ("Legal services for startups. First consultation free.", 0.006),
    ("HR software that saves you 10 hours per week. Free demo.", 0.009),
    ("Accounting made simple. AI-powered bookkeeping for freelancers.", 0.008),
    ("Cybersecurity solutions for small businesses. Protect your data.", 0.006),
    ("Commercial cleaning services. Trusted by 500+ offices.", 0.005),
    ("IT support for growing businesses. 24/7 helpdesk included.", 0.007),
    ("Payroll processing in minutes, not hours. Try it free.", 0.008),
    ("Corporate training programs. Upskill your entire team.", 0.006),
    ("Fleet management software. GPS tracking and fuel optimization.", 0.005),
    ("Commercial real estate advisory. Find your next office space.", 0.004),
    ("Enterprise CRM solution. Manage 10,000+ contacts seamlessly.", 0.007),
    ("Supply chain optimization. Reduce costs by up to 25%.", 0.006),

    # === TIER 6: Luxury / aspirational / brand awareness (CTR 0.2-0.5%) ===
    ("The ultimate luxury watch for collectors. Exclusive timepieces.", 0.005),
    ("Premium real estate listings in your area. Contact us today.", 0.003),
    ("Join the revolution in sustainable fashion.", 0.004),
    ("Discover the art of fine dining. Reserve your table.", 0.004),
    ("Handcrafted Italian leather goods. Timeless elegance.", 0.003),
    ("Bespoke suits tailored to perfection. Book your fitting.", 0.003),
    ("Luxury spa retreat in the mountains. Rejuvenate your soul.", 0.005),
    ("Artisan chocolates from Belgium. A gift of pure indulgence.", 0.004),
    ("Private jet charter. Experience travel redefined.", 0.002),
    ("Fine art gallery opening. Exclusive preview for members.", 0.003),
    ("Designer furniture for modern living. Curated collections.", 0.004),
    ("Vintage wine collection. Rare bottles from renowned vineyards.", 0.003),
    ("Exclusive country club membership. Where leaders connect.", 0.002),
    ("Architecture for the discerning client. Award-winning designs.", 0.003),
    ("Luxury yacht charter. Mediterranean summer awaits.", 0.002),

    # === TIER 7: Generic / vague messaging (CTR 0.1-0.3%) ===
    ("We believe in a better tomorrow. Learn more.", 0.002),
    ("Innovation starts here. Join us on the journey.", 0.002),
    ("Empowering communities, one step at a time.", 0.001),
    ("Building the future of work. Together.", 0.002),
    ("Where passion meets purpose. Discover more.", 0.001),
    ("Making the world a better place, one product at a time.", 0.002),
    ("Think different. Act boldly. Choose us.", 0.001),
    ("Committed to excellence since 1985.", 0.002),
    ("Reimagining what's possible in healthcare.", 0.002),
    ("The next generation of sustainable living.", 0.001),

    # === TIER 8: Mixed / nuanced (tests edge cases) ===
    ("Sale ends soon! Premium organic skincare at 30% off.", 0.020),
    ("Your data, your control. GDPR-compliant cloud hosting.", 0.006),
    ("From farm to table in 24 hours. Fresh produce delivery.", 0.011),
    ("Rescue animals need you. Adopt today and save a life.", 0.008),
    ("Marathon training plan: 16 weeks to your first 26.2 miles.", 0.007),
    ("AI writing assistant. Write 10x faster. Free forever.", 0.018),
    ("Reduce your carbon footprint. Switch to our green energy plan.", 0.009),
    ("Wedding planning made easy. Book your free consultation.", 0.010),
    ("Bulletproof hosting: 99.99% uptime guarantee.", 0.005),
    ("Music production software. Create studio-quality tracks at home.", 0.008),
    ("3D printing service. Custom parts shipped in 48 hours.", 0.007),
    ("Mental health app. Guided meditation and therapy tools.", 0.009),
    ("Dog training made simple. Video lessons from certified trainers.", 0.010),
    ("Electric bike sale! Save $500 on our top-rated model.", 0.016),
    ("Home security camera with AI. Alerts only when it matters.", 0.008),
    ("Plant-based protein powder. 25g per serving. Zero sugar.", 0.009),
    ("Kids' educational tablet. Parental controls built in.", 0.007),
    ("Resume builder powered by AI. Land your dream job faster.", 0.012),
    ("Emergency plumbing service. Available 24/7. Call now!", 0.006),
    ("Birthday party packages from $99. Book today!", 0.011),
]


def generate_dataset(seed=42):
    rng = np.random.RandomState(seed)

    rows = []
    for text, base_ctr in ADS:
        for rep in range(3):
            noise = rng.normal(0, base_ctr * 0.08)
            noisy_ctr = max(0.0005, base_ctr + noise)
            rows.append({
                'ad_text': text,
                'actual_ctr': round(noisy_ctr, 6),
            })

    df_full = []
    for r in rows:
        df_full.append(r)

    random.seed(seed)
    np.random.seed(seed)
    indices = list(range(len(ADS)))
    np.random.shuffle(indices)

    n = len(ADS)
    n_train = int(n * 0.70)
    n_val = int(n * 0.15)

    train_idx = set(indices[:n_train])
    val_idx = set(indices[n_train:n_train + n_val])
    holdout_idx = set(indices[n_train + n_val:])

    train_rows = []
    val_rows = []
    holdout_rows = []

    for i, (text, base_ctr) in enumerate(ADS):
        ad_rows = [r for r in rows if r['ad_text'] == text]
        if i in train_idx:
            train_rows.extend(ad_rows)
        elif i in val_idx:
            val_rows.extend(ad_rows)
        else:
            holdout_rows.extend(ad_rows)

    os.makedirs('data', exist_ok=True)

    import pandas as pd
    for name, data in [('train', train_rows), ('val', val_rows), ('holdout', holdout_rows)]:
        df = pd.DataFrame(data)
        df.to_csv(f'data/{name}.csv', index=False)
        unique = df['ad_text'].nunique()
        print(f'{name}.csv: {len(df)} rows, {unique} unique texts')

    all_df = pd.DataFrame(rows)
    all_df.to_csv('data/expanded_ads.csv', index=False)
    print(f'\nexpanded_ads.csv: {len(all_df)} rows, {all_df["ad_text"].nunique()} unique texts')
    print(f'CTR range: [{all_df.actual_ctr.min():.4f}, {all_df.actual_ctr.max():.4f}]')

    return train_rows, val_rows, holdout_rows


if __name__ == '__main__':
    generate_dataset()
