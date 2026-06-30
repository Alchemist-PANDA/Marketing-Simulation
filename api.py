import sys
import os
import httpx
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Security, BackgroundTasks, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.ad_processing.ad import Ad
from src.simulation.max_engine import MaxSimulation, generate_reasoning
from src.simulation.calibrator import Calibrator
from src.simulation.failure_analysis import analyze_failure
from scripts.validate_with_real_data import validate_data

app = FastAPI(
    title="Marketing Simulation Engine API",
    description="Digital Wind Tunnel API for DTC E-Commerce: Validate ads before you spend.",
    version="2.0.0"
)

API_KEY = os.environ.get("MARKETING_SIM_API_KEY", "sk-demo-key-12345")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Could not validate API key")

# --- Persistence ---
DEFAULT_HISTORICAL = [
    {"predicted_ctr": 0.05, "actual_ctr": 0.04, "predicted_cvr": 0.10, "actual_cvr": 0.08},
    {"predicted_ctr": 0.08, "actual_ctr": 0.07, "predicted_cvr": 0.12, "actual_cvr": 0.10},
]
_calibrator = Calibrator(reference_n=10)
_calibrator.fit(DEFAULT_HISTORICAL)

# --- Models ---
class AdRequest(BaseModel):
    text: str = Field(..., description="Ad creative text")
    price: float = Field(default=49.99, description="Product price")
    category: str = Field(default="ecommerce", description="Product category")
    channel: str = Field(default="facebook", description="Marketing channel")
    agents: int = Field(default=1000, description="Number of psychographic agents")
    webhook_url: Optional[str] = Field(None, description="URL to ping upon completion")

class ValidationRequest(BaseModel):
    csv_path: str = Field(..., description="Absolute path to CSV file on server or accessible URL.")
    webhook_url: Optional[str] = None

# --- Webhooks ---
async def send_webhook(url: str, payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, timeout=10.0)
    except Exception as e:
        print(f"Webhook failed: {e}")

# --- Endpoints ---

@app.post("/predict", tags=["Simulation"])
async def predict(request: AdRequest, background_tasks: BackgroundTasks, api_key: str = Depends(get_api_key)):
    """Predicts ad performance and generates deterministic reasoning."""
    try:
        ad = Ad(text=request.text, channel=request.channel, creative_type='text', price=request.price)
        sim = MaxSimulation(num_agents=request.agents)
        results = sim.simulate_exposure(ad)

        raw_ctr = results['likes'] / request.agents
        raw_cvr = results['conversions'] / max(1, results['likes'])
        adj_ctr, adj_cvr, confidence = _calibrator.calibrate(raw_ctr, raw_cvr)
        
        # We need two ads for generate_reasoning gap analysis. Let's create a baseline ad.
        baseline_ad = Ad(text="Buy our product.", channel=request.channel, creative_type='text', price=request.price)
        baseline_res = sim.simulate_exposure(baseline_ad)
        
        reasoning = generate_reasoning(results, baseline_res)

        response_payload = {
            "predicted_ctr": round(adj_ctr, 6),
            "predicted_cvr": round(adj_cvr, 6),
            "confidence_score": round(confidence, 4),
            "raw_metrics": {
                "likes": results['likes'],
                "conversions": results['conversions'],
                "shares": results['shares']
            },
            "reasoning": reasoning
        }
        
        if request.webhook_url:
            background_tasks.add_task(send_webhook, request.webhook_url, response_payload)
            return {"status": "processing", "message": f"Results will be sent to {request.webhook_url}"}

        return response_payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate", tags=["Validation"])
async def run_validation(request: ValidationRequest, background_tasks: BackgroundTasks, api_key: str = Depends(get_api_key)):
    """Runs the real-world validation pipeline against a provided dataset."""
    try:
        if not os.path.exists(request.csv_path):
            raise HTTPException(status_code=400, detail="CSV file not found.")
            
        report = validate_data(request.csv_path, output_dir="outputs")
        
        if request.webhook_url:
            background_tasks.add_task(send_webhook, request.webhook_url, report)
            return {"status": "processing", "message": f"Validation report will be sent to {request.webhook_url}"}
            
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", tags=["System"])
async def health():
    return {"status": "healthy", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
