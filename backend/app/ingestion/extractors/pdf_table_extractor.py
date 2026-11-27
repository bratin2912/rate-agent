
from typing import Any

from app.ingestion.core.profile_models import PDFTableProfile
from app.ingestion.readers.pdf_reader import PDFReader


class PDFTableExtractor:
    """
    Extract HDFC ERGO logical tables from PDF documents.

    Supports:
    - Commission grids
    - Geographical / RTO mappings

    Returns a common extraction structure compatible with
    the existing InsuranceDataNormalizer.
    """

    def __init__(
        self,
        reader: PDFReader,
        profile: PDFTableProfile,
    ) -> None:
        self.reader = reader
        self.profile = profile

    @staticmethod
    def _clean(value: Any) -> str:
        if value is None:
            return ""

        return " ".join(str(value).split()).strip()

    def _get_tables(self, file_path: str) -> list[dict]:
        """Extract tables and restrict them to configured pages."""
        return [
            table
            for table in self.reader.extract_tables(file_path)
            if table["page_number"] in self.profile.page_numbers
        ]

    # ---------------------------------------------------------
    # TABLE IDENTIFICATION
    # ---------------------------------------------------------

    def _is_commission_table(self, table: dict) -> bool:
        """Identify a commission grid using its multi-row headers."""
        rows = table["rows"]

        if len(rows) < 9:
            return False

        header_text = " ".join(
            self._clean(cell).upper()
            for row in rows[:4]
            for cell in row
        )

        zone_found = any(
            self._clean(cell).upper() in ("ZONE 1", "ZONE 2")
            for row in rows[:2]
            for cell in row
        )

        return (
            zone_found
            and "CATEGORY" in header_text
            and "PACKAGE" in header_text
            and "SAOD" in header_text
        )

    def _is_mapping_table(self, table: dict) -> bool:
        """Identify geographical tables using exact header labels."""
        for row in table["rows"]:
            cells = {
                self._clean(cell).upper()
                for cell in row
            }

            if {
                "ZONE",
                "STATE NAME",
                "ZONE-1",
                "ZONE-2",
            }.issubset(cells):
                return True

        return False

    # ---------------------------------------------------------
    # EVIDENCE
    # ---------------------------------------------------------

    @staticmethod
    def _evidence(
        table: dict,
        row_number: int,
        column_number: int | None,
        value: Any,
    ) -> dict:
        return {
            "page_number": table["page_number"],
            "table_number": table["table_number"],
            "row_number": row_number,
            "column_number": column_number,
            "value": value,
        }

    # ---------------------------------------------------------
    # COMMISSION GRID
    # ---------------------------------------------------------

    def _extract_commission_records(
        self,
        table: dict,
    ) -> list[dict]:
        """
        Extract six commission combinations for each GWP slab.

        PDF structure:
            Row 1: Zone heading
            Row 2: Package / SAOD
            Row 3: Petrol / Non-Petrol
            Row 4: NCB categories
            Rows 5-9: GWP slabs and commission rates
        """
        rows = table["rows"]

        zone = ""

        for row in rows[:2]:
            for cell in row:
                value = self._clean(cell).upper()

                if value in ("ZONE 1", "ZONE 2"):
                    zone = value.title()
                    break

            if zone:
                break

        if not zone:
            return []

        combinations = [
            {
                "product_type": "Package",
                "fuel_category": "Petrol",
                "ncb_category": "NCB & N-NCB",
                "rate_column": 1,
            },
            {
                "product_type": "Package",
                "fuel_category": "Non-Petrol",
                "ncb_category": "NCB",
                "rate_column": 2,
            },
            {
                "product_type": "Package",
                "fuel_category": "Non-Petrol",
                "ncb_category": "N-NCB",
                "rate_column": 3,
            },
            {
                "product_type": "SAOD",
                "fuel_category": "Petrol",
                "ncb_category": "NCB & N-NCB",
                "rate_column": 4,
            },
            {
                "product_type": "SAOD",
                "fuel_category": "Non-Petrol",
                "ncb_category": "NCB",
                "rate_column": 5,
            },
            {
                "product_type": "SAOD",
                "fuel_category": "Non-Petrol",
                "ncb_category": "N-NCB",
                "rate_column": 6,
            },
        ]

        records = []

        # Skip the four header rows.
        for row_index in range(4, len(rows)):
            row = rows[row_index]

            slab = self._clean(
                row[0] if row else None
            )

            if not slab:
                continue

            # Only accept known GWP slab labels.
            if slab.lower() not in {
                "<10k",
                ">10-50k",
                ">50k-1l",
                ">1l-2l",
                ">2l",
            }:
                continue

            for combination in combinations:
                rate_column = combination["rate_column"]

                rate = self._clean(
                    row[rate_column]
                    if rate_column < len(row)
                    else None
                )

                if not rate:
                    continue

                values = {
                    "zone": zone,
                    "product_type": combination["product_type"],
                    "fuel_category": combination["fuel_category"],
                    "ncb_category": combination["ncb_category"],
                    "gwp_slab": slab,
                    "commission_rate": rate,
                }

                evidence = {
                    "zone": self._evidence(
                        table, 1, None, zone
                    ),
                    "product_type": self._evidence(
                        table,
                        2,
                        rate_column + 1,
                        combination["product_type"],
                    ),
                    "fuel_category": self._evidence(
                        table,
                        3,
                        rate_column + 1,
                        combination["fuel_category"],
                    ),
                    "ncb_category": self._evidence(
                        table,
                        4,
                        rate_column + 1,
                        combination["ncb_category"],
                    ),
                    "gwp_slab": self._evidence(
                        table,
                        row_index + 1,
                        1,
                        slab,
                    ),
                    "commission_rate": self._evidence(
                        table,
                        row_index + 1,
                        rate_column + 1,
                        rate,
                    ),
                }

                records.append({
                    "record_id": (
                        f"{zone}:{slab}:"
                        f"{combination['product_type']}:"
                        f"{combination['fuel_category']}:"
                        f"{combination['ncb_category']}"
                    ),
                    "row_number": row_index + 1,
                    "values": values,
                    "evidence": evidence,
                })

        return records

    # ---------------------------------------------------------
    # GEOGRAPHICAL MAPPING
    # ---------------------------------------------------------

    def _extract_mapping_records(
        self,
        tables: list[dict],
    ) -> list[dict]:
        """
        Extract state/location/zone mappings.

        Handles:
        - Vertically merged state names.
        - Multiple locations for one state.
        - Both zones for one state.
        - Mapping continuation across PDF pages.
        """
        records = []

        current_state = ""
        current_region = ""

        for table in tables:
            rows = table["rows"]

            header_index = None

            for index, row in enumerate(rows):
                cells = {
                    self._clean(cell).upper()
                    for cell in row
                }

                if {
                    "ZONE",
                    "STATE NAME",
                    "ZONE-1",
                    "ZONE-2",
                }.issubset(cells):
                    header_index = index
                    break

            if header_index is None:
                continue

            for row_index in range(header_index + 1, len(rows)):
                row = rows[row_index]

                region = self._clean(
                    row[0] if len(row) > 0 else None
                )

                state = self._clean(
                    row[1] if len(row) > 1 else None
                )

                zone_1_location = self._clean(
                    row[3] if len(row) > 3 else None
                )

                zone_2_location = self._clean(
                    row[6] if len(row) > 6 else None
                )

                if region:
                    current_region = region

                if state:
                    current_state = state

                if not current_state:
                    continue

                locations = [
                    ("Zone 1", zone_1_location, 3),
                    ("Zone 2", zone_2_location, 6),
                ]

                for zone, location, column_index in locations:
                    if not location:
                        continue

                    values = {
                        "region": current_region,
                        "state_name": current_state,
                        "location_name": location,
                        "zone": zone,
                    }

                    evidence = {
                        "region": self._evidence(
                            table,
                            row_index + 1,
                            1,
                            current_region,
                        ),
                        "state_name": self._evidence(
                            table,
                            row_index + 1,
                            2,
                            current_state,
                        ),
                        "location_name": self._evidence(
                            table,
                            row_index + 1,
                            column_index + 1,
                            location,
                        ),
                        "zone": self._evidence(
                            table,
                            header_index + 1,
                            column_index + 1,
                            zone,
                        ),
                    }

                    records.append({
                        "record_id": (
                            f"{table['page_number']}:"
                            f"{row_index + 1}:"
                            f"{current_state}:"
                            f"{zone}:{location}"
                        ),
                        "row_number": row_index + 1,
                        "values": values,
                        "evidence": evidence,
                    })

        return records

    # ---------------------------------------------------------
    # PUBLIC EXTRACTION METHOD
    # ---------------------------------------------------------

    def extract(self, file_path: str) -> dict:
        """Extract the configured logical table."""
        tables = self._get_tables(file_path)

        if self.profile.table_type == "commission_grid":
            matched_tables = [
                table
                for table in tables
                if self._is_commission_table(table)
            ]

            records = []

            for table in matched_tables:
                records.extend(
                    self._extract_commission_records(table)
                )

        elif self.profile.table_type == "rto_mapping":
            matched_tables = [
                table
                for table in tables
                if self._is_mapping_table(table)
            ]

            records = self._extract_mapping_records(
                matched_tables
            )

        else:
            raise NotImplementedError(
                f"Unsupported PDF table type: "
                f"{self.profile.table_type}"
            )

        return {
            "table_id": self.profile.table_id,
            "product_line": self.profile.product_line,
            "table_type": self.profile.table_type,
            "page_numbers": list(self.profile.page_numbers),
            "matched_tables": [
                {
                    "page_number": table["page_number"],
                    "table_number": table["table_number"],
                }
                for table in matched_tables
            ],
            "record_count": len(records),
            "records": records,
        }
