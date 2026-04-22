import sys
import os
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.ad_processing.ad import Ad
from src.simulation.max_engine import MaxSimulation
from src.simulation.calibrator import Calibrator
from src.simulation.failure_analysis import analyze_failure

app = FastAPI(
    title="Marketing Simulation API",
    description="Digital Wind Tunnel API: Predict ad performance using psychographic agent simulation."
)

# --- Persistence (In-Memory for this version) ---
DEFAULT_HISTORICAL = [
    {"predicted_ctr": 0.05, "actual_ctr": 0.04, "predicted_cvr": 0.10, "actual_cvr": 0.08},
    {"predicted_ctr": 0.08, "actual_ctr": 0.07, "predicted_cvr": 0.12, "actual_cvr": 0.10},
    {"predicted_ctr": 0.03, "actual_ctr": 0.03, "predicted_cvr": 0.09, "actual_cvr": 0.09},
    {"predicted_ctr": 0.10, "actual_ctr": 0.09, "predicted_cvr": 0.15, "actual_cvr": 0.13},
]

_calibrator = Calibrator(reference_n=10)
_calibrator.fit(DEFAULT_HISTORICAL)

# --- Models ---

class AdRequest(BaseModel):
    text: str = Field(..., description="Ad creative text")
    price: float = Field(default=20.0, ge=0, description="Product price")
    category: str = Field(default="general", description="Product category")
    social_proof: float = Field(default=2.5, ge=0, le=5, description="Social proof rating (0-5)")
    urgency: float = Field(default=2.5, ge=0, le=5, description="Urgency/Scarcity level (0-5)")
    channel: str = Field(default="facebook", description="Marketing channel")
    agents: int = Field(default=1000, ge=100, le=10000, description="Number of agents to simulate")

class SimulateResponse(BaseModel):
    predicted_ctr: float
    predicted_cvr: float
    confidence_score: float
    raw_metrics: Dict[str, int]
    failure_reasons: List[str]

class CalibrationRecord(BaseModel):
    predicted_ctr: float
    actual_ctr: float
    predicted_cvr: float
    actual_cvr: float

# --- Endpoints ---

@app.post("/simulate", response_model=SimulateResponse)
async def simulate(request: AdRequest):
    try:
        # 1. Initialize Ad and Simulation
        ad = Ad(
            text=request.text,
            channel=request.channel,
            creative_type='text',
            price=request.price,
            category=request.category,
            social_proof=request.social_proof,
            urgency=request.urgency
        )

        sim = MaxSimulation(num_agents=request.agents)

        # 2. Run Simulation
        results = sim.simulate_exposure(ad)

        # 3. Calculate Raw Metrics
        # CTR = Likes / Total Agents (as proxy for clicks in this simulation context)
        raw_ctr = results['likes'] / request.agents
        # CVR = Conversions / Likes (Conversion conditional on interest)
        raw_cvr = results['conversions'] / max(1, results['likes'])

        # 4. Apply Calibration
        adj_ctr, adj_cvr, confidence = _calibrator.calibrate(raw_ctr, raw_cvr)

        # 5. Forensic Failure Analysis
        analysis = analyze_failure(
            ad.price_score, ad.trust_score, ad.urgency_score,
            ctr=raw_ctr, cvr=raw_cvr
        )

        return SimulateResponse(
            predicted_ctr=round(adj_ctr, 6),
            predicted_cvr=round(adj_cvr, 6),
            confidence_score=round(confidence, 4),
            raw_metrics={
                "likes": results['likes'],
                "conversions": results['conversions'],
                "shares": results['shares']
            },
            failure_reasons=analysis['failure_reasons']
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calibrate")
async def add_calibration_data(record: CalibrationRecord):
    """Add a new historical record and update the calibrator."""
    global DEFAULT_HISTORICAL, _calibrator
    DEFAULT_HISTORICAL.append(record.dict())
    _calibrator.fit(DEFAULT_HISTORICAL)
    return {
        "status": "calibrator updated",
        "num_samples": _calibrator.num_samples,
        "ctr_factor": round(_calibrator.ctr_factor, 4),
        "cvr_factor": round(_calibrator.cvr_factor, 4)
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
