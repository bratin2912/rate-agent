
from sqlalchemy import select
from sqlalchemy.orm import Session
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from app.models.policy import PolicyDocument, PolicyAnalysis


class PolicyRepository:
    def __init__(self, db: Session):
        self.db = db

    # Keep your existing create_document,
    # update_document_status, create_analysis,
    # and record_failure methods.

    @router.get("/")
    def list_policies(
        limit: int = 20,
        offset: int = 0,
        db: Session = Depends(get_db),
    ):
        if not 1 <= limit <= 100 or offset < 0:
            raise HTTPException(400, "Invalid pagination parameters.")
    
        repository = PolicyRepository(db)
        documents = repository.list_documents(limit, offset)
    
        return {
            "items": [
                {
                    "document_id": document.id,
                    "filename": document.original_filename,
                    "status": document.status,
                    "created_at": document.created_at,
                }
                for document in documents
            ],
            "limit": limit,
            "offset": offset,
        }
    
    
    @router.get("/{document_id}")
    def get_policy(
        document_id: str,
        db: Session = Depends(get_db),
    ):
        repository = PolicyRepository(db)
        document = repository.get_document(document_id)
    
        if not document:
            raise HTTPException(404, "Policy document not found.")
    
        analyses = repository.list_analyses(document_id)
    
        return {
            "document_id": document.id,
            "filename": document.original_filename,
            "status": document.status,
            "created_at": document.created_at,
            "analyses": [
                {
                    "analysis_id": analysis.id,
                    "status": analysis.status,
                    "created_at": analysis.created_at,
                }
                for analysis in analyses
            ],
        }
    
    
    @router.get("/{document_id}/document")
    def get_original_document(
        document_id: str,
        db: Session = Depends(get_db),
    ):
        repository = PolicyRepository(db)
        document = repository.get_document(document_id)
    
        if not document:
            raise HTTPException(404, "Policy document not found.")
    
        path = Path(document.storage_path)
    
        if not path.is_file():
            raise HTTPException(404, "Stored PDF not found.")
    
        return FileResponse(
            path=path,
            media_type="application/pdf",
            filename=document.original_filename,
        )
    
    
    @router.get("/{document_id}/analyses/{analysis_id}")
    def get_analysis_details(
        document_id: str,
        analysis_id: str,
        db: Session = Depends(get_db),
    ):
        repository = PolicyRepository(db)
    
        document = repository.get_document(document_id)
        if not document:
            raise HTTPException(404, "Policy document not found.")
    
        analysis = repository.get_analysis(analysis_id)
    
        if not analysis or analysis.document_id != document_id:
            raise HTTPException(404, "Policy analysis not found.")
    
        return {
            "document_id": document.id,
            "analysis_id": analysis.id,
            "status": analysis.status,
            "extracted_data": analysis.extracted_data,
            "normalized_data": analysis.normalized_data,
            "error_message": analysis.error_message,
            "created_at": analysis.created_at,
        }
