from dataclasses import dataclass
from typing import Optional

from app.rating.engine.metric_interpreter import InterpretedMetric


@dataclass
class CommissionComponentMapping:
    source_metric: str
    component: Optional[str]
    rate_percent: Optional[float]
    status: str
    explanation: str


class CommissionComponentMapper:
    """
    Maps interpreted grid metrics to OD/TP commission components.

    Until the insurer's documentation establishes the relationship
    between CD1/CD2 and OD/TP, those metrics remain unmapped.
    """

    def map_metric(
        self,
        metric: InterpretedMetric,
        product_context: Optional[str] = None,
    ) -> CommissionComponentMapping:

        if metric.status == "declined":
            return CommissionComponentMapping(
                source_metric=metric.source_metric,
                component=None,
                rate_percent=None,
                status="declined",
                explanation=metric.explanation,
            )

        if metric.status != "interpreted":
            return CommissionComponentMapping(
                source_metric=metric.source_metric,
                component=None,
                rate_percent=None,
                status="insufficient_data",
                explanation=metric.explanation,
            )

        return CommissionComponentMapping(
            source_metric=metric.source_metric,
            component=None,
            rate_percent=float(metric.rate_percent),
            status="component_unverified",
            explanation=(
                f"{metric.source_metric} was numerically interpreted, "
                f"but its OD/TP component mapping is not established. "
                f"Product context: {product_context or 'unknown'}."
            ),
        )