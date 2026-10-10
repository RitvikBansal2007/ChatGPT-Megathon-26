# Green Customer Insights Platform: Winning Product Strategy

### 1. Core Problem Definition

**Customers** are interested in greener choices (EVs, solar, efficient homes, going paperless). But they face a trust gap: they can't tell what's relevant to them, what it would really save, or whether the bank's claim is credible, so interest rarely becomes action. **Banks and portfolio managers** have green products and green-intent customers but no auditable bridge between the two. Today's carbon trackers stop at "here's your footprint" and can't produce defensible, regulator-safe, actionable opportunities.

The real problem is **trust and actionability**, not carbon measurement.

---

### 2. Analysis of the AI Research

**The Best Existing Approaches (proven, adopt as the foundation)**
- **Strict separation of roles.** All five responses agree: ML ranks (propensity), deterministic rules filter (eligibility), a rules-based carbon engine quantifies impact, and the LLM only explains. This is the brief's core rule and the judges' main lens.
- **Reason codes plus evidence timestamps** as the explainability backbone.
- **Documented, versioned emission factors** (DEFRA/DESNZ) with explicit baselines and "estimate" labelling.
- **Digital adoption reported separately from carbon.** The brief demands it.
- **Dual-view product** (customer cards and a business drill-down) and **customer-level data splits** with documented synthetic-label logic.

**The Gaps (where we can win)**
- Trackers (NatWest/Cogo, Doconomy, Personetics) stop at awareness. None clearly shows *propensity, eligibility and impact as three separate, visible verdicts*.
- Nobody shows **uncertainty honestly**. Tools present one confident number, though NatWest itself admits its figures are coarse averages.
- Nobody closes the loop: there is no "estimated vs. what actually happened" view, which is exactly the PCAF avoided-emissions criticism.
- Journeys are fragmented. The customer must bridge advice, assessment, finance and installer on their own.
- Data gaps are treated as failures, not as product moments.
- Most hackathon teams will build a chatbot plus charts. Few will make the system's *refusals* visible.

**The Goldmine (highest-innovation concepts)**
1. **Abstention as a first-class output** (Kimi). "Insufficient data" and "ruled out" are designed states, not errors.
2. **Machine-checked anti-greenwashing guardrail** (Kimi). Every LLM sentence is verified against the carbon engine before display, and the FCA's May 2024 rule gives it real regulatory weight.
3. **Confidence decomposition** (Perplexity). Completeness, recency, model certainty and out-of-distribution risk are shown separately instead of as one black-box score.
4. **Solar Confidence Ladder** and **"Why Now" temporal triggers** (Perplexity). Examples: mortgage just started, car finance ending, usage drifting up.
5. **Closed-loop verification** (Kimi). Estimated vs. realised impact after take-up.
6. **Readiness journey with a memory that never overrides ML or rules** (Perplexity/Grok), and **staged, bills-first framing** (Kimi). The strongest motivator is bill savings, not carbon.
7. **Fairness as a feature** (Kimi). A visible audit by income, age and region.
8. **Honesty about synthetic data** (Manus). Judges reward teams that don't overclaim.

**A caution on the research:** several statistics (mail-theft figures, Lloyds EV-share claims, the April 2027 loan scheme, exact emission factors) are unverified. Check each against a primary source before it goes on a slide. One wrong number undermines a pitch about trust.

---

### 3. The Proposed Winning Solution

## **GreenProof: the green recommendation that shows its receipts**

**Concept:** Every insight GreenProof produces is a **Proof Card**, a recommendation that carries its own receipt. The receipt shows three separate verdicts (Likelihood, Eligibility, Impact), the evidence behind each, how sure we are and why, and a visible stamp showing the explanation was checked against the numbers before the customer saw it. A second layer, **Promise vs. Proof**, tracks estimated impact against what customers actually did.

**Core value proposition:** "Carbon trackers tell you your footprint. GreenProof tells you your next step, proves why, admits what it doesn't know, and later shows whether it was right."

**Why it beats standard dashboards**
- **It makes trust the product.** Judges see responsible AI on screen, not in an appendix.
- **It turns weaknesses into features.** Missing data becomes a "Confidence Ladder" step and a one-tap question. Refusals become a "Why not?" view.
- **It speaks to both audiences.** Customers get a clear next action. Relationship teams get a ranked, evidence-backed pipeline tied to Lloyds' green-lending targets.
- **It has a live demo moment:** an injected hallucination gets caught and blocked in front of the judges.

**Pitch lines**
- "We treat greenwashing as a product-design problem: every sentence is checked before a customer sees it."
- "Our engine knows when to say 'I don't know.'"

---

### 4. Detailed Product Requirements

#### A. Customer Experience (UX)

**The four pathways** (EV Finance, Green Home, Solar Finance, Paperless) always appear as explorable options. A low score never hides a product. It just changes the card's prominence and wording.

**The Proof Card journey (exact flow):**

1. **The Insight (headline).** Lead with bills, then carbon, for example "Your fuel spend has run above your usual level for 4 months. An EV could be worth exploring." A small "Why now?" tag cites a real trigger, such as car finance ending in 90 days.
2. **The Evidence ("Why you're seeing this").** Plain-language reason codes with actual values and dates, for example "Fuel spend: £142/month avg, last 12 months (data as of 30 Sep)." Customer-declared facts are visibly distinguished from transaction-inferred ones.
3. **The Impact Calculation (tap to expand).** Show the estimated annual CO2e range, the formula in plain words, the baseline ("vs. your current petrol car"), the time horizon, and the factor source and year. Label it "Estimate, not a guarantee."
4. **Three separate badges, never merged:**
   - *Likelihood this suits you:* High / Medium / Low
   - *Eligibility:* "Checked by product rules: passed / needs verification / not eligible"
   - *Impact estimate quality:* Low / Medium / High, with the Confidence Ladder ("Add your annual mileage to sharpen this")
