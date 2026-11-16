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

# Priority 2: Streamlit Secrets (for Streamlit Community Cloud)
if not SUPABASE_URL or not SUPABASE_KEY:
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "SUPABASE_URL" in st.secrets:
                SUPABASE_URL = str(st.secrets["SUPABASE_URL"])
            if "SUPABASE_KEY" in st.secrets:
                SUPABASE_KEY = str(st.secrets["SUPABASE_KEY"])
    except Exception:
        pass

if SUPABASE_URL and SUPABASE_KEY:
    print("[OK] Supabase credentials loaded successfully.")
else:
    print("[WARN] SUPABASE_URL or SUPABASE_KEY not configured. Portal will run in offline draft storage mode.")
