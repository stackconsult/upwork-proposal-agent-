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
    if not json_str:
        raise ValueError("Service account JSON is empty or None")
    
    try:
        # Handle case where it might be a dict already
        if isinstance(json_str, dict):
            return json_str
            
        # Try to parse as JSON
        creds = json.loads(json_str)
        
        # Validate required fields
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        return creds
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in service account credentials: {e}")
