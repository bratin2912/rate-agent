
from typing import Any

from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    source_id: str
    filename: str

    # Excel source information
    sheet_name: str | None = None
    cell_coordinates: list[str] = Field(default_factory=list)

    # PDF source information
    page_number: int | None = None
    table_id: str | None = None
    row_number: int | None = None


class NormalizedField(BaseModel):
    canonical_name: str | None = None
    source_header: str
    raw_value: Any
    normalized_value: Any = None
    data_type: str | None = None
    source: SourceReference


class NormalizedRecord(BaseModel):
    record_id: str
    source_id: str
    product_line: str
    table_type: str
    source_row: int
    fields: dict[str, NormalizedField]


class NormalizedTable(BaseModel):
    source_id: str
    insurer: str
    source_version: str

    # Excel uses sheet_name; PDF uses table_id.
    sheet_name: str | None = None
    table_id: str | None = None

    product_line: str
    table_type: str
    record_count: int
    records: list[NormalizedRecord]
