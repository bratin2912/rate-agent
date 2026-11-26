
from app.ingestion.core.normalized_models import NormalizedTable


class InsuranceFieldMapper:
    """
    Maps insurer-specific source headers to canonical field names.

    The engine is generic. Insurer-specific mappings are injected
    through the constructor.
    """

    def __init__(self, field_mappings: dict[str, dict[str, str]]):
        self.field_mappings = field_mappings

    def map_table(self, table: NormalizedTable) -> NormalizedTable:
        """
        Apply the mapping configuration for this table's worksheet.

        Unmapped fields are preserved with canonical_name=None.
        """
        sheet_mappings = self.field_mappings.get(table.sheet_name, {})

        for record in table.records:
            for field in record.fields.values():
                canonical_name = sheet_mappings.get(field.source_header)

                if canonical_name:
                    field.canonical_name = canonical_name

        return table

    def get_mapping_report(self, table: NormalizedTable) -> dict:
        """
        Report which source headers were mapped and which remain unmapped.
        """
        sheet_mappings = self.field_mappings.get(table.sheet_name, {})

        mapped_fields = set()
        unmapped_fields = set()

        for record in table.records:
            for field in record.fields.values():
                if field.canonical_name:
                    mapped_fields.add(field.source_header)
                else:
                    unmapped_fields.add(field.source_header)

        return {
            "sheet_name": table.sheet_name,
            "configured_mapping_count": len(sheet_mappings),
            "mapped_headers": sorted(mapped_fields),
            "unmapped_headers": sorted(unmapped_fields),
            "mapped_header_count": len(mapped_fields),
            "unmapped_header_count": len(unmapped_fields),
        }
