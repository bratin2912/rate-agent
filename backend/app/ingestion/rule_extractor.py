
from typing import Any

from app.ingestion.core.rule_models import (
    CommissionRule,
    RuleCondition,
    RuleValue,
)


class CommissionRuleExtractor:
    """
    Converts mapped normalized records into structured commission rules.
    """

    CONDITION_FIELDS = {
        "geographic_cluster",
        "vehicle_segment",
        "vehicle_make",
        "vehicle_age_min",
        "vehicle_age_max",
        "vehicle_age_eligibility",
        "rto_code",
        "addon_condition",
    }

    NOTE_FIELDS = {
        "underwriting_note",
    }

    def extract(
        self,
        document: dict[str, Any],
    ) -> list[CommissionRule]:

        source = document["source"]
        source_id = source["source_id"]
        insurer = source.get("publisher", "Unknown")
        source_version = source.get("version", "Unknown")
        filename = source.get("original_filename", "Unknown")

        rules = []

        for sheet_name, table in document["sheets"].items():

            # We are extracting commission rules only.
            # RTO mappings will be handled separately.
            if table["table_type"] != "commission_grid":
                continue

            for record in table["records"]:

                conditions = []
                rule_values = []
                underwriting_notes = []
                source_evidence = {}

                for field in record["fields"].values():

                    canonical_name = field.get("canonical_name")
                    source_header = field["source_header"]

                    raw_value = field.get("raw_value")
                    normalized_value = field.get("normalized_value")

                    value = (
                        normalized_value
                        if normalized_value is not None
                        else raw_value
                    )

                    if value is None:
                        continue

                    source_ref = field.get("source", {})

                    source_evidence[source_header] = {
                        "cells": source_ref.get(
                            "cell_coordinates", []
                        ),
                        "raw_value": raw_value,
                    }

                    if canonical_name in self.NOTE_FIELDS:
                        underwriting_notes.append(str(value))
                        continue

                    if canonical_name in self.CONDITION_FIELDS:
                        conditions.append(
                            RuleCondition(
                                field=canonical_name,
                                operator="equals",
                                value=value,
                            )
                        )
                        continue

                    # Preserve all other fields without
                    # assuming their business meaning.
                    rule_values.append(
                        RuleValue(
                            source_field=source_header,
                            raw_value=raw_value,
                            interpreted_value=None,
                            interpretation_status="unresolved",
                        )
                    )

                source_row = record["source_row"]

                rule = CommissionRule(
                    rule_id=(
                        f"{source_id}:"
                        f"{sheet_name}:"
                        f"{source_row}"
                    ),
                    source_id=source_id,
                    insurer=insurer,
                    source_version=source_version,
                    product_line=table["product_line"],
                    table_type=table["table_type"],
                    conditions=conditions,
                    rule_values=rule_values,
                    underwriting_notes=underwriting_notes,
                    source_sheet=sheet_name,
                    source_row=source_row,
                    source_evidence=source_evidence,
                )

                rules.append(rule)

        return rules
