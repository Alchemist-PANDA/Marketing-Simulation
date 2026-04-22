import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Optional
import uuid
import random
from datetime import datetime

from .models import CampaignRequest, SimulationResult, AgentProfile, SegmentType

app = FastAPI(
    title="Marketing Simulation API",
    description="Advanced API for running high-fidelity marketing simulations",
    version="1.0.0"
)

# In-memory storage for simplicity in this prototype
simulations: Dict[str, SimulationResult] = {}
agents: List[AgentProfile] = [
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

# DASHBOARD UI
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marketing Simulation Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .card { @apply bg-white p-6 rounded-lg shadow-md; }
        .btn { @apply px-4 py-2 rounded font-semibold transition; }
        .btn-primary { @apply bg-blue-600 text-white hover:bg-blue-700; }
        .btn-secondary { @apply bg-gray-200 text-gray-800 hover:bg-gray-300; }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <nav class="bg-blue-800 text-white p-4 shadow-lg">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-bold">MarketSim Dashboard</h1>
            <div id="status-indicator" class="flex items-center">
                <span class="w-3 h-3 bg-green-400 rounded-full mr-2"></span>
                <span>System Live</span>
            </div>
        </div>
    </nav>

    <main class="container mx-auto py-8 px-4">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="card">
                <h3 class="text-gray-500 text-sm font-bold uppercase">Total Agents</h3>
                <p id="total-agents" class="text-3xl font-bold">100</p>
            </div>
            <div class="card">
                <h3 class="text-gray-500 text-sm font-bold uppercase">Active Simulations</h3>
                <p id="active-sims" class="text-3xl font-bold">0</p>
            </div>
            <div class="card">
                <h3 class="text-gray-500 text-sm font-bold uppercase">Avg. Conversion Rate</h3>
                <p id="avg-cr" class="text-3xl font-bold">0.0%</p>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div class="card">
                <h2 class="text-xl font-bold mb-4">Run New Simulation</h2>
                <form id="sim-form" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Campaign Name</label>
                        <input type="text" id="camp-name" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2 border" value="Summer Launch">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Channel</label>
                        <select id="camp-channel" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2 border">
                            <option value="email">Email</option>
                            <option value="social">Social Media</option>
                            <option value="search">Search Engine</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Budget ($)</label>
                        <input type="number" id="camp-budget" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2 border" value="5000">
                    </div>
                    <button type="submit" class="btn btn-primary w-full">Launch Simulation</button>
                </form>
            </div>

            <div class="card">
                <h2 class="text-xl font-bold mb-4">Performance Trends</h2>
                <canvas id="performanceChart" height="200"></canvas>
            </div>
        </div>

        <div class="mt-8 card">
            <h2 class="text-xl font-bold mb-4">Recent Results</h2>
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead>
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Channel</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Budget</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Conversions</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">CR %</th>
                        </tr>
                    </thead>
                    <tbody id="results-table" class="bg-white divide-y divide-gray-200">
                        <!-- Data populated via JS -->
                    </tbody>
                </table>
            </div>
        </div>
    </main>

    <script>
        const ctx = document.getElementById('performanceChart').getContext('2d');
        const performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Conversion Rate %',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    tension: 0.1
                }]
            },
            options: {
                scales: {
                    y: { beginAtZero: true, max: 20 }
                }
            }
        });

        document.getElementById('sim-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = e.target.querySelector('button');
            btn.disabled = true;
            btn.innerText = 'Processing...';

            const payload = {
                id: Math.random().toString(36).substr(2, 9),
                name: document.getElementById('camp-name').value,
                channel: document.getElementById('camp-channel').value,
                budget: parseFloat(document.getElementById('camp-budget').value),
                target_segments: ["budget", "tech_savvy"]
            };

            try {
                const response = await fetch('/simulate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await response.json();
                updateDashboard(result);
            } catch (err) {
                console.error('Sim failed', err);
            } finally {
                btn.disabled = false;
                btn.innerText = 'Launch Simulation';
            }
        });

        function updateDashboard(result) {
            // Update stats
            const currentSims = parseInt(document.getElementById('active-sims').innerText) + 1;
            document.getElementById('active-sims').innerText = currentSims;

            // Add to table
            const row = `<tr>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">${result.campaign_id}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${result.total_spend > 0 ? 'Digital' : 'Organic'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">$${result.total_spend}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${result.conversions}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-bold">${(result.conversion_rate * 100).toFixed(1)}%</td>
            </tr>`;
            document.getElementById('results-table').insertAdjacentHTML('afterbegin', row);

            // Update chart
            performanceChart.data.labels.push(new Date().toLocaleTimeString());
            performanceChart.data.datasets[0].data.push(result.conversion_rate * 100);
            if (performanceChart.data.labels.length > 10) {
                performanceChart.data.labels.shift();
                performanceChart.data.datasets[0].data.shift();
            }
            performanceChart.update();
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return DASHBOARD_HTML

@app.get("/agents", response_model=List[AgentProfile])
async def get_agents(segment: Optional[SegmentType] = None):
    if segment:
        return [a for a in agents if a.segment == segment]
    return agents

@app.post("/simulate", response_model=SimulationResult)
async def run_simulation(request: CampaignRequest):
    # Simulation Logic
    conversions = 0
    target_agents = [a for a in agents if a.segment in request.target_segments]

    if not target_agents:
        target_agents = agents # Default to all if none specified

    for agent in target_agents:
        # Simplified probability calculation
        prob = agent.base_conversion_prob
        if request.channel in agent.preferred_channels:
            prob *= 1.5

        # Budget impact
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
