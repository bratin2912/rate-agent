
import re
from typing import Any


class RTOResolver:
    """Resolve an RTO code to the insurer-specific product cluster."""

    RTO_SHEET = "CV RTO Mapping"

    PRODUCT_COLUMN_MAPPING = {
        "gcv3": "CV_GCV3(EV/Non-EV)",
        "lcv": "CV_LCV",
        "mcv": "CV_MCV",
        "hcv": "CV_HCV",
        "pcv_2w_3w": "CV_PCV2W(All)_3W_Non-electric",
        "pcv_3w_electric": "PCV_3W_Electric",
        "pcv_4w_upto_5_seating": "CV_PCV4(Upto 5 seating)",
        "pcv_6plus_seating": "CV_PCV_6+Seating",
        "misc": "CV_MiscD",
    }

    def __init__(self, normalized_document: dict[str, Any]):
        self.document = normalized_document
        self.rto_records = self._load_rto_records()

    def _load_rto_records(self) -> list[dict[str, Any]]:
        sheets = self.document.get("sheets", {})
        table = sheets.get(self.RTO_SHEET)

        if not table:
            raise ValueError(
                f"RTO mapping sheet not found: {self.RTO_SHEET}"
            )

        records = table.get("records", [])

        if not isinstance(records, list):
            raise ValueError(
                f"Invalid records structure in sheet: {self.RTO_SHEET}"
            )

        return records

    def resolve(
        self,
        rto_code: str,
        vehicle_category: str,
    ) -> dict[str, Any]:

        normalized_rto = self._normalize_rto(rto_code)

        if not normalized_rto:
            return self._build_result(
                status="invalid_rto",
                rto_code=rto_code,
                vehicle_category=vehicle_category,
            )

        normalized_category = (
            vehicle_category.strip().lower()
            if isinstance(vehicle_category, str)
            else ""
        )

        if normalized_category not in self.PRODUCT_COLUMN_MAPPING:
            return self._build_result(
                status="unsupported_category",
                rto_code=rto_code,
                vehicle_category=vehicle_category,
            )

        target_column = self.PRODUCT_COLUMN_MAPPING[
            normalized_category
        ]

        for record in self.rto_records:
            fields = record.get("fields", {})

            rto_field = self._find_field(fields, "rto_code")

            if rto_field is None:
                continue

            source_rto = self._get_field_value(rto_field)

            if self._normalize_rto(source_rto) != normalized_rto:
                continue

            cluster_field = self._find_field(
                fields,
                target_column,
            )

            if cluster_field is None:
                return self._build_result(
                    status="mapping_column_missing",
                    rto_code=rto_code,
                    vehicle_category=normalized_category,
                    record=record,
                )

            cluster = self._get_field_value(cluster_field)

            evidence = self._build_evidence(
                record,
                cluster_field,
            )

            if cluster is None or not str(cluster).strip():
                return self._build_result(
                    status="cluster_not_available",
                    rto_code=rto_code,
                    vehicle_category=normalized_category,
                    record=record,
                    evidence=evidence,
                )

            return self._build_result(
                status="resolved",
                rto_code=rto_code,
                vehicle_category=normalized_category,
                cluster=str(cluster).strip(),
                record=record,
                evidence=evidence,
            )

        return self._build_result(
            status="not_found",
            rto_code=rto_code,
            vehicle_category=normalized_category,
        )

    @staticmethod
    def _normalize_rto(value: Any) -> str:
        """Normalize RTO codes while preserving meaningful characters."""
        if value is None:
            return ""

        return re.sub(r"\s+", "", str(value)).upper()

    @staticmethod
    def _get_field_value(field: dict[str, Any]) -> Any:
        """Prefer normalized value, falling back to raw value."""
        value = field.get("normalized_value")

        if value is None:
            value = field.get("raw_value")

        return value

    @staticmethod
    def _build_evidence(
        record: dict[str, Any],
        field: dict[str, Any],
    ) -> dict[str, Any]:
        source = field.get("source") or {}

        return {
            "source_id": record.get("source_id"),
            "sheet": RTOResolver.RTO_SHEET,
            "row": record.get("source_row"),
            "cells": source.get("cell_coordinates", []),
        }

    @staticmethod
    def _build_result(
        status: str,
        rto_code: str,
        vehicle_category: str,
        cluster: Any = None,
        record: dict[str, Any] | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if evidence is None and record is not None:
            evidence = {
                "source_id": record.get("source_id"),
                "sheet": RTOResolver.RTO_SHEET,
                "row": record.get("source_row"),
                "cells": [],
            }

        return {
            "status": status,
            "rto_code": rto_code,
            "vehicle_category": vehicle_category,
            "cluster": cluster,
            "evidence": evidence,
        }

    @staticmethod
    def _find_field(
        fields: dict[str, Any],
        canonical_name: str,
    ) -> dict[str, Any] | None:
        for field in fields.values():
            if not isinstance(field, dict):
                continue

            if (
                field.get("canonical_name") == canonical_name
                or field.get("source_header") == canonical_name
            ):
                return field

        return None
