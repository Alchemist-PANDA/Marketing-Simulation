import os
import easyocr
import numpy as np
from PIL import Image
import io

_READER = None

def get_reader():
    global _READER
    if _READER is None:
        gpu = os.environ.get("EASYOCR_GPU", "false").lower() == "true"
        _READER = easyocr.Reader(['en'], gpu=gpu, verbose=False)
    return _READER

def extract_text_from_image(image_bytes: bytes) -> str:
    if not image_bytes:
        return ""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img_np = np.array(img)
        reader = get_reader()
        results = reader.readtext(img_np)
        return " ".join([item[1] for item in results]).strip()
    except Exception:
        return ""
