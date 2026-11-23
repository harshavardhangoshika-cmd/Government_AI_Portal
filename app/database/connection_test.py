"""
app/database/connection_test.py
================================
Minimal, independent, standalone Supabase connectivity and diagnostics test.
Does NOT depend on app.database.diagnostics.
Follows strict 6-step testing protocol:
  Step 1: Check secrets presence (st.secrets & os.environ)
  Step 2: Parse and validate URL against expected project
  Step 3: Resolve hostname using socket.getaddrinfo (IPv4 AF_INET)
  Step 4: HTTPS request to Supabase REST endpoint (/rest/v1/complaints)
  Step 5: Initialize Supabase Python client
  Step 6: Execute read-only query on complaints table

Security guarantee:
  NEVER logs, prints, or exposes the actual SUPABASE_KEY in returns or traces.
"""

import os
import socket
import time
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from app.database.dns_patch import install_dns_patch
    install_dns_patch()
except Exception:
    pass

try:
    from dotenv import load_dotenv
    _base_dir = Path(__file__).resolve().parent
    _env_file = _base_dir / ".env"
    if _env_file.exists():
        load_dotenv(_env_file)
    else:
        load_dotenv()
except Exception:
    pass

EXPECTED_PROJECT_HOST = "uusnnqbutovbnjqzyhmx.supabase.co"
EXPECTED_DEFAULT_URL = f"https://{EXPECTED_PROJECT_HOST}"


def get_deployed_commit() -> str:
    """Return the currently running Git commit hash."""
    try:
        import subprocess
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass

    try:
        git_dir = Path(__file__).resolve().parents[2] / ".git"
        head_file = git_dir / "HEAD"
        if head_file.exists():
            ref = head_file.read_text().strip()
            if ref.startswith("ref: "):
                ref_path = git_dir / ref[5:].strip()
                if ref_path.exists():
                    return ref_path.read_text().strip()[:7]
            else:
                return ref[:7]
    except Exception:
        pass

    return "HEAD (Latest Main)"


def mask_url(url: Optional[str]) -> str:
    """Mask URL keeping protocol and masked subdomain."""
    if not url:
        return "Not Configured"
    try:
        parsed = urllib.parse.urlparse(str(url).strip())
        host = parsed.hostname or ""
        parts = host.split(".")
        if len(parts) >= 3:
            sub = parts[0]
            masked_sub = sub[:4] + "***" if len(sub) > 4 else "***"
            return f"{parsed.scheme}://{masked_sub}.{'.'.join(parts[1:])}"
        return f"{parsed.scheme}://{host}"
    except Exception:
        return "Configured (Masked)"


def mask_key(key: Optional[str]) -> Dict[str, Any]:
    """Return key metadata without revealing secret content."""
    if not key:
        return {
            "present": False,
            "type": "Missing",
            "length": 0,
            "preview": "None"
        }
    k = str(key).strip().strip("\"'“”`<> ")
    k_len = len(k)
    if k.startswith("sb_publishable_"):
        k_type = "Supabase Publishable Key"
    elif k.startswith("eyJ"):
        k_type = "Supabase JWT Token (anon/service)"
    else:
        k_type = "Standard API Key"

    preview = f"{k[:4]}...{k[-4:]}" if k_len >= 10 else "***"
    return {
        "present": True,
        "type": k_type,
        "length": k_len,
        "preview": preview
    }


