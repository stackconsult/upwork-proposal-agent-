from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from upwork_agent.config import parse_gcp_json
from upwork_agent.errors import AuthenticationError

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
        creds_dict = parse_gcp_json(service_account_json)
        credentials = Credentials.from_service_account_info(
            creds_dict,
            scopes=SCOPES
        )
        return build("slides", "v1", credentials=credentials)
    except Exception as e:
        raise AuthenticationError(f"Failed to authenticate Slides API: {e}")

def get_authenticated_drive_service(service_account_json: str):
    """
    Build authenticated Google Drive API client.
    Args:
        service_account_json: JSON string of service account credentials
    """
    try:
        creds_dict = parse_gcp_json(service_account_json)
        credentials = Credentials.from_service_account_info(
            creds_dict,
            scopes=SCOPES
        )
        return build("drive", "v3", credentials=credentials)
    except Exception as e:
        raise AuthenticationError(f"Failed to authenticate Drive API: {e}")
