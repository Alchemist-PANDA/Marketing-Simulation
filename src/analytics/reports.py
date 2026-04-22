from .metrics import calculate_roi, calculate_cpa, calculate_ctr

def generate_summary(campaign_name, results, revenue_per_conversion=50.0):
    revenue = results["conversions"] * revenue_per_conversion
    roi = calculate_roi(results["spend"], revenue)
    cpa = calculate_cpa(results["spend"], results["conversions"])
    ctr = calculate_ctr(results["clicks"], results["impressions"])

    return {
        "campaign": campaign_name,
        "spend": round(results["spend"], 2),
        "conversions": results["conversions"],
        "revenue": round(revenue, 2),
        "roi": round(roi, 2),
        "cpa": round(cpa, 2),
        "ctr": round(ctr, 4)
    }