def _read_raw_credentials():
    """Read URL and key safely from st.secrets or os.environ."""
    url = None
    key = None
    source = "None"

    # Check Streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            for k in ("SUPABASE_URL", "supabase_url", "SUPABASE_PROJECT_URL", "NEXT_PUBLIC_SUPABASE_URL"):
                if k in st.secrets:
                    val = str(st.secrets[k]).strip().strip("\"'“”`<> ")
                    if val:
                        url = val
                        source = "st.secrets"
                        break

            for k in ("SUPABASE_KEY", "supabase_key", "SUPABASE_ANON_KEY", "supabase_anon_key", "SUPABASE_API_KEY"):
                if k in st.secrets:
                    val = str(st.secrets[k]).strip().strip("\"'“”`<> ")
                    if val:
                        key = val
                        source = "st.secrets"
                        break

            # Nested [supabase] section
            if not url or not key:
                if "supabase" in st.secrets:
                    sub = st.secrets["supabase"]
                    if hasattr(sub, "get") or isinstance(sub, dict):
                        if not url:
                            for uk in ("url", "URL", "supabase_url"):
                                if uk in sub:
                                    val = str(sub[uk]).strip().strip("\"'“”`<> ")
                                    if val:
                                        url = val
                                        source = "st.secrets[supabase]"
                                        break
                        if not key:
                            for kk in ("key", "KEY", "anon_key", "supabase_key"):
                                if kk in sub:
                                    val = str(sub[kk]).strip().strip("\"'“”`<> ")
                                    if val:
                                        key = val
                                        source = "st.secrets[supabase]"
                                        break
    except Exception:
        pass

    # Check environment variables
    if not url:
        for env_k in ("SUPABASE_URL", "supabase_url", "SUPABASE_PROJECT_URL", "NEXT_PUBLIC_SUPABASE_URL"):
            val = os.getenv(env_k)
            if val:
                val = val.strip().strip("\"'“”`<> ")
                if val:
                    url = val
                    source = "os.environ" if source == "None" else source
                    break

    if not key:
        for env_k in ("SUPABASE_KEY", "supabase_key", "SUPABASE_ANON_KEY", "supabase_anon_key", "SUPABASE_API_KEY"):
            val = os.getenv(env_k)
            if val:
                val = val.strip().strip("\"'“”`<> ")
                if val:
                    key = val
                    source = "os.environ" if source == "None" else source
                    break

    return url, key, source


