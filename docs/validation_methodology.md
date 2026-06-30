# Validation Methodology

The Marketing Simulation Engine is designed to provide *directional indicators* of ad performance, rather than absolute predictions of precise metrics (like a 2.45% exact Conversion Rate). To bridge the gap between simulation and real-world asset value, we focus on **Directional Accuracy**.

## What is Directional Accuracy?

Directional Accuracy measures how often the simulation correctly identifies the winning ad compared to real-world performance data.

For example, if you run 10 historical A/B tests through the engine:
- In 7 of those tests, the engine predicted Ad A would have a higher conversion rate, and in reality, Ad A actually won.
- In 3 tests, the engine predicted Ad B, but Ad A won in reality.
- **Directional Accuracy = 70%**

## Smart CSV Parsing & Column Mapping

To calculate Directional Accuracy, you must upload a historical CSV containing past ad tests and their real-world conversion metrics.

**Smart CSV Parsing:** The UI includes a smart CSV parser that accepts raw data exports from Meta, TikTok, or Google Ads. It auto-detects column names using common aliases (e.g., `Sales`, `Purchases`, `Goal Completions` map to `conversions`, and `Copy`, `Creative`, `Message` map to `ad_text`). If you upload a messy CSV, the UI will present a dropdown mapping interface allowing you to manually map your columns before running the validation.

**Missing Data Fallbacks:** 
- If your export is missing `impressions` (e.g. just raw sales data), the system will automatically assume a baseline of 1000 impressions to prevent errors. 
- If you don't have a `test_id` column to group A/B tests, the system treats your entire CSV as a single large test and ranks all creatives simultaneously to see if the simulation successfully predicted your overall top-performing ad.

### Required Logical Columns (can be mapped from anything):
- **Ad Name** (Optional, auto-generated if missing)
- **Ad Text / Copy** (Strictly Required)
- **Conversions / Sales** (Strictly Required)
- **Impressions / Views** (Optional, defaults to 1000)
- **Platform / Channel** (Optional, defaults to facebook)

## Why Directional Accuracy?

Simulating human behavior is immensely complex. While our engine utilizes OCEAN traits and Prospect Theory to model psychological responses, it cannot account for real-time market conditions, competitor ad spend, or algorithmic platform changes. 

By measuring Directional Accuracy, we evaluate the engine on its core purpose: **helping marketers make the right choice between variations before spending budget.**

## Interpreting Validation Reports

When you run a validation report (via the script or UI), you will see:
1. **Total Tests Analyzed:** The number of unique A/B (or A/B/C) tests compared.
2. **Directional Match Rate (Accuracy):** The percentage of tests where the simulation correctly ranked the top-performing ad.
3. **Outlier Warnings:** If the engine was completely wrong, the report highlights the discrepancy (e.g., the simulation vastly preferred Ad A, but Ad B won by a landslide). This is crucial for refining the engine's psychological weights over time.

## How to Validate Your Own Data

1. Export your historical ad data from Facebook Ads Manager, Google Ads, or TikTok. (Don't worry about column names!).
2. Use the "Validate Against Your Data" tool in the application dashboard to upload your CSV.
3. Confirm the Smart Column Mapping.
4. Run the validation and review your custom Validation Report.
