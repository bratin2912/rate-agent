
from app.rating.services.grid_repository import GridRepository


class RTOResolver:
    """Resolve a vehicle RTO code to its insurer-specific cluster."""

    def __init__(self, repository: GridRepository):
        self.repository = repository

    def resolve(
        self,
        source_id: str,
        sheet_name: str,
        rto_code: str,
        cluster_column: str,
    ) -> dict | None:
        table = self.repository.get_sheet(
            source_id=source_id,
            sheet_name=sheet_name,
        )

        if table is None:
            raise ValueError(
                f"RTO mapping sheet not found: {sheet_name}"
            )

        normalized_rto = self._normalize(rto_code)

        for record in table.records:
            fields = record.fields

            rto_field = self._find_field(fields, "rto_code")
            cluster_field = self._find_field(fields, cluster_column)

            if rto_field is None or cluster_field is None:
                continue

            source_rto = self._normalize(str(rto_field.raw_value))

            if source_rto != normalized_rto:
                continue

            cluster = cluster_field.raw_value

            if cluster is None or not str(cluster).strip():
                return None

            return {
                "rto_code": rto_code,
                "cluster": str(cluster).strip(),
                "evidence": [
                    {
                        "sheet_name": table.sheet_name,
                        "source_row": record.source_row,
                        "cell_coordinates": (
                            cluster_field.source.cell_coordinates
                        ),
                    }
                ],
            }

        return None

    @staticmethod
    def _normalize(value: str) -> str:
        return value.strip().upper().replace(" ", "")

    @staticmethod
    def _find_field(fields: dict, canonical_name: str):
        for field in fields.values():
            if field.canonical_name == canonical_name:
                return field

        return None
