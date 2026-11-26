
import json
from pathlib import Path
from typing import Any

from app.ingestion.core.normalized_models import NormalizedTable


class GridRepository:
    def __init__(self, data_directory: str = "data/mapped"):
        self.data_directory = Path(data_directory)
        self._cache: dict[str, dict[str, Any]] = {}

    def load(self, source_id: str) -> dict[str, Any]:
        if source_id not in self._cache:
            file_path = self.data_directory / f"{source_id}.json"

            if not file_path.is_file():
                raise FileNotFoundError(
                    f"Mapped grid not found: {file_path}"
                )

            with file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            actual_source_id = data.get("source", {}).get("source_id")

            if actual_source_id != source_id:
                raise ValueError(
                    f"Expected source {source_id}, got {actual_source_id}"
                )

            self._cache[source_id] = data

        return self._cache[source_id]

    def get_tables(
        self,
        source_id: str,
        product_line: str | None = None,
        table_type: str | None = None,
    ) -> list[NormalizedTable]:
        data = self.load(source_id)
        tables = []

        for table_data in data.get("sheets", {}).values():
            table = NormalizedTable.model_validate(table_data)

            if product_line and table.product_line != product_line:
                continue

            if table_type and table.table_type != table_type:
                continue

            tables.append(table)

        return tables

    def get_sheet(
        self,
        source_id: str,
        sheet_name: str,
    ) -> NormalizedTable | None:
        data = self.load(source_id)
        table_data = data.get("sheets", {}).get(sheet_name)

        if table_data is None:
            return None

        return NormalizedTable.model_validate(table_data)

    def get_records(
        self,
        source_id: str,
        product_line: str | None = None,
        table_type: str | None = None,
    ) -> list:
        return [
            record
            for table in self.get_tables(
                source_id,
                product_line,
                table_type,
            )
            for record in table.records
        ]

    def clear_cache(self, source_id: str | None = None) -> None:
        if source_id:
            self._cache.pop(source_id, None)
        else:
            self._cache.clear()
