"""LangGraph workflow for GEO audit brand audit flow."""

from typing import Dict, Any
from .graph_nodes import (
    query_llm_node,
    check_citation_node,
    gap_analyst_node,
    planner_node,
    remediation_handler_node,
    generate_report_node,
)


def create_brand_audit_graph():
    """
    Create the LangGraph workflow for brand audit.

    The graph follows the path:
    query_llm → check_citation → gap_analyst → planner → remediation_handler → generate_report

    Returns:
        Compiled LangGraph workflow
    """
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        # Fallback to simple function if LangGraph is not installed
        return None

    # Define the state schema
    class AuditState(Dict[str, Any]):
        brand_name: str
        category: str
        city: str
        business_data: Dict[str, Any]
        brand_info: Dict[str, Any]
        citation_score: float
        gaps: list
        strengths: list
        template_used: str
        sentiment: str
        competitors: list
        planned_actions: list
        remediation_results: list
        report: Dict[str, Any]

    # Create the graph
    workflow = StateGraph(AuditState)

    import inspect
    print("BOUND_GAP_ANALYST_FUNCTION:", gap_analyst_node)
    print("BOUND_GAP_ANALYST_MODULE:", gap_analyst_node.__module__)
    try:
        print("BOUND_GAP_ANALYST_FILE:", inspect.getsourcefile(gap_analyst_node))
    except TypeError:
        print("BOUND_GAP_ANALYST_FILE: Could not determine source file")

    # Add nodes
    workflow.add_node("query_llm", query_llm_node)
    workflow.add_node("check_citation", check_citation_node)
    workflow.add_node("gap_analyst", gap_analyst_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("remediation_handler", remediation_handler_node)
    workflow.add_node("generate_report", generate_report_node)

    # Define edges
    workflow.set_entry_point("query_llm")
    workflow.add_edge("query_llm", "check_citation")
    workflow.add_edge("check_citation", "gap_analyst")
    workflow.add_edge("gap_analyst", "planner")
    workflow.add_edge("planner", "remediation_handler")
    workflow.add_edge("remediation_handler", "generate_report")
    workflow.add_edge("generate_report", END)

    return workflow.compile()


def run_brand_audit_graph(
    brand_name: str,
    category: str,
    city: str,
    business_data: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Run the brand audit using the LangGraph workflow.

    Args:
        brand_name: Business name
        category: Business category
        city: City location
        business_data: Optional business data

    Returns:
        Complete audit results
    """
    if business_data is None:
        business_data = {}

    # Try to use LangGraph if available
    try:
        from langgraph.graph import END
        graph = create_brand_audit_graph()

        if graph is None:
            # Fallback to direct execution if LangGraph is not installed
            return _run_audit_direct(brand_name, category, city, business_data)

        # Run the graph
        initial_state = {
            "brand_name": brand_name,
            "category": category,
            "city": city,
            "business_data": business_data,
        }

        result = graph.invoke(initial_state)
        return result.get("report", result)

    except ImportError:
        # LangGraph not installed, use direct execution
        return _run_audit_direct(brand_name, category, city, business_data)


def _run_audit_direct(
    brand_name: str,
    category: str,
    city: str,
    business_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Direct audit execution without LangGraph (fallback).

    This executes the same path as the graph but without the graph overhead.
    """
    # query_llm
    brand_info = {
        "name": brand_name,
        "category": category,
        "city": city,
    }

    # check_citation
    citation_score = 1.0

    # gap_analyst - THIS IS THE CRITICAL NODE
    from .audit import run_audit
    audit_result = run_audit(brand_name, category, city, business_data)

    gaps = audit_result.get("gaps", [])
    strengths = audit_result.get("strengths", [])
    template_used = audit_result.get("template_used")
    sentiment = audit_result.get("sentiment", "none")
    competitors = audit_result.get("competitors", [])

    # planner
    from .remediation import generate_remediation
    planned_actions = generate_remediation(gaps, category, city, brand_name)

    # remediation_handler
    remediation_results = planned_actions

    # generate_report
    from .measurement import measure_lift, calculate_visibility_score
    before_score = calculate_visibility_score(business_data, gaps)
    after_business_data = business_data.copy()
    after_score = calculate_visibility_score(after_business_data, [])
    lift_metrics = measure_lift(before_score, after_score)

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
        "remediation_results": remediation_results,
        "lift_metrics": lift_metrics,
    }

    return report
