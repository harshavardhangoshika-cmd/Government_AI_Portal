from dotenv import load_dotenv
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()


def _sanitize_secret(val):
    """Strip whitespace and accidental enclosing quotes from secrets."""
    if val is None:
        return None
    val = str(val).strip()
    # Strip accidental single or double quotes entered in TOML or env
    val = val.strip("\"'").strip()
    return val if val else None


def get_credentials():
    """
    Ultra-resilient credentials loader for Supabase.
    Checks environment variables and Streamlit Cloud secrets in all common casing
    and table formats (e.g. SUPABASE_URL, supabase_url, [supabase] section).
    """
    url = None
    key = None

    # 1. Check Streamlit Secrets (highest priority for Streamlit Cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            # Check direct keys (case variations)
            for k in ("SUPABASE_URL", "supabase_url", "SUPABASE_PROJECT_URL", "NEXT_PUBLIC_SUPABASE_URL"):
                if k in st.secrets:
                    url = _sanitize_secret(st.secrets[k])
                    if url:
                        break

            for k in ("SUPABASE_KEY", "supabase_key", "SUPABASE_ANON_KEY", "supabase_anon_key", "SUPABASE_API_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY"):
                if k in st.secrets:
                    key = _sanitize_secret(st.secrets[k])
                    if key:
                        break

            # Check nested table e.g. [supabase] url = "...", key = "..."
            if not url or not key:
                if "supabase" in st.secrets:
                    sub = st.secrets["supabase"]
                    if hasattr(sub, "get") or isinstance(sub, dict):
                        if not url:
                            for uk in ("url", "URL", "SUPABASE_URL", "supabase_url"):
                                if uk in sub:
                                    url = _sanitize_secret(sub[uk])
                                    if url:
                                        break
                        if not key:
                            for kk in ("key", "KEY", "anon_key", "SUPABASE_KEY", "supabase_key"):
                                if kk in sub:
                                    key = _sanitize_secret(sub[kk])
                                    if key:
                                        break
    except Exception:
        pass

    # 2. Check Environment Variables (priority for local development & Docker/FastAPI)
    if not url:
        for env_k in ("SUPABASE_URL", "supabase_url", "SUPABASE_PROJECT_URL", "NEXT_PUBLIC_SUPABASE_URL"):
            val = os.getenv(env_k)
            if val:
                url = _sanitize_secret(val)
                if url:
                    break

    if not key:
        for env_k in ("SUPABASE_KEY", "supabase_key", "SUPABASE_ANON_KEY", "supabase_anon_key", "SUPABASE_API_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY"):
            val = os.getenv(env_k)
            if val:
                key = _sanitize_secret(val)
                if key:
                    break

    return url, key


# Module-level cached variables for backward compatibility
SUPABASE_URL, SUPABASE_KEY = get_credentials()

if SUPABASE_URL and SUPABASE_KEY:
    print("[OK] Supabase credentials loaded successfully.")
else:
    print("[WARN] SUPABASE_URL or SUPABASE_KEY not configured. Portal will run in offline draft storage mode.")
