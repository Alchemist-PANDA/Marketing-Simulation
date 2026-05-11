"""LangGraph nodes for GEO audit brand audit flow."""

from typing import Dict, Any
from .audit import run_audit
from .measurement import measure_lift, calculate_visibility_score
from .remediation import generate_remediation


def query_llm_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node that queries the LLM for brand information.

    Args:
        state: Current graph state containing brand_name, category, city

    Returns:
        Updated state with brand_info extracted from LLM
    """
    brand_name = state.get("brand_name", "")
    category = state.get("category", "")
    city = state.get("city", "")

    # In a real implementation, this would call an LLM
    # For now, we use the business_context from state
    return {
        "brand_info": {
            "name": brand_name,
            "category": category,
            "city": city,
        }
    }


def check_citation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node that checks citation/presence of the brand.

    Args:
        state: Current graph state

    Returns:
        Updated state with citation score
    """
    # For now, return a placeholder citation score
    return {"citation_score": 1.0}


def gap_analyst_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node that analyzes gaps using industry-specific templates.

    This is the critical node that selects the correct template based on category.
    For "dental clinic", it should use DentalClinicTemplate.

    Args:
        state: Current graph state containing brand_name, category, city, business_data

    Returns:
        Updated state with gaps, strengths, template_used, and remediation-compatible data
    """
    brand_name = state.get("brand_name", "")
    category = state.get("category", "")
    city = state.get("city", "")
    business_data = state.get("business_data", {})

    # Run the audit - this uses get_template internally
    audit_result = run_audit(brand_name, category, city, business_data)

    return {
        "gaps": audit_result.get("gaps", []),
        "strengths": audit_result.get("strengths", []),
        "template_used": audit_result.get("template_used"),
        "sentiment": audit_result.get("sentiment"),
        "competitors": audit_result.get("competitors", []),
    }


def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node that plans remediation actions based on gaps.

    Args:
        state: Current graph state containing gaps, category, city, brand_name

    Returns:
        Updated state with planned_actions
    """
    gaps = state.get("gaps", [])
    category = state.get("category", "")
    city = state.get("city", "")
    brand_name = state.get("brand_name", "")

    if not gaps:
        return {"planned_actions": []}

    # Generate remediation using the template-aware function
    remediation = generate_remediation(gaps, category, city, brand_name)

    return {"planned_actions": remediation}


def remediation_handler_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node that handles remediation execution.

    Args:
        state: Current graph state containing planned_actions

    Returns:
        Updated state with remediation_results
    """
    planned_actions = state.get("planned_actions", [])

    return {"remediation_results": planned_actions}


def generate_report_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node that generates the final audit report.

    Args:
        state: Current graph state containing all audit data

    Returns:
        Final audit report
    """
    brand_name = state.get("brand_name", "")
    category = state.get("category", "")
    city = state.get("city", "")
    business_data = state.get("business_data", {})
    gaps = state.get("gaps", [])
    strengths = state.get("strengths", [])
    template_used = state.get("template_used")
    sentiment = state.get("sentiment", "none")
    competitors = state.get("competitors", [])
    planned_actions = state.get("planned_actions", [])
    citation_score = state.get("citation_score", 0.0)

    # Calculate lift metrics
    before_score = calculate_visibility_score(business_data or {}, gaps)
    after_business_data = (business_data or {}).copy()
    after_score = calculate_visibility_score(after_business_data, [])
    lift_metrics = measure_lift(before_score, after_score)

    # Generate final report
    report = {
        "brand_name": brand_name,
        "category": category,
        "city": city,
        "template_used": template_used,
        "citation_score": citation_score,
        "sentiment": sentiment,
        "competitors": competitors,
        "strengths": strengths,
        "gaps": gaps,
        "planned_actions": planned_actions,
        "lift_metrics": lift_metrics,
    }

    return {"report": report}
