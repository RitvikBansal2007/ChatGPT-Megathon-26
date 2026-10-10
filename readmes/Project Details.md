# 🧾 GreenProof

> **The green recommendation that shows its receipts.** GreenProof turns everyday banking data into personalised, trustworthy green next steps for customers, and an evidence-backed opportunity pipeline for the bank, where every number has a source, every refusal is explained, and every AI-written sentence is checked before anyone sees it.

---

## 🚨 The Problem

Customers want to make greener choices: switching to an EV, insulating their home, installing solar, going paperless. Banks already offer green products to support these choices. **Yet interest rarely turns into action.**

**The friction point is trust and actionability, not carbon measurement.**

- **For customers:** they can't tell which green options are relevant to *them*, what a switch would really save, or whether the bank's claim is credible. The journey is fragmented, so the customer is left to connect advice, assessment, finance and installation on their own.
- **For banks and relationship teams:** they have green products and green-intent customers, but **no auditable bridge** between the two. They need to know who is likely to be interested, who is actually eligible, and what the realistic impact would be, without crossing into greenwashing.

**Why current solutions fall short:**

- **Carbon trackers stop at awareness.** They answer "what's my footprint?" but not "what should I do next, and why?"
- **They project false certainty.** A single confident number hides coarse averages and missing data.
- **They blur the lines.** Likelihood, eligibility and impact are often merged into one opaque "green score", which is exactly what a regulator, or a sceptical customer, cannot audit.
- **They treat gaps as failures.** Missing or conflicting data either breaks the experience or gets silently papered over with a default.

> 💬 **Key insight:** In green finance, an AI that sounds confident but can't show its working is a liability. The winning product is the one that makes **trust itself the feature**.

---

## 💡 Our Solution

**GreenProof** is an AI platform that analyses a customer's transactions, products and behaviour to surface green finance opportunities across four pathways (**EV Finance, Green Home, Solar Finance and Paperless Banking**), with a clear, honest explanation behind each one.

Every insight is delivered as a **Proof Card**: a recommendation that carries its own receipt. Each card shows:

- **Three separate verdicts that never merge:**
  - 🎯 **Likelihood**: how well this suits you (from a machine-learning model)
  - ✅ **Eligibility**: whether product rules allow it (from a deterministic rules engine)
  - 🌱 **Impact**: the estimated sustainability benefit, as a range with its formula (from a rules-based carbon engine)
- **The evidence behind each verdict**, with real values and dates, clearly marking what the customer declared versus what was inferred from transactions.
- **How confident the system is, and why**, so missing data is a visible prompt, never a hidden guess.
- **A Claim-Check stamp** confirming that every sentence of the explanation was verified against the underlying numbers.

One rule runs through the whole system and appears on every screen:

> **ML predicts. Rules decide eligibility. The carbon engine calculates. The LLM only explains. Claim-Check verifies.**

### 🛤 The Golden Path

**Customer view: from transaction data to a confident next step**

1. **Open the Customer Hub.** All four green pathways are always visible; a low score changes a card's prominence and wording, never hides it.
2. **See the headline insight, bills first.** For example, a commuter whose fuel spend runs above their usual range sees an EV Finance card with a **"Why now?"** tag, such as their car finance ending soon.
3. **Check the evidence.** Plain-language reason codes with actual values and data timestamps explain *why* this card appeared.
4. **Expand the impact estimate.** A low–high CO2e range, the formula in plain words, the baseline ("vs. your current petrol car"), the time horizon and the emissions-factor source, all labelled **"Estimate, not a guarantee."**
5. **Take one clear action.** A primary action ("Explore EV options"), a lighter staged option (a short suitability check), and a constant reminder: **"Not a credit decision."**

**Business view: from portfolio to a single customer's receipt**

Relationship and portfolio teams drill down through **Portfolio → Opportunity → Customer → Evidence → Impact → Action**, with emissions, energy, paper and digital-adoption metrics always reported **separately**.

**When the answer is "no" or "not sure", GreenProof says so, by design:**

| Status | What the customer sees |
|---|---|
| **RECOMMEND** | A full Proof Card with a clear next action |
| **SOFT_SURFACE** | Visible with lower prominence and educational wording |
| **ABSTAIN** | *"Not enough information to estimate"*, plus one question to unlock the estimate (the Confidence Ladder) |
| **REVIEW** | *"We're seeing mixed signals"*: impact hidden, one confirming question asked |
| **RULED_OUT** | A plain-language **"Why not?"** naming the exact rule that applied |

