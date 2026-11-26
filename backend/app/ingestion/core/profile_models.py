
from dataclasses import dataclass
from typing import Literal


FileType = Literal["xlsx", "pdf"]

TableType = Literal[
    "commission_grid",
    "rto_mapping",
    "vehicle_mapping",
    "reference_data",
]


@dataclass(frozen=True)
class SheetProfile:
    sheet_name: str
    table_type: TableType
    header_rows: tuple[int, ...]
    data_start_row: int
    product_line: str
    description: str


@dataclass(frozen=True)
class SourceProfile:
    source_id: str
    publisher: str
    version: str
    file_type: FileType
    sheets: dict[str, SheetProfile]
