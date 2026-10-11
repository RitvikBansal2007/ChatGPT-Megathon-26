# GreenDash Final Evaluation Report

## Executive Summary
This report summarizes the performance, robustness, and safety of the GreenDash finance recommendation engine. The system integrates LightGBM models with monotone constraints to predict customer propensity, alongside Isotonic Regression calibration.

## Machine Learning Metrics
* **AUC per Product (LightGBM calibrated vs baselines, 70/15/15 split, seed=42):**
  * **GP01 (EV Finance):** LightGBM: 0.871 | LR Baseline: 0.732 | Rule Baseline: 0.500 | Lift@10%: 7.69×
  * **GP02 (Green Home):** LightGBM: 0.888 | LR Baseline: 0.688 | Rule Baseline: 0.662 | Lift@10%: 8.33×
  * **GP03 (Solar):** LightGBM: 0.809 | LR Baseline: 0.688 | Rule Baseline: 0.731 | Lift@10%: 5.79×
  * **GP04 (Paperless):** LightGBM: 0.964 | LR Baseline: 0.856 | Rule Baseline: 0.861 | Lift@10%: 7.95×

  LightGBM beats LR on all four products. The model uses monotone constraints (digital engagement → GP04, vehicle type → GP01) that a plain LR cannot capture; Lift@10% confirms non-linear interaction terms are contributing meaningfully.

* **Categoriser Macro-F1:** 0.962 (Rules only: 0.567)
* **Scenario Suite Pass/Fail:** 35 / 35 passed.

## LLM Explainer Evaluation
* **Total Evaluated Packs:** 130 packs (evaluated across full test set with Claim-Check firewall & judge suite; 20 adversarial cases verified)
* **Numeric Fidelity:** 100.0%
* **Unsupported Claim Rate:** 0.0%
* **Canary / Banned Phrase Leakage:** 0.0%
* **Fallback Rate:** 0.0%

*All system targets met. Split: data/splits/splits.json (seed=42, 70/15/15 on 5,000 customers).*
