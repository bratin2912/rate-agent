
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.ingestion.core.normalized_models import NormalizedRecord
from app.rating.engine.rule_evaluator import RuleEvaluator


@dataclass
class GridMatch:
    record: NormalizedRecord
    matched_fields: list[str]
    evidence: list[dict[str, Any]]


class GridMatcher:
    """
    Matches normalized policy criteria against insurer grid records.

    Does not calculate commission rates or automatically select
    the first matching record.
    """

    def __init__(
        self,
        evaluator: RuleEvaluator | None = None,
    ):
        self.evaluator = evaluator or RuleEvaluator()

    def match(
        self,
        records: list[NormalizedRecord],
        criteria: dict[str, Any],
        wildcard_values: tuple[str, ...] = (),
        decline_values: tuple[str, ...] = (),
        age: int | None = None,
        age_range_fields: tuple[str, str] | None = None,
    ) -> dict:
        matches = []
        declined_records = []
        rejected_records = []

        if not criteria and not age_range_fields:
            return {
                "status": "insufficient_data",
                "matches": [],
                "declined_records": [],
                "rejected_records": [],
                "match_count": 0,
            }

        for record in records:
            matched_fields = []
            evidence = []
            failed = False
            declined = False

            # Match ordinary policy attributes.
            for canonical_name, expected_value in criteria.items():
                field = self._find_field(
                    record.fields,
                    canonical_name,
                )

                if field is None:
                    failed = True
                    break

                source_value = (
                    field.normalized_value
                    if field.normalized_value is not None
                    else field.raw_value
                )

                outcome = self.evaluator.evaluate_value(
                    source_value=source_value,
                    expected_value=expected_value,
                    wildcard_values=wildcard_values,
                    decline_values=decline_values,
                )

                if outcome == "declined":
                    declined = True
                    break

                if outcome != "match":
                    failed = True
                    break

                matched_fields.append(canonical_name)
                evidence.append(self._build_evidence(field))

            # Match age ranges when configured.
            if not failed and not declined and age_range_fields:
                min_field_name, max_field_name = age_range_fields

                min_field = self._find_field(
                    record.fields,
                    min_field_name,
                )

                max_field = self._find_field(
                    record.fields,
                    max_field_name,
                )

                if min_field is None or max_field is None:
                    failed = True
                else:
                    age_outcome = self.evaluator.evaluate_age_range(
                        age=age,
                        minimum=min_field.raw_value,
                        maximum=max_field.raw_value,
                    )

                    if age_outcome == "match":
                        matched_fields.append("vehicle_age")
                        evidence.extend([
                            self._build_evidence(min_field),
                            self._build_evidence(max_field),
                        ])
                    else:
                        failed = True

            # Classify the record.
            if declined:
                declined_records.append(record)

            elif failed:
                rejected_records.append(record)

            else:
                matches.append(
                    GridMatch(
                        record=record,
                        matched_fields=matched_fields,
                        evidence=evidence,
                    )
                )

        status = self._resolve_status(
            matches,
            declined_records,
        )

        return {
            "status": status,
            "matches": matches,
            "declined_records": declined_records,
            "rejected_records": rejected_records,
            "match_count": len(matches),
        }

    @staticmethod
    def _find_field(
        fields: dict,
        canonical_name: str,
    ):
        return next(
            (
                field
                for field in fields.values()
                if field.canonical_name == canonical_name
            ),
            None,
        )

    @staticmethod
    def _build_evidence(field) -> dict:
        return {
            "source_id": field.source.source_id,
            "filename": field.source.filename,
            "sheet_name": field.source.sheet_name,
            "source_header": field.source_header,
            "raw_value": field.raw_value,
            "cell_coordinates": field.source.cell_coordinates,
        }

    @staticmethod
    def _resolve_status(
        matches: list[GridMatch],
        declined_records: list[NormalizedRecord],
    ) -> str:
        if len(matches) == 1:
            return "matched"

        if len(matches) > 1:
            return "ambiguous"

        if declined_records:
            return "declined"

        return "no_match"
