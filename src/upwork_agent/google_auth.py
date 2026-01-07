from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from upwork_agent.config import parse_gcp_json
from upwork_agent.errors import AuthenticationError
import json

SCOPES = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive",
]

def get_authenticated_slides_service(service_account_json: str):
    """
    Build authenticated Google Slides API client.
    Args:
        service_account_json: JSON string of service account credentials
    """
    try:
        # Debug: Print first 50 chars of JSON to verify it's being passed
        print(f"DEBUG: Service account JSON (first 50 chars): {service_account_json[:50] if service_account_json else 'None'}")
        
        creds_dict = parse_gcp_json(service_account_json)
        
        # Debug: Verify required fields exist
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in creds_dict:
                raise AuthenticationError(f"Missing required field '{field}' in service account JSON")
        
        print(f"DEBUG: Service account email: {creds_dict.get('client_email')}")
        print(f"DEBUG: Project ID: {creds_dict.get('project_id')}")
        
        credentials = Credentials.from_service_account_info(
            creds_dict,
            scopes=SCOPES
        )
        
        # Debug: Check if credentials are properly created
        print(f"DEBUG: Credentials created, valid: {credentials.valid}")
        
        service = build("slides", "v1", credentials=credentials)
        print(f"DEBUG: Slides service created successfully")
        return service
        
    except json.JSONDecodeError as e:
        raise AuthenticationError(f"Invalid JSON format in service account credentials: {e}")
    except KeyError as e:
        raise AuthenticationError(f"Missing required field in service account JSON: {e}")
    except Exception as e:
        raise AuthenticationError(f"Failed to authenticate Slides API: {e}")

def get_authenticated_drive_service(service_account_json: str):
    """
    Build authenticated Google Drive API client.
    Args:
        service_account_json: JSON string of service account credentials
    """
    try:
        # Debug: Print first 50 chars of JSON to verify it's being passed
        print(f"DEBUG: Service account JSON (first 50 chars): {service_account_json[:50] if service_account_json else 'None'}")
        
        creds_dict = parse_gcp_json(service_account_json)
        
        # Debug: Verify required fields exist
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in creds_dict:
                raise AuthenticationError(f"Missing required field '{field}' in service account JSON")
        
        print(f"DEBUG: Service account email: {creds_dict.get('client_email')}")
        print(f"DEBUG: Project ID: {creds_dict.get('project_id')}")
        
        credentials = Credentials.from_service_account_info(
            creds_dict,
            scopes=SCOPES
        )
        
        # Debug: Check if credentials are properly created
        print(f"DEBUG: Credentials created, valid: {credentials.valid}")
        
        service = build("drive", "v3", credentials=credentials)
        print(f"DEBUG: Drive service created successfully")
        return service
        
    except json.JSONDecodeError as e:
        raise AuthenticationError(f"Invalid JSON format in service account credentials: {e}")
    except KeyError as e:
        raise AuthenticationError(f"Missing required field in service account JSON: {e}")
    except Exception as e:
        raise AuthenticationError(f"Failed to authenticate Drive API: {e}")
