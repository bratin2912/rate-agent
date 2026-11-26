
from decimal import Decimal, InvalidOperation


class FourWheelerSegmentResolver:
    """
    Resolves private-car fuel and engine capacity into
    a Go Digit 4W SATP segment.

    Only explicitly configured segment boundaries are supported.
    """

    SEGMENT_RULES = {
        "cng": {
            "threshold": Decimal("1000"),
            "below": "CNG<1000",
            "above": "CNG>1000",
        },
        "diesel": {
            "threshold": Decimal("1500"),
            "below": "Diesel<1500",
            "above": "Diesel>1500",
        },
        "petrol": {
            "threshold": Decimal("1000"),
            "below": "Petrol<1000",
            "above": "Petrol>1000",
        },
    }

    def resolve(
        self,
        fuel_type: str | None,
        engine_cc: int | None,
    ) -> dict:
        if not fuel_type or engine_cc is None:
            return {
                "status": "insufficient_data",
                "segment": None,
                "reason": "Fuel type or engine capacity is missing.",
            }

        fuel = fuel_type.strip().casefold()
        rule = self.SEGMENT_RULES.get(fuel)

        if rule is None:
            return {
                "status": "unsupported",
                "segment": None,
                "reason": f"No verified segment rule for fuel: {fuel}",
            }

        try:
            capacity = Decimal(str(engine_cc))
        except (InvalidOperation, ValueError):
            return {
                "status": "invalid_data",
                "segment": None,
                "reason": "Invalid engine capacity.",
            }

        if capacity <= 0:
            return {
                "status": "invalid_data",
                "segment": None,
                "reason": "Engine capacity must be positive.",
            }

        threshold = rule["threshold"]

        # The source labels do not establish the exact-boundary
        # treatment. Do not invent one.
        if capacity == threshold:
            return {
                "status": "ambiguous",
                "segment": None,
                "reason": (
                    f"Engine capacity equals the {threshold} CC "
                    "boundary; source boundary convention is unverified."
                ),
            }

        segment = (
            rule["below"]
            if capacity < threshold
            else rule["above"]
        )

        return {
            "status": "resolved",
            "segment": segment,
            "fuel_type": fuel,
            "engine_cc": int(capacity),
        }
