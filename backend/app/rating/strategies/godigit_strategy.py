
from app.rating.services.grid_repository import GridRepository
from app.rating.engine.rto_resolver import RTOResolver
from app.rating.engine.age_matcher import AgeMatcher
from app.rating.engine.segment_resolver import FourWheelerSegmentResolver
from app.rating.engine.metric_interpreter import MetricInterpreter
from app.rating.engine.commission_component_mapper import (
    CommissionComponentMapper,
)


class GoDigitRatingStrategy:
    SOURCE_ID = "godigit_mar_2026"

    RTO_SHEET = "4W  RTO"
    GRID_SHEET = "4W SATP"

    RTO_CLUSTER_FIELD = "four_wheeler_tp_cluster"

    def __init__(self, repository: GridRepository):
        self.repository = repository
        self.rto_resolver = RTOResolver(repository)
        self.age_matcher = AgeMatcher()
        self.segment_resolver = FourWheelerSegmentResolver()
        self.metric_interpreter = MetricInterpreter()
        self.component_mapper = CommissionComponentMapper()

    @staticmethod
    def _value(record, field_name):
        field = record.fields.get(field_name)

        if field is None:
            return None

        return getattr(field, "normalized_value", None) or getattr(
            field, "raw_value", None
        )

    def evaluate(self, policy):
        trace = []
        warnings = []

        vehicle = policy.vehicle

        # 1. Validate supported product
        if vehicle.vehicle_category != "private_car":
            return self._failure(
                "insufficient_data",
                "Currently only private-car policies are supported.",
            )

        if policy.policy_type != "standalone_tp":
            return self._failure(
                "insufficient_data",
                "Go Digit integration currently supports 4W SATP only.",
            )

        trace.append("Product identified: private-car standalone TP")

        # 2. Resolve RTO cluster
        if not vehicle.rto_code:
            return self._failure(
                "insufficient_data",
                "RTO code is missing from the policy.",
                trace,
            )

        rto_result = self.rto_resolver.resolve(
            source_id=self.SOURCE_ID,
            sheet_name=self.RTO_SHEET,
            rto_code=vehicle.rto_code,
            cluster_field_name=self.RTO_CLUSTER_FIELD,
        )

        if not rto_result or rto_result.get("status") != "matched":
            return self._failure(
                "no_match",
                "Could not resolve a unique Go Digit TP RTO cluster.",
                trace,
            )

        cluster = rto_result["cluster"]
        trace.append(f"RTO {vehicle.rto_code} resolved to {cluster}")

        # 3. Resolve vehicle segment
        segment_result = self.segment_resolver.resolve(
            fuel_type=vehicle.fuel_type,
            engine_cc=vehicle.engine_cc,
        )

        if segment_result.get("status") != "matched":
            return self._failure(
                "insufficient_data",
                segment_result.get("explanation", "Vehicle segment unresolved."),
                trace,
            )

        segment = segment_result["segment"]
        trace.append(f"Vehicle segment resolved: {segment}")

        # 4. Load SATP grid
        records = self.repository.get_records(
            self.SOURCE_ID,
            self.GRID_SHEET,
        )

        if not records:
            return self._failure(
                "no_match",
                "Go Digit 4W SATP grid is empty or unavailable.",
                trace,
            )

        # 5. Find rows matching vehicle segment and age.
        # Decline rows are evaluated separately from normal cluster rows.
        matching_records = []
        decline_records = []

        for record in records:
            row_segment = self._value(record, "vehicle_segment")
            row_cluster = self._value(record, "geographic_cluster")
            row_age = self._value(record, "vehicle_age_eligibility")

            if str(row_segment).strip().lower() != segment.lower():
                continue

            if not self.age_matcher.matches(vehicle.vehicle_age, row_age):
                continue

            if str(row_cluster).strip().upper() == "ALL_INDIA_DECLINE":
                decline_records.append(record)
                continue

            if str(row_cluster).strip().lower() == cluster.lower():
                matching_records.append(record)

        trace.append(
            f"Grid lookup completed: {len(matching_records)} matching rows, "
            f"{len(decline_records)} decline rows."
        )

        # 6. Do not assume every decline note applies to every RTO.
        # The source says some declines apply only to a few RTOs.
        if decline_records and not matching_records:
            return self._failure(
                "insufficient_data",
                "A decline-related source row exists, but its RTO applicability "
                "cannot be established from the available mapping.",
                trace,
            )

        if not matching_records:
            return self._failure(
                "no_match",
                "No Go Digit SATP grid row matches the resolved vehicle criteria.",
                trace,
            )

        if len(matching_records) > 1:
            return self._failure(
                "ambiguous",
                "Multiple Go Digit SATP rows matched the same vehicle criteria.",
                trace,
            )

        record = matching_records[0]

        # 7. Interpret the source metric
        raw_rate = self._value(record, "Max CD2")

        metric = self.metric_interpreter.interpret(
            source_metric="Max CD2",
            raw_value=raw_rate,
        )

        mapped_metric = self.component_mapper.map_metric(
            metric,
            product_context="standalone_tp",
        )

        trace.append(
            f"Source metric Max CD2 interpreted with status: {metric.status}"
        )

        return {
            "source_id": self.SOURCE_ID,
            "overall_status": mapped_metric.status,
            "od": {
                "status": "not_applicable",
                "rate_percent": None,
            },
            "tp": {
                "status": mapped_metric.status,
                "rate_percent": mapped_metric.rate_percent,
                "source_metric": mapped_metric.source_metric,
            },
            "trace": trace,
            "warnings": [
                mapped_metric.explanation,
                "CD2-to-TP brokerage mapping is not verified.",
            ],
            "matched_record_id": getattr(record, "record_id", None),
        }

    @staticmethod
    def _failure(status, message, trace=None):
        return {
            "source_id": GoDigitRatingStrategy.SOURCE_ID,
            "overall_status": status,
            "od": {
                "status": "not_applicable",
                "rate_percent": None,
            },
            "tp": {
                "status": status,
                "rate_percent": None,
            },
            "trace": trace or [],
            "warnings": [message],
            "matched_record_id": None,
        }