5. **The Claim-Check stamp.** "Every statement above was verified against our calculation engine." A tap shows which fields back each sentence.
6. **The Action.** One clear primary action ("Explore EV options"), with a staged secondary ("Start with a 2-minute suitability check"). A "Talk to a human" option is always available. Copy states "Not a credit decision."
7. **Feedback controls:** "Not relevant," "This is wrong," "Remind me later."

**Paperless card:** reports paper statements avoided and digital adoption as separate metrics, with *no* carbon claim unless a documented method supports it.

**Staged, not overwhelming:** for Green Home, show the cheapest high-return first step, not a £9k whole-house package.

**Promise vs. Proof (customer side):** after take-up, a gentle "You estimated 1,200 kg. Here's what your fuel spend shows so far."

#### B. Business / Portfolio Dashboard

**Drill-down path:** Portfolio → Segment → Customer → Opportunity → Evidence → Impact → Action

- **Level 1, Portfolio:** headline tiles with CO2e (estimated vs. realised, never netted), energy (kWh), paper statements avoided, and digital adoption (separate), plus the opportunity funnel (identified → eligible → surfaced → engaged → taken up). Everything is labelled estimate or realised.
- **Level 2, Opportunity quadrant** (propensity × impact × confidence). The four zones carry different actions:
  - High propensity, high impact, strong evidence → relationship-manager call list
  - High impact, low confidence → data-enrichment prompt
  - High propensity, low impact → lightweight digital nudge (paperless)
  - High impact, low propensity → education content, no hard sell
- **Level 3, Customer 360:** profile with data freshness, product history, reason codes, and the three verdicts.
- **Level 4, Evidence and Impact:** source data, formula, factor version, confidence breakdown.
- **Level 5, Action:** auto-generated relationship-manager brief, campaign suggestion, memory timeline.
- **Governance tab:** fairness audit by income, age and region; abstention rate; claims blocked by the checker; calibration by segment; synthetic-data banner.

#### C. Edge Cases and Scenario Handling

| Scenario | Product behaviour |
|---|---|
| **Missing data** | Show "Not enough information to estimate," never a made-up number. Offer a one-tap data-completion step (mileage, bill upload). Demote the card to a "suitability check" action. |
| **Conflicting data** (vehicle record says EV, fuel spend is high) | Show a "We're seeing mixed signals" state, lower confidence, hide the impact number, ask one confirming question. Possibly a second car or a hybrid. |
| **Hard exclusion** (existing EV, already has solar, non-homeowner) | Card becomes "Not recommended" with a plain reason. A "Why not?" view makes the exclusion visible and shows the system working. |
| **Changed circumstances** (customer just sold their car) | Event-driven re-evaluation. The EV insight is retired immediately, replaced by "Your circumstances changed, so we've paused this suggestion." Fuel-spend drop and customer feedback both trigger it. The memory logs the reason and suppresses it. |
| **Stale data** | Insights past a freshness threshold show an "Is this still right?" check. |
| **Dismissed repeatedly** | Suppress after three dismissals. Memory changes delivery and timing, never the underlying propensity, eligibility or carbon number. |
| **Vulnerability indicators** | Suppress finance prompts, route to a human, apply Consumer Duty-aligned tone. |

#### D. Explainability and Responsible AI (key judging criterion)

**Hallucination-proof**
- The LLM only rewrites approved structured results. All figures come from the carbon engine.
- A **sentence-level claim check** blocks new numbers, unsupported claims, and banned words ("guaranteed," "approved," "will save").
- Failed output is replaced by safe template copy.
- Customers can hover over any sentence to see its source field.
- **Live demo:** inject a fake claim and show it blocked, with the block counter on the business dashboard.

**Unbiased**
- A "What we used / what we didn't" panel states that age, income and fine-grained postcode are not used to drive recommendations.
- Fairness audit shown on the governance tab (recommendation rates and error rates by income, age and region).
- The loan-based, not subsidy-based, framing is noted as progressive.
- A plain statement that "likelihood is not worthiness or creditworthiness."

**Privacy-preserving**
- The LLM sees only a minimal, customer-scoped structured object: no raw transactions, names or other customers' data.
- Pseudonymous IDs, visible data-purpose note, and a customer control to switch off insights.

**Honest by design**
- The three verdicts are always separate.
- Avoided emissions are shown separately and never netted against a bank's own footprint, with a stated counterfactual for each number.
- A persistent synthetic-data banner and a "known limitations" note. Admitting what the demo cannot prove will score better than overclaiming.

---

### Suggested Demo Storyline (5 minutes)

1. **Paperless customer:** a quick win showing the metrics separated.
2. **EV candidate:** full Proof Card, impact calculation, Claim-Check stamp.
3. **Solar candidate with a missing roof:** Confidence Ladder and "suitability check."
4. **Existing EV owner:** the "Why not?" refusal. **Then sell their car:** the insight retires live.
5. **Hallucination trap:** a blocked fake claim.
6. **Business dashboard drill-down** from portfolio to a single customer's evidence, ending on the fairness and governance tab.

**Where to spend your time:** judges will forgive a plain UI more readily than a weak data, validation or guardrail story. Prioritise the synthetic data with documented rules, the three-verdict separation and the claim checker, then layer on memory and Promise vs. Proof if time allows.