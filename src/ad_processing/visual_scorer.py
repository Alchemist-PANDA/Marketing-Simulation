import os
from typing import Dict, Optional

# Lazy-loaded globals
_model = None
_processor = None
_device = None

def _load_clip_model():
    global _model, _processor, _device
    if _model is None:
        try:
            import torch
            from transformers import CLIPProcessor, CLIPModel
            _device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Loading CLIP model on {_device}...")
            _model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(_device)
            _processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        except Exception as e:
            print(f"Failed to load CLIP model: {e}")
            _model = "failed"
            _processor = "failed"

def score_image(image_path: Optional[str] = None) -> Dict[str, float]:
    """
    Scores an image using zero-shot classification via CLIP.
    Returns scores between 0 and 1.
    """
    default_scores = {
        "visual_excitement": 0.5,
        "visual_trust": 0.5,
        "visual_urgency": 0.5,
        "visual_aesthetic": 0.5,
        "visual_premium": 0.5
    }
    
    if not image_path or not os.path.exists(image_path):
        return default_scores
        
    _load_clip_model()
    
    if _model == "failed" or _model is None:
        return default_scores
        
    try:
        from PIL import Image
        import torch
        image = Image.open(image_path)
        
        # Prompts tailored for the specific attributes
        prompts = [
            "an exciting, dynamic, and engaging image", # excitement (pos)
            "a boring, dull, and static image",         # excitement (neg)
            "a highly trustworthy and professional brand image", # trust (pos)
            "a scammy, untrustworthy, low-quality image",        # trust (neg)
            "an urgent, limited time, fast-paced offer image",   # urgency (pos)
            "a calm, slow, relaxed, timeless image",             # urgency (neg)
            "a beautiful, highly aesthetic, well-composed image",# aesthetic (pos)
            "an ugly, messy, poorly composed image",             # aesthetic (neg)
            "a luxury, premium, high-end product image",         # premium (pos)
            "a cheap, low-end, budget product image"             # premium (neg)
        ]
        
        inputs = _processor(text=prompts, images=image, return_tensors="pt", padding=True).to(_device)
        with torch.no_grad():
            outputs = _model(**inputs)
            
        logits_per_image = outputs.logits_per_image # this is the image-text similarity score
        probs = logits_per_image.softmax(dim=1)[0].cpu().numpy()
        
        def get_score(pos_idx, neg_idx):
            pair_probs = torch.tensor([probs[pos_idx], probs[neg_idx]]).softmax(dim=0).numpy()
            return float(pair_probs[0])
            
        return {
            "visual_excitement": get_score(0, 1),
            "visual_trust": get_score(2, 3),
            "visual_urgency": get_score(4, 5),
            "visual_aesthetic": get_score(6, 7),
            "visual_premium": get_score(8, 9)
        }
        
    except Exception as e:
        print(f"Error scoring image {image_path}: {e}")
        return default_scores
