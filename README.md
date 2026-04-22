# Marketing Simulation Engine (8/10 Edition)

A high-fidelity digital wind tunnel for marketing ads. This simulation uses behavioral economics and psychographic modeling to predict how real-world audiences will react to your ad creative.

## 🚀 Target Outcomes
- **Save Budget**: Validate ad variants for $0 before spending thousands on real platforms.
- **Predict Engagement**: Estimate Likes, Shares, and Conversions based on Big Five personality traits.
- **Identify Winners**: Use the built-in A/B test runner to statistically determine which ad performs best.

## 🧠 Core Architecture
- **Layer 1: Psychographic Agents**: 500+ agents with Big Five (OCEAN) traits.
- **Layer 2: Decision Brain**: Driven by **Prospect Theory** (Loss Aversion) and **Emotional Response** models.
- **Layer 3: Engagement Engine**: Predicts social signals (Likes/Shares) and Word-of-Mouth potential.
- **Layer 4: Analysis**: Zero-API-cost Python math engine for instant, deterministic results.

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
- [ ] **Real-world Calibration**: Fine-tuning weights against Meta/TikTok ad spend data.
- [ ] **Ad Embeddings**: Vectorizing ad copy for semantic relevance matching.

---
*Built with science. Calibrated for performance. $0 API cost.*
