"""GEO Audit Agent - orchestrates audit, measurement, and remediation."""

from typing import Optional, Dict
from .audit import run_audit
from .measurement import measure_lift, calculate_visibility_score
from .remediation import generate_remediation


class GeoAuditAgent:
    """Main agent for GEO audit operations."""

    def __init__(self):
        pass

    def run_full_audit(
        self,
        brand_name: str,
        category: str,
        city: str,
        business_data: Optional[Dict] = None
    ) -> Dict:
        """
        Run complete GEO audit with lift simulation.

        Args:
            brand_name: Business name
            category: Business category
            city: City location
            business_data: Optional business data

        Returns:
            Complete audit results with lift metrics and remediation
        """
        # Run audit
        audit_results = run_audit(brand_name, category, city, business_data)

        # Calculate before score
        before_score = calculate_visibility_score(business_data or {}, audit_results['gaps'])

        # Simulate after score (assume gaps are fixed)
        after_business_data = (business_data or {}).copy()
        after_score = calculate_visibility_score(after_business_data, [])

        # Measure lift
        lift_metrics = measure_lift(before_score, after_score)

        # Generate remediation
        remediation = generate_remediation(
            audit_results['gaps'],
            category,
            city,
            brand_name
        )

        return {
            **audit_results,
            'lift_metrics': lift_metrics,
            'remediation': remediation,
        }
