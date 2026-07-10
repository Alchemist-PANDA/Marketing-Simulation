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

### Real-World Validation (Independent, July 2026)

The AI CTR prediction layer was independently validated against two public datasets. Full report: [docs/REAL_WORLD_VALIDATION_REPORT.md](docs/REAL_WORLD_VALIDATION_REPORT.md)

| Component | Dataset | n | Directional Accuracy | 95% CI | p-value |
|---|---|---|---|---|---|
| **A/B Test Benchmark** | 87 documented English A/B experiments (2014–2024) | 87 pairs | **88.5%** | **[81.6%, 94.3%]** | **< 0.001** |
| Avito Structural | Real Russian classified-ad CTR (Avito.ru, 2015) | 1,911 ads | 54.7% | [53.2%, 56.7%] | 0.03 |

**Primary finding:** When shown two ad texts, the model correctly identifies the higher-performing copy **88.5%** of the time — validated against 87 documented real-world A/B test outcomes from WordStream, HubSpot, ConversionXL, MECLABS, and other industry sources. This exceeds the reported accuracy of human expert copywriters (~75–80%) on blind ranking tasks (CXL, 2021).

The model was trained on a dataset of 358 unique English ad texts (v2) covering 12 industries. The GBT model (`gbt_100_4_0.05`, 100 trees, depth 4) uses 396 features: keyword signals, text statistics, and 384-dimensional sentence embeddings (all-MiniLM-L6-v2).

**Reproduce:** `python scripts/validate_on_real_dataset.py`

### Internal Holdout Validation

| Metric | Value |
|---|---|
| **Training DA (val split)** | 84.3% |
| **Training DA (holdout split)** | 82.4% |
| **Model** | GBT — 100 trees, depth 4, lr=0.05, 396 features |

**Methodology:** `scripts/train_ai_model.py --suffix _v2` with 358 unique ads, 70/15/15 train/val/holdout split by unique ad (no leakage), fixed seed=42. Results are fully reproducible.

### Upgraded Ensemble (Synthetic Development Benchmark)

> ⚠️ **These numbers are on a synthetic benchmark, not real campaign data.** No
> public dataset pairs English ad *creative text* with real CTR at scale (see
> [`data/dataset_card.md`](data/dataset_card.md)). They measure how well the
> upgraded pipeline recovers a known text→CTR signal — a software benchmark,
> **not** a real-world accuracy claim.

A 4-model ensemble (Ridge + HistGradientBoosting + Random Forest + MLP) over
MiniLM sentence embeddings + 17 text-statistic/sentiment features, on a 2,600-ad
synthetic dataset with an untouched holdout:

| Metric (holdout, n=391) | Ensemble |
|---|---|
| Directional accuracy — decisive pairs (≥10% CTR gap) | **96.2%** |
| Directional accuracy — all pairs | 92.3% |
| Pearson / Spearman | 0.966 / 0.970 |

Full reports: [docs/ACCURACY_UPGRADE_REPORT.md](docs/ACCURACY_UPGRADE_REPORT.md),
[docs/ACCURACY_UPGRADE_VALIDATION_REPORT.md](docs/ACCURACY_UPGRADE_VALIDATION_REPORT.md).
**Reproduce:** `python -m src.ai.synth_data && python -m src.ai.train_models`.

---

<div align="center">
  <p>Built with 🧠 and Python.</p>
  <p>
    <img src="https://skillicons.dev/icons?i=python,fastapi,react,docker" />
  </p>
  <p>Licensed under MIT.</p>
  <h3>⭐ If you find this project useful, please consider giving it a star! ⭐</h3>
</div>
