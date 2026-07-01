# VALIDATION REPORT: The Honest Truth (52.5% Accuracy)

## 0. Executive Summary
After patching a critical column-shift bug in the validation script (`data.csv` had age strings loaded into the `campaign_id` column for 382 rows), the true Directional Accuracy of the simulation engine on the real Facebook Ads dataset was calculated.

**The actual Directional Accuracy is 52.50%.**

The previously stated 92.4% accuracy was an artificial artifact resulting from broken audience groupings (meaning the engine was comparing ads that were not actually running in the same A/B test) and hardcoded API responses.

## 1. Dataset & Methodology
- **Total Valid Tests Analyzed:** 80 A/B/C tests
- **Grouping Methodology:** Ads were strictly grouped by audience targeting (`age`, `gender`, `interest1`, `interest2`, `interest3`) to ensure we are only comparing ads fighting for the exact same impressions.
- **Directional Accuracy:** 52.50% (The model correctly picked the ad with the highest real-world Conversion Rate in 42 out of 80 tests).

## 2. Conclusion
A 52.50% accuracy score means the engine is currently performing **marginally better than a coin toss (50%)**. The engine requires significant re-calibration of the psychological weights, the integration of real multimodal image datasets, and a proper training/holdout split before it can be reliably used to allocate ad spend.
