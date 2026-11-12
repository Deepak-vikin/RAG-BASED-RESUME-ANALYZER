import re
import os
from typing import Tuple
from backend.app.config import settings
from backend.app.core.exceptions import InvalidFileTypeError, FileSizeExceededError


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and remove dangerous characters.
    """
    # Extract only the base name
    basename = os.path.basename(filename)
    # Replace anything that isn't alphanumeric, dash, underscore, space or dot
    clean_name = re.sub(r"[^\w\s\.-]", "_", basename).strip()
    # Prevent empty or reserved filenames
    if not clean_name or clean_name.startswith("."):
        clean_name = f"doc_{clean_name.lstrip('.') or 'file'}"
    return clean_name


def validate_file(filename: str, content_size: int) -> Tuple[str, str]:
    """
    Validates file extension and size against configured limits.
    Returns (sanitized_filename, extension).
    """
    clean_name = sanitize_filename(filename)
    _, ext = os.path.splitext(clean_name)
    ext = ext.lower()

    if ext not in settings.ALLOWED_EXTENSIONS:
        raise InvalidFileTypeError(clean_name, settings.ALLOWED_EXTENSIONS)

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if content_size > max_bytes:
        raise FileSizeExceededError(settings.MAX_UPLOAD_SIZE_MB)

    return clean_name, ext

