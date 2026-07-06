# Marketing Simulation Engine — The Digital Wind Tunnel 🌪️

**A digital wind tunnel that stress-tests your ad creative against 500+ AI-simulated consumers — each wired with real behavioral psychology — so you catch losing ads before wasting real budget, and understand exactly *why* they failed.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat-square&logo=plotly)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 🔴 The Problem This Solves

Billions are wasted annually on untested or poorly performing ad campaigns. Focus groups are too slow and expensive, while live A/B testing on platforms like Facebook or TikTok burns real budget on the "losing" variant before you even know it's failing. Nobody can effectively pre-test creative copy at scale without incurring real-world costs. **This tool solves that.**

## 🚀 What This Project Actually Does

You give it two ad variants. It spawns 500 AI‑simulated consumers, each with a distinct personality based on the Big Five (OCEAN) model — high Openness, high Neuroticism, high Conscientiousness, etc. These agents react to the ad through a Prospect Theory lens, valuing losses 2× more than gains. The simulation outputs not only a winner but a forensic breakdown of WHY the other ad failed (price sensitivity, channel mismatch, lost trust).

---

## ⚙️ Capabilities

| Capability | Description |
| :--- | :--- |
| **Psychographic Agent Simulation** | Models 500 unique OCEAN persona vectors to represent a diverse audience. |
| **Prospect Theory Engine** | Applies behavioral economics (loss aversion, probability weighting) to agent decisions. |
| **Multi‑channel A/B Testing** | Simulates performance across Facebook, TikTok, Instagram, Google, and Email. |
| **Neural Semantic Scoring** | Uses MiniLM sentence‑transformers to understand the semantic nuance of ad copy. |
| **Forensic Failure Analysis** | Diagnoses exact failure reasons (e.g., trust issues, price aversion) for losing variants. |
| **Live Streamlit Dashboard** | Provides interactive visualizations of engagement and conversion metrics. |
| **FastAPI Integration** | Enables programmatic access to run simulations via API endpoints. |
| **Calibration Module** | Tunes agent behavior for real‑world accuracy and platform-specific dynamics. |
| **Validation Pipeline** | Holdout validation against real ad CTR data with bootstrap confidence intervals. |
| **CLI for Batch Processing** | Run high-throughput A/B tests directly from the terminal. |

---

## 🏗️ The Engineering Decisions

**Why agent‑based modelling?**
Aggregate statistics obscure the nuances of human behavior. By simulating individual agents, we capture emergent, nonlinear responses to ad creatives that simple regression models miss.

**Why Prospect Theory?**
Humans are not perfectly rational actors. Prospect theory allows agents to exhibit real-world biases, such as loss aversion, ensuring their simulated decisions closely mimic actual consumer purchasing behavior.

**Why OCEAN?**
The Big Five personality traits provide a robust, scientifically validated framework for diverse consumer profiles, allowing the simulation to test ads against highly specific psychographic segments.

**Why NumPy‑only (no API costs)?**
Relying on external LLM APIs for 500+ agents per test would be prohibitively expensive and slow. A vectorized NumPy approach ensures lightning-fast execution with zero marginal cost.

**Why sentence‑transformers?**
They provide a lightweight, efficient way to extract semantic meaning from ad copy locally, without needing heavy API calls, allowing the engine to instantly "understand" the text.

**Why forensic analysis?**
Knowing which ad won isn't enough. Marketers need actionable insights. Forensic analysis reverse-engineers the simulation to explain exactly why specific personas rejected the losing ad.

**Why Streamlit + FastAPI?**
Streamlit allows for rapid iteration of a highly interactive, visual dashboard for end-users, while FastAPI provides a robust, asynchronous backbone for programmatic integration into larger marketing stacks.

---

## 🗺️ Architecture Diagram

```text
Ad Creative 
    │
    ▼
[ Neural Scorer (MiniLM) ]
    │
    ▼
[ Psychographic Agents (500+ OCEAN Vectors) ]
    │
    ▼
[ Prospect Theory Engine ]
    │
    ▼
[ Engagement Prediction ]
    │
    ▼
[ Forensic Analysis ]
    │
    ▼
Winner + Diagnosis
```

---

## ⚡ Getting Started

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Alchemist-PANDA/Marketing-Simulation.git
   cd Marketing-Simulation
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Dashboard:**
   ```bash
   streamlit run app.py
   ```

The app will run in **Local Mode** (no authentication, save/history disabled). To enable full features with Supabase, see the deployment guide below.

### Deployment

Deploy to Streamlit Community Cloud with Supabase backend for authentication, persistence, and multi-user support.

**Quick Start:**
1. Set up a Supabase project and run the migration
2. Deploy to Streamlit Cloud
3. Configure secrets (SUPABASE_URL, SUPABASE_ANON_KEY)

**Full Guide:** See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

---

## 📂 Project Structure

```text
Marketing-Simulation/
├── app.py                     # Streamlit interactive dashboard
├── api.py                     # FastAPI endpoints
├── cli.py                     # Command-line interface for batch runs
├── requirements.txt           # Project dependencies
├── .env.example               # Example environment configuration
├── src/                       # Core engine and modules
│   ├── agents/                # Psychographic agent logic
│   ├── simulation/            # Simulation and Prospect Theory engine
│   └── analysis/              # Forensic failure analysis
├── models/                    # Local NLP models (e.g., sentence-transformers)
├── data/                      # Calibration and persona datasets
└── docs/
    └── screenshots/           # Application screenshots and guides
```

---

## 🎯 Validation & Accuracy

The simulation engine is validated against a dataset of 20 unique Facebook ad texts with realistic CTR values (0.003-0.029 range).

| Metric | Value |
|---|---|
| **Directional Accuracy (all-pairs)** | 87.9% (167/190 pairs) |
| **Pearson Correlation** | 0.92 (p < 0.001) |
| **Spearman Rank Correlation** | 0.92 |
| **95% Bootstrap CI** | [0.80, 0.94] |

Directional accuracy measures pairwise concordance: given any two ads, how often does the simulation correctly predict which has higher CTR. This is a zero-shot evaluation — no weights were fit to the validation data. The keyword-based text scorer and the psychographic engine are the only components driving predictions.

**Methodology:** `scripts/holdout_validation.py` with fixed seed=42, 10,000 simulated agents, 200 bootstrap iterations. Results are fully reproducible.

---

<div align="center">
  <p>Built with 🧠 and Python.</p>
  <p>
    <img src="https://skillicons.dev/icons?i=python,fastapi,react,docker" />
  </p>
  <p>Licensed under MIT.</p>
  <h3>⭐ If you find this project useful, please consider giving it a star! ⭐</h3>
</div>
