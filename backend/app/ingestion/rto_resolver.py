
from typing import Any


class RTOResolver:

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

    def _load_rto_records(self):
        sheets = self.document.get("sheets", {})
        table = sheets.get(self.RTO_SHEET)

        if not table:
            raise ValueError(
                f"RTO mapping sheet not found: {self.RTO_SHEET}"
            )

        return table.get("records", [])

    def resolve(
        self,
        rto_code: str,
        vehicle_category: str,
    ) -> dict[str, Any]:

        if vehicle_category not in self.PRODUCT_COLUMN_MAPPING:
            return {
                "status": "unsupported_category",
                "rto_code": rto_code,
                "vehicle_category": vehicle_category,
                "cluster": None,
                "evidence": None,
            }

        target_column = self.PRODUCT_COLUMN_MAPPING[
            vehicle_category
        ]

        for record in self.rto_records:
            fields = record.get("fields", {})

            rto_field = self._find_field(
                fields,
                "rto_code",
            )

            if not rto_field:
                continue

            source_rto = rto_field.get("normalized_value")
            if source_rto is None:
                source_rto = rto_field.get("raw_value")

            if str(source_rto).strip().upper() != rto_code.strip().upper():
                continue

            cluster_field = self._find_field(
                fields,
                target_column,
            )

            if not cluster_field:
                return {
                    "status": "mapping_column_missing",
                    "rto_code": rto_code,
                    "vehicle_category": vehicle_category,
                    "cluster": None,
                    "evidence": None,
                }

            cluster = cluster_field.get("normalized_value")
            if cluster is None:
                cluster = cluster_field.get("raw_value")

            source = cluster_field.get("source", {})

            if cluster is None or str(cluster).strip() == "":
                return {
                    "status": "cluster_not_available",
                    "rto_code": rto_code,
                    "vehicle_category": vehicle_category,
                    "cluster": None,
                    "evidence": {
                        "sheet": self.RTO_SHEET,
                        "row": record.get("source_row"),
                        "cells": source.get("cell_coordinates", []),
                    },
                }

            return {
                "status": "resolved",
                "rto_code": rto_code,
                "vehicle_category": vehicle_category,
                "cluster": cluster,
                "evidence": {
                    "source_id": record.get("source_id"),
                    "sheet": self.RTO_SHEET,
                    "row": record.get("source_row"),
                    "cells": source.get("cell_coordinates", []),
                },
            }

        return {
            "status": "not_found",
            "rto_code": rto_code,
            "vehicle_category": vehicle_category,
            "cluster": None,
            "evidence": None,
        }

    @staticmethod
    def _find_field(
        fields: dict[str, Any],
        canonical_name: str,
    ):
        for field in fields.values():
            if field.get("canonical_name") == canonical_name:
                return field

            if field.get("source_header") == canonical_name:
                return field

        return None
