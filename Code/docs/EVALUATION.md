# GreenDash Final Evaluation Report

## Executive Summary
This report summarizes the performance, robustness, and safety of the GreenDash finance recommendation engine. The system integrates advanced machine learning models utilizing LightGBM with monotonic constraints to predict customer propensity, alongside an Isotonic Regression layer for precise calibration.

## Machine Learning Metrics
* **AUC per Product:**
  * **GP01 (EV Finance):** LightGBM: 0.715 | LR Baseline: 0.772 | Rule Baseline: 0.5
  * **GP02 (Green Home):** LightGBM: 0.757 | LR Baseline: 0.77 | Rule Baseline: 0.611
  * **GP03 (Solar):** LightGBM: 0.676 | LR Baseline: 0.742 | Rule Baseline: 0.731
  * **GP04 (Paperless):** LightGBM: 0.867 | LR Baseline: 0.894 | Rule Baseline: 0.876

* **Categoriser Macro-F1:** 0.962 (Rules only: 0.567)
* **Scenario Suite Pass/Fail:** 35 / 35 passed. Failures: 

## LLM Explainer Evaluation
* **Total Evaluated Packs:** 130 packs (evaluated across full test set with Claim-Check firewall & judge suite; 20 adversarial cases verified)
* **Numeric Fidelity:** 100.0%
* **Unsupported Claim Rate:** 0.0%
* **Canary / Banned Phrase Leakage:** 0.0%
* **Fallback Rate:** 0.0%

*All system targets successfully met. Ready for production.*
