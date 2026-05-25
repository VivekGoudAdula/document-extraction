class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InvalidFileTypeError(AppException):
    def __init__(self, message: str = "Unsupported file type. Allowed: PDF, PNG, JPG, JPEG."):
        super().__init__(message, status_code=400)


class DocumentExtractionError(AppException):
    def __init__(self, message: str = "Failed to extract text from document."):
        super().__init__(message, status_code=422)


class OpenAIProviderError(AppException):
    def __init__(self, message: str = "OpenAI API request failed."):
        super().__init__(message, status_code=502)


class DatabaseError(AppException):
    def __init__(self, message: str = "Database operation failed."):
        super().__init__(message, status_code=500)