---

## 🚀 Why We Stand Out (Market Differentiation)

### The Competitive Gap

Existing carbon trackers and personalisation tools stop at **"here's your footprint."** None of them clearly separates propensity, eligibility and impact into independent, visible verdicts. They present a single confident number despite coarse underlying data, treat missing information as an error, and rarely show what the system *refused* to recommend. Most competing approaches lean on a chatbot plus charts, often letting the language model do the arithmetic.

### Our Edge

- 🛡️ **A greenwashing firewall, not just a disclaimer.** Our **Claim-Check** verifier sits between the LLM and the screen and checks every sentence: no number that isn't in the evidence, no unsupported claims, no banned phrases like *"guaranteed"*, *"will save"* or *"pre-approved."* If a sentence fails twice, a safe template takes over. In our live demo, we inject a fake claim and watch it get blocked in real time, while the "claims blocked" counter ticks up.

- 🧪 **Honesty as a product feature.** "I don't know" and "not for you" are designed states with their own wording and actions. Confidence is decomposed into **completeness, recency, model stability and in-distribution risk** instead of one black-box score, and it is validated: reliability improves as confidence rises. Missing data becomes a single, specific question, never a made-up number.

- 🔬 **Proof you can poke at.** The **Scenario Lab** lets anyone, judges included, mutate a customer live (*set the vehicle to EV, remove mileage, add a conflicting signal, make the data stale, mark as renter, sell the car*) and watch all three verdicts recompute with a before/after diff and the exact cause of each change. The same scenarios run as an automated test suite, so our handling of missing data, conflicting signals, ruled-out products and insufficient information is verified before anyone asks.

> 💬 **Why judges will remember this:** most demos only show the happy path. GreenProof's most memorable moments are the system **catching a lie and refusing a recommendation, live.**

---

## ⚙️ Core Features Being Implemented

### Phase 1: Foundation (Must-Haves)

- **🗃️ Synthetic Data Generator & Customer 360.** A seeded, fully documented generator creates a realistic population of 5,000 customers plus 8 named "golden personas", combined into one view per customer. Take-up labels are driven by hidden behavioural factors and noise, so the models must learn genuine patterns rather than recovering a simple rule. Every source carries a data timestamp, completeness score and conflict flags. *Benefit: credible, leak-free data that anyone can regenerate with one command.*

- **🏷️ Transaction Categoriser.** Every transaction gets exactly one of eight sustainability categories (Fuel, Electricity, Gas, Public Transport, Home Improvement, Automotive, Utilities, Other). Ordered keyword rules handle the clear cases and a lightweight text classifier handles the rest, with documented boundary decisions (for example, public EV charging counts as transport energy, and taxis count as Other). *Benefit: consistent, auditable spend signals, evaluated on merchants the model has never seen.*

- **📈 Calibrated Propensity Models with Validated Confidence.** One gradient-boosted model per product, calibrated so probabilities mean what they say, and benchmarked against two simple baselines. Customer-level train/validation/test splits plus an automated leakage test keep the results honest. Each prediction carries reason codes and a decomposed confidence score. *Benefit: a ranking you can trust, with measured lift over baseline.*

- **✅ Eligibility Rules Engine.** Deterministic, versioned product rules (for example, existing EV owner with no second vehicle, renter, existing solar, accessibility need for paper statements) return Eligible, Needs Verification or Not Eligible, along with the exact rule ID that fired. *Benefit: products the data rules out are never recommended, and the reason is always visible.*

- **🌱 Carbon Engine.** Pure, hand-tested functions compute impact from a pinned set of official UK government (DESNZ/Defra) emissions factors, each traceable to its source sheet and row. Outputs are low/central/high ranges with formula, baseline and time horizon, or an explicit "insufficient data" state naming what's missing. Paperless reports paper sheets saved and digital adoption, **never** a carbon claim. *Benefit: defensible, reproducible impact estimates.*

- **🧾 Proof Card Customer Hub & Portfolio Cockpit.** The customer experience described above, plus a business cockpit with four separate impact tiles (CO2e, energy, paper, digital adoption), an opportunity funnel, a propensity × impact quadrant, a segment table and the full drill-down to a single customer's evidence. *Benefit: one engine, two audiences.*

### Phase 2: The "Wow" Factor (Differentiators)

