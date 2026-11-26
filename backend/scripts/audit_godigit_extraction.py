
import json
from pathlib import Path


INPUT_PATH = Path("data/extracted/godigit_mar_2026.json")


def audit_extraction():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Extracted JSON not found: {INPUT_PATH.resolve()}"
        )

    with INPUT_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    sheets = data["sheets"]

    print("=" * 65)
    print("GODIGIT EXTRACTION QUALITY REPORT")
    print("=" * 65)

    print("\nSOURCE INFORMATION")
    print("Publisher:", data["source"]["publisher"])
    print("Version:", data["source"]["version"])
    print("Filename:", data["source"]["original_filename"])

    print("\nEXTRACTION SUMMARY")
    print("Expected sheets:", 14)
    print("Extracted sheets:", len(sheets))
    print("Total records:", data["extraction"]["total_records"])

    print("\nSHEET-WISE AUDIT")

    empty_sheets = []
    empty_records = []
    missing_evidence = []

    for sheet_name, sheet in sheets.items():

        records = sheet.get("records", [])
        headers = sheet.get("headers", {})

        print("\n" + "-" * 50)
        print("Sheet:", sheet_name)
        print("Type:", sheet["table_type"])
        print("Product:", sheet["product_line"])
        print("Records:", len(records))
        print("Headers:", len(headers))

        if not records:
            empty_sheets.append(sheet_name)

        for index, record in enumerate(records):
            values = record.get("values", {})
            evidence = record.get("evidence", {})

            if not values:
                empty_records.append(
                    (sheet_name, record.get("row_number"))
                )

            for field in values:
                if field not in evidence:
                    missing_evidence.append(
                        (sheet_name, record.get("row_number"), field)
                    )

        print("Sample headers:")
        for header in headers.values():
            print("  -", header["name"])

        if records:
            print("First record:")
            print(
                json.dumps(
                    records[0]["values"],
                    indent=2,
                    default=str,
                )
            )

    print("\n" + "=" * 65)
    print("AUDIT RESULTS")
    print("=" * 65)

    print("Empty sheets:", empty_sheets)
    print("Empty records:", len(empty_records))
    print("Missing evidence entries:", len(missing_evidence))

    if (
        len(sheets) == 14
        and not empty_sheets
        and not empty_records
        and not missing_evidence
    ):
        print("\nBasic structural checks passed.")
    else:
        print("\nReview the warnings before normalization.")


if __name__ == "__main__":
    audit_extraction()
