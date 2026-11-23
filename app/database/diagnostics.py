import os
import socket
import urllib.parse
import requests
from app.database.config import get_credentials

def mask_supabase_url(url: str) -> str:
    """Safely mask Supabase URL for diagnostics without exposing full project ID."""
    if not url:
        return "Not Configured"
    try:
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or ""
        parts = host.split(".")
        if len(parts) >= 3:
            subdomain = parts[0]
            masked_sub = subdomain[:4] + "***" if len(subdomain) > 4 else "***"
            masked_host = f"{masked_sub}.{'.'.join(parts[1:])}"
            return f"{parsed.scheme}://{masked_host}"
        return f"{parsed.scheme}://***.{host}"
    except Exception:
        return "Configured (Masked)"


def get_key_metadata(key: str) -> dict:
    """Safely analyze key characteristics without revealing key content."""
    if not key:
        return {"present": False, "type": "Missing", "length": 0}
    
    key_clean = key.strip()
    if key_clean.startswith("sb_publishable_"):
        k_type = "Supabase Publishable Key (sb_publishable_...)"
    elif key_clean.startswith("eyJ"):
        k_type = "Supabase JWT Token (anon/service)"
    else:
        k_type = "Custom API Key"
        
    return {
        "present": True,
        "type": k_type,
        "length": len(key_clean)
    }


def run_supabase_diagnostic() -> dict:
    """
    Comprehensive, non-destructive, safe diagnostic of the Supabase connection.
    Tests credentials presence, DNS resolution, HTTPS reachability, and
    executes a single read-only test query on the 'complaints' table.
    
    NEVER logs, prints, or returns actual secrets.
    """
    url, key = get_credentials()
    
    report = {
        "status": "UNKNOWN",
        "url_present": bool(url),
        "url_masked": mask_supabase_url(url),
        "key_present": bool(key),
        "key_meta": get_key_metadata(key),
        "dns_resolved": False,
        "dns_ip": None,
        "dns_error": None,
        "https_ok": False,
        "https_status": None,
        "https_error": None,
        "client_initialized": False,
        "query_ok": False,
        "complaint_count": 0,
        "classification": None,
        "actionable_guidance": None,
        "error_message": None
    }
    
    # 1. Credentials Presence
    if not url or not key:
        missing = []
        if not url:
            missing.append("SUPABASE_URL")
        if not key:
            missing.append("SUPABASE_KEY")
        report["status"] = "ERROR"
        report["classification"] = "MISSING_CREDENTIALS"
        report["error_message"] = f"Missing required secrets: {', '.join(missing)}"
        report["actionable_guidance"] = (
            "Add SUPABASE_URL and SUPABASE_KEY to your Streamlit Cloud app secrets. "
            "Go to Share.streamlit.io -> App Settings -> Secrets and paste your credentials."
        )
        return report

    # 2. DNS Resolution
    hostname = None
    try:
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            raise ValueError(f"Invalid URL structure: {url}")
        
        addr_info = socket.getaddrinfo(hostname, 443, socket.AF_UNSPEC, socket.SOCK_STREAM)
        if addr_info:
            report["dns_resolved"] = True
            report["dns_ip"] = addr_info[0][4][0]
    except Exception as e:
        report["status"] = "ERROR"
        report["classification"] = "DNS_RESOLUTION_FAILURE"
        report["dns_error"] = str(e)
        report["error_message"] = f"Cannot resolve Supabase hostname: {e}"
        report["actionable_guidance"] = (
            f"DNS lookup failed for hostname '{hostname}'. Verify that SUPABASE_URL "
            "is typed correctly and that your Supabase project is active (not paused)."
        )
        return report

    # 3. HTTPS Reachability
    try:
        rest_url = f"{url.rstrip('/')}/rest/v1/complaints?select=id&limit=1"
        headers = {"apikey": key, "Authorization": f"Bearer {key}"}
        resp = requests.get(rest_url, headers=headers, timeout=4.0)
        report["https_ok"] = True
        report["https_status"] = resp.status_code
    except requests.exceptions.Timeout:
        report["status"] = "ERROR"
        report["classification"] = "NETWORK_TIMEOUT"
        report["https_error"] = "Connection timed out (4.0s)"
        report["error_message"] = "Network timeout attempting to connect to Supabase REST endpoint."
        report["actionable_guidance"] = (
            "The HTTPS connection to Supabase timed out. Check Supabase cloud status or regional network."
        )
        return report
    except Exception as e:
        report["status"] = "ERROR"
        report["classification"] = "NETWORK_FAILURE"
        report["https_error"] = str(e)
        report["error_message"] = f"HTTPS connection failure: {e}"
        report["actionable_guidance"] = (
            "Failed to establish an HTTPS connection to Supabase. Check outbound internet connectivity."
        )
        return report

    # 4. Client Initialization & Read Query
    try:
        from supabase import create_client
        client = create_client(url, key)
        if client is None:
            raise RuntimeError("Failed to create Supabase client instance.")
        report["client_initialized"] = True
        
        # Read-only count query on complaints
        query_res = client.table("complaints").select("id", count="exact").limit(1).execute()
        report["query_ok"] = True
        report["complaint_count"] = query_res.count if query_res.count is not None else len(query_res.data)
        report["status"] = "HEALTHY"
        report["classification"] = "CONNECTED"
        report["actionable_guidance"] = "Supabase connection is fully operational."
        return report
    except Exception as e:
        err_str = str(e)
        # Scrub key from error string if present
        if key and key in err_str:
            err_str = err_str.replace(key, "[REDACTED]")
            
        report["status"] = "ERROR"
        report["error_message"] = err_str
        
        # Classify the exception
        if "401" in err_str or "JWSError" in err_str or "Invalid API key" in err_str or "invalid JWT" in err_str:
            report["classification"] = "AUTH_INVALID_KEY"
            report["actionable_guidance"] = (
                "Supabase rejected your SUPABASE_KEY (HTTP 401 Unauthorized). "
                "Verify in the Supabase Dashboard -> Project Settings -> API that you copied "
                "the active anon/public key or publishable key without extra spaces or quotes."
            )
        elif "403" in err_str or "42501" in err_str or "permission denied" in err_str.lower():
            report["classification"] = "RLS_PERMISSION_DENIED"
            report["actionable_guidance"] = (
                "Row Level Security (RLS) is enabled on the 'complaints' table and does not "
                "allow SELECT for the anon role. Add a policy: "
                "CREATE POLICY \"Allow anon read\" ON complaints FOR SELECT USING (true);"
            )
        elif "404" in err_str or "42P01" in err_str or "does not exist" in err_str.lower():
            report["classification"] = "TABLE_NOT_FOUND"
            report["actionable_guidance"] = (
                "The table 'complaints' was not found in the Supabase database. "
                "Verify table schema or run the migration script in Supabase SQL editor."
            )
        else:
            report["classification"] = f"QUERY_ERROR_{type(e).__name__}"
            report["actionable_guidance"] = (
                f"Supabase query failed with exception {type(e).__name__}. Check database schema and logs."
            )
            
        return report
