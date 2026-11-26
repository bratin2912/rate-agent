
from sqlalchemy.orm import Session

from app.models.policy import PolicyDocument, PolicyAnalysis


class PolicyRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_document(
        self,
        filename: str,
        storage_path: str,
    ) -> PolicyDocument:
        document = PolicyDocument(
            original_filename=filename,
            storage_path=storage_path,
            status="uploaded",
        )

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        return document

    def update_document_status(
        self,
        document: PolicyDocument,
        status: str,
    ) -> None:
        document.status = status
        self.db.commit()

    def create_analysis(
        self,
        document_id: str,
        extracted_data: dict,
        normalized_data: dict,
    ) -> PolicyAnalysis:
        analysis = PolicyAnalysis(
            document_id=document_id,
            extracted_data=extracted_data,
            normalized_data=normalized_data,
            status="completed",
        )

        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)

        return analysis

    def record_failure(
        self,
        document: PolicyDocument,
        error_message: str,
    ) -> None:
        document.status = "failed"

        analysis = PolicyAnalysis(
            document_id=document.id,
            extracted_data={},
            normalized_data={},
            status="failed",
            error_message=error_message,
        )

        self.db.add(analysis)
        self.db.commit()
