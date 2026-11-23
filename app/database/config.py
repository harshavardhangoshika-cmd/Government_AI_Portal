from dotenv import load_dotenv
import os
import urllib.parse
from pathlib import Path

# Install resilient IPv4 DNS resolver hook for Supabase cloud endpoints
try:
    from app.database.dns_patch import install_dns_patch
    install_dns_patch()
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()

# The canonical production Supabase project hostname & default URL
PROJECT_EXPECTED_HOST = "uusnnqbutovbnjqzyhmx.supabase.co"
PROJECT_DEFAULT_URL = f"https://{PROJECT_EXPECTED_HOST}"


def _sanitize_url(val):
    """
    Ultra-resilient URL sanitizer:
    - Strips whitespace, straight/curly quotes, backticks, angle brackets, zero-width chars.
    - Guarantees 'https://' scheme.
    - Extracts pure root origin (strips any accidentally appended path like /rest/v1 or trailing slashes).
    - Detects unconfigured example placeholders ('your-project-id.supabase.co')
      and safely auto-resolves to the project canonical URL.
    - Preserves hostname verification and avoids hardcoded IPs.
    """
    if val is None:
        return None
    val = str(val).strip()
    # Strip accidental straight/curly quotes, backticks, brackets
    val = val.strip("\"'“”`<> ").strip()
    # Remove invisible zero-width and non-breaking space characters
    val = val.replace("\u200b", "").replace("\u00a0", "").replace("\ufeff", "").strip()
    if not val:
        return None

    # Detect example placeholder
    if "your-project-id" in val or "your-project" in val or "your_project" in val:
        print(f"[WARN] Placeholder Supabase URL '{val}' detected in secrets. Auto-resolving to project URL: {PROJECT_DEFAULT_URL}")
        return PROJECT_DEFAULT_URL

    # Ensure valid scheme
    if not val.startswith("http://") and not val.startswith("https://"):
        val = f"https://{val}"
    elif val.startswith("http://"):
        val = "https://" + val[7:]

    # Parse and extract pure root origin (scheme + netloc without path or port)
    try:
        parsed = urllib.parse.urlparse(val)
        host = (parsed.netloc or parsed.path).split("/")[0].strip()
        # If port was included, keep it only if not default 443
        if ":" in host:
            h_parts = host.split(":")
            if h_parts[1] in ("443", "80"):
                host = h_parts[0]
        if host:
            val = f"https://{host}"
        else:
            val = val.rstrip("/")
    except Exception:
        val = val.rstrip("/")

    return val


def _sanitize_key(val):
    """Strip whitespace, zero-width chars, and accidental enclosing quotes from keys."""
    if val is None:
        return None
    val = str(val).strip()
    # Strip accidental straight/curly quotes, backticks, brackets
    val = val.strip("\"'“”`<> ").strip()
    val = val.replace("\u200b", "").replace("\u00a0", "").replace("\ufeff", "").strip()
    return val if val else None


def get_credentials():
    """
    Ultra-resilient credentials loader for Supabase.
    Checks environment variables and Streamlit Cloud secrets in all common casing
    and table formats (e.g. SUPABASE_URL, supabase_url, [supabase] section).
    Falls back safely to the project canonical URL if URL is missing or set to template placeholder.
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
                    url = _sanitize_url(st.secrets[k])
                    if url:
                        break

            for k in ("SUPABASE_KEY", "supabase_key", "SUPABASE_ANON_KEY", "supabase_anon_key", "SUPABASE_API_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY"):
                if k in st.secrets:
                    key = _sanitize_key(st.secrets[k])
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
                                    url = _sanitize_url(sub[uk])
                                    if url:
                                        break
                        if not key:
                            for kk in ("key", "KEY", "anon_key", "SUPABASE_KEY", "supabase_key"):
                                if kk in sub:
                                    key = _sanitize_key(sub[kk])
                                    if key:
                                        break
    except Exception:
        pass

    # 2. Check Environment Variables (priority for local development & Docker/FastAPI)
    if not url:
        for env_k in ("SUPABASE_URL", "supabase_url", "SUPABASE_PROJECT_URL", "NEXT_PUBLIC_SUPABASE_URL"):
            val = os.getenv(env_k)
            if val:
                url = _sanitize_url(val)
                if url:
                    break

    if not key:
        for env_k in ("SUPABASE_KEY", "supabase_key", "SUPABASE_ANON_KEY", "supabase_anon_key", "SUPABASE_API_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY"):
            val = os.getenv(env_k)
            if val:
                key = _sanitize_key(val)
                if key:
                    break

    # 3. Canonical Project URL Fallback:
    # If a valid SUPABASE_KEY was supplied (e.g. in Streamlit Secrets) but SUPABASE_URL
    # was either not provided or was left as a placeholder, fall back to the known project URL.
    if key and not url:
        url = PROJECT_DEFAULT_URL
        print(f"[INFO] Using canonical Supabase Project URL: {url}")

    return url, key


# Module-level cached variables for backward compatibility
SUPABASE_URL, SUPABASE_KEY = get_credentials()

if SUPABASE_URL and SUPABASE_KEY:
    print("[OK] Supabase credentials loaded successfully.")
else:
    print("[WARN] SUPABASE_URL or SUPABASE_KEY not configured. Portal will run in offline draft storage mode.")
