import json
import os
from typing import Optional
import streamlit as st
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Load from environment or Streamlit secrets."""
    
    gemini_api_key: Optional[str] = None
    google_service_account_json: Optional[str] = None
    streamlit_cloud: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

def load_secrets() -> tuple[Optional[str], Optional[str]]:
    """
    Load secrets from Streamlit Cloud or local .env.
    Returns: (gemini_api_key, google_service_account_json)
    """
    try:
        # Try Streamlit secrets (Cloud deployment)
        gemini_key = st.secrets.get("GEMINI_API_KEY")
        gcp_json = st.secrets.get("GOOGLE_SERVICE_ACCOUNT_JSON")
        return gemini_key, gcp_json
    except Exception:
        # Fallback to environment variables (local dev)
        gemini_key = os.getenv("GEMINI_API_KEY")
        gcp_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        return gemini_key, gcp_json

def init_session_state():
    """Initialize all session state variables with defaults."""
    defaults = {
        "generating": False,
        "current_proposal": None,
        "job_analysis": None,
        "slide_deck": None,
        "cover_letter": None,
        "screening_answers": None,
        "error_message": None,
        "api_call_count": 0,
        "last_api_call": None,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def rate_limit_check(max_calls_per_minute: int = 10) -> bool:
    """Check if user is rate limited."""
    import time
    
    current_time = time.time()
    last_call = st.session_state.get("last_api_call", 0)
    call_count = st.session_state.get("api_call_count", 0)
    
    # Reset counter if more than a minute has passed
    if current_time - last_call > 60:
        st.session_state.api_call_count = 0
        return False
    
    # Check if over limit
    if call_count >= max_calls_per_minute:
        return True
    
    return False

def update_api_call_stats():
    """Update API call statistics."""
    import time
    st.session_state.api_call_count += 1
    st.session_state.last_api_call = time.time()

def cleanup_session_state():
    """Clean up large objects from session state to prevent memory leaks."""
    # Keep only essential data
    essential_keys = ["generating", "api_call_count", "last_api_call", "error_message"]
    
    for key in list(st.session_state.keys()):
        if key not in essential_keys and key.startswith("temp_"):
            del st.session_state[key]
