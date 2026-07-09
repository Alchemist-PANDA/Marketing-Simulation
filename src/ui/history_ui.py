"""
Streamlit UI component for displaying simulation report history.
Supports search, sort, CSV/JSON/PDF download, and delete.
"""
import streamlit as st
import json
import pandas as pd
from io import BytesIO, StringIO
from datetime import datetime
from typing import Dict, Any, List
from src.services.persistence_service import PersistenceService
from src.core.auth_utils import safe_get


def render_history_tab():
    """Render the simulation report history view."""
    st.header("📂 Report History")

    user = st.session_state.get("user")

    if not user:
        st.warning("🔐 Log in to view your saved reports.")
        return

    user_id = safe_get(user, "id")
    user_mode = safe_get(user, "mode")

    if user_mode == "local" or not user_id:
        st.info("📂 History unavailable in local mode. Connect to Supabase to enable persistence.")
        return

    service = PersistenceService()
    with st.spinner("Loading reports..."):
        result = service.list_reports(user_id)

    if result.get("status") != "success":
        st.error(f"❌ Failed to load reports: {result.get('message', 'Unknown error')}")
        return

    reports = result.get("data", [])

    if not reports:
        st.info("📭 No reports yet. Run a simulation — reports are saved automatically.")
        return

    # Search and filter controls
    col_search, col_filter = st.columns([3, 1])
    with col_search:
        search_query = st.text_input("🔍 Search reports", placeholder="Search by ad text, campaign name, or winner...")
    with col_filter:
        sort_by = st.selectbox("Sort by", ["Newest", "Oldest", "Highest Lift", "Lowest Lift"])

    # Apply search filter
    if search_query:
        q = search_query.lower()
        reports = [r for r in reports if (
            q in (r.get("ad_a_text") or "").lower() or
            q in (r.get("ad_b_text") or "").lower() or
            q in (r.get("campaign_name") or "").lower() or
            q in (r.get("winner") or "").lower() or
            q in (r.get("channel") or "").lower()
        )]

    # Apply sort
    if sort_by == "Newest":
        reports.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    elif sort_by == "Oldest":
        reports.sort(key=lambda x: x.get("created_at", ""))
    elif sort_by == "Highest Lift":
        reports.sort(key=lambda x: x.get("lift_percentage", 0) or 0, reverse=True)
    elif sort_by == "Lowest Lift":
        reports.sort(key=lambda x: x.get("lift_percentage", 0) or 0)

    st.caption(f"Showing {len(reports)} report{'s' if len(reports) != 1 else ''}")

    # Render each report
    for report in reports:
        _render_report_entry(report, user_id, service)


def _render_report_entry(report: Dict[str, Any], user_id: str, service: PersistenceService):
    """Render a single report entry with expandable details and actions."""
    report_id = report.get("id", "")
    report_num = report.get("report_number", "?")
    winner = report.get("winner", "?")
    lift = report.get("lift_percentage", 0) or 0
    channel = report.get("channel", "—")
    ad_a_preview = (report.get("ad_a_text") or "—")[:60]
    ad_b_preview = (report.get("ad_b_text") or "—")[:60]
    campaign_name = report.get("campaign_name") or ""

    # Format date
    date_str = report.get("created_at", "")
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        display_date = dt.strftime("%b %d, %Y — %H:%M UTC")
    except Exception:
        display_date = date_str

    # Build header
    title = f"📊 Report #{report_num}"
    if campaign_name:
        title += f" — {campaign_name}"
    title += f"  |  Winner: Ad {winner}  |  Lift: {lift:.2f}%  |  {channel}"

    with st.expander(title, expanded=False):
        st.caption(f"Created: {display_date}")

        # Summary metrics
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Winner", f"Ad {winner}")
        with m2:
            st.metric("Lift", f"{lift:.2f}%")
        with m3:
            st.metric("Channel", channel.title())
        with m4:
            st.metric("Agents", f"{report.get('num_agents', 0):,}")

        # Ad text previews
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Ad A:**")
            st.text(report.get("ad_a_text") or "—")
        with c2:
            st.markdown("**Ad B:**")
            st.text(report.get("ad_b_text") or "—")

        # Result details from JSON
        result_json = report.get("result_json", {})
        if result_json:
            ad_a = result_json.get("ad_a", {})
            ad_b = result_json.get("ad_b", {})
            if ad_a or ad_b:
                st.markdown("**Detailed Metrics:**")
                mc1, mc2, mc3, mc4, mc5, mc6 = st.columns(6)
                with mc1:
                    st.metric("A Likes", ad_a.get("likes", 0))
                with mc2:
                    st.metric("A Conv", ad_a.get("conversions", 0))
                with mc3:
                    st.metric("A Shares", ad_a.get("shares", 0))
                with mc4:
                    st.metric("B Likes", ad_b.get("likes", 0))
                with mc5:
                    st.metric("B Conv", ad_b.get("conversions", 0))
                with mc6:
                    st.metric("B Shares", ad_b.get("shares", 0))

        # Action buttons
        st.divider()
        btn_cols = st.columns([1, 1, 1, 1, 2])

        with btn_cols[0]:
            csv_data = _report_to_csv(report)
            st.download_button("📥 CSV", data=csv_data, file_name=f"report_{report_num}.csv",
                               mime="text/csv", key=f"csv_{report_id}")
        with btn_cols[1]:
            json_data = json.dumps(result_json, indent=2)
            st.download_button("📥 JSON", data=json_data, file_name=f"report_{report_num}.json",
                               mime="application/json", key=f"json_{report_id}")
        with btn_cols[2]:
            pdf_bytes = _report_to_pdf(report)
            st.download_button("📥 PDF", data=pdf_bytes, file_name=f"report_{report_num}.pdf",
                               mime="application/pdf", key=f"pdf_{report_id}")
        with btn_cols[3]:
            if st.button("🗑️ Delete", key=f"del_{report_id}", type="secondary"):
                st.session_state[f"confirm_delete_{report_id}"] = True

        # Delete confirmation
        if st.session_state.get(f"confirm_delete_{report_id}"):
            st.warning(f"⚠️ Are you sure you want to delete Report #{report_num}? This cannot be undone.")
            cc1, cc2 = st.columns(2)
            with cc1:
                if st.button("Yes, delete", key=f"confirm_yes_{report_id}", type="primary"):
                    res = service.delete_report(report_id, user_id)
                    if res.get("status") == "success":
                        st.toast(f"Report #{report_num} deleted", icon="🗑️")
                        st.session_state.pop(f"confirm_delete_{report_id}", None)
                        st.rerun()
                    else:
                        st.error(f"Failed to delete: {res.get('message')}")
            with cc2:
                if st.button("Cancel", key=f"confirm_no_{report_id}"):
                    st.session_state.pop(f"confirm_delete_{report_id}", None)
                    st.rerun()


