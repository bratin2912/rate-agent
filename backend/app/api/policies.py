
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.repositories.policy_repository import PolicyRepository
from app.storage.local_storage import LocalStorage
from app.policy_extraction.services.policy_processor import PolicyProcessor

router = APIRouter(prefix="/api/v1/policies", tags=["Policies"])

storage = LocalStorage()
processor = PolicyProcessor()

MAX_FILE_SIZE = 15 * 1024 * 1024


@router.post("/extract")
async def extract_policy(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename or Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(400, "Only PDF files are supported.")

    repository = PolicyRepository(db)
    storage_path = None
    document = None

    try:
        storage_path, file_size = await storage.save(file)

        if file_size == 0:
            raise HTTPException(400, "Uploaded PDF is empty.")

        document = repository.create_document(
            filename=file.filename,
            storage_path=storage_path,
        )

        repository.update_document_status(document, "processing")

        result = processor.process(storage_path)

        extraction_data = result["extraction"].model_dump(mode="json")
        normalized_data = result["normalized_policy"].model_dump(mode="json")

        analysis = repository.create_analysis(
            document_id=document.id,
            extracted_data=extraction_data,
            normalized_data=normalized_data,
        )

        repository.update_document_status(document, "completed")

        return {
            "document_id": document.id,
            "analysis_id": analysis.id,
            "status": "completed",
            "filename": document.original_filename,
            "policy": normalized_data,
            "extraction": extraction_data,
        }

    except HTTPException:
        if storage_path:
            storage.delete(storage_path)
        raise

    except Exception as exc:
        if document:
            repository.record_failure(document, str(exc))
        elif storage_path:
            storage.delete(storage_path)

        raise HTTPException(
            status_code=500,
            detail=f"Policy processing failed: {str(exc)}",
        ) from exc

    finally:
        await file.close()
