
from dataclasses import dataclass, field
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
    """Profile describing a structured Excel sheet."""

    sheet_name: str
    table_type: TableType
    header_rows: tuple[int, ...]
    data_start_row: int
    product_line: str
    description: str


@dataclass(frozen=True)
class PDFTableProfile:
    """Profile describing a logical table inside a PDF."""

    table_id: str
    page_numbers: tuple[int, ...]
    table_type: TableType
    product_line: str
    description: str
    extraction_method: Literal["table", "text"] = "table"
    header_keywords: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceProfile:
    """Insurer-specific source document profile."""

    source_id: str
    publisher: str
    version: str
    file_type: FileType

    # Excel configuration
    sheets: dict[str, SheetProfile] = field(default_factory=dict)

    # PDF configuration
    tables: dict[str, PDFTableProfile] = field(default_factory=dict)
