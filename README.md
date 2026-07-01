# Marketing Simulation Engine (DTC E-Commerce Edition)

A digital wind tunnel for Direct-to-Consumer (DTC) E-Commerce ads. This engine **simulates behavioral responses based on OCEAN personality and Prospect Theory** to help you validate creatives before spending real ad budget.

## 🚀 Target Outcomes
- **Save Budget**: Validate ad variants for $0 before spending on real platforms.
- **Estimate Engagement**: Simulate engagement signals (Likes, Shares, and Conversions) based on Big Five personality traits.
- **Identify Winners**: Use the built-in A/B test runner to statistically determine which ad creative performs best in the simulation.

## 🧠 Core Architecture
- **Layer 1: Psychographic Agents**: 500+ agents generated with Big Five (OCEAN) traits.
- **Layer 2: Decision Brain**: Uses **Prospect Theory** (Kahneman & Tversky, 2002) as a behavioral foundation for loss aversion and emotional response modeling.
- **Layer 3: Engagement Engine**: Predicts social signals and word-of-mouth potential.
- **Layer 4: Analysis**: Zero-API-cost Python math engine for instant, deterministic results.

## 🏆 Validation Results

We validated our simulation against **$20,000+ of real Facebook ad spend**:

- **Directional Accuracy:** 92.4%
- **Total Campaigns:** 7
- **Total Ads Tested:** 1,143
- **Total Impressions:** 78.5M
- **Methodology:** A/B tests grouped by identical audience targeting (age, gender, interests), simulated winners compared to real winners.

**[Read the Full Case Study →](./docs/case_study_marketing.md)**

## ⚠️ Known Limitations
- Uses **synthetic agents**, not actual consumer models trained on private consumer data.
- Results are **directional indicators**, not absolute predictions of exact CTR/CVR.

## 🛠️ Quick Start

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Run an A/B Test
Compare two ad creatives across 500 agents:
```bash
python cli.py --ad1 "Get 50% off today!" --ad2 "Experience ultimate luxury." --agents 500
```

### 3. Run Tests
Verify the psychological modeling:
```bash
python -m pytest tests/
```

## 📊 Roadmap
- [x] **Hardened Base**: Cleaned repo, unified agent models.
- [x] **Psychology Engine**: Prospect Theory and Big Five integration.
- [x] **A/B Test CLI**: Ready-to-use tool for creative comparison.
- [x] **API Integration**: REST API with webhooks and API Key auth.
- [ ] **Real-world Calibration**: Fine-tuning weights against Meta/TikTok ad spend data.

## 🔌 API Documentation

The Marketing Simulation Engine provides a robust REST API for integrating into your existing workflow (Figma, Zapier, Chrome Extensions).

### Start the API Server
```bash
python api.py
```

### 1. Predict Ad Performance (`/predict`)
```bash
curl -X POST "http://localhost:8000/predict" \
     -H "X-API-Key: sk-demo-key-12345" \
     -H "Content-Type: application/json" \
     -d '{"text": "Get 50% off your first order today!", "price": 49.99, "channel": "facebook"}'
```

### 2. Validate Against Real Data (`/validate`)
```bash
curl -X POST "http://localhost:8000/validate" \
     -H "X-API-Key: sk-demo-key-12345" \
     -H "Content-Type: application/json" \
     -d '{"csv_path": "/absolute/path/to/historical_ads.csv"}'
```

*Note: Add `"webhook_url": "https://your-server.com/webhook"` to any payload to run the simulation asynchronously.*

---
*Built with science. Designed for directional insights. $0 API cost.*
