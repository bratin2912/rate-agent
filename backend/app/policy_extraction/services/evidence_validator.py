
import re
from decimal import Decimal
from datetime import date, datetime

from app.policy_extraction.schemas.policy import PolicyExtractionResult


class EvidenceValidator:
    """Validate and reconcile extracted evidence against original PDF text."""

    @staticmethod
    def _normalize_text(value: str) -> str:
        """Normalize whitespace without changing meaningful characters."""
        return re.sub(r"\s+", " ", value).strip().casefold()

    @staticmethod
    def _get_field_value(
        result: PolicyExtractionResult,
        field_path: str,
    ):
        """Retrieve an extracted value using its schema field path."""

        data = result.model_dump(mode="python")

        current = data

        try:
            for part in field_path.split("."):
                current = current[part]

            return current

        except (KeyError, TypeError):
            return None

    @staticmethod
    def _find_exact_value(
        value,
        page_text: str,
    ) -> str | None:
        """
        Find the exact extracted value in OCR text.

        Allows whitespace differences but does not allow fuzzy
        character matching or digit substitutions.
        """

        if value is None:
            return None

        if isinstance(value, (date, datetime)):
            value = value.isoformat()

        elif isinstance(value, Decimal):
            value = format(value, "f")

        elif isinstance(value, (int, float)):
            value = str(value)

        elif not isinstance(value, str):
            return None

        value = value.strip()

        if not value:
            return None

        # Permit OCR line breaks and whitespace differences.
        pattern = re.escape(value)
        pattern = pattern.replace(r"\ ", r"\s+")

        # Avoid matching the value as part of a larger identifier.
        pattern = rf"(?<![A-Za-z0-9]){pattern}(?![A-Za-z0-9])"

        match = re.search(
            pattern,
            page_text,
            flags=re.IGNORECASE,
        )

        return match.group(0) if match else None

    def validate(
        self,
        result: PolicyExtractionResult,
        pages: list[dict],
    ) -> list[str]:
        """
        Validate evidence.

        If the original evidence quote is invalid but the exact
        extracted field value exists on the same page, replace
        the quote with the actual OCR substring.

        Unverifiable evidence remains an error.
        """

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

            normalized_quote = self._normalize_text(quote)
            normalized_page = self._normalize_text(page_text)

            # First attempt: validate the original evidence.
            if normalized_quote in normalized_page:
                continue

            # Second attempt: verify the actual extracted field value.
            extracted_value = self._get_field_value(
                result,
                evidence.field_path,
            )

            matched_value = self._find_exact_value(
                extracted_value,
                page_text,
            )

            if matched_value is not None:
                # Store the actual OCR substring as evidence.
                evidence.quote = matched_value
                continue

            errors.append(
                f"{evidence.field_path}: "
                f"Evidence quote not found on page "
                f"{evidence.page_number}, and extracted value "
                f"could not be independently verified. "
                f"Quote: {quote!r}"
            )

        return errors
