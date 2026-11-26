
import json
from pathlib import Path
from collections import defaultdict

INPUT_PATH = Path("data/normalized/godigit_mar_2026.json")


def inspect_workbook():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Normalized file not found: {INPUT_PATH}")

    with INPUT_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    print("\n========== SOURCE INFORMATION ==========")
    print(json.dumps(data.get("source", {}), indent=2))

    sheets = data.get("sheets", {})

    print("\n========== SHEET INSPECTION ==========")

    for sheet_name, table in sheets.items():
        records = table.get("records", [])

        print("\n" + "=" * 70)
        print(f"SHEET: {sheet_name}")
        print(f"PRODUCT LINE: {table.get('product_line')}")
        print(f"TABLE TYPE: {table.get('table_type')}")
        print(f"RECORD COUNT: {len(records)}")

        # Collect all source headers and representative values.
        header_values = defaultdict(list)

        for record in records:
            fields = record.get("fields", {})

            for field_key, field in fields.items():
                value = field.get("raw_value")

                if value is not None and len(header_values[field_key]) < 5:
                    header_values[field_key].append(value)

        print("\nFIELDS AND SAMPLE VALUES:")

        for header, values in header_values.items():
            print(f"\n  Field: {header}")
            print(f"  Sample values: {values}")

        # Display one complete record with its source evidence.
        if records:
            print("\nFIRST RECORD:")
            print(json.dumps(records[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    inspect_workbook()
