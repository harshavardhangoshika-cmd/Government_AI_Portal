import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import requests

from app.database.database import get_all_complaints
from app.utils.sla_engine import enrich_complaints_with_sla

API_URL = "http://127.0.0.1:8000"


def fetch_complaints():
    """Fetch complaints from API or database with SLA enrichment fallback."""
    try:
        res = requests.get(f"{API_URL}/government/complaints", timeout=5)
        if res.status_code == 200:
            return res.json().get("data", [])
    except Exception:
        pass
    raw = get_all_complaints() or []
    return enrich_complaints_with_sla(raw)


def show():
    st.title("📄 Executive Briefing & Supervisor Report")
    st.caption("Auto-generated executive summary memo summarizing SLA compliance, emergency incidents, and district hotspots for senior supervisors.")
    st.divider()

    raw_complaints = fetch_complaints()

    if not raw_complaints:
        st.info("No complaint records available to generate executive briefing.")
        return

    # Check Jurisdiction Scope
    jurisdiction_scope = st.session_state.get("official_jurisdiction", "All Jurisdictions (Statewide)")
    if jurisdiction_scope and jurisdiction_scope != "All Jurisdictions (Statewide)":
        st.info(f"🔒 Scope Active: Generating Executive Briefing specifically for **{jurisdiction_scope}**.")
        complaints = [
            c for c in raw_complaints
            if str(c.get("district") or "Bengaluru Urban").strip().lower() == jurisdiction_scope.lower()
        ]
    else:
        complaints = raw_complaints

    if not complaints:
        st.warning(f"No complaint records found under jurisdiction scope: {jurisdiction_scope}")
        return

    total = len(complaints)
    resolved = sum(1 for c in complaints if str(c.get("status") or "").strip().lower() == "resolved")
    pending = total - resolved
    resolution_rate = (resolved / total * 100) if total > 0 else 0.0

    emergency_count = sum(1 for c in complaints if c.get("emergency") in [True, "true", "1", "yes", "Emergency"])
    overdue_count = sum(1 for c in complaints if c.get("is_overdue"))
    sla_compliance_rate = ((total - overdue_count) / total * 100) if total > 0 else 100.0

    # Department breakdown
    dept_counts = {}
    for c in complaints:
        d = str(c.get("department") or "Unassigned").strip()
        dept_counts[d] = dept_counts.get(d, 0) + 1

    sorted_depts = sorted(dept_counts.items(), key=lambda x: x[1], reverse=True)
    top_dept_str = f"{sorted_depts[0][0]} ({sorted_depts[0][1]} cases)" if sorted_depts else "N/A"

    # District breakdown
    dist_counts = {}
    for c in complaints:
        d = str(c.get("district") or "Bengaluru Urban").strip()
        dist_counts[d] = dist_counts.get(d, 0) + 1

    sorted_dists = sorted(dist_counts.items(), key=lambda x: x[1], reverse=True)
    top_dist_str = f"{sorted_dists[0][0]} ({sorted_dists[0][1]} cases)" if sorted_dists else "N/A"

    # Top KPI Metrics Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("📋 Total Complaints", total)
    with k2:
        st.metric("✅ Resolution Rate", f"{resolution_rate:.1f}%")
    with k3:
        st.metric("🚨 Emergency Cases", emergency_count)
    with k4:
        st.metric("🛡️ SLA Compliance", f"{sla_compliance_rate:.1f}%")

    st.divider()

    # Formatted Executive Memo String
    now_str = datetime.now().strftime("%B %d, %Y - %H:%M HRS")
    
    memo_content = f"""================================================================================
                    GOVERNMENT EXECUTIVE BRIEFING MEMORANDUM
================================================================================
DATE       : {now_str}
SCOPE      : {jurisdiction_scope}
AUTHOR     : Government Citizen Intelligence System (AI Engine)
SECURITY   : OFFICIAL FOR SUPERVISORY REVIEW ONLY

--------------------------------------------------------------------------------
1. EXECUTIVE SUMMARY
--------------------------------------------------------------------------------
This executive briefing details current citizen complaint resolution activity, SLA
compliance rates, and high-priority incidents within the designated jurisdiction.

- Total Complaints Received  : {total}
- Pending Action Required    : {pending}
- Successfully Resolved      : {resolved} ({resolution_rate:.1f}% Resolution Rate)
- Active Emergency Incidents : {emergency_count}
- SLA Overdue Complaints     : {overdue_count} ({sla_compliance_rate:.1f}% SLA Compliance)

--------------------------------------------------------------------------------
2. KEY OPERATIONAL HIGHLIGHTS
--------------------------------------------------------------------------------
* Peak Department Activity  : {top_dept_str}
* Primary Hotspot Location   : {top_dist_str}
* Emergency Status Alert     : {"CRITICAL ATTENTION NEEDED (" + str(emergency_count) + " Emergency Cases)" if emergency_count > 0 else "NORMAL (0 Emergency Cases Active)"}
* SLA Overdue Alert          : {"OVERDUE SLA VIOLATIONS DETECTED (" + str(overdue_count) + " Overdue)" if overdue_count > 0 else "FULLY COMPLIANT (0 Overdue)"}

--------------------------------------------------------------------------------
3. DEPARTMENTAL BREAKDOWN
--------------------------------------------------------------------------------
"""
    for d_name, d_cnt in sorted_depts:
        pct = (d_cnt / total * 100) if total > 0 else 0
        memo_content += f"  - {d_name:<30} : {d_cnt:>5} complaints ({pct:>5.1f}%)\n"

    memo_content += """
--------------------------------------------------------------------------------
4. RECOMMENDED ACTION ITEMS
--------------------------------------------------------------------------------
1. Immediate dispatch for all active Emergency & Overdue SLA cases in the Action Queue.
2. Inter-departmental coordination with top active department heads.
3. Priority resource allocation to designated hotspot districts.

================================================================================
END OF EXECUTIVE MEMORANDUM - GOVERNMENT CITIZEN INTELLIGENCE SYSTEM
================================================================================
"""

    st.subheader("📋 Executive Briefing Memo Preview")
    st.code(memo_content, language="markdown")

    st.divider()

    # Download Button & Export Action
    d_col1, d_col2 = st.columns([2, 3])
    with d_col1:
        file_filename = f"Executive_Briefing_{jurisdiction_scope.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt"
        st.download_button(
            label="📥 Download Executive Briefing (.txt)",
            data=memo_content,
            file_name=file_filename,
            mime="text/plain",
            use_container_width=True
        )
    with d_col2:
        st.success("✅ Executive Briefing generated and ready to download or forward to supervisors!")
