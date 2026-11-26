
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.policy_extraction.schemas.policy import PolicyDetails


class NormalizedVehicle(BaseModel):
    registration_number: str | None = None
    rto_code: str | None = None
    make: str | None = None
    model: str | None = None

    fuel_type: Literal[
        "petrol",
        "diesel",
        "cng",
        "lpg",
        "electric",
        "hybrid",
        "other",
        "unknown",
    ] = "unknown"

    engine_cc: int | None = None
    manufacture_year: int | None = None
    vehicle_age: int | None = None


class NormalizedInsurer(BaseModel):
    current_insurer: str | None = None
    previous_insurer: str | None = None

    business_type: Literal[
        "new_business",
        "rollover",
        "renewal",
        "unknown",
    ] = "unknown"


class NormalizedPremium(BaseModel):
    own_damage: Decimal | None = None
    third_party: Decimal | None = None
    addons: Decimal | None = None
    net_premium: Decimal | None = None
    gst: Decimal | None = None
    total_premium: Decimal | None = None


class NormalizedPolicy(BaseModel):
    policy_number: str | None = None

    policy_type: Literal[
        "comprehensive",
        "standalone_od",
        "standalone_tp",
        "unknown",
    ] = "unknown"

    policy_start_date: date | None = None
    policy_end_date: date | None = None
    ncb_percentage: Decimal | None = None

    vehicle: NormalizedVehicle
    insurer: NormalizedInsurer
    premium: NormalizedPremium

    source_policy: PolicyDetails = Field(exclude=True)
