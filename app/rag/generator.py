"""
Civic AI Help RAG Response Generator
====================================
Synthesizes verified knowledge base context into structured, authoritative,
and citizen-friendly answers with SLAs, acts, and actionable next steps.
"""

import re
from typing import List, Dict, Any, Optional

try:
    from app.database.database import get_complaint_by_number
except ImportError:
    get_complaint_by_number = None


def extract_complaint_number(text: str) -> Optional[str]:
    """Detects complaint IDs like CMP-2026-0808-1234 or similar patterns."""
    match = re.search(r"\b(CMP[-_]\w+[-_]\w+[-_]\w+)\b", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None


def generate_rag_response(query: str, retrieved_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Synthesizes a structured RAG response from retrieved knowledge documents.
    """
    # 1. Check for live complaint tracking intent
    complaint_no = extract_complaint_number(query)
    complaint_info = None
    if complaint_no and get_complaint_by_number:
        try:
            complaint_info = get_complaint_by_number(complaint_no)
        except Exception:
            complaint_info = None

    if complaint_info:
        status = complaint_info.get("status", "Submitted")
        dept = complaint_info.get("department", "Assigned Department")
        prio = complaint_info.get("priority", "Normal")
        officer = complaint_info.get("assigned_officer", "Pending Assignment")
        remarks = complaint_info.get("officer_remarks", "None yet")

        tracking_msg = (
            f"### 🔍 Live Status for Complaint `{complaint_no}`\n\n"
            f"- **Current Status:** `{status}`\n"
            f"- **Responsible Department:** {dept}\n"
            f"- **Priority:** {prio}\n"
            f"- **Assigned Officer:** {officer}\n"
            f"- **Officer Remarks:** {remarks}\n\n"
        )

        if str(status).lower() in ["overdue", "delayed", "pending"]:
            tracking_msg += (
                "⚠️ **Escalation Advice:** If your complaint exceeds its statutory SLA under the "
                "Karnataka Sakala Services Act, you are entitled to file a First Appeal or claim "
                "compensatory delay cost (Rs 20/day) with the designated Appellate Authority.\n\n"
            )

        return {
            "answer": tracking_msg,
            "category": "tracking",
            "authority": dept,
            "sla_hours": None,
            "sources": [],
            "suggested_actions": ["Track Another Complaint", "Escalate to Appellate Authority"],
            "has_live_tracking": True
        }

    # 2. General Knowledge Base synthesis
    if not retrieved_docs:
        fallback_answer = (
            "I could not locate specific government bylaws or welfare schemes matching your exact query. "
            "However, you can:\n\n"
            "1. **Submit a Complaint:** Use the portal's **Submit Complaint** form to log your grievance with our AI classifier.\n"
            "2. **Official Help Desk:** Contact the State Grievance Cell or call Central CPGRAMS toll-free helpline (1800-11-4000).\n"
            "3. **Local Municipal Ward:** Contact your local Ward Assistant Executive Engineer (AEE)."
        )
        return {
            "answer": fallback_answer,
            "category": "general",
            "authority": "Municipal Administration",
            "sla_hours": 48,
            "sources": [],
            "suggested_actions": ["Submit a Complaint", "Browse Welfare Schemes"]
        }

    top_doc = retrieved_docs[0]
    topic = top_doc.get("topic", "Civic Grievance Redressal")
    authority = top_doc.get("authority", "Concerned Government Department")
    sla = top_doc.get("sla_hours", 48)
    act = top_doc.get("act_or_scheme", "Citizen Charter Guidelines")
    content = top_doc.get("content", "")
    escalation = top_doc.get("escalation", "")
    action = top_doc.get("action_suggested", "")
    category = top_doc.get("category", "")

    # Structured Response Synthesis
    answer_parts = [
        f"### 🏛️ {topic}\n",
        f"**Responsible Authority:** {authority}  ",
        f"**Official Resolution SLA:** `{sla} Hours`  ",
        f"**Governing Act / Scheme:** *{act}*\n",
        f"#### 📋 Summary of Guidelines & Citizen Rights\n{content}\n"
    ]

    if escalation:
        answer_parts.append(f"#### 📈 Escalation Matrix (If SLA is Breached)\n`{escalation}`\n")

    if action:
        answer_parts.append(f"#### 💡 Recommended Next Step\n{action}")

    # Additional secondary citations if multiple docs match
    citations = []
    for d in retrieved_docs[:3]:
        citations.append({
            "id": d.get("id"),
            "topic": d.get("topic"),
            "authority": d.get("authority"),
            "act_or_scheme": d.get("act_or_scheme"),
            "sla_hours": d.get("sla_hours")
        })

    # Actionable suggestions
    suggestions = [
        f"How to escalate if {authority} misses the {sla}h SLA?",
        "What photo evidence is required for faster resolution?",
        "Can I claim compensation under the Sakala Act?"
    ]

    return {
        "answer": "\n".join(answer_parts),
        "category": category,
        "authority": authority,
        "sla_hours": sla,
        "act_or_scheme": act,
        "sources": citations,
        "suggested_actions": suggestions,
        "has_live_tracking": False
    }
