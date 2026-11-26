
import json
from pathlib import Path

from app.ingestion.core.mapping_engine import InsuranceFieldMapper
from app.ingestion.core.normalized_models import NormalizedTable
from app.ingestion.profiles.godigit.field_mappings import (
    GODIGIT_FIELD_MAPPINGS,
)


INPUT_PATH = Path("data/normalized/godigit_mar_2026.json")
OUTPUT_PATH = Path("data/mapped/godigit_mar_2026.json")


def map_godigit_workbook():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Normalized input file not found: {INPUT_PATH}"
        )

    with INPUT_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    mapper = InsuranceFieldMapper(GODIGIT_FIELD_MAPPINGS)

    mapped_sheets = {}
    mapping_reports = []

    for sheet_name, sheet_data in data["sheets"].items():
        table = NormalizedTable.model_validate(sheet_data)

        mapped_table = mapper.map_table(table)
        report = mapper.get_mapping_report(mapped_table)

        mapped_sheets[sheet_name] = mapped_table.model_dump(mode="json")
        mapping_reports.append(report)

        print(f"\nSHEET: {sheet_name}")
        print(f"Mapped headers: {report['mapped_header_count']}")
        print(f"Unmapped headers: {report['unmapped_header_count']}")

    output = {
        "source": data["source"],
        "normalization": data["normalization"],
        "mapping": {
            "mapping_type": "semantic",
            "configured_sheets": len(GODIGIT_FIELD_MAPPINGS),
            "processed_sheets": len(mapped_sheets),
            "reports": mapping_reports,
        },
        "sheets": mapped_sheets,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)

    print("\n========== MAPPING COMPLETE ==========")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    map_godigit_workbook()
