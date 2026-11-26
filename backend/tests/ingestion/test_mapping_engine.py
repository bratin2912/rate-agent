from app.ingestion.core.mapping_engine import InsuranceFieldMapper
from app.ingestion.core.normalized_models import (
    NormalizedField,
    NormalizedRecord,
    NormalizedTable,
    SourceReference,
)


def create_test_table():
    source = SourceReference(
        source_id="godigit_mar_2026",
        filename="godigit.xlsx",
        sheet_name="4W SATP",
        cell_coordinates=["B3"],
    )

    record = NormalizedRecord(
        record_id="record_1",
        source_id="godigit_mar_2026",
        product_line="four_wheeler",
        table_type="commission_grid",
        source_row=3,
        fields={
            "Cluster": NormalizedField(
                source_header="Cluster",
                raw_value="All_India_Decline",
                normalized_value=None,
                source=source,
            ),
            "Segment": NormalizedField(
                source_header="Segment",
                raw_value="CNG<1000",
                normalized_value=None,
                source=source,
            ),
            "Max CD2": NormalizedField(
                source_header="Max CD2",
                raw_value=0,
                normalized_value=None,
                source=source,
            ),
        },
    )

    return NormalizedTable(
        source_id="godigit_mar_2026",
        insurer="Go Digit",
        source_version="March 2026",
        sheet_name="4W SATP",
        product_line="four_wheeler",
        table_type="commission_grid",
        record_count=1,
        records=[record],
    )


FIELD_MAPPINGS = {
    "4W SATP": {
        "Cluster": "geographic_cluster",
        "Segment": "vehicle_segment",
    }
}


def test_maps_configured_fields():
    table = create_test_table()
    mapper = InsuranceFieldMapper(FIELD_MAPPINGS)

    mapper.map_table(table)

    fields = table.records[0].fields

    assert fields["Cluster"].canonical_name == "geographic_cluster"
    assert fields["Segment"].canonical_name == "vehicle_segment"


def test_preserves_unmapped_fields():
    table = create_test_table()
    mapper = InsuranceFieldMapper(FIELD_MAPPINGS)

    mapper.map_table(table)

    max_cd2 = table.records[0].fields["Max CD2"]

    assert max_cd2.canonical_name is None
    assert max_cd2.raw_value == 0


def test_mapping_does_not_modify_raw_values_or_evidence():
    table = create_test_table()
    mapper = InsuranceFieldMapper(FIELD_MAPPINGS)

    mapper.map_table(table)

    cluster = table.records[0].fields["Cluster"]

    assert cluster.raw_value == "All_India_Decline"
    assert cluster.source.cell_coordinates == ["B3"]


def test_mapping_report_identifies_mapped_and_unmapped_fields():
    table = create_test_table()
    mapper = InsuranceFieldMapper(FIELD_MAPPINGS)

    mapper.map_table(table)
    report = mapper.get_mapping_report(table)

    assert report["mapped_headers"] == ["Cluster", "Segment"]
    assert report["unmapped_headers"] == ["Max CD2"]
    assert report["mapped_header_count"] == 2
    assert report["unmapped_header_count"] == 1