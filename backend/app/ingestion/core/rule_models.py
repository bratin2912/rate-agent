
from typing import Any

from pydantic import BaseModel, Field


class RuleCondition(BaseModel):
    """
    A condition that must match for a source rule to apply.
    """

    field: str
    operator: str = "equals"
    value: Any


class RuleValue(BaseModel):
    """
    A value extracted from the source grid.

    We preserve the original source field and value.
    Business interpretation will be added only after verification.
    """

    source_field: str
    raw_value: Any
    interpreted_value: Any = None
    interpretation_status: str = "unresolved"


class CommissionRule(BaseModel):
    """
    A structured representation of one source-grid record.
    """

    rule_id: str

    source_id: str
    insurer: str
    source_version: str

    product_line: str
    table_type: str

    conditions: list[RuleCondition] = Field(default_factory=list)

    rule_values: list[RuleValue] = Field(default_factory=list)

    underwriting_notes: list[str] = Field(default_factory=list)

    source_sheet: str
    source_row: int
    source_evidence: dict[str, Any] = Field(default_factory=dict)
