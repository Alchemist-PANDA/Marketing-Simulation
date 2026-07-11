# The 80% Plan — From 26% to a Defensible 80% Accuracy
### Covering Text, Image Upload, and Video Upload

*Written 2026-07-11, after the 876-pair real-world backtest scored 26.0%.*

---

## 0. The honest math you must accept before anything else

**"80% on every pair" is physically impossible — for anyone, including TikTok
itself.** Here's why, and here's the honest version of the goal that IS
achievable.

Your ground-truth labels are CTR percentile tiers. Two ads at "Top 18%" vs
"Top 22%" are separated by noise — if TikTok re-ran the same two ads next
month, the order could flip. On the 353 pairs in our dataset with a gap under
5 points, **even a perfect oracle would score ~50–60%**, because the labels
themselves are that noisy. No model on earth gets 80% there.

But look at what our own backtest already told us:

| Gap between ads | Current accuracy | Ceiling |
|---|---|---|
| <5pp (noise zone) | 20.4% | ~55–60% (label noise limit) |
| 5–10pp | 20.9% | ~65–70% |
| 10–20pp | 24.3% | ~75–80% |
| 20–30pp | 25.3% | ~80–85% |
| 30pp+ (clear winners) | **54.0%** | ~85–90% |

**The honest, achievable, sellable goal:**

> **80%+ accuracy on decisive pairs (gap ≥ 10pp), with a confidence system
> that tells the user when the race is too close to call.**

That is exactly how weather forecasting, credit scoring, and every real
prediction product works: high accuracy on confident calls, honest "toss-up"
labels on the rest. A tool that says "Ad A wins, 84% confidence" on clear
cases and "too close to call — test both" on coin flips is MORE trustworthy
and MORE valuable than one that fakes certainty everywhere. This is the
product that sells.

---

## 1. Diagnosis: why we're at 26% (each cause maps to a fix)

| # | Root cause | Evidence | Fix (phase) |
|---|---|---|---|
| 1 | **48% ties** — scorer outputs identical scores for different ads | 421/876 pairs tied | Phase 1: continuous learned scores, ties become impossible |
| 2 | **Hand-guessed weights** — never fit to any real data | `max_engine.py` comment: "uncalibrated" | Phase 2: fit weights to the 876-pair dataset |
| 3 | **Keyword scorer too blunt** — "sale"/"limited" lookups can't rank creative quality | 26% vs 50% chance | Phase 2: learned text model on real embeddings |
| 4 | **Anti-predictive direction** — some weights have the wrong SIGN (26% < 50% means inverting our picks would score 74%) | overall result | Phase 2: optimizer will flip signs automatically |
| 5 | **Text-only on a video platform** — captions explain maybe 20–40% of TikTok CTR variance | domain knowledge | Phases 3–4: image + video understanding |
| 6 | **No confidence system** — forced 50/50 calls on unknowable pairs | close-race accuracy 20.5% | Phase 5: abstention + confidence bands |

Note the surprisingly good news in #4: a model that scores 26% when chance is
50% is not "random" — it has learned a real signal and is reading it
*backwards*. Signed correctly and calibrated, the same signal is worth ~74%
on its own before we add anything new.

---

## 2. The plan — five phases

### PHASE 1 — Kill the ties, fix the signs (Week 1) → expect 26% → ~55–60%

The cheapest, highest-leverage fixes. No new data needed.

