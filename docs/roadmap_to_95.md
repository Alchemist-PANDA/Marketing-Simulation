# Strategic Roadmap: The Path to 95%+ Accuracy

Having achieved a baseline of **92.4% Directional Accuracy** on real-world Facebook Ad data, our engine is already outperforming human intuition. However, to establish absolute market dominance and approach a "perfect" prediction engine, we must cross the 95% threshold.

Here is the strategic roadmap for the next major iteration (V3):

## 1. Multimodal Datasets (Real Image Integration)
**Current State:** The V2 validation was performed on a dataset where image paths were missing, meaning the CLIP visual scorer fell back to neutral benchmarks (0.5). The 92.4% was achieved entirely through calibrated psychographic text analysis.
**Next Step:** Procure and integrate a dataset that includes full ad creatives (images and carousels). By allowing the CLIP engine to dynamically score `visual_excitement` and `visual_premium`, the engine will capture the visual variance that text alone misses.

## 2. Video Analysis via Keyframe Extraction
**Current State:** The engine processes text and static images.
**Next Step:** Ad spend is heavily skewing toward short-form video (TikTok, Reels). We will implement a pre-processor that extracts 3-5 keyframes from video creatives, runs them through the CLIP scorer, and averages the psychometric visual scores to predict video performance.

## 3. Competitor Intelligence & Market Saturation
**Current State:** The simulation runs in a vacuum. It assumes the ad is the only one the user is seeing.
**Next Step:** Integrate a Meta Ad Library scraper. Before simulating an ad, the engine will scan the competitor landscape to establish a baseline "market saturation" penalty. If a user is launching an ad in a highly saturated niche (e.g., fast fashion), the engine will dynamically increase the `skepticism` penalty.

## 4. Real-Time ML Calibration
**Current State:** Weights are statically calibrated using the `calibrate_weights.py` script and a historical CSV.
**Next Step:** Build an automated feedback loop. As users run real ads and report the actual ROI back to the platform, the Logistic Regression model will constantly re-train in the background, updating `learned_weights.json` nightly based on live macroeconomic conditions.

## 5. Industry-Specific Persona Models
**Current State:** The 100,000 virtual agents represent a broad, general population.
**Next Step:** Create specialized agent populations (e.g., B2B SaaS Buyers, High-Net-Worth Luxury Consumers, Gen-Z Gamers). When simulating an ad, the marketer selects the industry, and the simulation runs against a hyper-calibrated, niche-specific slice of the population, vastly increasing accuracy for specialized products.
