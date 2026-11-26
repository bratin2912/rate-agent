from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.policy import PolicyDocument, PolicyAnalysis


class PolicyRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_document(self, filename: str, storage_path: str):
        document = PolicyDocument(
            original_filename=filename,
            storage_path=storage_path,
            status="uploaded",
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def update_document_status(self, document, status: str):
        document.status = status
        self.db.commit()
        self.db.refresh(document)
        return document

    def create_analysis(
        self,
        document_id,
        extracted_data: dict,
        normalized_data: dict,
    ):
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

    def record_failure(self, document, error_message: str):
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

    def list_documents(self, limit: int = 20, offset: int = 0):
        statement = (
            select(PolicyDocument)
            .order_by(PolicyDocument.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return self.db.scalars(statement).all()

    def get_document(self, document_id):
        return self.db.get(PolicyDocument, document_id)

    def list_analyses(self, document_id):
        statement = (
            select(PolicyAnalysis)
            .where(PolicyAnalysis.document_id == document_id)
            .order_by(PolicyAnalysis.created_at.desc())
        )
        return self.db.scalars(statement).all()

    def get_analysis(self, analysis_id):
        return self.db.get(PolicyAnalysis, analysis_id)
