from googleapiclient.discovery import Resource
from upwork_agent.errors import PdfExportError

def export_slides_to_pdf(presentation_id: str, drive_service: Resource) -> bytes:
    """
    Export Google Slides presentation to PDF.
    Returns PDF as bytes.
    """
    try:
        request = drive_service.files().export_media(
            fileId=presentation_id,
            mimeType="application/pdf"
        )
        pdf_bytes = request.execute()
        return pdf_bytes
    except Exception as e:
        raise PdfExportError(f"Failed to export PDF: {e}")

def cleanup_presentation(presentation_id: str, drive_service: Resource):
    """
    Optional: Delete the temporary Google Slides presentation after PDF export.
    """
    try:
        drive_service.files().delete(fileId=presentation_id).execute()
    except Exception as e:
        print(f"Warning: Could not delete presentation {presentation_id}: {e}")
