"""
Inference wrapper for the trained CTR ensemble.

Loads models/ensemble_model.pkl (Ridge + HistGBR + RandomForest + MLP with
validation-learned weights, plus the fitted scaler) and predicts CTR for a
single ad. Heavy pieces (the MiniLM embedder inside feature_extractor) load
lazily, so importing this module is cheap.

⚠️  The model is trained on a SYNTHETIC development benchmark. Predictions are a
useful *relative* signal (which ad is likely stronger) for demos and testing,
not a calibrated real-world CTR. See docs/ACCURACY_UPGRADE_REPORT.md.
"""
from __future__ import annotations

import os
import pickle

import numpy as np

ENSEMBLE_PATH = "models/ensemble_model.pkl"

_instance: EnsemblePredictor | None = None


class EnsemblePredictor:
    def __init__(self, path: str = ENSEMBLE_PATH):
        self.available = False
        self.model_version = None
        self._bundle = None
        if os.path.exists(path):
            with open(path, "rb") as f:
                self._bundle = pickle.load(f)
            self.model_version = self._bundle.get("model_version", "ensemble")
            self.available = True

    def predict(self, text: str) -> dict:
        """Return {predicted_ctr, model_version, confidence, per_model} for one ad."""
        if not self.available:
            raise RuntimeError("Ensemble model not loaded")

        from src.ai.feature_extractor import build_features

        bundle = self._bundle
        scaler = bundle["scaler"]
        models = bundle["models"]
        weights = bundle["weights"]
        y_scale = bundle.get("y_scale", 1.0)

        X = scaler.transform(build_features([text]))
        per_model = {k: float(m.predict(X)[0]) / y_scale for k, m in models.items()}
        ctr = sum(weights[k] * per_model[k] for k in models)
        ctr = float(max(0.0001, ctr))

        # Confidence proxy: agreement among base models (low spread -> high conf).
        vals = np.array(list(per_model.values()))
        spread = float(np.std(vals) / (np.mean(np.abs(vals)) + 1e-9))
        confidence = float(np.clip(1.0 - spread, 0.0, 1.0))

        return {
            "predicted_ctr": ctr,
            "model_version": self.model_version,
            "confidence": round(confidence, 3),
            "per_model": {k: round(v, 6) for k, v in per_model.items()},
        }


def get_ensemble_predictor() -> EnsemblePredictor:
    """Singleton accessor."""
    global _instance
    if _instance is None:
        _instance = EnsemblePredictor()
    return _instance
