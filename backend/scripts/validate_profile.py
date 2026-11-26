
import argparse
from pathlib import Path

from openpyxl import load_workbook

from app.ingestion.profiles.godigit.source import PROFILE


def validate_profile(file_path: Path) -> None:
    if not file_path.exists():
        raise FileNotFoundError(
            f"Workbook not found: {file_path.resolve()}"
        )

    workbook = load_workbook(
        file_path,
        read_only=True,
        data_only=False,
    )

    try:
        actual_sheets = set(workbook.sheetnames)
        configured_sheets = set(PROFILE.sheets.keys())

        missing_profiles = actual_sheets - configured_sheets
        missing_sheets = configured_sheets - actual_sheets

        print(f"\nSource: {PROFILE.source_id}")
        print(f"Publisher: {PROFILE.publisher}")
        print(f"Version: {PROFILE.version}")
        print(f"Actual sheets: {len(actual_sheets)}")
        print(f"Configured sheets: {len(configured_sheets)}")

        if missing_profiles:
            print("\nSheets without profiles:")
            for name in sorted(missing_profiles):
                print(f"  - {name!r}")

        if missing_sheets:
            print("\nConfigured sheets not found:")
            for name in sorted(missing_sheets):
                print(f"  - {name!r}")

        for name, profile in PROFILE.sheets.items():
            if name not in actual_sheets:
                continue

            worksheet = workbook[name]

            if profile.data_start_row > worksheet.max_row:
                print(f"WARNING: Invalid data start row: {name}")
                continue

            if any(row < 1 or row > worksheet.max_row
                   for row in profile.header_rows):
                print(f"WARNING: Invalid header row: {name}")
                continue

            print(
                f"\n{name!r}"
                f"\n  Type: {profile.table_type}"
                f"\n  Headers: {profile.header_rows}"
                f"\n  Data starts: {profile.data_start_row}"
            )

        if not missing_profiles and not missing_sheets:
            print("\nAll workbook sheets have matching profiles.")

    finally:
        workbook.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "workbook",
        type=Path,
        help="Path to the Go Digit workbook",
    )
    args = parser.parse_args()

    validate_profile(args.workbook)
