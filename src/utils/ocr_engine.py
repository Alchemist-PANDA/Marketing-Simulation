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
    # Debug logging for input image
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes))
        logger.info(f"OCR input image: size={img.size}, format={img.format}, mode={img.mode}, len={len(image_bytes)}")
        print(f"OCR debug: size={img.size}, format={img.format}, mode={img.mode}, len={len(image_bytes)}")
    except Exception as img_err:
        logger.error(f"OCR: Failed to parse image properties: {img_err}")
        print(f"OCR debug: Failed to parse image properties: {img_err}")

    try:
        logger.info("Initializing EasyOCR reader...")
        reader = get_reader()
        logger.info("Running EasyOCR on image bytes...")
        results = reader.readtext(image_bytes, detail=0)
        extracted = " ".join(results).strip()
        logger.info(f"EasyOCR success. Extracted {len(extracted)} characters.")
        print(f"OCR debug: Extracted '{extracted[:100]}...' (len={len(extracted)})")
        return extracted
    except Exception as ocr_err:
        logger.error(f"EasyOCR reader failed: {ocr_err}")
        print(f"OCR debug failed: {ocr_err}")
        raise ocr_err
