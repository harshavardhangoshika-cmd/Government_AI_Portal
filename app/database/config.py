from dotenv import load_dotenv
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()

# Priority 1: Environment Variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_credentials():
    global SUPABASE_URL, SUPABASE_KEY
    # Check Streamlit Cloud Secrets if not loaded from environment
    if not SUPABASE_URL or not SUPABASE_KEY:
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                if "SUPABASE_URL" in st.secrets:
                    SUPABASE_URL = str(st.secrets["SUPABASE_URL"]).strip()
                if "SUPABASE_KEY" in st.secrets:
                    SUPABASE_KEY = str(st.secrets["SUPABASE_KEY"]).strip()
        except Exception:
            pass

    # Fallback to os.getenv in case env was populated later
    if not SUPABASE_URL:
        SUPABASE_URL = os.getenv("SUPABASE_URL")
    if not SUPABASE_KEY:
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    return SUPABASE_URL, SUPABASE_KEY

# Initialize on import
get_credentials()

if SUPABASE_URL and SUPABASE_KEY:
    print("[OK] Supabase credentials loaded successfully.")
else:
    print("[WARN] SUPABASE_URL or SUPABASE_KEY not configured. Portal will run in offline draft storage mode.")
