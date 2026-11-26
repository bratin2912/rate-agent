
from pathlib import Path

from app.ingestion.readers.excel_reader import ExcelWorkbookReader


WORKBOOK_PATH = Path(
    "data/raters/godigit/march-2026/"
    "Large Insurance Brokers Mar'26 - Shared.xlsx"
)


def main():
    with ExcelWorkbookReader(WORKBOOK_PATH) as reader:

        print("WORKBOOK:", reader.file_path.name)

        print("\nWORKSHEETS:")
        for sheet_name in reader.get_sheet_names():
            dimensions = reader.get_sheet_dimensions(sheet_name)

            print(
                f"{sheet_name!r}: "
                f"{dimensions['max_row']} rows, "
                f"{dimensions['max_column']} columns"
            )

        print("\nSAMPLE CELLS:")

        result = reader.read_cell(
            sheet_name="4W SATP",
            row=2,
            column=1,
        )

        print(result)

        print("\nSAMPLE ROWS:")
        rows = reader.read_rows(
            sheet_name="4W SATP",
            start_row=1,
            end_row=5,
        )

        for row in rows:
            print(row)


if __name__ == "__main__":
    main()
