import uvicorn
import time
import collections
from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Dict, Optional, Any
import uuid
import random
import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.ad_processing.ad import Ad
from src.simulation.max_engine import MaxSimulation
from src.simulation.calibrator import Calibrator
from src.simulation.failure_analysis import analyze_failure
from src.api.auth_handler import get_current_user_logic
from src.core.auth_utils import is_auth_enabled
from .models import (CampaignRequest, SimulationResult, AgentProfile,
                     SegmentType, AdRequest, SimulateResponse, CalibrationRecord)

app = FastAPI(
    title="Marketing Simulation API",
    description="Advanced API for running high-fidelity marketing simulations",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rate Limiting ---
_rate_store: Dict[str, collections.deque] = {}
RATE_LIMIT = 10
RATE_WINDOW = 60


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path in ("/health", "/api/health", "/agents"):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    if client_ip in ("testclient", "testserver"):
        return await call_next(request)

    now = time.time()

    if client_ip not in _rate_store:
        _rate_store[client_ip] = collections.deque()

    timestamps = _rate_store[client_ip]
    while timestamps and timestamps[0] < now - RATE_WINDOW:
        timestamps.popleft()

    if len(timestamps) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Max 10 requests per minute."}
        )

    timestamps.append(now)
    return await call_next(request)


# --- Persistence & Setup ---
DEFAULT_HISTORICAL = [
    {"predicted_ctr": 0.05, "actual_ctr": 0.04, "predicted_cvr": 0.10, "actual_cvr": 0.08},
    {"predicted_ctr": 0.08, "actual_ctr": 0.07, "predicted_cvr": 0.12, "actual_cvr": 0.10},
    {"predicted_ctr": 0.03, "actual_ctr": 0.03, "predicted_cvr": 0.09, "actual_cvr": 0.09},
    {"predicted_ctr": 0.10, "actual_ctr": 0.09, "predicted_cvr": 0.15, "actual_cvr": 0.13},
]

_calibrator = Calibrator(reference_n=10)
_calibrator.fit(DEFAULT_HISTORICAL)

simulations: Dict[str, Any] = {}
agents_list: List[AgentProfile] = [
    AgentProfile(
        id=str(uuid.uuid4()),
        name=f"Agent_{i}",
        segment=SegmentType.BUDGET if i % 2 == 0 else SegmentType.TECH_SAVVY,
        traits=["price_sensitive", "online_shopper"],
        base_conversion_prob=0.05,
        preferred_channels=["email", "social"],
        sensitivity_to_price=0.8
    ) for i in range(100)
]


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/api/health")
async def api_health():
    return await health()


async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not is_auth_enabled():
        return get_current_user_logic(None)

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]
    user = get_current_user_logic(token)

    if user.get("mode") == "local":
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user


@app.get("/api/me")
async def get_me(user: Dict[str, Any] = Depends(get_current_user)):
    return user


@app.post("/simulate", response_model=SimulateResponse)
async def simulate(request: AdRequest):
    try:
        ad = Ad(
            text=request.text,
            channel=request.channel.value if hasattr(request.channel, 'value') else request.channel,
            creative_type='text',
            price=request.price,
            category=request.category,
            social_proof=request.social_proof,
            urgency=request.urgency
        )

        sim = MaxSimulation(num_agents=request.agents, seed=request.seed)
        results = sim.simulate_exposure(ad)

        raw_ctr = results['likes'] / request.agents
        raw_cvr = results['conversions'] / max(1, results['likes'])

        adj_ctr, adj_cvr, confidence = _calibrator.calibrate(raw_ctr, raw_cvr)

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


@app.post("/api/simulate", response_model=SimulateResponse)
async def api_simulate(request: AdRequest):
    return await simulate(request)


@app.post("/calibrate")
async def add_calibration_data(record: CalibrationRecord):
    global DEFAULT_HISTORICAL, _calibrator
    DEFAULT_HISTORICAL.append(record.model_dump())
    _calibrator.fit(DEFAULT_HISTORICAL)
    return {
        "status": "calibrator updated",
        "num_samples": _calibrator.num_samples,
        "ctr_factor": round(_calibrator.ctr_factor, 4),
        "cvr_factor": round(_calibrator.cvr_factor, 4)
    }


@app.post("/api/calibrate")
async def api_add_calibration_data(record: CalibrationRecord):
    return await add_calibration_data(record)


@app.get("/agents", response_model=List[AgentProfile])
async def get_agents(segment: Optional[SegmentType] = None):
    if segment:
        return [a for a in agents_list if a.segment == segment]
    return agents_list


@app.post("/legacy_simulate", response_model=SimulationResult)
async def run_legacy_simulation(request: CampaignRequest):
    conversions = 0
    target_agents = [a for a in agents_list if a.segment in request.target_segments]

    if not target_agents:
        target_agents = agents_list

    for agent in target_agents:
        prob = agent.base_conversion_prob
        if request.channel in agent.preferred_channels:
            prob *= 1.5
        prob *= (1 + (request.budget / 10000))

        if random.random() < min(prob, 0.95):
            conversions += 1

    result = SimulationResult(
        campaign_id=request.id,
        total_agents=len(target_agents),
        conversions=conversions,
        conversion_rate=conversions / len(target_agents) if target_agents else 0,
        total_spend=request.budget,
        estimated_roi=(conversions * 50) / request.budget if request.budget > 0 else 0,
        segment_performance={}
    )

    simulations[request.id] = result
    return result


@app.get("/results/{campaign_id}", response_model=SimulationResult)
async def get_result(campaign_id: str):
    if campaign_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return simulations[campaign_id]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
