
from backend.app.ingestion.normalizer import (
    NormalizedField,
    NormalizedRecord,
    NormalizedTable,
    SourceReference,
)


class InsuranceDataNormalizer:
    """
    Converts extracted insurer tables into a common structure.

    This first version performs structural normalization only.
    It does not interpret commission values or business rules.
    """

    def normalize_sheet(
        self,
        extracted_sheet: dict,
        source_metadata: dict,
    ) -> NormalizedTable:

        normalized_records = []

        for record in extracted_sheet["records"]:

            normalized_fields = {}

            for field_name, raw_value in record["values"].items():

                evidence = record["evidence"].get(field_name, {})

                source_reference = SourceReference(
                    source_id=source_metadata["source_id"],
                    filename=source_metadata["original_filename"],
                    sheet_name=record["sheet_name"],
                    cell_coordinates=[
                        evidence["cell"]
                    ] if evidence.get("cell") else [],
                )

                normalized_fields[field_name] = NormalizedField(
                    canonical_name=None,
                    source_header=field_name,
                    raw_value=raw_value,
                    normalized_value=None,
                    data_type=type(raw_value).__name__,
                    source=source_reference,
                )

            normalized_records.append(
                NormalizedRecord(
                    record_id=(
                        f"{source_metadata['source_id']}:"
                        f"{record['sheet_name']}:"
                        f"{record['row_number']}"
                    ),
                    source_id=source_metadata["source_id"],
                    product_line=extracted_sheet["product_line"],
                    table_type=extracted_sheet["table_type"],
                    source_row=record["row_number"],
                    fields=normalized_fields,
                )
            )

        return NormalizedTable(
            source_id=source_metadata["source_id"],
            insurer=source_metadata["publisher"],
            source_version=source_metadata["version"],
            sheet_name=extracted_sheet["sheet_name"],
            product_line=extracted_sheet["product_line"],
            table_type=extracted_sheet["table_type"],
            record_count=len(normalized_records),
            records=normalized_records,
        )
