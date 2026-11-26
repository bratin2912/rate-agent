
from datetime import date

from app.policy_extraction.schemas.policy import PolicyDetails


class PolicyValidator:
    """Validate and derive policy facts deterministically."""

    def validate(self, policy: PolicyDetails) -> list[str]:
        errors = []

        vehicle = policy.vehicle
        period = policy.period
        insurer = policy.insurer

        # 1. Validate policy dates.
        if period.start_date and period.end_date:
            if period.end_date < period.start_date:
                errors.append(
                    "Policy end date cannot be earlier than start date."
                )

        # 2. Validate manufacture year.
        current_year = date.today().year

        if vehicle.manufacture_year is not None:
            if not 1900 <= vehicle.manufacture_year <= current_year + 1:
                errors.append("Invalid vehicle manufacture year.")

        # 3. Validate engine capacity.
        if vehicle.engine_cc is not None and vehicle.engine_cc <= 0:
            errors.append("Engine capacity must be greater than zero.")

        # 4. Validate NCB.
        if policy.ncb_percentage is not None:
            allowed_ncb = {0, 20, 25, 35, 45, 50}

            if policy.ncb_percentage not in allowed_ncb:
                errors.append(
                    f"Unexpected NCB percentage: {policy.ncb_percentage}"
                )

        # 5. Validate premium amounts.
        premium = policy.premium

        for field_name in (
            "own_damage_premium",
            "third_party_premium",
            "add_on_premium",
            "net_premium",
            "gst",
            "total_premium",
        ):
            value = getattr(premium, field_name)

            if value is not None and value < 0:
                errors.append(
                    f"{field_name} cannot be negative."
                )

        # 6. Renewal consistency.
        if (
            insurer.current_insurer
            and insurer.previous_insurer
            and insurer.current_insurer.strip().casefold()
            == insurer.previous_insurer.strip().casefold()
            and insurer.business_type == "new_business"
        ):
            errors.append(
                "Business type is marked new_business, but current "
                "and previous insurer are the same. Verify the source."
            )

        return errors

    def derive_vehicle_age(self, policy: PolicyDetails) -> int | None:
        manufacture_year = policy.vehicle.manufacture_year
        policy_start_date = policy.period.start_date

        if manufacture_year is None or policy_start_date is None:
            return None

        return policy_start_date.year - manufacture_year