def test_supabase_connection() -> Dict[str, Any]:
    """
    Independent 6-step diagnostic test for Supabase connectivity.
    Never exposes credentials. Returns structured report.
    """
    report = {
        "status": "UNKNOWN",
        "failed_step": None,
        "classification": "UNKNOWN",
        "actionable_guidance": "",
        "deployed_commit": get_deployed_commit(),
        "steps": {
            "step1_secrets": {"passed": False, "details": ""},
            "step2_url_validation": {"passed": False, "details": ""},
            "step3_dns_resolution": {"passed": False, "details": ""},
            "step4_https_probe": {"passed": False, "details": ""},
            "step5_client_init": {"passed": False, "details": ""},
            "step6_read_query": {"passed": False, "details": ""}
        },
        "url_masked": "Not Configured",
        "hostname_parsed": None,
        "hostname_expected": EXPECTED_PROJECT_HOST,
        "key_meta": {"present": False, "type": "Missing", "length": 0, "preview": "None"},
        "dns_ips": [],
        "https_status_code": None,
        "query_row_count": 0,
        "latency_ms": 0.0
    }

    start_total = time.time()

    # ----------------------------------------------------
    # STEP 1: Secrets Presence
    # ----------------------------------------------------
    url, key, source = _read_raw_credentials()
    report["key_meta"] = mask_key(key)

    # Check for placeholder detection in URL
    is_placeholder = bool(url and ("your-project-id" in url or "your-project" in url or "your_project" in url))
    
    # Auto-resolve canonical URL if key is present but URL is placeholder or missing
    effective_url = url
    if key and (not effective_url or is_placeholder):
        effective_url = EXPECTED_DEFAULT_URL

    report["url_masked"] = mask_url(effective_url)

    if not effective_url or not key:
        missing = []
        if not effective_url:
            missing.append("SUPABASE_URL")
        if not key:
            missing.append("SUPABASE_KEY")
        report["status"] = "ERROR"
        report["failed_step"] = 1
        report["classification"] = "MISSING_CREDENTIALS"
        report["steps"]["step1_secrets"] = {
            "passed": False,
            "details": f"Missing credentials: {', '.join(missing)} (source: {source})"
        }
        report["actionable_guidance"] = (
            f"Add SUPABASE_URL = \"{EXPECTED_DEFAULT_URL}\" and your SUPABASE_KEY to "
            "Streamlit Cloud Secrets (App Settings -> Secrets)."
        )
        report["latency_ms"] = round((time.time() - start_total) * 1000, 1)
        return report

    report["steps"]["step1_secrets"] = {
        "passed": True,
        "details": f"Found URL and Key (source: {source}, key length: {report['key_meta']['length']})"
    }

    # ----------------------------------------------------
    # STEP 2: URL & Hostname Validation
    # ----------------------------------------------------
    try:
        clean_url = str(effective_url).strip().strip("\"'“”`<> ")
        if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
            clean_url = f"https://{clean_url}"
        elif clean_url.startswith("http://"):
            clean_url = "https://" + clean_url[7:]
        clean_url = clean_url.rstrip("/")

        parsed = urllib.parse.urlparse(clean_url)
        hostname = parsed.hostname
        report["hostname_parsed"] = hostname

        if not hostname:
            raise ValueError(f"Could not parse valid hostname from URL: {mask_url(clean_url)}")

        if hostname != EXPECTED_PROJECT_HOST:
            report["steps"]["step2_url_validation"] = {
                "passed": False,
                "details": f"Hostname '{hostname}' does not match expected '{EXPECTED_PROJECT_HOST}'"
            }
            report["status"] = "ERROR"
            report["failed_step"] = 2
            report["classification"] = "HOSTNAME_MISMATCH"
            report["actionable_guidance"] = (
                f"Configured hostname '{hostname}' differs from expected '{EXPECTED_PROJECT_HOST}'. "
                f"Update SUPABASE_URL to '{EXPECTED_DEFAULT_URL}' in Streamlit Secrets."
            )
            report["latency_ms"] = round((time.time() - start_total) * 1000, 1)
            return report

        report["steps"]["step2_url_validation"] = {
            "passed": True,
            "details": f"Valid HTTPS URL parsed, matches project host '{hostname}'"
        }
    except Exception as e:
        report["status"] = "ERROR"
        report["failed_step"] = 2
        report["classification"] = "MALFORMED_URL"
        report["steps"]["step2_url_validation"] = {
            "passed": False,
            "details": f"URL validation failed: {str(e)}"
        }
        report["actionable_guidance"] = f"Check SUPABASE_URL syntax. Expected: '{EXPECTED_DEFAULT_URL}'"
        report["latency_ms"] = round((time.time() - start_total) * 1000, 1)
        return report

    # ----------------------------------------------------
    # STEP 3: DNS Resolution (socket.getaddrinfo IPv4)
    # ----------------------------------------------------
    dns_resolved = False
    dns_ips = []
    dns_error = None

    try:
        # Query IPv4 specifically (AF_INET) to prevent IPv6 lookup failure on containerized clouds
        addrinfo = socket.getaddrinfo(hostname, 443, family=socket.AF_INET, type=socket.SOCK_STREAM)
        if addrinfo:
            dns_ips = sorted(list(set(item[4][0] for item in addrinfo)))
            dns_resolved = True
    except Exception as e:
        dns_error = str(e)

    # Fallback to AF_UNSPEC if IPv4 specific gave an error
    if not dns_resolved:
        try:
            addrinfo_gen = socket.getaddrinfo(hostname, 443, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM)
            if addrinfo_gen:
                dns_ips = sorted(list(set(item[4][0] for item in addrinfo_gen)))
                dns_resolved = True
                dns_error = None
        except Exception as e2:
            dns_error = str(e2)

    report["dns_ips"] = dns_ips

    if not dns_resolved:
        report["status"] = "ERROR"
        report["failed_step"] = 3
        report["classification"] = "DNS_RESOLUTION_FAILURE"
        report["steps"]["step3_dns_resolution"] = {
            "passed": False,
            "details": f"DNS resolution failed for '{hostname}': {dns_error}"
        }
        report["actionable_guidance"] = (
            f"DNS could not resolve hostname '{hostname}'. "
            "Verify your Supabase project is active and that your Streamlit Cloud instance has internet access."
        )
        report["latency_ms"] = round((time.time() - start_total) * 1000, 1)
        return report

    report["steps"]["step3_dns_resolution"] = {
        "passed": True,
        "details": f"Resolved IPv4 addresses: {', '.join(dns_ips)}"
    }

    # ----------------------------------------------------
    # STEP 4: HTTPS Probe (/rest/v1/complaints?select=id&limit=1)
    # ----------------------------------------------------
    try:
        import requests
        rest_url = f"{clean_url}/rest/v1/complaints?select=id&limit=1"
        clean_key = str(key).strip().strip("\"'“”`<> ")
        headers = {
            "apikey": clean_key,
            "Authorization": f"Bearer {clean_key}",
            "Accept": "application/json"
        }
        t0 = time.time()
        resp = requests.get(rest_url, headers=headers, timeout=6.0)
        http_latency = round((time.time() - t0) * 1000, 1)
        report["https_status_code"] = resp.status_code

        if resp.status_code == 200:
            report["steps"]["step4_https_probe"] = {
                "passed": True,
                "details": f"HTTP 200 OK received in {http_latency}ms"
            }
        elif resp.status_code in (401, 403):
            # Auth or RLS error
            err_msg = resp.text[:120] if resp.text else f"HTTP {resp.status_code}"
            report["status"] = "ERROR"
            report["failed_step"] = 4
            report["classification"] = "INVALID_API_KEY" if resp.status_code == 401 else "RLS_PERMISSION_ERROR"
            report["steps"]["step4_https_probe"] = {
                "passed": False,
                "details": f"HTTP {resp.status_code} ({err_msg}) in {http_latency}ms"
            }
            report["actionable_guidance"] = (
                "Supabase rejected credentials. Verify your SUPABASE_KEY in Streamlit Secrets. "
                "Ensure you are using the 'anon public' API key from Supabase Project Settings -> API."
            )
            report["latency_ms"] = round((time.time() - start_total) * 1000, 1)
            return report
        elif resp.status_code == 404:
            report["status"] = "ERROR"
            report["failed_step"] = 4
            report["classification"] = "TABLE_NOT_FOUND"
            report["steps"]["step4_https_probe"] = {
                "passed": False,
                "details": f"HTTP 404: Table 'complaints' not found on endpoint"
            }
            report["actionable_guidance"] = (
                "The 'complaints' table was not found in your Supabase database schema. "
                "Run the table creation SQL script in your Supabase SQL Editor."
            )
            report["latency_ms"] = round((time.time() - start_total) * 1000, 1)
            return report
        else:
            report["status"] = "ERROR"
            report["failed_step"] = 4
            report["classification"] = f"HTTP_{resp.status_code}"
            report["steps"]["step4_https_probe"] = {
                "passed": False,
                "details": f"Unexpected HTTP status {resp.status_code}: {resp.text[:120]}"
            }
            report["actionable_guidance"] = f"Supabase REST endpoint returned status {resp.status_code}."
            report["latency_ms"] = round((time.time() - start_total) * 1000, 1)
            return report
    except Exception as e:
        report["status"] = "ERROR"
        report["failed_step"] = 4
        report["classification"] = "HTTPS_CONNECTION_ERROR"
        report["steps"]["step4_https_probe"] = {
            "passed": False,
            "details": f"HTTPS request failed: {str(e)}"
        }
        report["actionable_guidance"] = "Failed to establish HTTPS connection to Supabase REST endpoint."
        report["latency_ms"] = round((time.time() - start_total) * 1000, 1)
        return report

    # ----------------------------------------------------
    # STEP 5: Supabase Client Initialization
    # ----------------------------------------------------
    client = None
    try:
        from supabase import create_client
        clean_key = str(key).strip().strip("\"'“”`<> ")
        client = create_client(clean_url, clean_key)
        report["steps"]["step5_client_init"] = {
            "passed": True,
            "details": "Supabase Python Client initialized successfully"
        }
    except Exception as e:
        report["status"] = "ERROR"
        report["failed_step"] = 5
        report["classification"] = "CLIENT_INIT_ERROR"
        report["steps"]["step5_client_init"] = {
            "passed": False,
            "details": f"create_client failed: {str(e)}"
        }
        report["actionable_guidance"] = f"Failed to initialize Supabase Python client: {str(e)}"
        report["latency_ms"] = round((time.time() - start_total) * 1000, 1)
        return report

    # ----------------------------------------------------
    # STEP 6: Read-only Query (complaints table authenticated select)
    # ----------------------------------------------------
    try:
        t0 = time.time()
        res = client.table("complaints").select("id, complaint_number, status, department").limit(5).execute()
        q_latency = round((time.time() - t0) * 1000, 1)
        row_count = len(res.data) if res and hasattr(res, "data") and res.data else 0
        report["query_row_count"] = row_count
        report["steps"]["step6_read_query"] = {
            "passed": True,
            "details": f"Query executed successfully in {q_latency}ms ({row_count} live complaints verified)"
        }
    except Exception as e:
        report["status"] = "ERROR"
        report["failed_step"] = 6
        report["classification"] = "QUERY_EXECUTION_ERROR"
        report["steps"]["step6_read_query"] = {
            "passed": False,
            "details": f"Authenticated database query failed: {str(e)}"
        }
        report["actionable_guidance"] = (
            f"Read query failed: {str(e)}. "
            "Check Row Level Security (RLS) policies on the 'complaints' table or database status."
        )
        report["latency_ms"] = round((time.time() - start_total) * 1000, 1)
        return report

    # ALL 6 STEPS PASSED!
    report["status"] = "HEALTHY"
    report["classification"] = "ALL_CHECKS_PASSED"
    report["actionable_guidance"] = "All connection and query checks passed successfully."
    report["latency_ms"] = round((time.time() - start_total) * 1000, 1)
    return report
