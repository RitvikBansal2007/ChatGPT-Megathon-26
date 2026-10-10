/* ==========================================================================
   greendash · synthetic demo data
   Every customer, number and factor label here is SYNTHETIC and ILLUSTRATIVE.
   No real statistics, no real emission-factor values. Factor references are
   placeholder labels; real values come only from the carbon engine with a
   verified, pinned DESNZ/Defra vintage.
   Shapes mirror the Evidence Pack contract in Architecture.md (section 1.5).
   ========================================================================== */
(function () {
  "use strict";

  var GD = (window.GD = window.GD || {});

  /* ------------------------------------------------------------ meta */
  GD.meta = {
    product: "greendash",
    cutoff: "2026-06-30",
    asOf: "30 Jun 2026",
    asOfShort: "30 JUN",
    outcomeWindowDays: 90,
    rulesVersion: "rules-1.0",
    factorLabel: "DESNZ 2025 · conversion factors (illustrative)",
    coreRule: "ML predicts. Rules decide eligibility. The carbon engine calculates. The LLM only explains. Claim-Check verifies.",
    synthetic: "Demo data. Every customer shown is synthetic.",
    disclaimer: "Not a credit decision.",
    likelihoodNote: "Likelihood is not creditworthiness.",
    estimateLabel: "Estimate, not a guarantee.",
    humanPath: "Talk to a person",
    freshnessDays: 180
  };

  /* ------------------------------------------------- pathways (GP01–GP04) */
  GD.pathways = [
    { id: "GP01", slug: "ev", name: "EV Finance", product: "GP01 EV Finance", icon: "car", family: "co2",
      action: "Explore EV options", secondary: "Start with a 2-minute suitability check",
      tagline: "Fuel spend and mileage against an electric alternative.",
      catalogue: "Finance for a new or used battery electric vehicle, replacing a petrol or diesel car." },
    { id: "GP02", slug: "home", name: "Green Home", product: "GP02 Green Home Loan", icon: "home-cut", family: "co2",
      action: "Explore home upgrades", secondary: "See the cheapest first step",
      tagline: "Heating and utility spend against a better-insulated home.",
      catalogue: "Borrowing for insulation, heating controls and heat pumps in a home you own. Staged: cheapest high-return step first." },
    { id: "GP03", slug: "solar", name: "Solar Finance", product: "GP03 Solar Finance", icon: "sun-roof", family: "co2",
      action: "Explore solar", secondary: "Check if your roof suits solar",
      tagline: "Electricity use against panels on your own roof.",
      catalogue: "Finance for rooftop solar panels (and optional battery) on a home you own." },
    { id: "GP04", slug: "paperless", name: "Paperless", product: "GP04 Paperless Banking", icon: "sheet-check", family: "paper",
      action: "Go paperless", secondary: "Choose which statements go digital",
      tagline: "Paper sheets saved and digital adoption. No carbon claim.",
      catalogue: "Switch statements and letters to digital. Reported as paper sheets and digital adoption only." }
  ];

  /* ------------------------------------------------- 4.5 status contract */
  GD.statuses = {
    RECOMMEND:    { cls: "recommend", label: "Worth exploring",              icon: "check-circle-fill", order: 1 },
    REVIEW:       { cls: "review",    label: "Mixed signals",                icon: "git-compare",       order: 2 },
    ABSTAIN:      { cls: "abstain",   label: "Need one thing",               icon: "help-circle",       order: 3 },
    SOFT_SURFACE: { cls: "soft",      label: "Good to know",                 icon: "lightbulb",         order: 4 },
    RULED_OUT:    { cls: "ruledout",  label: "Not for you, and here's why",  icon: "shield-check",      order: 5 }
  };
  GD.likelihood = {
    HIGH:   { cls: "high",   label: "High" },
    MEDIUM: { cls: "medium", label: "Medium" },
    LOW:    { cls: "low",    label: "Low" }
  };
  GD.eligibility = {
    PASSED:             { cls: "pass",  label: "Passed" },
    NEEDS_VERIFICATION: { cls: "needs", label: "Needs verification" },
    NOT_ELIGIBLE:       { cls: "no",    label: "Not eligible" }
  };
  GD.quality = { HIGH: 3, MEDIUM: 2, LOW: 1 };

  /* ------------------------------------------- eligibility rule catalogue */
  GD.rules = {
    "GP01-R1": { result: "NOT_ELIGIBLE", text: "You already have an electric vehicle and no replacement need on record.", change: "If you add a second car or your EV needs replacing, we'll re-check." },
    "GP01-R2": { result: "NOT_ELIGIBLE", text: "There's no vehicle on record for you right now.", change: "Your circumstances changed, so we've paused this suggestion. If you get a car again, we'll re-check." },
    "GP01-V1": { result: "NEEDS_VERIFICATION", text: "Your current car finance needs to be settled or transferred first. We'll check this with you.", change: "" },
    "GP02-R1": { result: "NOT_ELIGIBLE", text: "Green Home Loan is for homeowners, and our records show you rent.", change: "If you buy a home, we'll re-check." },
    "GP02-R2": { result: "NOT_ELIGIBLE", text: "You already have a Green Home Loan with us.", change: "We'll re-check when that loan is repaid." },
    "GP03-R1": { result: "NOT_ELIGIBLE", text: "Solar Finance is for homeowners, and our records show you rent.", change: "If you buy a home, we'll re-check." },
    "GP03-R2": { result: "NOT_ELIGIBLE", text: "Your home already has solar panels on record.", change: "If that record is wrong, tell us and we'll re-check." },
    "GP04-R1": { result: "NOT_ELIGIBLE", text: "You already receive all your statements digitally.", change: "Nothing to change. Your paper and digital figures are on the Progress tab." },
    "GP04-R2": { result: "NOT_ELIGIBLE", text: "You've told us you need paper statements, so we won't suggest switching.", change: "You can change this in Profile, Accessibility, at any time." }
  };

  /* --------------------------- illustrative engine coefficients (NOT DESNZ values) */
  GD.coef = {
    note: "Illustrative coefficients for the prototype only. Not DESNZ/Defra values.",
    evNetKgPerMile: 0.158,      // petrol factor minus EV kWh/mile × grid factor, combined
    evFuelSavingPerMile: 0.067, // £ per mile, fuel and servicing
    rangeLow: 0.79,
    rangeHigh: 1.21,
    homeGasShare: 0.2,          // first-step insulation saving share of gas kWh
    gasKgPerKwh: 0.18,
    gasPoundPerKwh: 0.07,
    solarKwhPerYear: 2900,
    elecKgPerKwh: 0.2,
    sheetsPerStatement: 4
  };

  /* ---------------------------------------------- reusable soft-surface copy */
  var SOFT = {
    GP01: { headline: "Running a car costs more each year. Here's how an EV compares for drivers like you.", bills: "Learn more" },
    GP02: { headline: "Homes like yours often start with a loft insulation top-up. Here's what to know.", bills: "Learn more" },
    GP03: { headline: "Your electricity use is around average. Solar may still be worth a look later.", bills: "Learn more" },
    GP04: { headline: "Paper statements are optional. Here's how digital statements work.", bills: "Learn more" }
  };

  function soft(gp, propensity, extra) {
    var o = {
      status: "SOFT_SURFACE", likelihood: propensity >= 0.4 ? "MEDIUM" : "LOW", propensity: propensity,
      eligibility: { result: "PASSED", rule: null }, impactQuality: "MEDIUM",
      headline: SOFT[gp].headline, whyNow: null, evidence: [], impact: null, ladder: null, review: null, whyNot: null,
      claim: { source: "template", sentences: [{ text: SOFT[gp].headline, fields: ["catalogue.education"] }] },
      actions: { primary: "Learn more", secondary: null }
    };
    for (var k in extra) o[k] = extra[k];
    return o;
  }

  function ruledOut(gp, rule, propensity, extra) {
    var r = GD.rules[rule];
    var o = {
      status: "RULED_OUT", likelihood: propensity >= 0.66 ? "HIGH" : propensity >= 0.4 ? "MEDIUM" : "LOW", propensity: propensity,
      eligibility: { result: "NOT_ELIGIBLE", rule: rule }, impactQuality: null,
      headline: "Not for you right now.", whyNow: null, evidence: [],
      impact: { status: "NOT_APPLICABLE" }, ladder: null, review: null,
      whyNot: { text: r.text, rule: rule, change: r.change },
      claim: { source: "template", sentences: [{ text: "Not for you right now. " + r.text, fields: ["eligibility.rule"] }] },
      actions: { primary: null, secondary: null }
    };
    for (var k in extra) o[k] = extra[k];
    return o;
  }

  var FACTOR = "DESNZ 2025 · conversion factors (illustrative)";

  /* ============================================================ personas */
  GD.personas = {

    /* ---- Priya: EV Finance RECOMMEND, Paperless quick win ---- */
    priya: {
      id: "CUST-0001", key: "cust_7f3a9c", name: "Priya", region: "South East",
      summary: "Commuter and homeowner. Eight-year-old petrol car, car finance ending soon.",
      tags: ["Commuter", "Homeowner", "Complete data"],
      products: [
        { name: "Current account", since: "Apr 2014", status: "Active" },
        { name: "Mortgage", since: "Mar 2019", status: "Active" },
        { name: "Car finance", since: "Sep 2022", status: "Ends 28 Sep 2026" }
      ],
      freshness: [
        { source: "Transactions", asOf: "30 Jun 2026", kind: "inferred" },
        { source: "Vehicle record", asOf: "14 May 2026", kind: "declared" },
        { source: "Energy usage", asOf: "31 May 2026", kind: "inferred" },
        { source: "Digital usage", asOf: "30 Jun 2026", kind: "inferred" }
      ],
      facts: {
        homeowner: true, vehicle: { fuel: "petrol", ageYears: 8, mileage: 9200, mileageSource: "inferred" },
        secondCar: false, fuelSpend: 142, carFinanceActive: true,
        energy: { elecKwh: 3100, gasKwh: 11800 }, epcKnown: true, solar: false, roofKnown: true, existingGreenHome: false,
        statementsPerYear: 12, digitalStatements: 9, digitalShare: 0.75, appUse: "Weekly", paperNeed: false,
        staleDays: 0, historyWeeks: 104,
        base: { GP01: 0.82, GP02: 0.38, GP03: 0.34, GP04: 0.71 },
        conf: { completeness: 0.86, recency: 0.92, stability: 0.84, inDist: 0.81 }
      },
      opp: {
        GP01: {
          status: "RECOMMEND", likelihood: "HIGH", propensity: 0.82,
          eligibility: { result: "NEEDS_VERIFICATION", rule: "GP01-V1" },
          impactQuality: "MEDIUM",
          headline: "Your fuel spend has run above your usual level for 4 months. An EV could be worth exploring.",
          whyNow: { text: "Your car finance ends in 90 days.", date: "30 Jun 2026", code: "CAR_FINANCE_ENDING" },
          evidence: [
            { code: "HIGH_FUEL_SPEND", label: "Fuel spend: £142 a month on average, last 12 months", date: "30 Jun 2026", source: "inferred" },
            { code: "FUEL_SPEND_RISING", label: "Above your usual level for 4 months in a row", date: "30 Jun 2026", source: "inferred" },
            { code: "EXISTING_VEHICLE", label: "Petrol car, 8 years old", date: "14 May 2026", source: "declared" },
            { code: "CAR_FINANCE_ENDING", label: "Car finance ends on 28 Sep 2026", date: "30 Jun 2026", source: "inferred" }
          ],
          impact: {
            status: "ESTIMATED", family: "co2", low: 1150, central: 1450, high: 1750, unit: "kg CO₂e a year",
            bills: "About £620 a year less on fuel and servicing, central estimate.",
            formula: "Yearly miles × (petrol car factor − EV energy per mile × grid electricity factor)",
            baseline: "Your current petrol car, same yearly mileage (about 9,200 miles, estimated from your fuel spend)",
            horizon: "12 months", factor: FACTOR, missing: []
          },
          confidence: { completeness: 0.86, recency: 0.92, stability: 0.84, inDist: 0.81 },
          ladder: { field: "annual_mileage", prompt: "Add your yearly mileage to sharpen this estimate.", cta: "Add mileage",
                    input: { type: "number", unit: "miles a year", min: 0, max: 100000, step: 100, placeholder: "e.g. 9,200" } },
          review: null, whyNot: null,
          claim: { source: "llm", sentences: [
            { text: "Your fuel spend has run above your usual level for 4 months.", fields: ["evidence.HIGH_FUEL_SPEND", "evidence.FUEL_SPEND_RISING"] },
            { text: "Switching to an EV could cut an estimated 1,150 to 1,750 kg CO₂e a year compared with your current petrol car.", fields: ["impact.low", "impact.high", "impact.baseline"] },
            { text: "Your car finance ends in 90 days, so this could be a good moment to compare options.", fields: ["why_now.CAR_FINANCE_ENDING"] }
          ] },
          actions: { primary: "Explore EV options", secondary: "Start with a 2-minute suitability check" }
        },
        GP02: soft("GP02", 0.38, {
          evidence: [{ code: "GAS_SPEND_TYPICAL", label: "Gas use: about 11,800 kWh a year, typical for your home", date: "31 May 2026", source: "inferred" }],
          impact: { status: "ESTIMATED", family: "co2", low: 280, central: 370, high: 460, unit: "kg CO₂e a year",
            secondary: { family: "energy", low: 1500, central: 2000, high: 2500, unit: "kWh a year" },
            bills: "About £140 a year less on heating, central estimate.",
            formula: "Yearly gas kWh × expected saving share of the first step × gas factor",
            baseline: "Your home as it is today, same heating habits", horizon: "12 months", factor: FACTOR, missing: [] }
        }),
        GP03: soft("GP03", 0.34, {
          evidence: [{ code: "ELEC_USE_TYPICAL", label: "Electricity use: about 3,100 kWh a year", date: "31 May 2026", source: "inferred" }],
          impact: { status: "ESTIMATED", family: "co2", low: 360, central: 440, high: 520, unit: "kg CO₂e a year",
            secondary: { family: "energy", low: 1800, central: 2200, high: 2600, unit: "kWh a year generated" },
            bills: "About £330 a year less on electricity, central estimate.",
            formula: "Expected solar kWh used at home × grid electricity factor",
            baseline: "All your electricity bought from the grid", horizon: "12 months", factor: FACTOR, missing: [] }
        }),
        GP04: {
          status: "RECOMMEND", likelihood: "HIGH", propensity: 0.71,
          eligibility: { result: "PASSED", rule: null }, impactQuality: "HIGH",
          headline: "3 of your 12 statements a year still arrive on paper. Going paperless takes about a minute.",
          whyNow: null,
          evidence: [
            { code: "PAPER_STATEMENTS", label: "Paper statements: 3 of 12 in the last year", date: "30 Jun 2026", source: "inferred" },
            { code: "HIGH_DIGITAL_ACTIVITY", label: "You use the app every week", date: "30 Jun 2026", source: "inferred" }
          ],
          impact: { status: "PAPER", paper: { value: 12, unit: "sheets a year", note: "About 4 sheets per statement" },
                    digital: { value: "75%", unit: "of your statements are digital", note: "9 of 12 statements" },
                    formula: "Paper statements a year × sheets per statement", baseline: "Your current statement settings", horizon: "12 months", factor: "Statement page counts (internal, illustrative)" },
          ladder: null, review: null, whyNot: null,
          claim: { source: "llm", sentences: [
            { text: "3 of your 12 statements a year still arrive on paper.", fields: ["evidence.PAPER_STATEMENTS"] },
            { text: "Switching them would avoid about 12 sheets of paper a year.", fields: ["impact.paper"] },
            { text: "Your digital adoption is reported on its own, next to paper sheets.", fields: ["impact.digital"] }
          ] },
          actions: { primary: "Go paperless", secondary: "Choose which statements go digital" }
        }
      }
    },

    /* ---- Marcus: EV REVIEW (mixed signals), Green Home ABSTAIN ---- */
    marcus: {
      id: "CUST-0002", key: "cust_2b81e4", name: "Marcus", region: "North West",
      summary: "Vehicle record says electric, but fuel spend continues. Home efficiency data missing.",
      tags: ["Mixed signals", "Homeowner", "Stale EPC"],
      products: [
        { name: "Current account", since: "Jan 2017", status: "Active" },
        { name: "Mortgage", since: "Aug 2020", status: "Active" }
      ],
      freshness: [
        { source: "Transactions", asOf: "30 Jun 2026", kind: "inferred" },
        { source: "Vehicle record", asOf: "2 Mar 2026", kind: "declared" },
        { source: "Energy rating (EPC)", asOf: "Not on record", kind: "declared" }
      ],
      facts: {
        homeowner: true, vehicle: { fuel: "bev", ageYears: 2, mileage: 10400, mileageSource: "declared" },
        secondCar: false, fuelSpend: 96, carFinanceActive: false,
        energy: { elecKwh: 4200, gasKwh: 14100 }, epcKnown: false, solar: false, roofKnown: true, existingGreenHome: false,
        statementsPerYear: 12, digitalStatements: 6, digitalShare: 0.5, appUse: "Monthly", paperNeed: false,
        staleDays: 0, historyWeeks: 160,
        base: { GP01: 0.58, GP02: 0.55, GP03: 0.32, GP04: 0.44 },
        conf: { completeness: 0.74, recency: 0.88, stability: 0.8, inDist: 0.77 }
      },
      opp: {
        GP01: {
          status: "REVIEW", likelihood: "MEDIUM", propensity: 0.58,
          eligibility: { result: "PASSED", rule: null }, impactQuality: null,
          headline: "We're seeing mixed signals about your car.",
          whyNow: null,
          evidence: [
            { code: "VEHICLE_BEV_ON_RECORD", label: "Vehicle record: battery electric", date: "2 Mar 2026", source: "declared" },
            { code: "FUEL_SPEND_CONTINUES", label: "Fuel spend: £96 a month on average, last 3 months", date: "30 Jun 2026", source: "inferred" }
          ],
          impact: { status: "HIDDEN", reason: "Impact hidden until the conflict is resolved." },
          ladder: null,
          review: {
            message: "We're seeing mixed signals: your vehicle record says electric, but you still spend on fuel.",
            question: "Is there a second car in the household?",
            options: ["Yes, we have a second car", "No, it's a plug-in hybrid", "No, the vehicle record is wrong", "Not sure"]
          },
          whyNot: null,
          claim: { source: "template", sentences: [
            { text: "We're seeing mixed signals: your vehicle record says electric, but you still spend on fuel.", fields: ["evidence.VEHICLE_BEV_ON_RECORD", "evidence.FUEL_SPEND_CONTINUES"] },
            { text: "We've hidden the impact estimate until this is cleared up.", fields: ["impact.status"] }
          ] },
          actions: { primary: "Answer one question", secondary: null }
        },
        GP02: {
          status: "ABSTAIN", likelihood: "MEDIUM", propensity: 0.55,
          eligibility: { result: "PASSED", rule: null }, impactQuality: "LOW",
          headline: "Not enough information to estimate this one yet.",
          whyNow: null,
          evidence: [
            { code: "HIGH_WINTER_GAS", label: "Winter gas spend above similar homes, last 2 winters", date: "30 Jun 2026", source: "inferred" },
            { code: "EPC_MISSING", label: "Home energy rating: not on record", date: "Not on record", source: "declared" }
          ],
          impact: { status: "INSUFFICIENT_DATA", family: "co2", missing: ["epc_rating"] },
          ladder: { field: "epc_rating", prompt: "Add your home's energy rating, or upload a recent energy bill, and we can give you a range.", cta: "Add energy rating",
                    input: { type: "choice", options: ["A or B", "C", "D", "E", "F or G", "I don't know: upload a bill instead"] } },
          review: null, whyNot: null,
          claim: { source: "template", sentences: [
            { text: "Not enough information to estimate this one yet.", fields: ["impact.status"] },
            { text: "Add your home's energy rating and we can give you a range.", fields: ["impact.missing.epc_rating"] }
          ] },
          actions: { primary: "Add energy rating", secondary: null }
        },
        GP03: soft("GP03", 0.32, {}),
        GP04: soft("GP04", 0.44, { evidence: [{ code: "PAPER_STATEMENTS", label: "Paper statements: 6 of 12 in the last year", date: "30 Jun 2026", source: "inferred" }] })
      }
    },

    /* ---- Aisha: everything RULED_OUT, "You're all set" ---- */
    aisha: {
      id: "CUST-0003", key: "cust_c0d517", name: "Aisha", region: "West Midlands",
      summary: "Owns an EV, has solar and a Green Home Loan, already fully paperless.",
      tags: ["All set", "Homeowner", "EV owner"],
      products: [
        { name: "Current account", since: "Jun 2012", status: "Active" },
        { name: "Green Home Loan", since: "Feb 2024", status: "Active" },
        { name: "Mortgage", since: "May 2016", status: "Active" }
      ],
      freshness: [
        { source: "Transactions", asOf: "30 Jun 2026", kind: "inferred" },
        { source: "Vehicle record", asOf: "9 Jan 2026", kind: "declared" },
        { source: "Solar installation", asOf: "12 Apr 2025", kind: "declared" }
      ],
      facts: {
        homeowner: true, vehicle: { fuel: "bev", ageYears: 1, mileage: 8100, mileageSource: "declared" },
        secondCar: false, fuelSpend: 0, carFinanceActive: false,
        energy: { elecKwh: 2600, gasKwh: 6200 }, epcKnown: true, solar: true, roofKnown: true, existingGreenHome: true,
        statementsPerYear: 12, digitalStatements: 12, digitalShare: 1, appUse: "Daily", paperNeed: false,
        staleDays: 0, historyWeeks: 210,
        base: { GP01: 0.12, GP02: 0.2, GP03: 0.08, GP04: 0.05 },
        conf: { completeness: 0.93, recency: 0.95, stability: 0.9, inDist: 0.86 }
      },
      opp: {
        GP01: ruledOut("GP01", "GP01-R1", 0.12),
        GP02: ruledOut("GP02", "GP02-R2", 0.2),
        GP03: ruledOut("GP03", "GP03-R2", 0.08),
        GP04: ruledOut("GP04", "GP04-R1", 0.05)
      }
    },

    /* ---- Tom: new customer, ABSTAIN ×3, Paperless RECOMMEND ---- */
    tom: {
      id: "CUST-0004", key: "cust_91aa20", name: "Tom", region: "Yorkshire and The Humber",
      summary: "New customer, 6 weeks of history, paper statements, high app use.",
      tags: ["New customer", "6 weeks of history", "Paper statements"],
      products: [{ name: "Current account", since: "18 May 2026", status: "Active" }],
      freshness: [
        { source: "Transactions", asOf: "30 Jun 2026 (6 weeks)", kind: "inferred" },
        { source: "Digital usage", asOf: "30 Jun 2026", kind: "inferred" }
      ],
      facts: {
        homeowner: true, vehicle: { fuel: "petrol", ageYears: 6, mileage: null, mileageSource: null },
        secondCar: false, fuelSpend: 120, carFinanceActive: false,
        energy: null, epcKnown: false, solar: false, roofKnown: false, existingGreenHome: false,
        statementsPerYear: 12, digitalStatements: 0, digitalShare: 0, appUse: "Most days", paperNeed: false,
        staleDays: 0, historyWeeks: 6,
        base: { GP01: 0.47, GP02: 0.41, GP03: 0.33, GP04: 0.76 },
        conf: { completeness: 0.42, recency: 0.98, stability: 0.55, inDist: 0.6 },
        confByProduct: { GP04: { completeness: 0.8, recency: 0.95, stability: 0.78, inDist: 0.7 } }
      },
      opp: {
        GP01: {
          status: "ABSTAIN", likelihood: "MEDIUM", propensity: 0.47,
          eligibility: { result: "PASSED", rule: null }, impactQuality: "LOW",
          headline: "Not enough information to estimate this one yet.",
          whyNow: null,
          evidence: [
            { code: "SHORT_HISTORY", label: "6 weeks of account history so far", date: "30 Jun 2026", source: "inferred" },
            { code: "EXISTING_VEHICLE", label: "Petrol car, 6 years old", date: "18 May 2026", source: "declared" }
          ],
          impact: { status: "INSUFFICIENT_DATA", family: "co2", missing: ["annual_mileage"] },
          ladder: { field: "annual_mileage", prompt: "Add your yearly mileage and we can give you a range. It takes about 20 seconds.", cta: "Add mileage",
                    input: { type: "number", unit: "miles a year", min: 0, max: 100000, step: 100, placeholder: "e.g. 8,000" } },
          review: null, whyNot: null,
          claim: { source: "template", sentences: [
            { text: "Not enough information to estimate this one yet.", fields: ["impact.status"] },
            { text: "Add your yearly mileage and we can give you a range.", fields: ["impact.missing.annual_mileage"] }
          ] },
          actions: { primary: "Add mileage", secondary: null }
        },
        GP02: {
          status: "ABSTAIN", likelihood: "MEDIUM", propensity: 0.41,
          eligibility: { result: "PASSED", rule: null }, impactQuality: "LOW",
          headline: "We're still getting to know your account.",
          whyNow: null,
          evidence: [{ code: "SHORT_HISTORY", label: "6 weeks of account history so far", date: "30 Jun 2026", source: "inferred" }],
          impact: { status: "INSUFFICIENT_DATA", family: "co2", missing: ["gas_kwh"] },
          ladder: { field: "gas_kwh", prompt: "Upload a recent energy bill and we can estimate this. Or check back in about 6 weeks.", cta: "Upload a bill",
                    input: { type: "upload" } },
          review: null, whyNot: null,
          claim: { source: "template", sentences: [{ text: "We're still getting to know your account.", fields: ["evidence.SHORT_HISTORY"] }] },
          actions: { primary: "Upload a bill", secondary: null }
        },
        GP03: {
          status: "ABSTAIN", likelihood: "LOW", propensity: 0.33,
          eligibility: { result: "PASSED", rule: null }, impactQuality: "LOW",
          headline: "We're still getting to know your account.",
          whyNow: null,
          evidence: [{ code: "SHORT_HISTORY", label: "6 weeks of account history so far", date: "30 Jun 2026", source: "inferred" }],
          impact: { status: "INSUFFICIENT_DATA", family: "co2", missing: ["electricity_kwh", "roof_suitability"] },
          ladder: { field: "electricity_kwh", prompt: "Upload a recent electricity bill and we can estimate this.", cta: "Upload a bill", input: { type: "upload" } },
          review: null, whyNot: null,
          claim: { source: "template", sentences: [{ text: "We're still getting to know your account.", fields: ["evidence.SHORT_HISTORY"] }] },
          actions: { primary: "Upload a bill", secondary: null }
        },
        GP04: {
          status: "RECOMMEND", likelihood: "HIGH", propensity: 0.76,
          eligibility: { result: "PASSED", rule: null }, impactQuality: "HIGH",
          headline: "Your statements arrive on paper, but you use the app most days. Going paperless takes about a minute.",
          whyNow: null,
          evidence: [
            { code: "PAPER_STATEMENTS", label: "Paper statements: all of them so far", date: "30 Jun 2026", source: "inferred" },
            { code: "HIGH_DIGITAL_ACTIVITY", label: "You open the app most days", date: "30 Jun 2026", source: "inferred" }
          ],
          impact: { status: "PAPER", paper: { value: 48, unit: "sheets a year", note: "12 statements, about 4 sheets each" },
                    digital: { value: "0%", unit: "of your statements are digital", note: "0 of 12 statements" },
                    formula: "Paper statements a year × sheets per statement", baseline: "Your current statement settings", horizon: "12 months", factor: "Statement page counts (internal, illustrative)" },
          ladder: null, review: null, whyNot: null,
          claim: { source: "llm", sentences: [
            { text: "Your statements arrive on paper, but you use the app most days.", fields: ["evidence.PAPER_STATEMENTS", "evidence.HIGH_DIGITAL_ACTIVITY"] },
            { text: "Going paperless would avoid about 48 sheets of paper a year.", fields: ["impact.paper"] }
          ] },
          actions: { primary: "Go paperless", secondary: "Choose which statements go digital" }
        }
      }
    },

    /* ---- Dave: Green Home RECOMMEND ---- */
    dave: {
      id: "CUST-0005", key: "cust_5e0c33", name: "Dave", region: "East Midlands",
      summary: "1960s semi, high winter gas, EPC D, homeowner.",
      tags: ["Homeowner", "1960s semi", "High winter gas"],
      products: [
        { name: "Current account", since: "Oct 2009", status: "Active" },
        { name: "Mortgage (fixed rate)", since: "Dec 2021", status: "Fixed rate ends Nov 2026" }
      ],
      freshness: [
        { source: "Transactions", asOf: "30 Jun 2026", kind: "inferred" },
        { source: "Energy usage", asOf: "31 May 2026", kind: "inferred" },
        { source: "Energy rating (EPC)", asOf: "3 Feb 2023", kind: "declared" }
      ],
      facts: {
        homeowner: true, vehicle: { fuel: "petrol", ageYears: 11, mileage: 7400, mileageSource: "declared" },
        secondCar: false, fuelSpend: 98, carFinanceActive: false,
        energy: { elecKwh: 3400, gasKwh: 18500 }, epcKnown: true, solar: false, roofKnown: true, existingGreenHome: false,
        statementsPerYear: 12, digitalStatements: 10, digitalShare: 0.83, appUse: "Weekly", paperNeed: false,
        staleDays: 0, historyWeeks: 300,
        base: { GP01: 0.32, GP02: 0.79, GP03: 0.41, GP04: 0.28 },
        conf: { completeness: 0.88, recency: 0.9, stability: 0.83, inDist: 0.82 }
      },
      opp: {
        GP01: soft("GP01", 0.32, {}),
        GP02: {
          status: "RECOMMEND", likelihood: "HIGH", propensity: 0.79,
          eligibility: { result: "PASSED", rule: null }, impactQuality: "HIGH",
          headline: "Your winter gas spend runs well above similar homes. A loft and cavity insulation first step could be worth exploring.",
          whyNow: { text: "Your fixed-rate mortgage ends in 5 months.", date: "30 Jun 2026", code: "MORTGAGE_RATE_ENDING" },
          evidence: [
            { code: "HIGH_WINTER_GAS", label: "Winter gas: about 18,500 kWh a year, above similar homes", date: "31 May 2026", source: "inferred" },
            { code: "OLDER_HOME", label: "Semi-detached home built in the 1960s", date: "3 Feb 2023", source: "declared" },
            { code: "EPC_D", label: "Home energy rating: D", date: "3 Feb 2023", source: "declared" }
          ],
          impact: {
            status: "ESTIMATED", family: "co2", low: 500, central: 650, high: 830, unit: "kg CO₂e a year",
            secondary: { family: "energy", low: 2800, central: 3700, high: 4600, unit: "kWh a year" },
            bills: "About £260 a year less on heating, central estimate.",
            firstStep: "Start with a loft insulation top-up and a cavity wall check, before any bigger upgrade.",
            formula: "Yearly gas kWh × expected saving share of the first step × gas factor",
            baseline: "Your home as it is today, same heating habits", horizon: "12 months", factor: FACTOR, missing: []
          },
          confidence: { completeness: 0.88, recency: 0.9, stability: 0.83, inDist: 0.82 },
          ladder: null, review: null, whyNot: null,
          claim: { source: "llm", sentences: [
            { text: "Your winter gas spend runs well above similar homes.", fields: ["evidence.HIGH_WINTER_GAS"] },
            { text: "A loft and cavity insulation first step could cut an estimated 500 to 830 kg CO₂e a year.", fields: ["impact.low", "impact.high"] },
            { text: "Your fixed-rate mortgage ends in 5 months, which can be a good time to review home upgrades.", fields: ["why_now.MORTGAGE_RATE_ENDING"] }
          ] },
          actions: { primary: "Explore home upgrades", secondary: "See the cheapest first step" }
        },
        GP03: soft("GP03", 0.41, {}),
        GP04: soft("GP04", 0.28, {})
      }
    },

    /* ---- Sam: Solar ABSTAIN with Confidence Ladder (roof) ---- */
    sam: {
      id: "CUST-0006", key: "cust_ab4410", name: "Sam", region: "South West",
      summary: "Homeowner with high electricity use; roof suitability unknown.",
      tags: ["Homeowner", "High electricity", "Roof unknown"],
      products: [
        { name: "Current account", since: "Jul 2015", status: "Active" },
        { name: "Mortgage", since: "Jun 2018", status: "Active" }
      ],
      freshness: [
        { source: "Transactions", asOf: "30 Jun 2026", kind: "inferred" },
        { source: "Energy usage", asOf: "31 May 2026", kind: "inferred" },
        { source: "Roof suitability", asOf: "Not on record", kind: "declared" }
      ],
      facts: {
        homeowner: true, vehicle: { fuel: "diesel", ageYears: 9, mileage: 6000, mileageSource: "declared" },
        secondCar: false, fuelSpend: 74, carFinanceActive: false,
        energy: { elecKwh: 5600, gasKwh: 9000 }, epcKnown: true, solar: false, roofKnown: false, existingGreenHome: false,
        statementsPerYear: 12, digitalStatements: 8, digitalShare: 0.67, appUse: "Weekly", paperNeed: false,
        staleDays: 0, historyWeeks: 180,
        base: { GP01: 0.36, GP02: 0.44, GP03: 0.61, GP04: 0.4 },
        conf: { completeness: 0.81, recency: 0.9, stability: 0.8, inDist: 0.79 }
      },
      opp: {
        GP01: soft("GP01", 0.36, {}),
        GP02: soft("GP02", 0.44, {}),
        GP03: {
          status: "ABSTAIN", likelihood: "MEDIUM", propensity: 0.61,
          eligibility: { result: "PASSED", rule: null }, impactQuality: "LOW",
          headline: "Solar could suit your electricity use, but we need one detail first.",
          whyNow: null,
          evidence: [
            { code: "HIGH_ELEC_USE", label: "Electricity use: about 5,600 kWh a year, above similar homes", date: "31 May 2026", source: "inferred" },
            { code: "HOMEOWNER", label: "You own your home", date: "30 Jun 2026", source: "inferred" }
          ],
          impact: { status: "INSUFFICIENT_DATA", family: "co2", missing: ["roof_suitability"] },
          ladder: { field: "roof_suitability", prompt: "Tell us about your roof and we can give you a range.", cta: "Answer roof question",
                    question: "Which way does most of your roof face, and is it shaded?",
                    input: { type: "choice", options: ["South, east or west, mostly unshaded", "North facing or heavily shaded", "Not sure"] } },
          ladderResult: {
            impactQuality: "MEDIUM",
            impact: { status: "ESTIMATED", family: "co2", low: 500, central: 580, high: 660, unit: "kg CO₂e a year",
              secondary: { family: "energy", low: 2500, central: 2900, high: 3300, unit: "kWh a year generated" },
              bills: "About £450 a year less on electricity, central estimate.",
              formula: "Expected solar kWh used at home × grid electricity factor",
              baseline: "All your electricity bought from the grid", horizon: "12 months", factor: FACTOR, missing: [] }
          },
          review: null, whyNot: null,
          claim: { source: "template", sentences: [
            { text: "Solar could suit your electricity use, but we need one detail first.", fields: ["evidence.HIGH_ELEC_USE"] },
            { text: "Tell us about your roof and we can give you a range.", fields: ["impact.missing.roof_suitability"] }
          ] },
          actions: { primary: "Answer roof question", secondary: null }
        },
        GP04: soft("GP04", 0.4, {})
      }
    },

    /* ---- Jordan: renter in a flat ---- */
    jordan: {
      id: "CUST-0007", key: "cust_6d2f98", name: "Jordan", region: "London",
      summary: "Rents a flat, high app use, paper statements.",
      tags: ["Renter", "High app use", "Paper statements"],
      products: [{ name: "Current account", since: "Sep 2020", status: "Active" }],
      freshness: [
        { source: "Transactions", asOf: "30 Jun 2026", kind: "inferred" },
        { source: "Home ownership", asOf: "30 Jun 2026", kind: "inferred" }
      ],
      facts: {
        homeowner: false, vehicle: { fuel: "petrol", ageYears: 12, mileage: 4000, mileageSource: "declared" },
        secondCar: false, fuelSpend: 46, carFinanceActive: false,
        energy: { elecKwh: 2100, gasKwh: 5200 }, epcKnown: true, solar: false, roofKnown: false, existingGreenHome: false,
        statementsPerYear: 12, digitalStatements: 0, digitalShare: 0, appUse: "Daily", paperNeed: false,
        staleDays: 0, historyWeeks: 300,
        base: { GP01: 0.22, GP02: 0.3, GP03: 0.18, GP04: 0.74 },
        conf: { completeness: 0.84, recency: 0.93, stability: 0.82, inDist: 0.8 }
      },
      opp: {
        GP01: soft("GP01", 0.22, {}),
        GP02: ruledOut("GP02", "GP02-R1", 0.3),
        GP03: ruledOut("GP03", "GP03-R1", 0.18),
        GP04: {
          status: "RECOMMEND", likelihood: "HIGH", propensity: 0.74,
          eligibility: { result: "PASSED", rule: null }, impactQuality: "HIGH",
          headline: "You bank in the app every day, but your statements still arrive on paper.",
          whyNow: null,
          evidence: [
            { code: "PAPER_STATEMENTS", label: "Paper statements: 12 of 12 in the last year", date: "30 Jun 2026", source: "inferred" },
            { code: "HIGH_DIGITAL_ACTIVITY", label: "You open the app every day", date: "30 Jun 2026", source: "inferred" }
          ],
          impact: { status: "PAPER", paper: { value: 48, unit: "sheets a year", note: "12 statements, about 4 sheets each" },
                    digital: { value: "0%", unit: "of your statements are digital", note: "0 of 12 statements" },
                    formula: "Paper statements a year × sheets per statement", baseline: "Your current statement settings", horizon: "12 months", factor: "Statement page counts (internal, illustrative)" },
          ladder: null, review: null, whyNot: null,
          claim: { source: "llm", sentences: [
            { text: "You bank in the app every day, but your statements still arrive on paper.", fields: ["evidence.PAPER_STATEMENTS", "evidence.HIGH_DIGITAL_ACTIVITY"] },
            { text: "Going paperless would avoid about 48 sheets of paper a year.", fields: ["impact.paper"] }
          ] },
          actions: { primary: "Go paperless", secondary: "Choose which statements go digital" }
        }
      }
    },

    /* ---- Eleanor: accessibility paper need (never nudged) ---- */
    eleanor: {
      id: "CUST-0008", key: "cust_e93b07", name: "Eleanor", region: "Wales",
      summary: "Accessibility paper need flagged. Paperless is never suggested.",
      tags: ["Accessibility: paper statements", "Homeowner"],
      products: [
        { name: "Current account", since: "Mar 1998", status: "Active" },
        { name: "Savings account", since: "Mar 2004", status: "Active" }
      ],
      freshness: [
        { source: "Transactions", asOf: "30 Jun 2026", kind: "inferred" },
        { source: "Accessibility preferences", asOf: "11 Nov 2025", kind: "declared" }
      ],
      facts: {
        homeowner: true, vehicle: { fuel: "petrol", ageYears: 14, mileage: 3200, mileageSource: "declared" },
        secondCar: false, fuelSpend: 38, carFinanceActive: false,
        energy: { elecKwh: 2400, gasKwh: 10200 }, epcKnown: true, solar: false, roofKnown: true, existingGreenHome: false,
        statementsPerYear: 12, digitalStatements: 0, digitalShare: 0, appUse: "Rarely", paperNeed: true,
        staleDays: 0, historyWeeks: 400,
        base: { GP01: 0.18, GP02: 0.35, GP03: 0.3, GP04: 0.6 },
        conf: { completeness: 0.85, recency: 0.9, stability: 0.84, inDist: 0.8 }
      },
      opp: {
        GP01: soft("GP01", 0.18, {}),
        GP02: soft("GP02", 0.35, {}),
        GP03: soft("GP03", 0.3, {}),
        GP04: ruledOut("GP04", "GP04-R2", 0.6)
      }
    }
  };

  GD.personaOrder = ["priya", "marcus", "aisha", "tom", "dave", "sam", "jordan", "eleanor"];

  /* ------------------------------------------- Scenario Lab mutations (enum) */
  GD.mutations = [
    { id: "SET_VEHICLE_BEV",   label: "Set vehicle to EV",         hint: "Vehicle record becomes battery electric; fuel spend stops." },
    { id: "REMOVE_MILEAGE",    label: "Remove annual mileage",     hint: "Yearly mileage becomes unknown." },
    { id: "REMOVE_ENERGY",     label: "Remove energy data",        hint: "Electricity and gas usage become unknown." },
    { id: "ADD_CONFLICT_FUEL", label: "Add conflicting signal",    hint: "EV on record plus 3 months of fuel spend." },
    { id: "MAKE_STALE",        label: "Make data stale",           hint: "Shift every data timestamp back 200 days." },
    { id: "SET_RENTER",        label: "Mark as renter",            hint: "Home ownership becomes renting." },
    { id: "SELL_CAR",          label: "Sell the car",              hint: "No vehicle on record; fuel spend drops to zero." }
  ];

  /* ============================================================ business */
  GD.portfolio = {
    asOf: "30 Jun 2026",
    customers: 5000,
    completeData: 0.82,
    abstained: 0.112,
    kpis: {
      co2:        { family: "co2", name: "Estimated CO₂e", status: "estimate", low: 1840, central: 2460, high: 3120, unit: "t CO₂e a year", note: "Avoided emissions if surfaced opportunities are taken up. Never netted against the bank's own footprint." },
      co2Realised:{ family: "co2", name: "Realised CO₂e", status: "pending", note: "Needs post-adoption data. Shown separately when it exists (Promise vs. Proof, documented design)." },
      energy:     { family: "energy", name: "Energy", status: "estimate", low: 4.1, central: 5.3, high: 6.8, unit: "GWh a year", note: "Green Home and Solar Finance only." },
      paper:      { family: "paper", name: "Paper sheets avoided", status: "estimate", central: 212400, unit: "sheets a year", note: "Paperless only. No carbon claim." },
      digital:    { family: "digital", name: "Digital adoption", status: "realised", central: 0.68, unit: "of statements digital", note: "Not a carbon reduction." }
    },
    funnel: {
      GP01: [["Identified", 1420], ["Eligible", 1180], ["Surfaced", 860], ["Engaged", 312], ["Taken up", 74]],
      GP02: [["Identified", 1610], ["Eligible", 1290], ["Surfaced", 940], ["Engaged", 288], ["Taken up", 61]],
      GP03: [["Identified", 980], ["Eligible", 720], ["Surfaced", 410], ["Engaged", 126], ["Taken up", 22]],
      GP04: [["Identified", 2240], ["Eligible", 2010], ["Surfaced", 1880], ["Engaged", 1102], ["Taken up", 618]]
    },
    /* Quadrant cohorts: x = propensity (0–1), y = estimated impact per customer (central, with range),
       conf = confidence (0–1), n = cohort size. Cohorts below 10 are suppressed. */
    cohorts: {
      GP01: [
        { id: "c01", name: "Commuter homeowners", n: 412, propensity: 0.78, conf: 0.84, low: 1150, central: 1450, high: 1750, status: "RECOMMEND", eligPass: 0.78, eligNeeds: 0.22, quality: "MEDIUM", reasons: ["HIGH_FUEL_SPEND", "EXISTING_VEHICLE", "FINANCE_ENDING"] },
        { id: "c02", name: "High-mileage diesel drivers", n: 186, propensity: 0.71, conf: 0.52, low: 1500, central: 1980, high: 2460, status: "RECOMMEND", eligPass: 0.64, eligNeeds: 0.36, quality: "LOW", reasons: ["HIGH_FUEL_SPEND", "HIGH_ANNUAL_MILEAGE"] },
        { id: "c03", name: "Low-mileage urban drivers", n: 344, propensity: 0.62, conf: 0.8, low: 260, central: 340, high: 420, status: "SOFT_SURFACE", eligPass: 0.86, eligNeeds: 0.14, quality: "HIGH", reasons: ["EXISTING_VEHICLE"] },
        { id: "c04", name: "Older-car rural households", n: 228, propensity: 0.29, conf: 0.76, low: 1350, central: 1720, high: 2090, status: "SOFT_SURFACE", eligPass: 0.81, eligNeeds: 0.19, quality: "MEDIUM", reasons: ["HIGH_ANNUAL_MILEAGE", "OLDER_VEHICLE"] },
        { id: "c05", name: "Occasional drivers", n: 301, propensity: 0.18, conf: 0.82, low: 140, central: 190, high: 240, status: "SOFT_SURFACE", eligPass: 0.9, eligNeeds: 0.1, quality: "HIGH", reasons: [] },
        { id: "c06", name: "Mixed-signal EV records", n: 58, propensity: 0.55, conf: 0.38, low: 0, central: 0, high: 0, status: "REVIEW", eligPass: 0.7, eligNeeds: 0.3, quality: null, reasons: ["VEHICLE_BEV_ON_RECORD", "FUEL_SPEND_CONTINUES"] },
        { id: "c07", name: "Company-car drivers", n: 7, suppressed: true }
      ],
      GP02: [
        { id: "h01", name: "Pre-1970 homes, high winter gas", n: 366, propensity: 0.76, conf: 0.81, low: 500, central: 650, high: 830, status: "RECOMMEND", eligPass: 0.83, eligNeeds: 0.17, quality: "HIGH", reasons: ["HIGH_WINTER_GAS", "OLDER_HOME"] },
        { id: "h02", name: "Homes without an EPC", n: 248, propensity: 0.58, conf: 0.41, low: 420, central: 610, high: 800, status: "ABSTAIN", eligPass: 0.8, eligNeeds: 0.2, quality: "LOW", reasons: ["HIGH_WINTER_GAS", "EPC_MISSING"] },
        { id: "h03", name: "Recently moved homeowners", n: 190, propensity: 0.66, conf: 0.72, low: 300, central: 400, high: 500, status: "RECOMMEND", eligPass: 0.75, eligNeeds: 0.25, quality: "MEDIUM", reasons: ["MORTGAGE_STARTED"] },
        { id: "h04", name: "Newer homes, typical gas", n: 512, propensity: 0.24, conf: 0.85, low: 150, central: 210, high: 270, status: "SOFT_SURFACE", eligPass: 0.92, eligNeeds: 0.08, quality: "HIGH", reasons: [] }
      ],
      GP03: [
        { id: "s01", name: "High-electricity homeowners", n: 214, propensity: 0.69, conf: 0.47, low: 500, central: 580, high: 660, status: "ABSTAIN", eligPass: 0.71, eligNeeds: 0.29, quality: "LOW", reasons: ["HIGH_ELEC_USE", "ROOF_UNKNOWN"] },
        { id: "s02", name: "South-facing roofs on record", n: 133, propensity: 0.64, conf: 0.79, low: 520, central: 610, high: 700, status: "RECOMMEND", eligPass: 0.88, eligNeeds: 0.12, quality: "HIGH", reasons: ["HIGH_ELEC_USE", "ROOF_SUITABLE"] },
        { id: "s03", name: "Average-use homeowners", n: 402, propensity: 0.31, conf: 0.8, low: 360, central: 440, high: 520, status: "SOFT_SURFACE", eligPass: 0.9, eligNeeds: 0.1, quality: "MEDIUM", reasons: [] }
      ],
      GP04: [
        { id: "p01", name: "App-first, paper statements", n: 1240, propensity: 0.81, conf: 0.86, low: 40, central: 48, high: 48, status: "RECOMMEND", eligPass: 0.97, eligNeeds: 0.03, quality: "HIGH", reasons: ["PAPER_STATEMENTS", "HIGH_DIGITAL_ACTIVITY"], unit: "sheets a year" },
        { id: "p02", name: "Mixed paper and digital", n: 860, propensity: 0.57, conf: 0.8, low: 8, central: 16, high: 24, status: "RECOMMEND", eligPass: 0.95, eligNeeds: 0.05, quality: "HIGH", reasons: ["PAPER_STATEMENTS"], unit: "sheets a year" },
        { id: "p03", name: "Low app use, paper statements", n: 420, propensity: 0.22, conf: 0.74, low: 40, central: 48, high: 48, status: "SOFT_SURFACE", eligPass: 0.9, eligNeeds: 0.1, quality: "HIGH", reasons: ["PAPER_STATEMENTS"], unit: "sheets a year" }
      ]
    },
    segments: [
      { name: "Commuter homeowners", customers: 412, recommend: 0.61, abstain: 0.06, impact: "1,150–1,750 kg" },
      { name: "Pre-1970 homes, high winter gas", customers: 366, recommend: 0.58, abstain: 0.09, impact: "500–830 kg" },
      { name: "Homes without an EPC", customers: 248, recommend: 0.12, abstain: 0.71, impact: "Not estimated" },
      { name: "High-electricity homeowners", customers: 214, recommend: 0.21, abstain: 0.62, impact: "Not estimated" },
      { name: "App-first, paper statements", customers: 1240, recommend: 0.74, abstain: 0.01, impact: "48 sheets" },
      { name: "Company-car drivers", customers: 7, suppressed: true }
    ],
    regions: [
      { name: "London", customers: 742, recommend: 0.31, abstain: 0.13 },
      { name: "South East", customers: 806, recommend: 0.36, abstain: 0.1 },
      { name: "South West", customers: 498, recommend: 0.33, abstain: 0.12 },
      { name: "East of England", customers: 455, recommend: 0.34, abstain: 0.11 },
      { name: "West Midlands", customers: 431, recommend: 0.32, abstain: 0.1 },
      { name: "East Midlands", customers: 372, recommend: 0.35, abstain: 0.09 },
      { name: "North West", customers: 560, recommend: 0.3, abstain: 0.12 },
      { name: "North East", customers: 214, recommend: 0.29, abstain: 0.13 },
      { name: "Yorkshire and The Humber", customers: 418, recommend: 0.31, abstain: 0.11 },
      { name: "Wales", customers: 236, recommend: 0.3, abstain: 0.12 },
      { name: "Scotland", customers: 268, recommend: 0.28, abstain: 0.14 }
    ],
    trends: {
      months: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
      surfaced: { GP01: [610, 655, 702, 760, 818, 860], GP02: [980, 960, 930, 905, 920, 940], GP03: [290, 320, 352, 380, 398, 410], GP04: [1420, 1510, 1600, 1690, 1790, 1880] },
      takenUp:  { GP01: [41, 48, 52, 60, 67, 74], GP02: [72, 70, 64, 58, 60, 61], GP03: [9, 11, 14, 17, 20, 22], GP04: [402, 440, 488, 530, 578, 618] }
    }
  };

  /* Relationship Manager book (pseudonymous keys; first names shown to the owning RM only) */
  GD.rmBook = [
    { persona: "priya",  key: "cust_7f3a9c", name: "Priya",  region: "South East", product: "GP01", status: "RECOMMEND", likelihood: "HIGH", eligibility: "NEEDS_VERIFICATION", quality: "MEDIUM", fresh: "30 Jun 2026", next: "Call within 14 days" },
    { persona: "dave",   key: "cust_5e0c33", name: "Dave",   region: "East Midlands", product: "GP02", status: "RECOMMEND", likelihood: "HIGH", eligibility: "PASSED", quality: "HIGH", fresh: "30 Jun 2026", next: "Send first-step guide" },
    { persona: "marcus", key: "cust_2b81e4", name: "Marcus", region: "North West", product: "GP01", status: "REVIEW", likelihood: "MEDIUM", eligibility: "PASSED", quality: null, fresh: "30 Jun 2026", next: "Resolve vehicle record" },
    { persona: "sam",    key: "cust_ab4410", name: "Sam",    region: "South West", product: "GP03", status: "ABSTAIN", likelihood: "MEDIUM", eligibility: "PASSED", quality: "LOW", fresh: "30 Jun 2026", next: "Data enrichment: roof" },
    { persona: "tom",    key: "cust_91aa20", name: "Tom",    region: "Yorkshire and The Humber", product: "GP04", status: "RECOMMEND", likelihood: "HIGH", eligibility: "PASSED", quality: "HIGH", fresh: "30 Jun 2026", next: "Digital nudge" },
    { persona: "jordan", key: "cust_6d2f98", name: "Jordan", region: "London", product: "GP04", status: "RECOMMEND", likelihood: "HIGH", eligibility: "PASSED", quality: "HIGH", fresh: "30 Jun 2026", next: "Digital nudge" },
    { persona: "aisha",  key: "cust_c0d517", name: "Aisha",  region: "West Midlands", product: "GP01", status: "RULED_OUT", likelihood: "LOW", eligibility: "NOT_ELIGIBLE", quality: null, fresh: "30 Jun 2026", next: "None: all set" },
    { persona: "eleanor",key: "cust_e93b07", name: "Eleanor",region: "Wales", product: "GP04", status: "RULED_OUT", likelihood: "MEDIUM", eligibility: "NOT_ELIGIBLE", quality: null, fresh: "30 Jun 2026", next: "None: paper need respected" },
    { persona: null, key: "cust_4c19d2", name: "Customer 4c19", region: "South East", product: "GP02", status: "SOFT_SURFACE", likelihood: "MEDIUM", eligibility: "PASSED", quality: "MEDIUM", fresh: "30 Jun 2026", next: "Education content" },
    { persona: null, key: "cust_88e0f1", name: "Customer 88e0", region: "East of England", product: "GP01", status: "RECOMMEND", likelihood: "HIGH", eligibility: "PASSED", quality: "HIGH", fresh: "30 Jun 2026", next: "Call within 14 days" },
    { persona: null, key: "cust_0a7b6e", name: "Customer 0a7b", region: "Scotland", product: "GP03", status: "ABSTAIN", likelihood: "MEDIUM", eligibility: "PASSED", quality: "LOW", fresh: "2 Jan 2026", next: "Is this still right? check", stale: true },
    { persona: null, key: "cust_d35c40", name: "Customer d35c", region: "North East", product: "GP01", status: "SOFT_SURFACE", likelihood: "LOW", eligibility: "PASSED", quality: "HIGH", fresh: "30 Jun 2026", next: "Education content" }
  ];

  /* Governance (Auditor) */
  GD.governance = {
    claimsVerified: 1284,
    claimsBlocked: 7,
    templateRate: 0.021,
    abstentionRate: 0.112,
    chain: { status: "ok", rows: 1291, lastVerified: "30 Jun 2026, 18:02", head: "sha256:9c1e…4b7a" },
    fairness: {
      income: [
        { band: "Lower income", customers: 1240, recommend: 0.33, abstain: 0.12, brier: 0.064 },
        { band: "Lower-middle income", customers: 1310, recommend: 0.34, abstain: 0.11, brier: 0.061 },
        { band: "Upper-middle income", customers: 1280, recommend: 0.32, abstain: 0.1, brier: 0.06 },
        { band: "Higher income", customers: 1170, recommend: 0.35, abstain: 0.11, brier: 0.062 }
      ],
      age: [
        { band: "18 to 34", customers: 1460, recommend: 0.3, abstain: 0.15, brier: 0.066 },
        { band: "35 to 54", customers: 1980, recommend: 0.36, abstain: 0.09, brier: 0.059 },
        { band: "55 and over", customers: 1560, recommend: 0.33, abstain: 0.1, brier: 0.061 }
      ]
    },
    calibration: [
      { segment: "All customers", ece: 0.018 },
      { segment: "Commuter homeowners", ece: 0.021 },
      { segment: "Pre-1970 homes", ece: 0.024 },
      { segment: "New customers (under 8 weeks)", ece: 0.047, flag: true },
      { segment: "Renters", ece: 0.019 }
    ],
    limitations: [
      "All customers and labels are synthetic. Metrics show the pipeline is honest, not real-world accuracy.",
      "Impact figures are modelled estimates with illustrative factor labels in this prototype.",
      "Realised CO₂e needs post-adoption data and is not shown as a number.",
      "New customers (under 8 weeks) calibrate less well; they are routed to ABSTAIN more often by design."
    ],
    alerts: [
      { level: "info", text: "Data as of 30 Jun 2026." },
      { level: "warning", text: "Calibration error for new customers is above the 0.04 threshold." }
    ],
    audit: [
      { time: "18:02", event: "Audit chain verified", actor: "system", detail: "1,291 rows, head sha256:9c1e…4b7a" },
      { time: "17:41", event: "Claim blocked", actor: "claimcheck", detail: "NUM, BAN · cust_88e0f1 · GP01" },
      { time: "17:12", event: "Scenario run", actor: "evaluator", detail: "SET_VEHICLE_BEV on cust_7f3a9c" },
      { time: "16:55", event: "Template fallback", actor: "explainer", detail: "LLM timeout · cust_0a7b6e · GP03" },
      { time: "16:20", event: "Customer-level read", actor: "rm_014", detail: "Purpose: scheduled call · cust_5e0c33" }
    ]
  };

  /* Receipts: evaluation summary. ILLUSTRATIVE until `make eval` produces EVALUATION.md. */
  GD.receipts = {
    note: "Illustrative figures. Final numbers come from make eval on the validation set and are reproduced from one command.",
    models: [
      { product: "GP01 EV Finance",  lgbm: { auc: 0.79, prauc: 0.31, brier: 0.058, lift: 3.2 }, logreg: { auc: 0.72, prauc: 0.22, brier: 0.064, lift: 2.4 }, rule: { auc: 0.65, prauc: 0.16, brier: null, lift: 1.8 } },
      { product: "GP02 Green Home",  lgbm: { auc: 0.77, prauc: 0.27, brier: 0.052, lift: 2.9 }, logreg: { auc: 0.71, prauc: 0.2, brier: 0.057, lift: 2.2 }, rule: { auc: 0.63, prauc: 0.14, brier: null, lift: 1.6 } },
      { product: "GP03 Solar",       lgbm: { auc: 0.74, prauc: 0.19, brier: 0.039, lift: 2.6 }, logreg: { auc: 0.69, prauc: 0.15, brier: 0.042, lift: 2.0 }, rule: { auc: 0.61, prauc: 0.11, brier: null, lift: 1.5 } },
      { product: "GP04 Paperless",   lgbm: { auc: 0.82, prauc: 0.48, brier: 0.121, lift: 2.1 }, logreg: { auc: 0.78, prauc: 0.42, brier: 0.13, lift: 1.9 }, rule: { auc: 0.7, prauc: 0.33, brier: null, lift: 1.5 } }
    ],
    calibration: [[0.05, 0.04], [0.15, 0.13], [0.25, 0.27], [0.35, 0.33], [0.45, 0.47], [0.55, 0.52], [0.65, 0.66], [0.75, 0.72], [0.85, 0.83], [0.95, 0.91]],
    terciles: [{ band: "Low confidence", brier: 0.094 }, { band: "Medium confidence", brier: 0.061 }, { band: "High confidence", brier: 0.038 }],
    categoriser: {
      labels: ["Fuel", "Electricity", "Gas", "Public Transport", "Home Improvement", "Automotive", "Utilities", "Other"],
      macroF1: 0.91, rulesOnlyF1: 0.84,
      matrix: [
        [182, 0, 0, 1, 0, 6, 0, 3],
        [0, 141, 2, 0, 0, 0, 5, 1],
        [0, 3, 128, 0, 0, 0, 6, 0],
        [2, 0, 0, 96, 0, 1, 0, 4],
        [0, 0, 0, 0, 77, 2, 0, 6],
        [5, 0, 0, 0, 1, 88, 0, 4],
        [0, 4, 5, 0, 0, 0, 119, 2],
        [3, 1, 0, 3, 4, 3, 1, 410]
      ]
    },
    carbonTests: { passed: 24, total: 24 },
    llm: [
      { metric: "Numeric fidelity", governed: "100%", naive: "82%" },
      { metric: "Unsupported-claim rate", governed: "0.7%", naive: "14%" },
      { metric: "Banned-phrase rate", governed: "0%", naive: "6%" },
      { metric: "Product-mapping accuracy", governed: "100%", naive: "96%" },
      { metric: "Correct abstain wording", governed: "98%", naive: "41%" },
      { metric: "Template fallback rate", governed: "2.1%", naive: "n/a" },
      { metric: "p50 latency", governed: "1.4 s", naive: "1.9 s" },
      { metric: "Cost per 1,000 insights", governed: "£0.38", naive: "£0.61" }
    ],
    scenarios: { passed: 32, total: 32, groups: [
      { name: "Missing data", passed: 9, total: 9 },
      { name: "Conflicting signals", passed: 7, total: 7 },
      { name: "Products that must not be recommended", passed: 10, total: 10 },
      { name: "Insufficient information to estimate impact", passed: 6, total: 6 }
    ] },
    gates: [
      { gate: "Schema conformance", result: "100%", ok: true },
      { gate: "Rows dated after cutoff in features", result: "0", ok: true },
      { gate: "Customers in more than one split", result: "0", ok: true },
      { gate: "Placebo AUC (shuffled labels)", result: "0.50", ok: true },
      { gate: "Highest single-feature AUC", result: "0.71 (< 0.80)", ok: true },
      { gate: "Golden personas match designed outcomes", result: "8 / 8", ok: true },
      { gate: "Same seed, identical artefact hashes", result: "Yes", ok: true }
    ]
  };

  /* Red-team: the fixed string and the expected verdict */
  GD.redteam = {
    persona: "priya",
    pathway: "GP01",
    fixed: "Switching will save you 4,000 kg a year and you're pre-approved.",
    template: "Your fuel spend has been above your usual level, so an EV could be worth exploring. Eligibility has not been confirmed.",
    banned: ["guaranteed", "will save", "pre-approved", "approved", "you qualify", "carbon neutral", "eco-friendly", "save the planet", "green score"],
    recommendingVerbs: ["you should", "we recommend", "switch now", "apply now"]
  };

  /* Navigation maps used by the hub and shells */
  GD.screens = {
    mobile: [
      ["splash", "Splash"], ["welcome-auth", "Welcome and sign in"], ["onboarding-consent", "Onboarding and data-use consent"],
      ["home", "Home: insight feed and why-now"], ["pathways", "Pathways: always four tiles"],
      ["proof-card-recommend", "Proof Card: RECOMMEND (Priya, EV)"], ["evidence-sheet", "Evidence sheet"], ["impact-sheet", "Impact calculation sheet"],
      ["claim-check-sheet", "Claim-Check sheet"], ["confidence-ladder-sheet", "Confidence Ladder sheet"],
      ["proof-card-abstain", "Proof Card: ABSTAIN (Sam, Solar)"], ["proof-card-review", "Proof Card: REVIEW (Marcus, EV)"],
      ["proof-card-ruled-out", "Proof Card: RULED_OUT, Why not?"], ["proof-card-soft-surface", "Proof Card: SOFT_SURFACE"],
      ["all-set", "You're all set (Aisha)"], ["paperless-card", "Paperless card: separate metrics"],
      ["progress", "Progress: paper and digital, never netted"], ["help", "Help: talk to a person"],
      ["profile-privacy", "Profile and privacy"], ["feedback-sheet", "Feedback sheet"], ["offline-state", "Offline state"]
    ],
    web: [
      ["landing", "Landing"], ["how-it-works", "How it works"], ["pathways", "Pathways overview"],
      ["trust", "Trust: responsible AI and fairness"], ["customer-hub", "Customer Hub (responsive)"]
    ],
    business: [
      ["login", "Login: demo role chooser"], ["portfolio", "Portfolio (Level 1)"], ["opportunity-quadrant", "Opportunity quadrant (Level 2)"],
      ["customer-list", "Customer list"], ["customer-360", "Customer 360"], ["evidence-impact", "Evidence and Impact"],
      ["action-rm-brief", "Action: RM brief"], ["governance", "Governance"], ["scenario-lab", "Scenario Lab"],
      ["claim-check-redteam", "Claim-Check red-team"], ["receipts", "Receipts (evaluation)"]
    ]
  };

  GD.roles = {
    RELATIONSHIP_MANAGER: { label: "Relationship Manager", landing: "customer-list.html", note: "Own book: ranked call list, Customer 360, RM brief." },
    PORTFOLIO_ANALYST:    { label: "Portfolio Analyst", landing: "portfolio.html", note: "Aggregates only. Segments under 10 customers are hidden." },
    AUDITOR:              { label: "Auditor", landing: "governance.html", note: "Claim audit, fairness, chain verification. No customer-level values." },
    EVALUATOR:            { label: "Evaluator", landing: "scenario-lab.html", note: "Scenario Lab, red-team Claim-Check and Receipts on the 8 personas." }
  };
})();