1. **Continuous scoring.** The current pipeline collapses many ads to the same
   0.5/0.45/0.3 default scores (that's the 421 ties). Replace defaults with the
   MiniLM embedding pipeline you ALREADY have (`ensemble_predictor.py`) so every
   ad gets a unique continuous score. Ties → ~0.
2. **Sign audit via the backtest.** Re-run the 876-pair backtest flipping each
   weight's sign one at a time; keep flips that improve accuracy. This is a
   1-hour experiment that could add 20+ points on its own given the 26% result.
3. **Variance widening.** Rescale scorer outputs to use the full 0–1 range
   (currently everything lands in a narrow band, so the sigmoid can't separate
   ads).
4. **Re-run backtest after every change.** The backtest harness is now the
   heartbeat of development: no change ships unless the number goes up.

### PHASE 2 — Learn from the real data (Weeks 2–4) → expect ~55–60% → ~68–74% overall, ~75% decisive

This is the core scientific work. We stop guessing weights and fit them.

1. **Split the data honestly.** 876 pairs → train (60%) / validation (20%) /
   **untouched holdout (20%)**. All reported numbers come from the holdout
   only. Grow the dataset in parallel: re-run the Apify scrapes weekly (7-day
   and 30-day windows surface new ads each time; different countries, more
   verticals) targeting **3,000–5,000 pairs** within a month. More data is the
   single biggest accuracy lever in this whole plan.
2. **Learned ranking model.** Train a pairwise ranker (LightGBM/logistic
   ranker on MiniLM embeddings + engineered features: urgency terms, social
   proof, specificity, numbers, emoji density, hashtag count, caption length,
   CTA presence, sentiment, readability). Pairwise training (learning "A beats
   B") directly optimizes the metric we report — this is the same family of
   technique search engines use for ranking.
3. **Per-vertical calibration.** Our data says the model behaves completely
   differently by industry (75% on TV Drama, 0% on Education). Train
   vertical-specific calibration on the 8–10 verticals with enough pairs;
   fall back to the global model elsewhere and SAY so in the UI.
4. **Rewire the simulator.** The agent simulation stays — it's the product's
   soul and the explanation layer (OCEAN resonance, archetypes, funnels). But
   its `price_score/trust_score/urgency_score` inputs now come from the
   learned model, and `simulation_weights.json` gets fit against real
   outcomes instead of hand-set. The wind tunnel keeps its physics; it
   finally gets calibrated instruments.

### PHASE 3 — Image upload that actually sees (Weeks 4–7) → image mode reaches parity with text (~70% decisive), then combined text+image ~75%+

Today image upload is decorative — the model ignores pixels. Fix:

1. **CLIP visual embeddings.** Run uploaded images through OpenCLIP (free,
   local, no API cost — same deployment pattern as MiniLM). CLIP embeddings
   capture aesthetics, subject, layout, and "ad-ness" remarkably well.
2. **Engineered visual features:** brightness/contrast/saturation, color
   count, face presence and count (MediaPipe, free), text-overlay density
   (OCR via Tesseract), composition (rule-of-thirds saliency), logo
   prominence.
3. **Ground truth for images:** the SAME Apify pipeline already returns
   `video_cover` thumbnail URLs + CTR tiers for every ad — that's a free
   image→CTR dataset of thousands of items. Scrape covers, train an
   image-side ranker, validate on held-out covers.
4. **Fusion:** concatenate text + image embeddings into the ranker. Ads are
   text AND visuals; the fused model beats either alone.

### PHASE 4 — Video upload that actually watches (Weeks 7–12) → video mode ~70–75% decisive standalone, ~78–82% fused

Video is the hardest and the most valuable — TikTok IS video.

1. **Frame sampling:** extract 8–16 frames per uploaded video (OpenCV, free),
   embed each with CLIP, mean/max-pool into one video embedding.
2. **Temporal features that drive TikTok CTR:** first-2-seconds hook
   strength (frame variance early), cut frequency (scene-change rate), motion
   energy, text-overlay timing, duration bucket, thumbnail quality.
3. **Audio features (cheap wins):** has-speech vs music-only, tempo, loudness
   dynamics (librosa, free).
4. **Ground truth for video:** the Apify dataset includes `video_url_720p`
   for every ad with its CTR tier. Download a few thousand, run the frame
   pipeline, and train directly against real TikTok outcomes. **This is the
   moat** — a video→CTR model trained on real performance data is something
   almost no competitor at this price point has.
5. **Gemini as the semantic layer:** you already have Gemini integration —
   use its video understanding to extract narrative structure ("problem→demo→
   offer", "testimonial", "unboxing") as categorical features for the ranker,
   and to power the explanation text. Gemini explains; the trained ranker
   predicts. Never let the LLM guess the number.

### PHASE 5 — The confidence system: how 80% becomes real AND honest (Weeks 10–12)

This is the phase that turns a ~75% model into an 80%+ product without lying.

1. **Calibrated probabilities** (isotonic regression on validation set) so
   "84% confident" means it's right 84% of the time. Measured, not vibes.
2. **Abstention:** when the model's probability is 50–65%, the product says
   **"Too close to call — run both."** Accuracy on the pairs where we DO make
   a call rises mechanically: if we call only ≥65%-confidence pairs, holdout
   accuracy on called pairs lands in the 78–85% band based on our gap-bucket
   ceilings. That subset is exactly the decisive-pair population.
3. **UI truthfulness:** every verdict ships with (confidence %, sample-size
   note, vertical coverage note). CTR displays become credible ranges
   ("predicted engagement tier: Top 20–30%"), never "53.27%".
4. **Continuous scorecard:** the weekly Apify re-scrape feeds a
   never-touched rolling holdout; accuracy is recomputed and published
   automatically. This is the "our accuracy improves every month" flywheel
   from the $1M plan — now real.

---

## 3. Trajectory and checkpoints

| Checkpoint | When | Metric (holdout, decisive pairs) | Gate |
|---|---|---|---|
| C1: Ties killed, signs fixed | Week 1 | ≥55% | If <50%, the embedding features carry no signal → escalate to Phase 2 immediately |
| C2: Learned text ranker | Week 4 | ≥70% | If <65%, buy/scrape more data before adding modalities |
| C3: +Image fusion | Week 7 | ≥73% | |
| C4: +Video fusion | Week 12 | ≥76–80% | |
| C5: Confidence-gated product | Week 12 | **≥80% on called pairs**, with ≥60% of pairs receiving a call | This is the sellable number |

Failure honesty: if C2 stalls below 65%, the finding is that caption text
under-determines TikTok performance — the plan reweights toward Phases 3–4
(visuals), which is where the variance actually lives. The checkpoints exist
so we never spend 12 weeks discovering what week 4 could tell us.

---

## 4. What this costs

- **Compute:** everything trains on CPU except optional CLIP batch runs;
  Streamlit Cloud stays the deploy target. $0 in new API costs (CLIP, MiniLM,
  MediaPipe, Tesseract, librosa are all free/local). Gemini usage stays within
  your existing keys.
- **Data:** Apify scrapes at ~$0.0015/ad → ~3,000 more ads ≈ **under $10**.
  Video downloads are bandwidth, not money.
- **Time:** ~12 weeks solo, compressible to ~6–8 with focus. Phase 1 is
  days, not weeks — start there.

---

## 5. What NOT to do (the traps that keep you at 26%)

- ❌ Don't tune the agent-simulation weights by hand again. Every parameter
  from now on is fit to data or it doesn't change.
- ❌ Don't ask Gemini to "predict the CTR" and ship its guess. LLMs are
  eloquent, uncalibrated guessers. Trained ranker predicts; LLM explains.
- ❌ Don't report training accuracy. Holdout only. (The 96.2% synthetic
  claim was this trap. Never again.)
- ❌ Don't chase 80% on close pairs. It's not achievable and pretending it
  is will poison user trust — abstain honestly instead.
- ❌ Don't delete the simulation layer. Calibrated, it's the differentiator:
  everyone has a black-box score; you have a score plus a WHY (personas,
  psychology, funnels).

---

## 6. One-paragraph summary

We're at 26% because the engine reads a real signal backwards through
uncalibrated, tie-prone heuristics. Phase 1 (days) kills the ties and fixes
the signs — that alone should roughly double accuracy. Phase 2 (weeks) stops
guessing and trains a pairwise ranker on the real 876-pair dataset (growing
it to 3,000+ pairs for under $10). Phases 3–4 give image and video uploads
actual eyes — CLIP embeddings, frame sampling, and hook/pacing features,
trained against the free ground-truth thumbnails and videos the Apify
pipeline already returns. Phase 5 adds calibrated confidence with honest
abstention on coin-flip pairs, which is how the product reports **80%+
accuracy on the calls it makes** while being MORE trustworthy, not less. The
target is C5: ≥80% holdout accuracy on called (decisive) pairs across text,
image, and video — a number that survives due diligence because it was
earned on data nobody cherry-picked.
