from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional, Union


RawMetricValue = Union[str, int, float, Decimal]


@dataclass
class InterpretedMetric:
    source_metric: str
    raw_value: RawMetricValue
    rate_percent: Optional[Decimal]
    status: str
    explanation: str


class MetricInterpreter:
    """
    Interprets values from insurer commission grids.

    Important:
    - Does not assume CD1 or CD2 means OD or TP.
    - Converts decimal fractions into percentages.
    - Preserves text values such as D and referral instructions.
    - Does not invent a rate when the source value is ambiguous.
    """

    DECLINE_MARKERS = {
        "D",
        "DECLINE",
        "DECLINED",
    }

    def interpret(
        self,
        source_metric: str,
        raw_value: RawMetricValue,
    ) -> InterpretedMetric:

        if raw_value is None or str(raw_value).strip() == "":
            return InterpretedMetric(
                source_metric=source_metric,
                raw_value=raw_value,
                rate_percent=None,
                status="missing",
                explanation="The source grid does not contain a value.",
            )

        if isinstance(raw_value, str):
            value = raw_value.strip()
            normalized = value.upper()

            if normalized in self.DECLINE_MARKERS:
                return InterpretedMetric(
                    source_metric=source_metric,
                    raw_value=raw_value,
                    rate_percent=None,
                    status="declined",
                    explanation=(
                        f"The source explicitly marks {value!r} "
                        "as a decline indicator."
                    ),
                )

            # Values such as "85%/90%" require an explicit rule
            # to determine which percentage applies.
            if "%" in value or "/" in value:
                return InterpretedMetric(
                    source_metric=source_metric,
                    raw_value=raw_value,
                    rate_percent=None,
                    status="ambiguous",
                    explanation=(
                        "The source contains a percentage expression "
                        "that requires additional applicability rules."
                    ),
                )

            try:
                numeric_value = Decimal(value)
            except InvalidOperation:
                return InterpretedMetric(
                    source_metric=source_metric,
                    raw_value=raw_value,
                    rate_percent=None,
                    status="uninterpreted",
                    explanation=(
                        "The source contains a textual instruction or "
                        "marker, not a directly interpretable numeric rate."
                    ),
                )
        else:
            try:
                numeric_value = Decimal(str(raw_value))
            except InvalidOperation:
                return InterpretedMetric(
                    source_metric=source_metric,
                    raw_value=raw_value,
                    rate_percent=None,
                    status="uninterpreted",
                    explanation="The numeric value could not be interpreted.",
                )

        if numeric_value < 0 or numeric_value > 1:
            return InterpretedMetric(
                source_metric=source_metric,
                raw_value=raw_value,
                rate_percent=None,
                status="ambiguous",
                explanation=(
                    "The numeric value is outside the supported decimal "
                    "fraction range [0, 1]. Its unit is not established."
                ),
            )

        percentage = numeric_value * Decimal("100")

        return InterpretedMetric(
            source_metric=source_metric,
            raw_value=raw_value,
            rate_percent=percentage,
            status="interpreted",
            explanation=(
                f"Interpreted source value {numeric_value} as "
                f"{percentage}% using decimal-fraction conversion. "
                "The original CD1/CD2 meaning remains unchanged."
            ),
        )