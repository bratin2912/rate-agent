
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.policy_extraction.schemas.normalized_policy import (
    NormalizedPolicy,
)


RatingStatus = Literal[
    "matched",
    "not_applicable",
    "declined",
    "no_match",
    "insufficient_data",
    "ambiguous",
]


class RatingRequest(BaseModel):
    policy: NormalizedPolicy

    # Identifies the insurer grid profile to use.
    # Example: godigit_mar_2026
    source_id: str


class GridEvidence(BaseModel):
    source_id: str
    filename: str
    sheet_name: str
    cell_coordinates: list[str] = Field(default_factory=list)


class CommissionComponent(BaseModel):
    status: RatingStatus

    # Percentage is populated only after the source metric
    # has been verified as a brokerage percentage.
    rate_percent: Decimal | None = None

    source_metric: str | None = None
    explanation: str


class DecisionTrace(BaseModel):
    step: int
    rule: str
    outcome: str
    explanation: str
    evidence: list[GridEvidence] = Field(default_factory=list)


class RatingResult(BaseModel):
    source_id: str
    od: CommissionComponent
    tp: CommissionComponent
    decision_trace: list[DecisionTrace] = Field(default_factory=list)
    overall_status: RatingStatus
    warnings: list[str] = Field(default_factory=list)
