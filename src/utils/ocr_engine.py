import os
import easyocr
import numpy as np
from PIL import Image
import io

# Global variable to hold the reader (lazy-loaded)
_READER = None

def get_reader():
    """Lazy-load the EasyOCR reader (only when first needed)."""
    global _READER
    if _READER is None:
        # Use GPU if available, otherwise CPU
        gpu = os.environ.get("EASYOCR_GPU", "false").lower() == "true"
        _READER = easyocr.Reader(['en'], gpu=gpu, verbose=False)
    return _READER

def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extract text from image bytes using EasyOCR.
    Returns concatenated text or empty string if no text found.
    """
    if not image_bytes:
        return ""
    
    # Convert bytes to PIL Image, then to numpy array
    try:
        img = Image.open(io.BytesIO(image_bytes))
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img_np = np.array(img)
    except Exception:
        return ""
    
    reader = get_reader()
    try:
        results = reader.readtext(img_np)
        # Combine all detected text
        text_parts = [item[1] for item in results]
        return " ".join(text_parts).strip()
    except Exception:
        return ""
