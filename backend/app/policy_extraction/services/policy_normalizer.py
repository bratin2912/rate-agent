from app.policy_extraction.schemas.policy import PolicyDetails
from app.policy_extraction.schemas.normalized_policy import (
    NormalizedPolicy,
    NormalizedVehicle,
    NormalizedInsurer,
    NormalizedPremium,
)


class PolicyNormalizer:
    """
    Converts extracted policy data into a consistent internal representation.

    This class normalizes formats and maps fields. It does not invent missing
    values or calculate insurance rates.
    """

    FUEL_TYPE_MAP = {
        "petrol": "petrol",
        "gasoline": "petrol",
        "diesel": "diesel",
        "cng": "cng",
        "compressed natural gas": "cng",
        "lpg": "lpg",
        "liquefied petroleum gas": "lpg",
        "electric": "electric",
        "ev": "electric",
        "hybrid": "hybrid",
        "other": "other",
    }

    def normalize(self, policy: PolicyDetails) -> NormalizedPolicy:
        vehicle = policy.vehicle
        insurer = policy.insurer
        premium = policy.premium
        period = policy.period

        return NormalizedPolicy(
            policy_number=self._clean_text(policy.policy_number),
            policy_type=policy.policy_type,
            policy_start_date=period.start_date,
            policy_end_date=period.end_date,
            ncb_percentage=policy.ncb_percentage,
            vehicle=NormalizedVehicle(
                registration_number=self._clean_text(
                    vehicle.registration_number
                ),
                rto_code=self._normalize_rto(vehicle.rto_code),
                make=self._clean_text(vehicle.make),
                model=self._clean_text(vehicle.model),
                fuel_type=self._normalize_fuel(vehicle.fuel_type),
                engine_cc=vehicle.engine_cc,
                manufacture_year=vehicle.manufacture_year,
                vehicle_age=vehicle.vehicle_age,
                vehicle_category=vehicle.vehicle_category,
            ),
            insurer=NormalizedInsurer(
                current_insurer=self._clean_text(
                    insurer.current_insurer
                ),
                previous_insurer=self._clean_text(
                    insurer.previous_insurer
                ),
                business_type=insurer.business_type,
            ),
            premium=NormalizedPremium(
                own_damage=premium.own_damage_premium,
                third_party=premium.third_party_premium,
                addons=premium.add_on_premium,
                net_premium=premium.net_premium,
                gst=premium.gst,
                total_premium=premium.total_premium,
            ),
            source_policy=policy,
        )

    @staticmethod
    def _clean_text(value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = " ".join(value.split())
        return cleaned or None

    @staticmethod
    def _normalize_rto(value: str | None) -> str | None:
        if value is None:
            return None

        # Remove spaces and standardize case, e.g. "wb 02" -> "WB02".
        return "".join(value.split()).upper() or None

    @classmethod
    def _normalize_fuel(cls, value: str | None) -> str:
        if not value:
            return "unknown"

        normalized = " ".join(value.lower().strip().split())
        return cls.FUEL_TYPE_MAP.get(normalized, "other")
