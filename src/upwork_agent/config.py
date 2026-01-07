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

def parse_gcp_json(json_str: str) -> dict:
    """Parse Google service account JSON string into dict."""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid Google service account JSON: {e}")
