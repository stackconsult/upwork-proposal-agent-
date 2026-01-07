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

def parse_gcp_credentials(credentials_str: str, project_id: str = None, client_email: str = None) -> dict:
    """Parse Google service account credentials - accepts either JSON string or private key + additional fields."""
    if not credentials_str:
        raise ValueError("Service account credentials are empty or None")
    
    try:
        # Handle case where it might be a dict already
        if isinstance(credentials_str, dict):
            return credentials_str
            
        # Check if it's just a private key (single line or multi-line)
        if '-----BEGIN PRIVATE KEY-----' in credentials_str or '-----BEGIN RSA PRIVATE KEY-----' in credentials_str:
            # This is just the private key - we need additional fields
            if not project_id or not client_email:
                raise ValueError("Private key detected. Please provide Project ID and Client Email fields when using a private key.")
            
            # Construct full service account JSON
            creds = {
                "type": "service_account",
                "project_id": project_id,
                "private_key": credentials_str,
                "client_email": client_email,
                "client_id": "",  # Can be empty for basic auth
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
            return creds
        
        # Try to parse as JSON
        creds = json.loads(credentials_str)
        
        # Validate required fields
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        return creds
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in service account credentials: {e}")
