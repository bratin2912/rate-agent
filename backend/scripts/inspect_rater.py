
import json

from app.ingestion.excel_inspector import ExcelInspector


FILE_PATH = "data/raters/godigit/march-2026/Large Insurance Brokers Mar'26 - Shared.xlsx"


def main():

    inspector = ExcelInspector(FILE_PATH)

    try:
        result = inspector.get_workbook_summary()

        print(
            json.dumps(
                result,
                indent=4,
                default=str
            )
        )

        # Save extracted workbook metadata.
        with open(
            "data/workbook_summary.json",
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                result,
                file,
                indent=4,
                default=str
            )

        print("\nWorkbook inspection completed!")

    finally:
        inspector.close()


if __name__ == "__main__":
    main()
