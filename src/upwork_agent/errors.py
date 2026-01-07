class UpworkAgentError(Exception):
    """Base exception."""
    pass

class AuthenticationError(UpworkAgentError):
    pass

class GeminiClientError(UpworkAgentError):
    pass

class SlidesRenderError(UpworkAgentError):
    pass

class PdfExportError(UpworkAgentError):
    pass

class DatabaseError(UpworkAgentError):
    pass
