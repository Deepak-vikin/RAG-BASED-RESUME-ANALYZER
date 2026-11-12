class DocumentAnalyzerException(Exception):
    """Base exception for Document Analyzer application."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class DocumentNotFoundError(DocumentAnalyzerException):
    def __init__(self, document_id: str):
        super().__init__(f"Document with ID '{document_id}' not found.", status_code=404)


class DocumentProcessingError(DocumentAnalyzerException):
    def __init__(self, message: str):
        super().__init__(f"Document processing error: {message}", status_code=422)


class InvalidFileTypeError(DocumentAnalyzerException):
    def __init__(self, filename: str, allowed: list):
        super().__init__(
            f"File '{filename}' has an unsupported extension. Allowed types: {', '.join(allowed)}",
            status_code=400
        )


class FileSizeExceededError(DocumentAnalyzerException):
    def __init__(self, max_size_mb: int):
        super().__init__(
            f"File size exceeds the maximum limit of {max_size_mb} MB.",
            status_code=413
        )


class OpenRouterAPIError(DocumentAnalyzerException):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(f"OpenRouter API error: {message}", status_code=status_code)


class VectorStoreError(DocumentAnalyzerException):
    def __init__(self, message: str):
        super().__init__(f"Vector store operation failed: {message}", status_code=500)
