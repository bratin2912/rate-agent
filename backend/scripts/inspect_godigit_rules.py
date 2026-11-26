
from pathlib import Path

from openpyxl import load_workbook


WORKBOOK_PATH = Path(
    "data/raters/godigit/march-2026/"
    "Large Insurance Brokers Mar'26 - Shared.xlsx"
)

SHEETS_TO_INSPECT = [
    "CV Grid (excl. HCV)",
    "HCV GRID",
    "4W SATP",
    "TW 1+1 & SATP",
    "TW 1+5",
    "2W Grid 5+5",
]

SPECIAL_MARKERS = {"D", "MISP"}

RULE_KEYWORDS = [
    "decline",
    "declined",
    "refer",
    "additional",
    "formula",
    "break-in",
    "break in",
    "note:",
]

MAX_SPECIAL_RESULTS_PER_SHEET = 150


def inspect_sheet_structure(ws):
    print("\n" + "=" * 90)
    print(f"SHEET: {ws.title}")
    print(f"DIMENSIONS: {ws.max_row} rows x {ws.max_column} columns")

    print("\nFIRST 15 ROWS:")

    for row in ws.iter_rows(
        min_row=1,
        max_row=min(15, ws.max_row),
        values_only=False,
    ):
        values = [
            f"{cell.coordinate}={cell.value!r}"
            for cell in row
            if cell.value is not None
        ]

        if values:
            print(" | ".join(values))



def inspect_special_values(ws):
    print(f"\nSPECIAL VALUES IN: {ws.title}")

    markers = {"D", "MISP"}

    marker_results = []
    note_results = []

    keywords = [
        "decline",
        "declined",
        "refer",
        "additional",
        "formula",
        "break-in",
        "break in",
        "commission",
        "brokerage",
        "cd1",
        "cd2",
    ]

    for row in ws.iter_rows():
        for cell in row:
            value = cell.value

            if not isinstance(value, str):
                continue

            cleaned = value.strip()
            lowered = cleaned.lower()

            if cleaned in markers:
                marker_results.append(
                    f"{cell.coordinate}: {cleaned}"
                )

            if any(keyword in lowered for keyword in keywords):
                note_results.append(
                    f"{cell.coordinate}: {cleaned}"
                )

    print("\n--- D / MISP MARKERS ---")
    print(f"Total: {len(marker_results)}")

    for result in marker_results[:50]:
        print(result)

    print("\n--- RULE NOTES / DEFINITIONS ---")
    print(f"Total: {len(note_results)}")

    for result in note_results[:50]:
        print(result)



def main():
    if not WORKBOOK_PATH.exists():
        raise FileNotFoundError(
            f"Workbook not found: {WORKBOOK_PATH.resolve()}"
        )

    workbook = load_workbook(
        WORKBOOK_PATH,
        data_only=False,
        read_only=False,
    )

    try:
        print("WORKBOOK:", WORKBOOK_PATH.name)
        print("ALL SHEETS:", workbook.sheetnames)

        print("\nDEFINED NAMES:")
        for name in workbook.defined_names.values():
            print(name)

        for sheet_name in SHEETS_TO_INSPECT:
            if sheet_name not in workbook.sheetnames:
                print(f"\nWARNING: Sheet not found: {sheet_name}")
                continue

            ws = workbook[sheet_name]

            inspect_sheet_structure(ws)
            inspect_special_values(ws)

    finally:
        workbook.close()


if __name__ == "__main__":
    main()
