
import json
from pathlib import Path

from app.ingestion.readers.excel_reader import ExcelWorkbookReader
from app.ingestion.extractors.table_extractor import ExcelTableExtractor
from app.ingestion.profiles.godigit.source import PROFILE


WORKBOOK_PATH = Path(
    "data/raters/godigit/march-2026/"
    "Large Insurance Brokers Mar'26 - Shared.xlsx"
)

OUTPUT_PATH = Path(
    "data/extracted/godigit_mar_2026.json"
)


def extract_workbook():
    if not WORKBOOK_PATH.exists():
        raise FileNotFoundError(
            f"Workbook not found: {WORKBOOK_PATH.resolve()}"
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    extracted_sheets = {}

    with ExcelWorkbookReader(WORKBOOK_PATH) as reader:

        actual_sheets = set(reader.get_sheet_names())
        configured_sheets = set(PROFILE.sheets.keys())

        missing_profiles = actual_sheets - configured_sheets
        missing_sheets = configured_sheets - actual_sheets

        if missing_profiles or missing_sheets:
            raise ValueError(
                f"Profile mismatch. "
                f"Unconfigured sheets: {missing_profiles}. "
                f"Missing workbook sheets: {missing_sheets}."
            )

        for sheet_name, sheet_profile in PROFILE.sheets.items():

            print(f"Extracting: {sheet_name}")

            extractor = ExcelTableExtractor(
                reader=reader,
                profile=sheet_profile,
            )

            extracted_sheets[sheet_name] = extractor.extract()

            print(
                f"  Extracted records: "
                f"{extracted_sheets[sheet_name]['record_count']}"
            )

    output = {
        "source": {
            "source_id": PROFILE.source_id,
            "publisher": PROFILE.publisher,
            "version": PROFILE.version,
            "file_type": PROFILE.file_type,
            "original_filename": WORKBOOK_PATH.name,
        },
        "extraction": {
            "sheet_count": len(extracted_sheets),
            "total_records": sum(
                sheet["record_count"]
                for sheet in extracted_sheets.values()
            ),
        },
        "sheets": extracted_sheets,
    }

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    print("\nExtraction completed.")
    print(f"Sheets: {output['extraction']['sheet_count']}")
    print(f"Total records: {output['extraction']['total_records']}")
    print(f"Output: {OUTPUT_PATH.resolve()}")


if __name__ == "__main__":
    extract_workbook()
