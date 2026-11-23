import os
import socket
import urllib.parse
import requests
from app.database.config import get_credentials, PROJECT_EXPECTED_HOST, PROJECT_DEFAULT_URL

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
    Tests:
      1. Secret presence (SUPABASE_URL and SUPABASE_KEY).
      2. Hostname parsing & comparison against expected project hostname.
      3. DNS resolution via socket.getaddrinfo() (IPv4 and AF_UNSPEC).
      4. HTTPS reachability to the Supabase REST endpoint.
      5. Supabase client initialization.
      6. A read-only query on the 'complaints' table.
    
    NEVER logs, prints, or returns actual secrets.
    """
    # Raw credentials check directly from Streamlit secrets / env before fallback
    raw_secrets_url = None
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            for k in ("SUPABASE_URL", "supabase_url", "SUPABASE_PROJECT_URL"):
                if k in st.secrets:
                    raw_secrets_url = str(st.secrets[k]).strip()
                    break
    except Exception:
        pass

    url, key = get_credentials()
    
    # Extract parsed hostname
    parsed_hostname = None
    if url:
        try:
            parsed = urllib.parse.urlparse(url)
            parsed_hostname = parsed.hostname
        except Exception:
            parsed_hostname = None

    hostname_matches = (parsed_hostname == PROJECT_EXPECTED_HOST)
    is_placeholder = bool(raw_secrets_url and ("your-project-id" in raw_secrets_url or "your-project" in raw_secrets_url))

    report = {
        "status": "UNKNOWN",
        "url_present": bool(url),
        "url_masked": mask_supabase_url(url),
        "hostname_parsed": parsed_hostname or "None",
        "hostname_expected": PROJECT_EXPECTED_HOST,
        "hostname_matches_expected": hostname_matches,
        "is_placeholder_url": is_placeholder,
        "key_present": bool(key),
        "key_meta": get_key_metadata(key),
        "dns_resolved": False,
        "dns_ipv4_ips": [],
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
    
    # 1. Credentials Presence Check
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
            f"Add SUPABASE_URL ('{PROJECT_DEFAULT_URL}') and SUPABASE_KEY to your Streamlit Cloud app secrets. "
            "Go to Share.streamlit.io -> App Settings -> Secrets and paste your credentials."
        )
        return report

    # 2. Hostname Validation
    if not parsed_hostname:
        report["status"] = "ERROR"
        report["classification"] = "MALFORMED_URL"
        report["error_message"] = f"Unable to parse valid hostname from configured URL: {url}"
        report["actionable_guidance"] = (
            f"Ensure SUPABASE_URL starts with 'https://' and matches your Supabase project (e.g. '{PROJECT_DEFAULT_URL}')."
        )
        return report

    # 3. DNS Resolution Test via socket.getaddrinfo()
    try:
        # Check IPv4 resolution specifically
        addr_info = socket.getaddrinfo(parsed_hostname, 443, socket.AF_INET, socket.SOCK_STREAM)
        if addr_info:
            report["dns_ipv4_ips"] = sorted(list(set(item[4][0] for item in addr_info)))
            report["dns_resolved"] = True
    except Exception as e:
        report["dns_resolved"] = False
        report["dns_error"] = str(e)

    # Fallback to general getaddrinfo if IPv4 specific failed
    if not report["dns_resolved"]:
        try:
            addr_info_gen = socket.getaddrinfo(parsed_hostname, 443, 0, socket.SOCK_STREAM)
            if addr_info_gen:
                report["dns_ipv4_ips"] = sorted(list(set(item[4][0] for item in addr_info_gen)))
                report["dns_resolved"] = True
                report["dns_error"] = None
        except Exception as e2:
            report["dns_error"] = str(e2)

    if not report["dns_resolved"]:
        report["status"] = "ERROR"
        report["classification"] = "DNS_RESOLUTION_FAILURE"
        report["error_message"] = f"DNS resolution failed for hostname '{parsed_hostname}': {report['dns_error']}"
        
        if is_placeholder:
            report["actionable_guidance"] = (
                f"Your Streamlit Secrets still contain the example template '{raw_secrets_url}'. "
                f"Please update SUPABASE_URL to '{PROJECT_DEFAULT_URL}' in Share.streamlit.io -> App Settings -> Secrets."
            )
        elif not hostname_matches:
            report["actionable_guidance"] = (
                f"Configured hostname '{parsed_hostname}' does not match expected project '{PROJECT_EXPECTED_HOST}'. "
                f"Verify SUPABASE_URL in Streamlit Cloud Secrets."
            )
        else:
            report["actionable_guidance"] = (
                f"DNS lookup failed for '{parsed_hostname}' with error '{report['dns_error']}'. "
                "Verify outbound DNS resolution in your Streamlit Cloud environment or check if Supabase is active."
            )
        return report

    # 4. HTTPS Reachability Test
    try:
        rest_url = f"{url.rstrip('/')}/rest/v1/complaints?select=id&limit=1"
        headers = {"apikey": key, "Authorization": f"Bearer {key}"}
        resp = requests.get(rest_url, headers=headers, timeout=4.5)
        report["https_status"] = resp.status_code
        # 200 is success, 401 is auth issue, 403 is RLS issue, but all mean HTTPS is reachable
        report["https_ok"] = True
    except requests.exceptions.Timeout:
        report["status"] = "ERROR"
        report["classification"] = "NETWORK_TIMEOUT"
        report["https_error"] = "Connection timed out (4.5s)"
        report["error_message"] = "Network timeout attempting to connect to Supabase REST endpoint over HTTPS."
        report["actionable_guidance"] = (
            "The HTTPS connection to Supabase timed out. Check Supabase project status or regional network."
        )
        return report
    except Exception as e:
        report["status"] = "ERROR"
        report["classification"] = "NETWORK_FAILURE"
        report["https_error"] = str(e)
        report["error_message"] = f"HTTPS connection failure: {e}"
        report["actionable_guidance"] = (
            f"Failed to establish an HTTPS connection to '{parsed_hostname}': {e}."
        )
        return report

    # 5. Client Initialization & Read Query
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
        report["actionable_guidance"] = "Supabase connection is fully operational and complaints table is readable."
        return report
    except Exception as e:
        err_str = str(e)
        # Scrub secret key from error string if present
        if key and key in err_str:
            err_str = err_str.replace(key, "[REDACTED]")
            
        report["status"] = "ERROR"
        report["error_message"] = err_str
        
        # Classify the exception clearly
        if "401" in err_str or "JWSError" in err_str or "Invalid API key" in err_str or "invalid JWT" in err_str:
            report["classification"] = "AUTH_INVALID_KEY"
            report["actionable_guidance"] = (
                "Supabase rejected your SUPABASE_KEY (HTTP 401 Unauthorized). "
                "Verify in Supabase Dashboard -> Project Settings -> API that you copied "
                "the active anon/public key or publishable key without extra quotes or spaces."
            )
        elif "403" in err_str or "42501" in err_str or "permission denied" in err_str.lower():
            report["classification"] = "RLS_PERMISSION_DENIED"
            report["actionable_guidance"] = (
                "Row Level Security (RLS) is enabled on the 'complaints' table and does not "
                "allow SELECT for the anon role. Add policy: "
                "CREATE POLICY \"Allow anon read\" ON complaints FOR SELECT USING (true);"
            )
        elif "404" in err_str or "42P01" in err_str or "does not exist" in err_str.lower():
            report["classification"] = "TABLE_NOT_FOUND"
            report["actionable_guidance"] = (
                "The table 'complaints' was not found in the Supabase database. "
                "Verify table schema or run the migration script in the Supabase SQL editor."
            )
        elif "Errno -2" in err_str or "Name or service not known" in err_str or "getaddrinfo" in err_str:
            report["classification"] = "DNS_RESOLUTION_FAILURE"
            report["actionable_guidance"] = (
                f"PostgREST query failed with DNS resolution error ([Errno -2] Name or service not known). "
                f"Verify that SUPABASE_URL in Streamlit Secrets exactly matches '{PROJECT_DEFAULT_URL}'."
            )
        else:
            report["classification"] = f"QUERY_ERROR_{type(e).__name__}"
            report["actionable_guidance"] = (
                f"Supabase query failed with exception {type(e).__name__}: {err_str}."
            )
            
        return report
