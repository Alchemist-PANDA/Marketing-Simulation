# Validation Methodology

The Marketing Simulation Engine is designed to provide *directional indicators* of ad performance, rather than absolute predictions of precise metrics (like a 2.45% exact Conversion Rate). To bridge the gap between simulation and real-world asset value, we focus on **Directional Accuracy**.

## What is Directional Accuracy?

Directional Accuracy measures how often the simulation correctly identifies the winning ad compared to real-world performance data.

For example, if you run 10 historical A/B tests through the engine:
- In 7 of those tests, the engine predicted Ad A would have a higher conversion rate, and in reality, Ad A actually won.
- In 3 tests, the engine predicted Ad B, but Ad A won in reality.
- **Directional Accuracy = 70%**

## Why Directional Accuracy?

Simulating human behavior is immensely complex. While our engine utilizes OCEAN traits and Prospect Theory to model psychological responses, it cannot account for real-time market conditions, competitor ad spend, or algorithmic platform changes. 

By measuring Directional Accuracy, we evaluate the engine on its core purpose: **helping marketers make the right choice between variations before spending budget.**

## Interpreting Validation Reports

When you run a validation report (via the script or UI), you will see:
1. **Total Tests Analyzed:** The number of unique A/B (or A/B/C) tests compared.
2. **Directional Match Rate (Accuracy):** The percentage of tests where the simulation correctly ranked the top-performing ad.
3. **Outlier Warnings:** If the engine was completely wrong, the report highlights the discrepancy (e.g., the simulation vastly preferred Ad A, but Ad B won by a landslide). This is crucial for refining the engine's psychological weights over time.

## How to Validate Your Own Data

1. Export your historical ad data from Facebook Ads Manager, Google Ads, or TikTok.
2. Format a CSV with at least: `ad_text`, `impressions`, `clicks`, `conversions`. (Optional: `spend`, `image_url`).
3. Use the "Validate Against Your Data" tool in the application dashboard to upload your CSV and generate your custom Validation Report.
