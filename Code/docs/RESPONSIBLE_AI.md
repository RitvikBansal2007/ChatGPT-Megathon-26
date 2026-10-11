# Responsible AI note

## Privacy

- All data is synthetic. No real customer or account data is loaded at any point.
- The provided smart-meter dataset is reduced to aggregate statistics; no household ID or reading is stored.
- The language model receives a minimised evidence pack: product, status, reason codes with values, and display strings already formatted by the engine. No name, customer ID, postcode, balance or raw transaction text is sent. An input guard rejects packs containing personal data.
- Database rows are keyed by a keyed hash of the customer ID. Free-text feedback is encrypted with AES-256-GCM.
- Small groups (fewer than 10 customers) are suppressed in every aggregate view.

## Bias and fairness

- Age, income band and fine-grained postcode are not model inputs.
- The Cockpit's Governance tab reports recommendation and abstention rates by income band and age band so that differences are visible.
- Likelihood is never presented as creditworthiness. Every card states "Not a credit decision".
- Customers with an accessibility need for paper statements are never nudged towards paperless (rule GP04-R2).

## Explainability

- Three verdicts are shown separately and never blended: likelihood (model), eligibility (rules), impact (carbon engine).
- Each card lists reason codes with value, date and whether the fact was declared or inferred, the confidence score with its four parts, the formula, the baseline and the factor source.
- A product that is ruled out shows the rule that fired, in plain words.

## Hallucination

- The model never calculates, predicts or decides eligibility. It rewrites facts it is given.
- Claim-Check verifies every sentence: numbers must exist in the pack, cited fields must exist, banned promises are blocked, paperless may not be described as carbon, and nothing may be recommended for a ruled-out or under-review status.
- A failed sentence is regenerated once and then replaced by fixed wording. Refusals are always explained by fixed rule wording, not by the model.
- A secret canary token in the prompt detects prompt leakage; leakage in evaluation is zero.
- Measured results are in `docs/EVALUATION.md` and on the Receipts page.

## Human oversight

- Conflicting records produce a REVIEW status that routes to a person instead of a recommendation.
- Every card offers "Talk to a person" and a "Not quite right?" feedback route; customers can switch insights off.
- Relationship managers see the evidence before acting; every Claim-Check result is written to an append-only, hash-chained audit table that an auditor can verify.

## Data limitations

- Labels are synthetic, generated from hidden traits plus noise. Metrics demonstrate a sound pipeline (held-out split, calibration, baselines), not real-world accuracy.
- Take-up is rare (2–6%), so held-out sets contain few positives and AUC differences of a few points are within noise. The model is level with a logistic-regression baseline.
- The confidence score has not yet been shown to track error.
- Impact figures are estimates built on published average factors and stated assumptions, shown as ranges. They are not measured outcomes.
- Emission factors are UK averages for 2024 and will need updating each year.
