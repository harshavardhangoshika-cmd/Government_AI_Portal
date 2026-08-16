import requests


# ============================================================
# FASTAPI ENDPOINTS
# ============================================================

API_URL = "http://127.0.0.1:8000"


# ============================================================
# SUBMIT COMPLAINT
# ============================================================

def submit_complaint(text, state="Karnataka", district="Bengaluru Urban"):
    """
    Send a citizen complaint to FastAPI with location details.
    """

    try:

        response = requests.post(
            f"{API_URL}/predict",
            json={
                "text": text,
                "state": state,
                "district": district
            },
            timeout=30
        )

        # Raise an exception for HTTP errors
        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Unable to connect to Government Backend: {e}"
        }

    except ValueError:

        return {
            "error": "Invalid response received from Government Backend."
        }


# ============================================================
# TRACK COMPLAINT
# ============================================================

def track_complaint(complaint_number):
    """
    Retrieve complaint information using Complaint ID.
    """

    try:

        response = requests.get(
            f"{API_URL}/track/{complaint_number}",
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Unable to connect to Government Backend: {e}"
        }

    except ValueError:

        return {
            "error": "Invalid response received from Government Backend."
        }


# ============================================================
# UPDATE COMPLAINT STATUS
# ============================================================

def update_complaint_status(complaint_number, status, assigned_officer=None, officer_remarks=None, department=None, priority=None):
    """
    Update complaint status, assigned officer, remarks, department, and priority.
    """
    try:
        response = requests.post(
            f"{API_URL}/government/update-status",
            json={
                "complaint_number": complaint_number,
                "status": status,
                "assigned_officer": assigned_officer,
                "officer_remarks": officer_remarks,
                "department": department,
                "priority": priority
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Unable to update complaint status: {e}"
        }
    except ValueError:
        return {
            "error": "Invalid response received from Government Backend."
        }