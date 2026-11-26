
from app.policy_extraction.schemas.policy import PolicyExtractionResult


class EvidenceValidator:
    """Validate extracted evidence against the original PDF text."""

    def validate(
        self,
        result: PolicyExtractionResult,
        pages: list[dict],
    ) -> list[str]:
        errors = []

        page_texts = {
            page["page_number"]: page.get("text", "")
            for page in pages
        }

        for evidence in result.evidence:
            page_text = page_texts.get(evidence.page_number)

            if page_text is None:
                errors.append(
                    f"{evidence.field_path}: "
                    f"Page {evidence.page_number} does not exist."
                )
                continue

            quote = evidence.quote.strip()

            if not quote:
                errors.append(
                    f"{evidence.field_path}: Evidence quote is empty."
                )
                continue

            if quote.casefold() not in page_text.casefold():
                errors.append(
                    f"{evidence.field_path}: "
                    f"Evidence quote not found on page "
                    f"{evidence.page_number}."
                )

        return errors
