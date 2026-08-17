import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import requests

from app.database.database import get_all_complaints, update_complaint_status as db_update_status
from app.utils.sla_engine import enrich_complaints_with_sla

API_URL = "https://government-ai-api.onrender.com"


def fetch_complaints():
    """Fetch enriched complaints from FastAPI or fallback to database directly."""
    try:
        res = requests.get(f"{API_URL}/government/complaints", timeout=5)
        if res.status_code == 200:
            return res.json().get("data", [])
    except Exception:
        pass

    # Fallback to direct DB query + SLA calculation
    raw = get_all_complaints() or []
    return enrich_complaints_with_sla(raw)


def save_status_update(complaint_number, status, officer, remarks, department=None, priority=None):
    """Update complaint status, department, priority, officer, and remarks via API or direct DB fallback."""
    try:
        res = requests.post(
            f"{API_URL}/government/update-status",
            json={
                "complaint_number": complaint_number,
                "status": status,
                "assigned_officer": officer,
                "officer_remarks": remarks,
                "department": department,
                "priority": priority
            },
            timeout=5
        )
        if res.status_code == 200:
            return True, "Updated successfully via API!"
    except Exception:
        pass

    # Fallback DB execution
    res = db_update_status(
        complaint_number=complaint_number,
        status=status,
        assigned_officer=officer,
        officer_remarks=remarks,
        department=department,
        priority=priority
    )
    if res:
        return True, "Updated successfully in Database!"
    return False, "Failed to update complaint status."