- **🛡️ Claim-Check Firewall + LLM Evaluation Harness.** A deterministic, sentence-level verifier with named rules covering numeric fidelity, cited fields, banned phrases, verdict consistency, metric separation, product naming and implied quantities ("halve", "double", percentages). The LLM sees only a minimal, pre-formatted evidence pack (no raw transactions, names or postcodes), and every check is logged to an audit trail. It is backed by a **150-case evaluation set** (personas × perturbations, prompt-injection attempts and hand-written adversarial sentences) comparing our governed pipeline with a naive prompt on fidelity, unsupported-claim rate, fallback rate, latency and cost.

- **🔬 Scenario Lab + Automated Scenario Suite.** A live panel with seven one-click mutations that recompute every verdict in under a second, showing the status transition, a field-level diff and the cause line (for example, *"Rule GP01-R1 fired"*). The Lab only ever edits inputs; an invariance test proves its outputs match a fresh run on the mutated data. More than 30 scenario cases run headlessly and render as a pass/fail table.

- **📊 Receipts Page.** A single page where every claim we make can be checked: lift versus both baselines, calibration curves, confidence-tier reliability, categoriser performance, LLM evaluation results, scenario pass/fail and the claims-blocked count. All of it is generated from one reproducible `make all` run.

---

## 🛠 Technical Architecture

GreenProof is one **Python 3.11** codebase built from pure-function engines behind typed contracts, so every component is independently testable and the whole pipeline reproduces from a single command.

- **Frontend:** **Streamlit** multi-page app (Customer Hub, Cockpit, Receipts) with **Plotly** visualisations. A `DEMO_MODE` switch (live / cached / fixtures) keeps the app running even with no network or API key.
- **Backend/Database:** **FastAPI** as a thin API layer over the engines; **Pydantic v2** typed contracts; **pandas + NumPy** with **Parquet** for data; **SQLite** for the claim audit trail and scenario runs; a **Makefile** for one-command, seeded, hash-manifested runs; **pytest** for carbon hand calculations, rules, leakage, invariance, the verifier and the scenario suite.
- **AI/APIs/Integrations:** **LightGBM** propensity models with isotonic calibration; **scikit-learn** (logistic regression baseline, TF-IDF categoriser, IsolationForest for in-distribution checks); **SHAP** for reason codes; one small **Anthropic or OpenAI** model at temperature 0, cached by input hash, with an always-on template fallback; official **DESNZ/Defra** emissions factors, pinned to a single vintage.

```text
Synthetic data ──> Categoriser ──> Feature store (Customer 360, timestamps, conflict flags)
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              ▼                            ▼                            ▼
       ML propensity               Eligibility rules               Carbon engine
   (+ confidence, reasons)        (+ rule IDs fired)          (range, formula, factors)
              └────────────────────────────┼────────────────────────────┘
                                           ▼
                     Orchestrator (assigns a status; never alters a verdict)
                                           ▼
                     LLM explainer ──> Claim-Check ──> pass / retry / template
                                           ▼
                        FastAPI ──> Streamlit (Customer Hub · Cockpit · Receipts)
```

> 💬 **Design principle:** the three verdicts are computed independently and passed downstream untouched. Nothing (not the orchestrator, the LLM or the Scenario Lab) is allowed to rewrite a prediction, an eligibility decision or an impact figure.

---

## 🔮 Future Scope

- **🔁 Promise vs. Proof.** Close the loop by tracking estimated impact against what actually happened after take-up (for example, *"You estimated this saving. Here's what your fuel spend shows so far."*), at both the customer and portfolio level. This addresses one of the strongest criticisms of avoided-emissions claims.

- **🧠 Persistent Customer Memory.** Remember past insights and customer responses ("Not relevant", "Remind me later") to adapt timing and delivery, including backing off after repeated dismissals, while never overriding the ML, rules or carbon engine outputs. This is paired with value-of-information prompts that ask for the single missing detail that would sharpen an estimate the most.

- **🏦 Expanded Products and Real-World Data.** Add Green Investments and Green Loans through the same catalogue and engines, a PCAF financed-emissions panel kept strictly separate from avoided-emissions estimates, Open Banking ingestion, and an installer marketplace that joins advice, assessment, finance and installation into one journey.

---

<sub>⚠️ GreenProof is built and evaluated entirely on synthetic data. All impact figures are modelled estimates, not measured results, and nothing in GreenProof is a credit decision.</sub>
