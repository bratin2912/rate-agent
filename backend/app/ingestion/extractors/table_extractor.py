
from typing import Any

from openpyxl.utils import get_column_letter

from app.ingestion.core.profile_models import SheetProfile
from app.ingestion.readers.excel_reader import ExcelWorkbookReader


class ExcelTableExtractor:
    """
    Extract structured tables from Excel worksheets
    using a configured SheetProfile.

    Preserves original Excel coordinates for evidence.
    """

    def __init__(
        self,
        reader: ExcelWorkbookReader,
        profile: SheetProfile,
    ) -> None:
        self.reader = reader
        self.profile = profile
        self.worksheet = reader.get_worksheet(profile.sheet_name)

    def _build_headers(self) -> dict[int, dict[str, Any]]:
        """
        Build column headers from one or more header rows.

        Example:
            Header row 1: Package | Package
            Header row 2: Petrol  | Diesel

        Result:
            Package | Petrol
            Package | Diesel

        Empty leading columns are ignored.
        """

        headers = {}

        for column in range(1, self.worksheet.max_column + 1):
            parts = []
            sources = []

            for row in self.profile.header_rows:
                value, source_coordinate = (
                    self.reader.get_merged_cell_value(
                        self.worksheet,
                        row,
                        column,
                    )
                )

                if value is None or str(value).strip() == "":
                    continue

                text_value = str(value).strip()

                # Avoid repeating the same merged header.
                if not parts or parts[-1] != text_value:
                    parts.append(text_value)

                if source_coordinate not in sources:
                    sources.append(source_coordinate)

            if not parts:
                continue

            headers[column] = {
                "name": " | ".join(parts),
                "source_coordinates": sources,
            }

        return headers

    def _build_unique_headers(
        self,
        headers: dict[int, dict[str, Any]],
    ) -> dict[int, dict[str, Any]]:
        """
        Ensure duplicate column names remain distinguishable.
        """

        counts = {}

        for column, header in headers.items():
            original_name = header["name"]

            counts[original_name] = counts.get(original_name, 0) + 1

            if counts[original_name] > 1:
                header["name"] = (
                    f"{original_name}_{counts[original_name]}"
                )

        return headers

    def extract_records(self) -> list[dict[str, Any]]:
        """
        Extract non-empty data rows.

        Each record contains:
        - Extracted values
        - Original cell coordinates
        - Worksheet name
        """

        headers = self._build_headers()
        headers = self._build_unique_headers(headers)

        records = []

        for row in range(
            self.profile.data_start_row,
            self.worksheet.max_row + 1,
        ):
            values = {}
            evidence = {}

            for column, header in headers.items():
                value, source_coordinate = (
                    self.reader.get_merged_cell_value(
                        self.worksheet,
                        row,
                        column,
                    )
                )

                # Ignore completely empty cells.
                if value is None:
                    continue

                name = header["name"]

                values[name] = value

                evidence[name] = {
                    "cell": source_coordinate,
                    "row": row,
                    "column": get_column_letter(column),
                    "value": value,
                }

            # Ignore completely empty rows.
            if not values:
                continue

            records.append({
                "sheet_name": self.profile.sheet_name,
                "row_number": row,
                "values": values,
                "evidence": evidence,
            })

        return records

    def extract(self) -> dict[str, Any]:
        """Extract the complete configured table."""

        headers = self._build_unique_headers(
            self._build_headers()
        )

        records = self.extract_records()

        return {
            "product_line": self.profile.product_line,
            "table_type": self.profile.table_type,
            "sheet_name": self.profile.sheet_name,
            "header_rows": list(self.profile.header_rows),
            "data_start_row": self.profile.data_start_row,
            "headers": headers,
            "record_count": len(records),
            "records": records,
        }
