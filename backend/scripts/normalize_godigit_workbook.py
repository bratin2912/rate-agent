
import json
from pathlib import Path

from app.ingestion.normalizer import InsuranceDataNormalizer

INPUT_PATH = Path("data/extracted/godigit_mar_2026.json")
OUTPUT_PATH = Path("data/normalized/godigit_mar_2026.json")


def normalize_workbook():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Extracted JSON not found: {INPUT_PATH.resolve()}"
        )

    with INPUT_PATH.open("r", encoding="utf-8") as file:
        extracted_data = json.load(file)

    normalizer = InsuranceDataNormalizer()

    normalized_sheets = {}

    for sheet_name, extracted_sheet in extracted_data["sheets"].items():

        print(f"Normalizing: {sheet_name}")

        normalized_table = normalizer.normalize_sheet(
            extracted_sheet=extracted_sheet,
            source_metadata=extracted_data["source"],
        )

        normalized_sheets[sheet_name] = (
            normalized_table.model_dump(mode="json")
        )

        print(
            f"  Normalized records: "
            f"{normalized_table.record_count}"
        )

    output = {
        "source": extracted_data["source"],
        "normalization": {
            "sheet_count": len(normalized_sheets),
            "total_records": sum(
                table["record_count"]
                for table in normalized_sheets.values()
            ),
            "normalization_type": "structural",
        },
        "sheets": normalized_sheets,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    print("\nNormalization completed.")
    print("Sheets:", output["normalization"]["sheet_count"])
    print("Records:", output["normalization"]["total_records"])
    print("Output:", OUTPUT_PATH.resolve())


if __name__ == "__main__":
    normalize_workbook()
