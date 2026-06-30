"""
OCR engine using EasyOCR for image-to-text extraction.
Pure Python — no Tesseract system binaries required.
"""

import logging

logger = logging.getLogger(__name__)

_READER = None


def get_reader():
    """Lazy-initialize EasyOCR reader (heavy model load, cached globally)."""
    global _READER
    if _READER is None:
        try:
            import easyocr
            _READER = easyocr.Reader(['en'], gpu=False)
        except ImportError:
            logger.error("easyocr not installed. Run: pip install easyocr")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            raise
    return _READER


def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extract text from image bytes using EasyOCR.

    Args:
        image_bytes: Raw image bytes (JPG, PNG, WEBP).

    Returns:
        Extracted text as a single string, or empty string if nothing found.
    """
    reader = get_reader()
    results = reader.readtext(image_bytes, detail=0)
    return " ".join(results).strip()