def show():
    st.title("⚡ Needs Action Now Queue")
    st.caption("Emergency-first action queue & SLA deadline management for government officials.")

    # Apply Official Jurisdiction Scope
    jurisdiction_scope = st.session_state.get("official_jurisdiction", "All Jurisdictions (Statewide)")
    if jurisdiction_scope and jurisdiction_scope != "All Jurisdictions (Statewide)":
        st.info(f"🔒 **Jurisdiction Scope Active**: Displaying complaints assigned to **{jurisdiction_scope}**.")

    st.divider()

    raw_complaints = fetch_complaints()

    if not raw_complaints:
        st.info("No complaints found in the system.")
        return

    if jurisdiction_scope and jurisdiction_scope != "All Jurisdictions (Statewide)":
        complaints = [
            c for c in raw_complaints
            if str(c.get("district") or "Bengaluru Urban").strip().lower() == jurisdiction_scope.lower()
        ]
    else:
        complaints = raw_complaints

    if not complaints:
        st.info(f"No complaints found for jurisdiction: {jurisdiction_scope}")
        return

    # Calculate Summary Metrics
    total_count = len(complaints)
    emergency_count = sum(1 for c in complaints if c.get("emergency") in [True, "true", "1", "yes", "Emergency"])
    overdue_count = sum(1 for c in complaints if c.get("is_overdue"))
    pending_count = sum(1 for c in complaints if str(c.get("status") or "").strip().lower() != "resolved")
    resolved_count = total_count - pending_count

    # Metric Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🚨 Emergency Cases", emergency_count)
    with col2:
        st.metric("⏰ Overdue SLA", overdue_count)
    with col3:
        st.metric("⚡ Pending Action", pending_count)
    with col4:
        st.metric("✅ Resolved", resolved_count)

    st.divider()

    # Filter Controls
    f_col1, f_col2, f_col3 = st.columns([2, 2, 2])
    with f_col1:
        view_filter = st.selectbox(
            "Filter Queue View",
            ["⚡ Needs Action (Pending)", "🚨 Emergency Only", "⏰ Overdue Only", "📋 All Complaints", "✅ Resolved Only"]
        )
    with f_col2:
        departments = sorted(list(set(str(c.get("department") or "Unassigned").strip() for c in complaints if c.get("department"))))
        selected_dept = st.selectbox("Filter Department", ["All Departments"] + departments)
    with f_col3:
        search_query = st.text_input("🔍 Search ID / Keyword", placeholder="GC-2026-000001 or text")

    # Filter Logic
    filtered = complaints[:]

    if view_filter == "⚡ Needs Action (Pending)":
        filtered = [c for c in filtered if str(c.get("status") or "").strip().lower() != "resolved"]
    elif view_filter == "🚨 Emergency Only":
        filtered = [c for c in filtered if c.get("emergency") in [True, "true", "1", "yes", "Emergency"]]
    elif view_filter == "⏰ Overdue Only":
        filtered = [c for c in filtered if c.get("is_overdue")]
    elif view_filter == "✅ Resolved Only":
        filtered = [c for c in filtered if str(c.get("status") or "").strip().lower() == "resolved"]

    if selected_dept != "All Departments":
        filtered = [c for c in filtered if str(c.get("department") or "").strip() == selected_dept]

    if search_query.strip():
        q = search_query.strip().lower()
        filtered = [
            c for c in filtered
            if q in str(c.get("complaint_number") or "").lower() or q in str(c.get("complaint_text") or "").lower()
        ]

    # Priority Rank Function
    def get_sort_key(c):
        is_emerg = c.get("emergency") in [True, "true", "1", "yes", "Emergency"]
        is_over = c.get("is_overdue")
        prio = str(c.get("priority") or "medium").strip().lower()
        prio_weight = {"urgent": 0, "high": 1, "medium": 2, "low": 3}.get(prio, 2)
        
        # Tuple sorting: (not emergency, not overdue, priority_weight, hours_remaining)
        return (not is_emerg, not is_over, prio_weight, c.get("hours_remaining") or 999)

    filtered.sort(key=get_sort_key)

    st.subheader(f"Action Queue ({len(filtered)} Complaints)")

    if not filtered:
        st.success("🎉 No complaints match your selected filter!")
        return

    statuses = ["Submitted", "Assigned", "Under Review", "Field Inspection", "Resolved"]

    # Render Expandable Cards for Each Complaint
    for c in filtered:
        c_num = c.get("complaint_number") or f"ID #{c.get('id')}"
        dept = c.get("department") or "Unassigned"
        prio = (c.get("priority") or "Medium").upper()
        status = c.get("status") or "Submitted"
        is_emerg = c.get("emergency") in [True, "true", "1", "yes", "Emergency"]
        is_over = c.get("is_overdue")
        hrs = c.get("hours_remaining")

        # Badges
        badges = []
        if is_emerg:
            badges.append("🚨 EMERGENCY")
        if is_over:
            badges.append("⏰ OVERDUE")
        elif hrs is not None and hrs > 0:
            badges.append(f"⏳ {hrs}h remaining")

        badge_str = " | ".join(badges)
        card_label = f"[{c_num}] [{dept}] - Priority: {prio} ({status}) {f'| {badge_str}' if badge_str else ''}"

        with st.expander(card_label, expanded=is_emerg or is_over):
            col_left, col_right = st.columns([3, 2])

            with col_left:
                st.markdown(f"**Complaint Details:**")
                st.info(c.get("complaint_text") or "No text provided.")

                st.write(f"**Department:** `{dept}` | **Category:** `{c.get('feedback_category') or 'General'}`")
                st.write(f"**Reason:** `{c.get('complaint_reason') or 'N/A'}` | **Sentiment:** `{c.get('sentiment') or 'N/A'}`")
                st.write(f"**Submitted At:** `{c.get('created_at') or 'N/A'}`")

                if is_over:
                    st.error(f"🚨 **SLA Violation**: Resolution deadline ({c.get('sla_hours')}h window) has passed!")
                elif hrs is not None and hrs > 0:
                    st.warning(f"⏰ **SLA Target**: {hrs} hours remaining to resolve ({c.get('sla_hours')}h total window).")

            with col_right:
                st.markdown("**Take Action & Update Pipeline:**")
                with st.form(key=f"form_{c_num}"):
                    curr_idx = statuses.index(status) if status in statuses else 0
                    new_status = st.selectbox("Pipeline Status", statuses, index=curr_idx)

                    dept_list = [
                        "BWSSB / Sanitation & Water",
                        "BBMP / Municipal Works",
                        "BESCOM / Power & Electricity",
                        "Traffic & Road Safety",
                        "Health & Family Welfare",
                        "Ministry of Social Justice & Empowerment",
                        "General Administration"
                    ]
                    if dept not in dept_list:
                        dept_list.insert(0, dept)
                    curr_dept_idx = dept_list.index(dept) if dept in dept_list else 0
                    new_dept = st.selectbox("🏢 Reassign Department", dept_list, index=curr_dept_idx)

                    prio_list = ["Low", "Medium", "High", "Urgent"]
                    curr_prio_val = (c.get("priority") or "Medium").capitalize()
                    curr_prio_idx = prio_list.index(curr_prio_val) if curr_prio_val in prio_list else 1
                    new_prio = st.selectbox("⚡ Priority Level", prio_list, index=curr_prio_idx)

                    assigned_off = st.text_input(
                        "Assigned Officer Name",
                        value=c.get("assigned_officer") or ""
                    )

                    remarks = st.text_area(
                        "Official Action Remarks",
                        value=c.get("officer_remarks") or "",
                        height=90,
                        placeholder="e.g. Field team dispatched to repair pipeline."
                    )

                    submit_btn = st.form_submit_button("💾 Save & Sync Status")

                    if submit_btn:
                        success, msg = save_status_update(
                            complaint_number=c_num,
                            status=new_status,
                            officer=assigned_off,
                            remarks=remarks,
                            department=new_dept,
                            priority=new_prio
                        )
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

