
from app.rating.services.grid_repository import GridRepository
from app.rating.strategies.godigit_strategy import GoDigitRatingStrategy


class RatingService:

    def __init__(self, repository=None):
        self.repository = repository or GridRepository()

        self.strategies = {
            "godigit_mar_2026": GoDigitRatingStrategy(self.repository),
        }

    def rate(self, source_id: str, policy):
        strategy = self.strategies.get(source_id)

        if strategy is None:
            return {
                "source_id": source_id,
                "overall_status": "insufficient_data",
                "warnings": [
                    f"No rating strategy registered for {source_id}."
                ],
                "od": {
                    "status": "insufficient_data",
                    "rate_percent": None,
                },
                "tp": {
                    "status": "insufficient_data",
                    "rate_percent": None,
                },
                "trace": [],
            }

        return strategy.evaluate(policy)
from app.policy_extraction.schemas.normalized_policy import NormalizedPolicy

from app.rating.engine.age_matcher import AgeMatcher
from app.rating.engine.grid_matcher import GridMatcher
from app.rating.engine.product_resolver import ProductResolver
from app.rating.engine.rto_resolver import RTOResolver
from app.rating.engine.segment_resolver import (
    FourWheelerSegmentResolver,
)
from app.rating.services.grid_repository import GridRepository
from app.rating.engine.underwriting_evaluator import UnderwritingEvaluator

