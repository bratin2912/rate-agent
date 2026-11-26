
from typing import Any

from app.ingestion.core.normalized_models import NormalizedRecord


class UnderwritingEvaluator:
    """
    Evaluates explicit Go Digit underwriting indicators.

    Conservative behavior:
    - Explicit All_India_Decline cluster => declined.
    - Free-text underwriting notes => manual review.
    - Zero commission-related values => never treated as decline.
    """

    DECLINE_CLUSTER = "ALL_INDIA_DECLINE"

    def evaluate(
        self,
        record: NormalizedRecord,
    ) -> dict[str, Any]:
        cluster_field = self._find_field(
            record,
            "geographic_cluster",
        )

        note_field = self._find_field(
            record,
            "underwriting_note",
        )

        cluster = (
            str(cluster_field.raw_value).strip()
            if cluster_field and cluster_field.raw_value is not None
            else None
        )

        note = (
            str(note_field.raw_value).strip()
            if note_field and note_field.raw_value is not None
            else None
        )

        evidence = []

        if cluster_field:
            evidence.append(self._evidence(cluster_field))

        if note_field and note:
            evidence.append(self._evidence(note_field))

        if cluster and cluster.upper() == self.DECLINE_CLUSTER:
            return {
                "status": "declined",
                "reason": "The grid explicitly marks this cluster as All_India_Decline.",
                "evidence": evidence,
            }

        if note:
            return {
                "status": "manual_review",
                "reason": (
                    "The grid contains an underwriting note whose "
                    "conditions have not yet been evaluated."
                ),
                "note": note,
                "evidence": evidence,
            }

        return {
            "status": "no_decline_indicator",
            "reason": "No explicit decline indicator was found in this record.",
            "evidence": evidence,
        }

    @staticmethod
    def _find_field(record: NormalizedRecord, canonical_name: str):
        return next(
            (
                field
                for field in record.fields.values()
                if field.canonical_name == canonical_name
            ),
            None,
        )

    @staticmethod
    def _evidence(field) -> dict:
        return {
            "source_id": field.source.source_id,
            "filename": field.source.filename,
            "sheet_name": field.source.sheet_name,
            "source_header": field.source_header,
            "raw_value": field.raw_value,
            "cell_coordinates": field.source.cell_coordinates,
        }
