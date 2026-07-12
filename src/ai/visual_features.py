"""
Visual feature extraction for image and video ad creatives.

Produces a heuristic ``visual_quality`` score in [0,1] plus a feature dict.
Honesty note: unlike the text ranker (validated against real TikTok CTR
tiers), these visual heuristics are NOT yet trained against ground truth.
They encode well-documented creative best practices (contrast, colorfulness,
brightness, aspect, motion pacing) and are given a deliberately small weight
in creative_ranker.score_ad. Training them against scraped thumbnail/CTR
data is the next data milestone.

Images: PIL only (always available).
Video: OpenCV if installed (opencv-python-headless in requirements);
       otherwise returns neutral scores with `available: False`.
"""

import io
import os
import tempfile
from typing import Dict, Any

import numpy as np


# --------------------------------------------------------------- images
def image_features(file_bytes: bytes) -> Dict[str, Any]:
    """Extract creative-quality features from an image (ad screenshot)."""
    try:
        from PIL import Image, ImageFilter, ImageStat
    except ImportError:
        return {"available": False, "visual_quality": 0.5}

    try:
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    except Exception:
        return {"available": False, "visual_quality": 0.5}

    img.thumbnail((512, 512))
    stat = ImageStat.Stat(img)
    arr = np.asarray(img, dtype=np.float32)

    brightness = float(np.mean(stat.mean)) / 255.0              # 0-1
    contrast = float(np.mean(stat.stddev)) / 128.0              # ~0-1
    # colorfulness (Hasler & Süsstrunk approximation)
    rg = arr[..., 0] - arr[..., 1]
    yb = 0.5 * (arr[..., 0] + arr[..., 1]) - arr[..., 2]
    colorfulness = float(
        np.sqrt(rg.std() ** 2 + yb.std() ** 2)
        + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2)
    ) / 100.0
    # edge density: proxy for visual busyness / text overlay presence
    edges = np.asarray(
        img.convert("L").filter(ImageFilter.FIND_EDGES), dtype=np.float32)
    edge_density = float((edges > 40).mean())
    w, h = img.size
    aspect = h / max(1, w)
    is_vertical = 1.0 if aspect > 1.2 else 0.0   # TikTok-native format

    # Heuristic quality: mid-high brightness, decent contrast + color,
    # some (not extreme) busyness, vertical format
    quality = 0.5
    quality += 0.10 * (1.0 - abs(brightness - 0.55) * 2)
    quality += 0.10 * min(contrast, 1.0)
    quality += 0.10 * min(colorfulness, 1.0)
    quality += 0.05 * (1.0 - abs(edge_density - 0.25) * 2)
    quality += 0.05 * is_vertical
    quality = float(min(1.0, max(0.0, quality)))

    return {
        "available": True,
        "visual_quality": round(quality, 4),
        "brightness": round(brightness, 4),
        "contrast": round(contrast, 4),
        "colorfulness": round(colorfulness, 4),
        "edge_density": round(edge_density, 4),
        "aspect_ratio": round(aspect, 3),
        "is_vertical": bool(is_vertical),
        "width": w, "height": h,
    }


# ---------------------------------------------------------------- video
def video_features(file_bytes: bytes, suffix: str = ".mp4",
                   max_frames: int = 12) -> Dict[str, Any]:
    """Extract pacing/hook features from a video ad via frame sampling."""
    try:
        import cv2
    except ImportError:
        return {"available": False, "visual_quality": 0.5,
                "note": "opencv not installed — video analyzed as metadata only"}

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            return {"available": False, "visual_quality": 0.5}

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = n_frames / fps if fps > 0 else 0.0

        idxs = np.linspace(0, max(0, n_frames - 1), max_frames).astype(int)
        frames, image_stats, native_frames = [], [], []
        for idx in idxs:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ok, frame = cap.read()
            if not ok:
                continue
            small = cv2.resize(frame, (160, 284))
            frames.append(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32))
            image_stats.append(small.astype(np.float32))
            native_frames.append(frame)  # native-res BGR for keyframe features
        cap.release()

        if len(frames) < 2:
            return {"available": False, "visual_quality": 0.5}

        diffs = [float(np.abs(frames[i + 1] - frames[i]).mean())
                 for i in range(len(frames) - 1)]
        motion_energy = float(np.mean(diffs)) / 64.0
        cut_rate = float(np.mean([d > 25 for d in diffs]))
        # hook strength: how much happens in the first ~2s worth of samples
        first_k = max(1, int(len(diffs) * (2.0 / max(duration, 2.0))))
        hook_strength = float(np.mean(diffs[:first_k])) / 64.0
        brightness = float(np.mean([f.mean() for f in frames])) / 255.0
        h, w = image_stats[0].shape[:2]

        # --- Keyframe still features (the part the trained model consumes) ---
        # The creative ranker's visual branch was trained on the 6 static
        # thumbnail features (brightness/contrast/colorfulness/edge_density/
        # aspect/quality). A video must expose those SAME keys or the ranker
        # silently discards its visual signal (visual_vector falls back to
        # neutral means, flag=0). We pick the frame nearest the median
        # brightness (a representative, non-black-cut still) and run it
        # through the exact same image_features() path used for thumbnails,
        # so an uploaded video feeds the trained visual model just like an
        # image upload does — via a real keyframe, not motion heuristics.
        still = {}
        try:
            fb = [float(f.mean()) for f in frames]
            mid_i = int(np.argsort(fb)[len(fb) // 2])
            bgr = native_frames[mid_i]  # native resolution -> real aspect ratio
            rgb = bgr[:, :, ::-1].astype(np.uint8)  # BGR -> RGB
            from PIL import Image as _Image
            buf = io.BytesIO()
            _Image.fromarray(rgb, "RGB").save(buf, format="PNG")
            still = image_features(buf.getvalue())
        except Exception:
            still = {}

        # heuristic pacing quality (for display) blended with the trained-
        # feature still quality (what actually correlates with real outcomes)
        pacing_q = 0.5
        pacing_q += 0.12 * min(hook_strength, 1.0)
        pacing_q += 0.08 * min(motion_energy, 1.0)
        pacing_q += 0.05 * (1.0 - abs(brightness - 0.5) * 2)
        if 8.0 <= duration <= 40.0:
            pacing_q += 0.10
        elif duration > 90.0:
            pacing_q -= 0.05
        pacing_q = float(min(1.0, max(0.0, pacing_q)))

        still_q = float(still.get("visual_quality", pacing_q)) if still.get("available") else pacing_q
        quality = round(0.5 * still_q + 0.5 * pacing_q, 4)

        out = {
            "available": True,
            "visual_quality": quality,
            "duration_s": round(duration, 2),
            "sampled_frames": len(frames),
            "motion_energy": round(motion_energy, 4),
            "cut_rate": round(cut_rate, 4),
            "hook_strength_2s": round(hook_strength, 4),
            "brightness": round(brightness, 4),
        }
        # Expose the 6 trained-model keys from the keyframe so visual_vector
        # actually uses them (this is what makes the video affect the pick).
        if still.get("available"):
            for k in ("brightness", "contrast", "colorfulness",
                      "edge_density", "aspect_ratio"):
                if k in still:
                    out[k] = still[k]
            out["keyframe_features"] = True
        return out
    except Exception:
        return {"available": False, "visual_quality": 0.5}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
