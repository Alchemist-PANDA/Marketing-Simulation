import uvicorn
import time
import os
import sys
import httpx
import hashlib
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException, Request, Depends, Header, BackgroundTasks, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security.api_key import APIKeyHeader

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.ad_processing.ad import Ad
from src.simulation.max_engine import MaxSimulation, generate_reasoning
from src.simulation.calibrator import Calibrator
from src.simulation.failure_analysis import analyze_failure
from src.api.auth_handler import get_current_user_logic
from src.core.auth_utils import is_auth_enabled
from src.core.supabase_client import SupabaseManager
from .models import (CampaignRequest, SimulationResult, AgentProfile,
                     SegmentType, AdRequest, SimulateResponse, CalibrationRecord)
from scripts.validate_with_real_data import validate_data

# Upstash Redis
from upstash_redis import Redis
UPSTASH_URL = os.environ.get("UPSTASH_REDIS_REST_URL")
UPSTASH_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN")
redis = Redis(url=UPSTASH_URL, token=UPSTASH_TOKEN) if UPSTASH_URL and UPSTASH_TOKEN else None

# Redpanda Kafka
from confluent_kafka import Producer
import json
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:9092")
try:
    kafka_producer = Producer({'bootstrap.servers': KAFKA_BROKER})
except Exception as e:
    print(f"Warning: Failed to connect to Kafka at {KAFKA_BROKER}: {e}")
    kafka_producer = None

app = FastAPI(
    title="Marketing Simulation Unified API",
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

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key_in_db(raw_key: str) -> Optional[Dict]:
    """Look up the API key hash in Supabase to verify it and retrieve limits."""
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    manager = SupabaseManager()
    res = manager.select("api_keys", filters={"key_hash": key_hash})
    if res.get("status") == "success" and res.get("data"):
        return res["data"][0]
    return None

async def check_rate_limit_redis(key_id: str, limit: int) -> bool:
    """Implement a sliding window rate limit in Upstash Redis."""
    if not redis:
        return True # Fail open if Redis is not configured
    
    now = int(time.time() * 1000)
    window_start = now - 60000 # 1 minute window
    redis_key = f"rate_limit:{key_id}"
    
    pipeline = redis.pipeline()
    pipeline.zremrangebyscore(redis_key, 0, window_start)
    pipeline.zrange(redis_key, 0, -1)
    pipeline.zadd(redis_key, {str(now): now})
    pipeline.expire(redis_key, 60)
    
    results = pipeline.exec()
    # The result of zrange is at index 1 of the pipeline execution list
    current_requests = len(results[1]) if len(results) > 1 else 0
    
    if current_requests >= limit:
        return False
    return True

async def get_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        return None
        
    key_record = verify_api_key_in_db(api_key)
    if not key_record:
        raise HTTPException(status_code=401, detail="Invalid API Key")
        
    # Check rate limit
    limit = key_record.get("rate_limit", 10)
    allowed = await check_rate_limit_redis(key_record["id"], limit)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
    # Update last_used
    manager = SupabaseManager()
    manager.update("api_keys", {"id": key_record["id"]}, {"last_used": "now()"})
    
    return key_record

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

async def auth_dependency(
    user: Optional[Dict[str, Any]] = Depends(get_current_user),
    api_key_record: Optional[Dict] = Depends(get_api_key)
):
    """Allow access if EITHER a valid JWT or a valid API Key is provided."""
    if api_key_record:
        return {"type": "api_key", "record": api_key_record}
    if user:
        return {"type": "jwt", "user": user}
    raise HTTPException(status_code=401, detail="Not authenticated. Provide Bearer token or X-API-Key.")


def publish_event(topic: str, event_data: dict):
    """Publish an event to Kafka/Redpanda."""
    if kafka_producer:
        try:
            kafka_producer.produce(topic, value=json.dumps(event_data).encode('utf-8'))
            kafka_producer.poll(0)
        except Exception as e:
            print(f"Failed to publish to Kafka: {e}")

async def send_webhook(url: str, payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, timeout=10.0)
    except Exception as e:
        print(f"Webhook failed: {e}")

# --- Setup & Calibration ---
DEFAULT_HISTORICAL = [
    {"predicted_ctr": 0.05, "actual_ctr": 0.04, "predicted_cvr": 0.10, "actual_cvr": 0.08},
    {"predicted_ctr": 0.08, "actual_ctr": 0.07, "predicted_cvr": 0.12, "actual_cvr": 0.10},
    {"predicted_ctr": 0.03, "actual_ctr": 0.03, "predicted_cvr": 0.09, "actual_cvr": 0.09},
    {"predicted_ctr": 0.10, "actual_ctr": 0.09, "predicted_cvr": 0.15, "actual_cvr": 0.13},
]
_calibrator = Calibrator(reference_n=10)
_calibrator.fit(DEFAULT_HISTORICAL)


@app.get("/")
async def root():
    """Serve the SaaS landing page."""
    landing_path = os.path.join(os.path.dirname(__file__), '../../landing_component/index.html')
    if not os.path.exists(landing_path):
        raise HTTPException(status_code=404, detail="Landing page not found")
    return FileResponse(landing_path)

@app.get("/health")
async def health():
    """Load balancer health check endpoint."""
    redis_status = "connected" if redis else "not_configured"
    kafka_status = "connected" if kafka_producer else "not_configured"
    return {
        "status": "healthy", 
        "version": "2.0.0",
        "redis": redis_status,
        "kafka": kafka_status
    }

@app.get("/api/me")
async def get_me(auth=Depends(auth_dependency)):
    return auth

@app.post("/predict", tags=["Simulation"])
async def predict(request: AdRequest, background_tasks: BackgroundTasks, auth=Depends(auth_dependency)):
    """Predicts ad performance and generates deterministic reasoning."""
    try:
        publish_event("simulation_started", {"ad_text": request.text, "channel": request.channel})
        
        ad = Ad(
            text=request.text, 
            channel=request.channel.value if hasattr(request.channel, 'value') else request.channel, 
            creative_type='text', 
            price=request.price
        )
        sim = MaxSimulation(num_agents=request.agents)
        results = sim.simulate_exposure(ad)

        raw_ctr = results['likes'] / request.agents
        raw_cvr = results['conversions'] / max(1, results['likes'])
        adj_ctr, adj_cvr, confidence = _calibrator.calibrate(raw_ctr, raw_cvr)
        
        baseline_ad = Ad(text="Buy our product.", channel=request.channel.value if hasattr(request.channel, 'value') else request.channel, creative_type='text', price=request.price)
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
        
        publish_event("simulation_completed", {"success": True, "predicted_ctr": response_payload["predicted_ctr"]})
        
        webhook_url = getattr(request, 'webhook_url', None)
        if webhook_url:
            background_tasks.add_task(send_webhook, webhook_url, response_payload)
            return {"status": "processing", "message": f"Results will be sent to {webhook_url}"}

        return response_payload

    except Exception as e:
        publish_event("simulation_completed", {"success": False, "error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
