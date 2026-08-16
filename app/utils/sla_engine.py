from datetime import datetime, timezone, timedelta


def compute_sla(complaint: dict) -> dict:
    """
    Computes SLA metrics for a complaint dictionary:
    - sla_hours (24 for emergency/urgent/critical, 48 for high, 240 for low, 120 default)
    - due_date (ISO format string)
    - hours_remaining (rounded float)
    - is_overdue (boolean)
    """
    if not isinstance(complaint, dict):
        return complaint

    created_at_str = complaint.get("created_at")
    priority = str(complaint.get("priority") or "medium").strip().lower()
    is_emergency = complaint.get("emergency") in [True, "true", "1", "yes", "Emergency"]

    if is_emergency or priority in ["urgent", "critical"]:
        sla_hours = 24
    elif priority == "high":
        sla_hours = 48
    elif priority == "low":
        sla_hours = 240
    else:
        sla_hours = 120

    created_at = None
    if created_at_str:
        try:
            created_at = datetime.fromisoformat(str(created_at_str).replace('Z', '+00:00'))
        except Exception:
            pass

    now = datetime.now(timezone.utc)
    if created_at:
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        due_date = created_at + timedelta(hours=sla_hours)
        hours_remaining = round((due_date - now).total_seconds() / 3600, 1)
        status = str(complaint.get("status") or "").strip().lower()
        is_overdue = (now > due_date) and (status != "resolved")
    else:
        due_date = None
        hours_remaining = None
        is_overdue = False

    complaint["sla_hours"] = sla_hours
    complaint["due_date"] = due_date.isoformat() if due_date else None
    complaint["hours_remaining"] = hours_remaining
    complaint["is_overdue"] = is_overdue
    return complaint


def enrich_complaints_with_sla(complaints: list) -> list:
    """
    Applies compute_sla to a list of complaint dicts.
    """
    if not complaints:
        return []
    return [compute_sla(dict(c)) for c in complaints]
