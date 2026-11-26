
import json
from pathlib import Path

from app.ingestion.readers.excel_reader import ExcelWorkbookReader
from app.ingestion.extractors.table_extractor import ExcelTableExtractor
from app.ingestion.profiles.godigit.sheet_profiles import SHEET_PROFILES


WORKBOOK_PATH = Path(
    "data/raters/godigit/march-2026/"
    "Large Insurance Brokers Mar'26 - Shared.xlsx"
)


def main():
    with ExcelWorkbookReader(WORKBOOK_PATH) as reader:

        profile = SHEET_PROFILES["4W SATP"]

        extractor = ExcelTableExtractor(
            reader=reader,
            profile=profile,
        )

        result = extractor.extract()

        print("PRODUCT:", result["product_line"])
        print("SHEET:", result["sheet_name"])
        print("RECORD COUNT:", result["record_count"])

        print("\nHEADERS:")
        for column, header in result["headers"].items():
            print(column, header)

        print("\nFIRST FIVE RECORDS:")

        for record in result["records"][:5]:
            print(json.dumps(record, indent=2, default=str))


if __name__ == "__main__":
    main()
