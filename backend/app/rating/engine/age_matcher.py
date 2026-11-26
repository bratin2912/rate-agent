
import re
from decimal import Decimal, InvalidOperation
from typing import Any


class AgeMatcher:
    def __init__(self, wildcard_values: tuple[str, ...] = ("All",)):
        self.wildcard_values = {
            value.casefold() for value in wildcard_values
        }

    def matches(self, vehicle_age: int | None, grid_value: Any) -> str:
        """
        Possible results:
        match, no_match, insufficient_data, unsupported_format
        """

        if vehicle_age is None or grid_value is None:
            return "insufficient_data"

        value = str(grid_value).strip()

        if not value:
            return "insufficient_data"

        if value.casefold() in self.wildcard_values:
            return "match"

        # Exact numeric age.
        number = self._decimal(value)

        if number is not None:
            return (
                "match"
                if Decimal(vehicle_age) == number
                else "no_match"
            )

        # Explicit ranges: 0-5, 0 to 5, 0–5.
        range_match = re.fullmatch(
            r"\s*(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*"
            r"(\d+(?:\.\d+)?)\s*",
            value,
            flags=re.IGNORECASE,
        )

        if not range_match:
            return "unsupported_format"

        minimum = Decimal(range_match.group(1))
        maximum = Decimal(range_match.group(2))

        if minimum > maximum:
            return "unsupported_format"

        age = Decimal(vehicle_age)

        return (
            "match"
            if minimum <= age <= maximum
            else "no_match"
        )

    @staticmethod
    def _decimal(value: str) -> Decimal | None:
        try:
            return Decimal(value)
        except (InvalidOperation, ValueError):
            return None