class GoDigitRatingStrategy:
    SOURCE_ID = "godigit_mar_2026"

    RTO_CONFIG = {
        "sheet_name": "4W  RTO",
        "cluster_field": "four_wheeler_tp_cluster",
    }

    GRID_CONFIG = {
        "4W SATP": {
            "age_field": "vehicle_age_eligibility",
        },
    }

    def __init__(self, repository: GridRepository):
        self.repository = repository
        self.product_resolver = ProductResolver()
        self.rto_resolver = RTOResolver(repository)
        self.segment_resolver = FourWheelerSegmentResolver()
        self.grid_matcher = GridMatcher()
        self.age_matcher = AgeMatcher()

    def evaluate(self, policy: NormalizedPolicy) -> dict:
        trace = []

        # 1. Resolve candidate worksheet.
        product = self.product_resolver.resolve(policy)

        trace.append({
            "step": 1,
            "rule": "product_resolution",
            "outcome": product["status"],
            "details": product,
        })

        if product["status"] != "candidates_identified":
            return self._result(
                product["status"],
                trace,
                product.get("reason"),
            )

        if product["candidate_sheets"] != ["4W SATP"]:
            return self._result(
                "unsupported_grid",
                trace,
                "This strategy currently supports only 4W SATP.",
            )

        # 2. Resolve RTO cluster.
        rto_code = policy.vehicle.rto_code

        if not rto_code:
            return self._result(
                "insufficient_data",
                trace,
                "Vehicle RTO code is missing.",
            )

        rto_result = self.rto_resolver.resolve(
            source_id=self.SOURCE_ID,
            sheet_name=self.RTO_CONFIG["sheet_name"],
            rto_code=rto_code,
            cluster_field_name=self.RTO_CONFIG["cluster_field"],
        )

        trace.append({
            "step": 2,
            "rule": "rto_cluster_resolution",
            "outcome": (
                rto_result["status"]
                if rto_result
                else "no_match"
            ),
            "details": rto_result,
        })

        if not rto_result or rto_result["status"] != "matched":
            return self._result(
                rto_result["status"] if rto_result else "no_match",
                trace,
                "Could not resolve a unique RTO cluster.",
            )

        cluster = rto_result["cluster"]

        # 3. Resolve vehicle segment.
        segment_result = self.segment_resolver.resolve(
            fuel_type=policy.vehicle.fuel_type,
            engine_cc=policy.vehicle.engine_cc,
        )

        trace.append({
            "step": 3,
            "rule": "vehicle_segment_resolution",
            "outcome": segment_result["status"],
            "details": segment_result,
        })

        if segment_result["status"] != "resolved":
            return self._result(
                segment_result["status"],
                trace,
                segment_result.get("reason"),
            )

        segment = segment_result["segment"]
        
            

        # 4. Load the commission grid.
        sheet_name = "4W SATP"

        table = self.repository.get_sheet(
            source_id=self.SOURCE_ID,
            sheet_name=sheet_name,
        )

        if table is None:
            return self._result(
                "no_match",
                trace,
                "Go Digit 4W SATP worksheet was not found.",
            )

        # 5. Match cluster and segment.
        match_result = self.grid_matcher.match(
            records=table.records,
            criteria={
                "geographic_cluster": cluster,
                "vehicle_segment": segment,
            },
        )

        # 6. Apply age eligibility.
        age_field_name = self.GRID_CONFIG[sheet_name]["age_field"]
        eligible = []
        unsupported_age_records = []

        for match in match_result["matches"]:
            age_field = next(
                (
                    field
                    for field in match.record.fields.values()
                    if field.canonical_name == age_field_name
                ),
                None,
            )

            if age_field is None:
                continue

            age_status = self.age_matcher.matches(
                vehicle_age=policy.vehicle.vehicle_age,
                grid_value=age_field.raw_value,
            )

            if age_status == "match":
                eligible.append(match)

            elif age_status == "unsupported_format":
                unsupported_age_records.append(match.record)

        status = (
            "matched" if len(eligible) == 1
            else "ambiguous" if len(eligible) > 1
            else "insufficient_data"
            if unsupported_age_records
            else "no_match"
        )

        trace.append({
            "step": 4,
            "rule": "grid_matching_and_age_eligibility",
            "outcome": status,
            "details": {
                "cluster": cluster,
                "segment": segment,
                "vehicle_age": policy.vehicle.vehicle_age,
                "matched_count": len(eligible),
                "unsupported_age_count": len(
                    unsupported_age_records
                ),
            },
        })

        matched_records = []

        for match in eligible:
            matched_records.append({
                "record": match.record.model_dump(mode="json"),
                "matched_fields": (
                    match.matched_fields + ["vehicle_age"]
                ),
                "evidence": match.evidence,
            })

        return {
            "source_id": self.SOURCE_ID,
            "status": status,
            "sheet_name": sheet_name,
            "matched_records": matched_records,
            "decision_trace": trace,
            "commission": {
                "od_rate_percent": None,
                "tp_rate_percent": None,
                "status": "not_calculated",
                "reason": (
                    "CD1/CD2 have not yet been verified as OD/TP "
                    "brokerage percentages."
                ),
            },
            "warnings": [
                "Only the 4W SATP grid is currently supported.",
                "Commission calculation is not yet implemented.",
            ],
        }

    def _result(
        self,
        status: str,
        trace: list[dict],
        reason: str | None = None,
    ) -> dict:
        return {
            "source_id": self.SOURCE_ID,
            "status": status,
            "matched_records": [],
            "decision_trace": trace,
            "commission": {
                "od_rate_percent": None,
                "tp_rate_percent": None,
                "status": "not_calculated",
                "reason": reason or "Rating could not be completed.",
            },
            "warnings": [reason] if reason else [],
        }

    def _evaluate_underwriting(
        self,
        records,
        segment: str,
        vehicle_age: int | None,
    ) -> dict:
        # First identify records matching the vehicle segment.
        segment_result = self.grid_matcher.match(
            records=records,
            criteria={
                "vehicle_segment": segment,
            },
        )

        declined = []
        manual_review = []

        for match in segment_result["matches"]:
            age_field = next(
                (
                    field
                    for field in match.record.fields.values()
                    if field.canonical_name == "vehicle_age_eligibility"
                ),
                None,
            )

            if age_field is None:
                continue

            age_status = self.age_matcher.matches(
                vehicle_age=vehicle_age,
                grid_value=age_field.raw_value,
            )

            if age_status != "match":
                continue

            result = self.underwriting_evaluator.evaluate(match.record)

            item = {
                "record_id": match.record.record_id,
                "source_row": match.record.source_row,
                **result,
            }

            if result["status"] == "declined":
                declined.append(item)

            elif result["status"] == "manual_review":
                manual_review.append(item)

        if declined:
            return {
                "status": "declined",
                "declined_records": declined,
                "manual_review_records": manual_review,
            }

        if manual_review:
            return {
                "status": "manual_review",
                "declined_records": [],
                "manual_review_records": manual_review,
            }

        return {
            "status": "no_decline_indicator",
            "declined_records": [],
            "manual_review_records": [],
        }


