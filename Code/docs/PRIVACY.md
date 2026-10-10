# Privacy and Security Controls (Data and AI lane)

Banking context: customer privacy is the top priority. These controls are enforced in code and tests, not just policy.

| Area | Control | Where |
| --- | --- | --- |
| Data origin | Fully synthetic population, seed 42. No real customer or account data is ever loaded. Public data is OGL/CC BY licensed priors only. | `greendash/generator`, `docs/LICENSES_DATA.md` |
| Licence gate | Sources without an approved licence are blocked before use. | `ingest/licence_gate.py` |
| Ingest hygiene | PII scan (emails, long digit runs) on every ingested table; drop-rate guard. | `ingest/sanitize.py` |
| PII detection | Patterns for email, IBAN, Luhn-valid card, sort code, account number, NI number, phone, postcode. | `security/privacy.py` |
| AI input minimisation | Models only see an allowlist of non-identifying fields. Unknown keys are dropped by default. Identifiers, address, balance, raw merchant text and the accessibility flag are forbidden outright. Strings are scrubbed. | `llm_payload` in `security/privacy.py` |
| Generalisation | Ages are shared as bands, not exact values. | `age_band`, eval sets |
| Pseudonyms | Keyed HMAC-SHA256; key read from `PSEUDONYM_KEY`, no default, fails closed. | `pseudonymise` |
| Output safety | Display strings restricted to a safe character set; no names or free text from customers reach the model. | `greendash/carbon/units.py` |
| Training data hygiene | Targets (`take_up_*`, `true_category`) never used as features; no single feature AUC above 0.80; persona rows held out of splits. | `eval/data_quality.py`, `docs/DATA.md` |
| Repo hygiene | Generated data, caches, keys and `.env` are gitignored; compiled caches (which embed local paths) are untracked. | `.gitignore` |
| Double-blind | Tests fail if personal, team or college names appear in tracked files. | `tests/unit/test_privacy.py` |

Rules for anyone extending this work:
1. Never put real customer data, API keys or secrets in the repo, notebooks or prompts.
2. Any new field sent to a model must be added deliberately to the allowlist and justified.
3. Never send raw transaction text to an external model; use the template category.
4. Keep synthetic data synthetic: no real merchant account numbers, names or postcodes.
5. Run `pytest tests/unit` and `python eval/data_quality.py` before every push.

Known limits: the PII patterns are heuristic (they reduce, not eliminate, risk); no encryption at rest is implemented in this lane (the security lane owns that); synthetic postcodes use a fake `XX` prefix.
