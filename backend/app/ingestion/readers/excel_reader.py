
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from openpyxl.cell.cell import Cell, MergedCell
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet


class ExcelWorkbookReader:
    """
    Generic Excel reader.

    Responsibilities:
    - Open an Excel workbook.
    - Read worksheet data.
    - Handle merged cells.
    - Retrieve cell values and coordinates.
    - Close the workbook safely.

    This class does not contain insurer-specific logic.
    """

    def __init__(
        self,
        file_path: str | Path,
        data_only: bool = False,
    ) -> None:
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(
                f"Excel file not found: {self.file_path.resolve()}"
            )

        self.workbook: Workbook = load_workbook(
            filename=self.file_path,
            data_only=data_only,
            read_only=False,
        )

    def get_sheet_names(self) -> list[str]:
        """Return all worksheet names."""
        return self.workbook.sheetnames

    def get_worksheet(self, sheet_name: str) -> Worksheet:
        """Return a worksheet by its exact name."""
        if sheet_name not in self.workbook.sheetnames:
            raise ValueError(
                f"Worksheet '{sheet_name}' not found. "
                f"Available sheets: {self.get_sheet_names()}"
            )

        return self.workbook[sheet_name]

    def get_sheet_dimensions(self, sheet_name: str) -> dict[str, int]:
        """Return worksheet dimensions."""
        worksheet = self.get_worksheet(sheet_name)

        return {
            "max_row": worksheet.max_row,
            "max_column": worksheet.max_column,
        }

    def get_merged_range(
        self,
        worksheet: Worksheet,
        row: int,
        column: int,
    ) -> str | None:
        """
        Find the merged range containing a cell.

        Returns None if the cell is not part of a merged range.
        """
        coordinate = worksheet.cell(row, column).coordinate

        for merged_range in worksheet.merged_cells.ranges:
            if coordinate in merged_range:
                return str(merged_range)

        return None

    def get_merged_cell_value(
        self,
        worksheet: Worksheet,
        row: int,
        column: int,
    ) -> tuple[Any, str]:
        """
        Return a cell's value and its original source coordinate.

        For merged cells, the value comes from the top-left cell
        of the merged range.

        Returns:
            (value, source_coordinate)
        """
        cell = worksheet.cell(row, column)

        if isinstance(cell, MergedCell):
            merged_range = self.get_merged_range(
                worksheet,
                row,
                column,
            )

            if merged_range is None:
                return None, cell.coordinate

            top_left = merged_range.split(":")[0]
            source_cell = worksheet[top_left]

            return source_cell.value, source_cell.coordinate

        return cell.value, cell.coordinate

    def read_cell(
        self,
        sheet_name: str,
        row: int,
        column: int,
    ) -> dict[str, Any]:
        """Read one cell with its value and source coordinate."""
        worksheet = self.get_worksheet(sheet_name)

        value, source_coordinate = self.get_merged_cell_value(
            worksheet,
            row,
            column,
        )

        return {
            "sheet_name": sheet_name,
            "row": row,
            "column": column,
            "value": value,
            "source_coordinate": source_coordinate,
        }

    def read_rows(
        self,
        sheet_name: str,
        start_row: int,
        end_row: int | None = None,
    ) -> list[list[Any]]:
        """Read worksheet rows as a list of values."""
        worksheet = self.get_worksheet(sheet_name)

        end_row = end_row or worksheet.max_row

        return [
            [
                worksheet.cell(row, column).value
                for column in range(1, worksheet.max_column + 1)
            ]
            for row in range(start_row, end_row + 1)
        ]

    def close(self) -> None:
        """Close the workbook."""
        self.workbook.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