def _report_to_csv(report: Dict[str, Any]) -> str:
    """Convert a report to CSV format."""
    result_json = report.get("result_json", {})
    ad_a = result_json.get("ad_a", {})
    ad_b = result_json.get("ad_b", {})

    rows = []
    for label, ad_data, text in [("Ad A", ad_a, report.get("ad_a_text", "")),
                                  ("Ad B", ad_b, report.get("ad_b_text", ""))]:
        rows.append({
            "Ad": label,
            "Text": text,
            "Likes": ad_data.get("likes", 0),
            "Conversions": ad_data.get("conversions", 0),
            "Shares": ad_data.get("shares", 0),
        })

    rows.append({
        "Ad": "Summary",
        "Text": f"Winner: Ad {report.get('winner', '?')}",
        "Likes": "",
        "Conversions": "",
        "Shares": f"Lift: {report.get('lift_percentage', 0):.2f}%",
    })

    df = pd.DataFrame(rows)
    buf = StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def _report_to_pdf(report: Dict[str, Any]) -> bytes:
    """Generate a PDF summary of the report."""
    try:
        from fpdf import FPDF
    except ImportError:
        return _report_to_pdf_fallback(report)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, f"Simulation Report #{report.get('report_number', '?')}", new_x="LMARGIN", new_y="NEXT")

    # Date
    date_str = report.get("created_at", "")
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        display_date = dt.strftime("%B %d, %Y at %H:%M UTC")
    except Exception:
        display_date = date_str
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Generated: {display_date}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Summary
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Winner: Ad {report.get('winner', '?')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Lift: {report.get('lift_percentage', 0):.2f}%", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Channel: {(report.get('channel') or 'N/A').title()}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Agents: {report.get('num_agents', 0):,}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Objective: {(report.get('objective') or 'N/A').replace('_', ' ').title()}", new_x="LMARGIN", new_y="NEXT")
    if report.get("campaign_name"):
        pdf.cell(0, 7, f"Campaign: {report['campaign_name']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Ad texts
    for label, key in [("Ad A", "ad_a_text"), ("Ad B", "ad_b_text")]:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, label, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        text = report.get(key) or "N/A"
        pdf.multi_cell(0, 6, text)
        pdf.ln(2)

    # Metrics table
    result_json = report.get("result_json", {})
    ad_a = result_json.get("ad_a", {})
    ad_b = result_json.get("ad_b", {})

    if ad_a or ad_b:
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Detailed Metrics", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "B", 10)
        col_w = [30, 40, 40, 40, 40]
        headers = ["Ad", "Likes", "Conversions", "Shares", "CTR"]
        for i, h in enumerate(headers):
            pdf.cell(col_w[i], 8, h, border=1)
        pdf.ln()

        pdf.set_font("Helvetica", "", 10)
        for label, data in [("Ad A", ad_a), ("Ad B", ad_b)]:
            analysis = data.get("analysis", {})
            vals = [
                label,
                str(data.get("likes", 0)),
                str(data.get("conversions", 0)),
                str(data.get("shares", 0)),
                f"{analysis.get('predicted_ctr', 0):.4f}" if analysis.get("predicted_ctr") else "—",
            ]
            for i, v in enumerate(vals):
                pdf.cell(col_w[i], 7, v, border=1)
            pdf.ln()

    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, "Generated by Marketing Simulation: Digital Wind Tunnel", new_x="LMARGIN", new_y="NEXT")

    return pdf.output()


def _report_to_pdf_fallback(report: Dict[str, Any]) -> bytes:
    """Simple text-based PDF fallback when fpdf is not available."""
    lines = [
        f"Simulation Report #{report.get('report_number', '?')}",
        f"Winner: Ad {report.get('winner', '?')}",
        f"Lift: {report.get('lift_percentage', 0):.2f}%",
        f"Channel: {report.get('channel', 'N/A')}",
        f"Agents: {report.get('num_agents', 0):,}",
        "",
        f"Ad A: {report.get('ad_a_text', 'N/A')}",
        f"Ad B: {report.get('ad_b_text', 'N/A')}",
    ]
    text = "\n".join(lines)
    return text.encode("utf-8")
