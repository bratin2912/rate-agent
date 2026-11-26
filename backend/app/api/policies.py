
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.database.dependencies import get_db
from app.repositories.policy_repository import PolicyRepository
from app.storage.local_storage import LocalStorage
from app.policy_extraction.services.policy_processor import PolicyProcessor
from app.rating.services.rating_service import RatingService


router = APIRouter(prefix="/api/v1/policies", tags=["Policies"])

logger = get_logger(__name__)

rating_service = RatingService()
storage = LocalStorage()
processor = PolicyProcessor()

MAX_FILE_SIZE = 15 * 1024 * 1024


def cleanup_uploaded_file(storage_path: str | None, request_id: str) -> None:
    """Delete a temporary uploaded file without hiding the original error."""
    if not storage_path:
        return

    try:
        storage.delete(storage_path)
        logger.info(
            "Uploaded file cleanup completed | request_id=%s",
            request_id,
        )
    except Exception:
        logger.exception(
            "Uploaded file cleanup failed | request_id=%s",
            request_id,
        )


@router.post("/extract")
async def extract_policy(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    request_id = str(uuid4())
    filename = file.filename or "unknown"

    logger.info(
        "Policy upload request received | request_id=%s | filename=%s",
        request_id,
        Path(filename).name,
    )

    repository = PolicyRepository(db)
    storage_path = None
    document = None

    try:
        # 1. Validate file
        if not file.filename or Path(file.filename).suffix.lower() != ".pdf":
            logger.warning(
                "Invalid file type | request_id=%s | filename=%s",
                request_id,
                Path(filename).name,
            )
            raise HTTPException(400, "Only PDF files are supported.")

        # 2. Save uploaded PDF
        storage_path, file_size = await storage.save(file)

        logger.info(
            "File uploaded | request_id=%s | file_size=%s",
            request_id,
            file_size,
        )

        if file_size == 0:
            logger.warning(
                "Empty PDF uploaded | request_id=%s",
                request_id,
            )
            raise HTTPException(400, "Uploaded PDF is empty.")

        if file_size > MAX_FILE_SIZE:
            logger.warning(
                "File size limit exceeded | request_id=%s | file_size=%s",
                request_id,
                file_size,
            )
            raise HTTPException(413, "Maximum file size is 15 MB.")

        # 3. Persist document metadata
        document = repository.create_document(
            filename=file.filename,
            storage_path=storage_path,
        )

        logger.info(
            "Policy document created | request_id=%s | document_id=%s",
            request_id,
            document.id,
        )

        repository.update_document_status(document, "processing")

        # 4. Extract and normalize policy details
        logger.info(
            "Policy extraction started | request_id=%s | document_id=%s",
            request_id,
            document.id,
        )

        result = processor.process(storage_path)

        extraction_data = result["extraction"].model_dump(mode="json")
        normalized_data = result["normalized_policy"].model_dump(mode="json")

        logger.info(
            "Policy extraction and normalization completed | "
            "request_id=%s | document_id=%s",
            request_id,
            document.id,
        )

        # 5. Run commission rating
        logger.info(
            "Rating evaluation started | request_id=%s | document_id=%s",
            request_id,
            document.id,
        )

        rating = rating_service.rate(
            source_id="godigit_mar_2026",
            policy=result["normalized_policy"],
        )

        logger.info(
            "Rating evaluation completed | request_id=%s | "
            "document_id=%s | status=%s",
            request_id,
            document.id,
            rating.get("overall_status", "unknown")
            if isinstance(rating, dict)
            else "unknown",
        )

        # 6. Persist analysis
        analysis = repository.create_analysis(
            document_id=document.id,
            extracted_data=extraction_data,
            normalized_data=normalized_data,
        )

        logger.info(
            "Policy analysis persisted | request_id=%s | "
            "document_id=%s | analysis_id=%s",
            request_id,
            document.id,
            analysis.id,
        )

        repository.update_document_status(document, "completed")

        logger.info(
            "Policy processing completed | request_id=%s | "
            "document_id=%s | analysis_id=%s",
            request_id,
            document.id,
            analysis.id,
        )

        return {
            "document_id": document.id,
            "analysis_id": analysis.id,
            "status": "completed",
            "filename": document.original_filename,
            "policy": normalized_data,
            "extraction": extraction_data,
            "rating": rating,
        }

    except HTTPException as exc:
        logger.warning(
            "Policy request rejected | request_id=%s | status_code=%s | "
            "reason=%s",
            request_id,
            exc.status_code,
            exc.detail,
        )

        if storage_path and not document:
            cleanup_uploaded_file(storage_path, request_id)

        raise

    except Exception:
        logger.exception(
            "Policy processing failed | request_id=%s | document_id=%s",
            request_id,
            document.id if document else None,
        )

        if document:
            try:
                repository.record_failure(
                    document,
                    "Policy processing failed. Check application logs using "
                    f"request_id={request_id}.",
                )
            except Exception:
                logger.exception(
                    "Failed to persist policy processing failure | "
                    "request_id=%s | document_id=%s",
                    request_id,
                    document.id,
                )

        elif storage_path:
            cleanup_uploaded_file(storage_path, request_id)

        raise HTTPException(
            status_code=500,
            detail=f"Policy processing failed. Reference: {request_id}",
        ) from None

    finally:
        await file.close()


@router.get("/")
def list_policies(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    request_id = str(uuid4())

    logger.info(
        "Policy listing requested | request_id=%s | limit=%s | offset=%s",
        request_id,
        limit,
        offset,
    )

    if not 1 <= limit <= 100 or offset < 0:
        logger.warning(
            "Invalid pagination parameters | request_id=%s | limit=%s | "
            "offset=%s",
            request_id,
            limit,
            offset,
        )
        raise HTTPException(400, "Invalid pagination parameters.")

    try:
        repository = PolicyRepository(db)
        documents = repository.list_documents(limit, offset)

        logger.info(
            "Policy listing completed | request_id=%s | count=%s",
            request_id,
            len(documents),
        )

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

    except Exception:
        logger.exception(
            "Failed to list policy documents | request_id=%s",
            request_id,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve policies. Reference: {request_id}",
        ) from None


@router.get("/{document_id}")
def get_policy(
    document_id: str,
    db: Session = Depends(get_db),
):
    request_id = str(uuid4())

    logger.info(
        "Policy details requested | request_id=%s | document_id=%s",
        request_id,
        document_id,
    )

    try:
        repository = PolicyRepository(db)
        document = repository.get_document(document_id)

        if not document:
            logger.warning(
                "Policy document not found | request_id=%s | document_id=%s",
                request_id,
                document_id,
            )
            raise HTTPException(404, "Policy document not found.")

        analyses = repository.list_analyses(document_id)

        logger.info(
            "Policy details retrieved | request_id=%s | document_id=%s | "
            "analysis_count=%s",
            request_id,
            document_id,
            len(analyses),
        )

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

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to retrieve policy details | request_id=%s | "
            "document_id=%s",
            request_id,
            document_id,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve policy details. Reference: {request_id}",
        ) from None


@router.get("/{document_id}/document")
def get_original_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    request_id = str(uuid4())

    logger.info(
        "Original policy document requested | request_id=%s | document_id=%s",
        request_id,
        document_id,
    )

    try:
        repository = PolicyRepository(db)
        document = repository.get_document(document_id)

        if not document:
            logger.warning(
                "Policy document not found | request_id=%s | document_id=%s",
                request_id,
                document_id,
            )
            raise HTTPException(404, "Policy document not found.")

        path = Path(document.storage_path)

        if not path.is_file():
            logger.error(
                "Stored PDF missing | request_id=%s | document_id=%s",
                request_id,
                document_id,
            )
            raise HTTPException(404, "Stored PDF not found.")

        logger.info(
            "Original PDF retrieved | request_id=%s | document_id=%s",
            request_id,
            document_id,
        )

        return FileResponse(
            path=path,
            media_type="application/pdf",
            filename=document.original_filename,
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to retrieve original PDF | request_id=%s | "
            "document_id=%s",
            request_id,
            document_id,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve original PDF. Reference: {request_id}",
        ) from None


@router.get("/{document_id}/analyses/{analysis_id}")
def get_analysis_details(
    document_id: str,
    analysis_id: str,
    db: Session = Depends(get_db),
):
    request_id = str(uuid4())

    logger.info(
        "Analysis details requested | request_id=%s | document_id=%s | "
        "analysis_id=%s",
        request_id,
        document_id,
        analysis_id,
    )

    try:
        repository = PolicyRepository(db)

        document = repository.get_document(document_id)

        if not document:
            logger.warning(
                "Policy document not found | request_id=%s | document_id=%s",
                request_id,
                document_id,
            )
            raise HTTPException(404, "Policy document not found.")

        analysis = repository.get_analysis(analysis_id)

        if not analysis or analysis.document_id != document_id:
            logger.warning(
                "Policy analysis not found | request_id=%s | "
                "document_id=%s | analysis_id=%s",
                request_id,
                document_id,
                analysis_id,
            )
            raise HTTPException(404, "Policy analysis not found.")

        logger.info(
            "Analysis details retrieved | request_id=%s | "
            "document_id=%s | analysis_id=%s",
            request_id,
            document_id,
            analysis_id,
        )

        return {
            "document_id": document.id,
            "analysis_id": analysis.id,
            "status": analysis.status,
            "extracted_data": analysis.extracted_data,
            "normalized_data": analysis.normalized_data,
            "error_message": analysis.error_message,
            "created_at": analysis.created_at,
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to retrieve analysis details | request_id=%s | "
            "document_id=%s | analysis_id=%s",
            request_id,
            document_id,
            analysis_id,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve analysis. Reference: {request_id}",
        ) from None
