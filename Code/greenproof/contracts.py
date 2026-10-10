# greenproof/contracts.py   (FROZEN at T+1:30; changes = 2-line PR + chat ping)
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class Frozen(BaseModel):
    """Base for every contract: strict, frozen, no unknown fields."""
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


# ---------- enums (the only words allowed) ----------
class ProductId(str, Enum):
    GP01 = "GP01"   # EV Finance
    GP02 = "GP02"   # Green Home Loan
    GP03 = "GP03"   # Solar Finance
    GP04 = "GP04"   # Paperless Banking


class Status(str, Enum):
    RECOMMEND = "RECOMMEND"
    SOFT_SURFACE = "SOFT_SURFACE"
    ABSTAIN = "ABSTAIN"
    REVIEW = "REVIEW"
    RULED_OUT = "RULED_OUT"


class EligibilityResult(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    NEEDS_VERIFICATION = "NEEDS_VERIFICATION"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"


class ImpactStatus(str, Enum):
    ESTIMATED = "ESTIMATED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class MetricFamily(str, Enum):          # four families, NEVER merged
    EMISSIONS = "emissions"             # kgCO2e per year
    ENERGY = "energy"                   # kWh per year
    PAPER = "paper"                     # sheets per year
    # digital adoption is a separate block, not an impact family


class Band(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MissingInput(str, Enum):
    ANNUAL_MILEAGE = "annual_mileage"
    ROOF_SUITABILITY = "roof_suitability"
    ENERGY_DATA = "energy_data"
    VEHICLE_RECORD = "vehicle_record"
    STATEMENT_HISTORY = "statement_history"


class Mutation(str, Enum):              # Scenario Lab
    SET_VEHICLE_BEV = "SET_VEHICLE_BEV"
    REMOVE_MILEAGE = "REMOVE_MILEAGE"
    REMOVE_ENERGY = "REMOVE_ENERGY"
    ADD_CONFLICT_FUEL = "ADD_CONFLICT_FUEL"
    MAKE_STALE = "MAKE_STALE"
    SET_RENTER = "SET_RENTER"
    SELL_CAR = "SELL_CAR"


# ---------- the three independent verdicts (frozen; nobody edits them) ----------
class ReasonCode(Frozen):
    code: str                                    # e.g. HIGH_FUEL_SPEND
    phrase: str                                  # catalogue phrase, never free text
    metric: str                                  # e.g. avg_monthly_fuel_gbp
    value: Union[float, int, str]
    display: str                                 # formatted by carbon/units.py only
    observed_at: date
    source: Literal["customer_declared", "inferred_transactions", "bank_record"]


class ConfidenceParts(Frozen):
    overall: float = Field(ge=0, le=1)
    completeness: float = Field(ge=0, le=1)
    recency: float = Field(ge=0, le=1)
    stability: float = Field(ge=0, le=1)
    in_distribution: float = Field(ge=0, le=1)


class PropensityVerdict(Frozen):                 # produced by Madhav's models.score
    propensity: float = Field(ge=0, le=1)
    likelihood_band: Band
    confidence: ConfidenceParts
    reason_codes: list[ReasonCode]


class EligibilityVerdict(Frozen):                # produced by YOUR rules.engine
    result: EligibilityResult
    rules_fired: list[str]                       # e.g. ["GP01-R1"]
    rules_version: str                           # e.g. "rules-1.0"
    plain_reasons: list[str]                     # plain-language reasons, from products.yaml


class ImpactVerdict(Frozen):                     # produced by the carbon engine (data hat)
    status: ImpactStatus
    metric_family: Optional[MetricFamily] = None
    unit: Optional[str] = None
    low: Optional[float] = None
    central: Optional[float] = None
    high: Optional[float] = None
    display: Optional[str] = None                # must match the SAFE regex
    formula: Optional[str] = None
    baseline: Optional[str] = None
    horizon: Optional[str] = None
    factor_refs: list[str] = []
    quality: Optional[Band] = None
    missing_inputs: list[MissingInput] = []


# ---------- pieces of the Evidence Pack ----------
class DigitalAdoption(Frozen):                   # GP04 only, never a carbon claim
    paper_statements_12m: int
    digital_share: float = Field(ge=0, le=1)


class WhyNow(Frozen):
    trigger: str                                 # e.g. CAR_FINANCE_ENDING
    display: str
    observed_at: date


class Sentence(Frozen):
    text: str
    fields: list[str]
    check: Literal["PASS", "BLOCKED", "TEMPLATE"]


class Explanation(Frozen):
    sentences: list[Sentence]
    source: Literal["llm", "template"]
    claimcheck_status: Literal["PASS", "FALLBACK"]


class NextAction(Frozen):
    label: str
    secondary: Optional[str] = None
    disclaimer: str                              # always includes "Not a credit decision."


class Opportunity(Frozen):                       # THE EVIDENCE PACK (one customer x one product)
    opportunity_id: ProductId
    opportunity_name: str
    status: Status
    propensity: float = Field(ge=0, le=1)
    likelihood_band: Band
    confidence: ConfidenceParts
    eligibility: EligibilityVerdict
    reason_codes: list[ReasonCode]
    why_now: Optional[WhyNow] = None
    impact: ImpactVerdict
    digital_adoption: Optional[DigitalAdoption] = None
    explanation: Optional[Explanation] = None
    next_action: Optional[NextAction] = None
    data_as_of: date


class CustomerOpportunities(Frozen):
    customer_id: str                             # display id, e.g. CUST-0001
    persona: Optional[str] = None
    cutoff_date: date
    outcome_window_days: int
    run_manifest: str
    opportunities: list[Opportunity]


# ---------- Scenario Lab ----------
class ScenarioRequest(Frozen):
    customer_id: str = Field(pattern=r"^CUST-\d{4}$")
    mutations: list[Mutation] = Field(min_length=1, max_length=7)


class StatusSnapshot(Frozen):
    status: Status
    propensity: float
    eligibility: EligibilityResult
    impact_status: ImpactStatus


class DiffRow(Frozen):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, populate_by_name=True)
    product: ProductId
    field: str
    from_: str = Field(alias="from")
    to: str
    cause: str                                   # "Rule GP01-R1: ..." or "Model rescored: field X changed"


class ScenarioResponse(Frozen):
    before: dict[ProductId, StatusSnapshot]
    after: dict[ProductId, StatusSnapshot]
    diff: list[DiffRow]
    invariance_ok: bool
    elapsed_ms: int
