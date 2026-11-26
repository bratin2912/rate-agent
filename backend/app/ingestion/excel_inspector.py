
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


class ExcelInspector:
    """
    Inspects an Excel workbook and extracts its structure.

    It does not calculate commission rates or modify
    the original workbook.
    """

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(
                f"Excel file not found: {self.file_path}"
            )

        # Load formulas and original cell values.
        self.workbook = load_workbook(
            self.file_path,
            data_only=False
        )

    def get_workbook_summary(self) -> dict[str, Any]:
        """
        Returns metadata about all worksheets.
        """

        sheets = []

        for worksheet in self.workbook.worksheets:

            non_empty_cells = 0
            formula_count = 0

            for row in worksheet.iter_rows():

                for cell in row:

                    if cell.value is not None:
                        non_empty_cells += 1

                    if (
                        isinstance(cell.value, str)
                        and cell.value.startswith("=")
                    ):
                        formula_count += 1

            sheets.append({
                "sheet_name": worksheet.title,
                "total_rows": worksheet.max_row,
                "total_columns": worksheet.max_column,
                "non_empty_cells": non_empty_cells,
                "formula_count": formula_count,
                "merged_cells": [
                    str(r)
                    for r in worksheet.merged_cells.ranges
                ],
                "headers": self.get_sample_rows(
                    worksheet.title,
                    start_row=1,
                    end_row=min(5, worksheet.max_row)
                )
            })

        return {
            "file_name": self.file_path.name,
            "total_sheets": len(sheets),
            "sheets": sheets
        }

    def get_sample_rows(
        self,
        sheet_name: str,
        start_row: int = 1,
        end_row: int = 10
    ) -> list[dict[str, Any]]:
        """
        Extracts sample rows while preserving
        original Excel cell coordinates.
        """

        worksheet = self.workbook[sheet_name]

        extracted_rows = []

        for row in worksheet.iter_rows(
            min_row=start_row,
            max_row=min(end_row, worksheet.max_row)
        ):

            row_data = {}

            for cell in row:

                if cell.value is not None:

                    row_data[cell.coordinate] = cell.value

            if row_data:
                extracted_rows.append({
                    "row_number": row[0].row,
                    "cells": row_data
                })

        return extracted_rows

    def close(self):
        self.workbook.close()
