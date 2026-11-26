
from pathlib import Path

from app.policy_extraction.readers.pdf_reader import PDFReader
from app.policy_extraction.services.policy_extraction_service import (
    PolicyExtractionService,
)
from app.policy_extraction.services.evidence_validator import EvidenceValidator
from app.policy_extraction.services.policy_validator import PolicyValidator
from app.policy_extraction.services.policy_normalizer import PolicyNormalizer

from app.policy_extraction.schemas.policy import PolicyExtractionResult
from app.policy_extraction.schemas.normalized_policy import NormalizedPolicy


class PolicyProcessor:

    def __init__(
        self,
        pdf_reader: PDFReader | None = None,
        extraction_service: PolicyExtractionService | None = None,
        evidence_validator: EvidenceValidator | None = None,
        policy_validator: PolicyValidator | None = None,
        policy_normalizer: PolicyNormalizer | None = None,
    ):
        self.pdf_reader = pdf_reader or PDFReader()
        self.extraction_service = (
            extraction_service or PolicyExtractionService()
        )
        self.evidence_validator = evidence_validator or EvidenceValidator()
        self.policy_validator = policy_validator or PolicyValidator()
        self.policy_normalizer = policy_normalizer or PolicyNormalizer()

    def process(self, file_path: str) -> dict:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Policy PDF not found: {file_path}")

        # 1. Read the PDF.
        pages = self.pdf_reader.extract_text(str(path))

        # 2. Extract structured policy information.
        extraction: PolicyExtractionResult = (
            self.extraction_service.extract(pages)
        )

        # 3. Validate evidence against the original PDF.
        evidence_errors = self.evidence_validator.validate(
            extraction,
            pages,
        )

        if evidence_errors:
            raise ValueError(
                "Evidence validation failed:\n"
                + "\n".join(evidence_errors)
            )

        # 4. Validate extracted policy facts.
        policy_errors = self.policy_validator.validate(
            extraction.policy
        )

        if policy_errors:
            raise ValueError(
                "Policy validation failed:\n"
                + "\n".join(policy_errors)
            )

        # 5. Normalize policy information.
        normalized_policy: NormalizedPolicy = (
            self.policy_normalizer.normalize(extraction.policy)
        )

        # 6. Return all information needed by downstream services.
        return {
            "normalized_policy": normalized_policy,
            "extraction": extraction,
            "source_file": path.name,
            "status": "completed",
        }
