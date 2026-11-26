
from decimal import Decimal, InvalidOperation
from typing import Any


class RuleEvaluator:
    def evaluate_value(
        self,
        source_value: Any,
        expected_value: Any,
        wildcard_values: tuple[str, ...] = (),
        decline_values: tuple[str, ...] = (),
    ) -> str:
        """
        Returns: match, no_match, declined, or insufficient_data.
        """

        if source_value is None or expected_value is None:
            return "insufficient_data"

        source_text = str(source_value).strip()
        expected_text = str(expected_value).strip()

        if not source_text or not expected_text:
            return "insufficient_data"

        if source_text.casefold() in {
            value.casefold() for value in decline_values
        }:
            return "declined"

        if source_text.casefold() in {
            value.casefold() for value in wildcard_values
        }:
            return "match"

        return (
            "match"
            if source_text.casefold() == expected_text.casefold()
            else "no_match"
        )

    def evaluate_age_range(
        self,
        age: int | None,
        minimum: Any,
        maximum: Any,
    ) -> str:
        if age is None:
            return "insufficient_data"

        min_value = self._to_decimal(minimum)
        max_value = self._to_decimal(maximum)

        if min_value is None or max_value is None:
            return "insufficient_data"

        return (
            "match"
            if min_value <= Decimal(age) <= max_value
            else "no_match"
        )

    @staticmethod
    def _to_decimal(value: Any) -> Decimal | None:
        if value is None:
            return None

        try:
            return Decimal(str(value).strip())
        except (InvalidOperation, ValueError):
            return None
