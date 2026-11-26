
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class VehicleDetails(BaseModel):
    registration_number: str | None = None
    rto_code: str | None = None
    make: str | None = None
    model: str | None = None
    fuel_type: str | None = None
    engine_cc: int | None = None
    manufacture_year: int | None = None
    vehicle_age: int | None = None


class InsurerDetails(BaseModel):
    current_insurer: str | None = None
    previous_insurer: str | None = None
    business_type: Literal[
        "new_business",
        "rollover",
        "renewal",
        "unknown",
    ] = "unknown"


class PolicyPeriod(BaseModel):
    start_date: date | None = None
    end_date: date | None = None


class PremiumBreakup(BaseModel):
    own_damage_premium: Decimal | None = None
    third_party_premium: Decimal | None = None
    add_on_premium: Decimal | None = None
    net_premium: Decimal | None = None
    gst: Decimal | None = None
    total_premium: Decimal | None = None


class PolicyDetails(BaseModel):
    policy_number: str | None = None
    policy_type: Literal[
        "comprehensive",
        "standalone_od",
        "standalone_tp",
        "unknown",
    ] = "unknown"

    ncb_percentage: Decimal | None = None

    vehicle: VehicleDetails = Field(default_factory=VehicleDetails)
    insurer: InsurerDetails = Field(default_factory=InsurerDetails)
    period: PolicyPeriod = Field(default_factory=PolicyPeriod)
    premium: PremiumBreakup = Field(default_factory=PremiumBreakup)


class PolicyFieldEvidence(BaseModel):
    field_path: str
    page_number: int
    quote: str


class PolicyExtractionResult(BaseModel):
    policy: PolicyDetails
    evidence: list[PolicyFieldEvidence] = Field(default_factory=list)
