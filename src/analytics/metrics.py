def calculate_roi(spend, revenue):
    if spend == 0:
        return 0
    return (revenue - spend) / spend

def calculate_cpa(spend, conversions):
    if conversions == 0:
        return float('inf')
    return spend / conversions

def calculate_ctr(clicks, impressions):
    if impressions == 0:
        return 0
    return clicks / impressions
