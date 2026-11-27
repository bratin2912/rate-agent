
import os
import json

from openai import OpenAI
from pydantic import ValidationError

from app.policy_extraction.schemas.policy import PolicyExtractionResult
from app.core.logging_config import get_logger


logger = get_logger(__name__)


SYSTEM_PROMPT = """
You are an insurance policy document extraction system.

Extract motor insurance policy information from the supplied PDF text.
Return data strictly according to the provided PolicyExtractionResult schema.

GENERAL EXTRACTION RULES:
- Extract only information explicitly supported by the supplied document.
- Never invent, guess, assume, or infer missing values.
- If a value cannot be identified confidently, return null or "unknown"
  according to the schema.
- Preserve the original meaning of the document.
- Do not calculate or derive values unless explicitly requested.
- Do not confuse policyholder, intermediary, broker, insurer, or vehicle details.

POLICY NUMBER AND DOCUMENT IDENTIFIERS:
- Extract policy_number only from a value explicitly associated with
  the label "Policy No.", "Policy Number", or an equivalent
  unambiguous policy-number label.
- Do not confuse policy_number with:
  "Proposal No.", "Proposal Number", "Invoice No.",
  "Customer ID", "UIN", "EIA No.", registration number,
  chassis number, engine number, or barcode numbers.
- A numeric value appearing in a document header, footer,
  barcode, or near the policy details section is not sufficient
  evidence by itself.
- Prefer the explicitly labelled Policy No. in the current
  policy schedule or certificate.
- If a page contains a Proposal No. but no explicitly labelled
  Policy No., do not use the Proposal No. as policy_number.
- If the policy number cannot be identified confidently,
  return null.
- Evidence for policy_number must contain the policy-number
  label and its associated value, copied from the same page.
- Never combine a label and value from different pages.
- Do not use an invoice number, proposal number, UIN,
  or other identifier as a fallback.
- Never extract a policy number based only on a numeric pattern.

CURRENT INSURER:
- The current insurer is the company issuing the policy being extracted.
- Identify it from the policy header, certificate, or issuing company details.
- Do not use the previous insurer as the current insurer.
- A company mentioned alongside "Previous Policy No.", "Previous Policy",
  or previous policy details belongs to the previous insurer.
- Do not identify an insurer based only on its occurrence in the document.
- Use the issuing insurer's name exactly as printed in the document.
- Do not confuse OCR-corrupted text with a different insurer.
- Do not invent or expand the insurer's legal name.

PREVIOUS INSURER:
- Extract the previous insurer only from the previous policy details section.
- Do not copy the current insurer into previous_insurer unless explicitly
  supported by the document.
- Do not confuse the previous insurer with the current policy issuer.

BUSINESS TYPE:
- Identify business_type using explicit policy information.
- Use "renewal" when the document clearly establishes that the policy
  continues from a previous policy with the same insurer.
- Use "rollover" when the previous insurer is different from the current insurer
  and the document supports this classification.
- Use "new_business" only when supported by the document.
- Otherwise return "unknown".
- Do not determine business type from insurer names alone.

POLICY DATES:
- Extract dates belonging to the current policy period only.
- Prefer sections labelled "Period of Insurance", "Policy Period",
  or equivalent current-policy wording.
- Do not use dates from previous policy details, proposal dates,
  payment dates, or document generation dates.
- Extract start_date and end_date separately.
- Convert dates to ISO format (YYYY-MM-DD) in the structured field.
- Do not calculate, assume, or modify dates.
- If multiple date ranges exist, select only the range explicitly
  associated with the current policy period.
- If the current policy period cannot be identified confidently,
  return null for the relevant date field.

VEHICLE DETAILS:
- Extract registration number, RTO code, make, model, fuel type,
  engine capacity, manufacture year, vehicle age, and vehicle category
  only when supported by the document.
- Do not derive manufacture year or vehicle age unless explicitly stated.
- Do not confuse vehicle registration details with engine or chassis numbers.
- vehicle_category must be one of:
  "private_car", "two_wheeler", "commercial_vehicle", "unknown".
- Never return null for vehicle_category. Use "unknown" if unavailable.

POLICY TYPE:
- Identify whether the policy is comprehensive, standalone OD,
  or standalone TP based on the actual coverage described.
- Do not infer policy type from the document title alone.
- If coverage cannot be established confidently, return "unknown".
- Never return null for policy_type.

PREMIUM DETAILS:
- Extract own damage premium, third-party premium, add-on premium,
  net premium, GST, and total premium separately.
- Do not confuse total premium with net premium.
- Do not treat commission, brokerage, discounts, or insured declared value
  as premium components.
- If a premium component is not explicitly available, return null.
- Do not calculate missing premium components.

NCB:
- Extract the NCB percentage only when explicitly stated.
- Do not infer NCB from previous policy information.

EVIDENCE REQUIREMENTS:
- Every non-null extracted field must have corresponding evidence
  wherever the schema supports evidence.
- Evidence quote must be copied verbatim from the supplied OCR text.
- Evidence must be taken from the correct PDF page.
- The quote must be an exact substring of that page's supplied text.
- Preserve spelling, punctuation, spacing, and date formatting in quotes.
- Never rewrite, paraphrase, normalize, or reconstruct evidence quotes.
- Keep evidence quotes short and specific to the field.
- For dates, prefer the exact individual date token as evidence
  rather than constructing a combined date-range quote.
- For current_insurer, use evidence identifying the issuing insurer.
- For previous_insurer, use evidence from the previous policy section.
- Never use evidence from a different page just because it contains
  a similar value.
- If valid evidence cannot be found, return null for the corresponding
  extracted field and do not create evidence for it.

OUTPUT:
- Return one valid JSON object.
- Follow the supplied PolicyExtractionResult schema exactly.
- Do not include Markdown, explanations, comments, or additional keys.
"""


class PolicyExtractionService:

    BATCH_SIZE = 2

    def __init__(self, client: OpenAI | None = None):

        api_key = os.getenv("GROQ_API_KEY")

        if client is None and not api_key:
            raise RuntimeError("GROQ_API_KEY is not configured.")

        self.client = client or OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )

        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b",
        )

        self.response_schema = PolicyExtractionResult.model_json_schema()

        logger.info(
            "PolicyExtractionService initialized | provider=groq | model=%s",
            self.model,
        )

    def extract(self, pages: list[dict]) -> PolicyExtractionResult:
        """
        Extract policy information in batches and merge the results.
        """

        if not pages:
            raise ValueError("No PDF pages supplied for extraction.")

        if not any(page.get("text", "").strip() for page in pages):
            raise ValueError("PDF contains no extractable text.")

        batches = [
            pages[index:index + self.BATCH_SIZE]
            for index in range(0, len(pages), self.BATCH_SIZE)
        ]

        logger.info(
            "Starting batched policy extraction | "
            "model=%s | pages=%s | batches=%s",
            self.model,
            len(pages),
            len(batches),
        )

        batch_results = []

        for batch_number, batch in enumerate(batches, start=1):

            page_numbers = [
                page["page_number"]
                for page in batch
            ]

            logger.info(
                "Processing extraction batch | batch=%s/%s | pages=%s",
                batch_number,
                len(batches),
                page_numbers,
            )

            result = self._extract_batch(batch)

            batch_results.append(result)

            logger.info(
                "Extraction batch completed | batch=%s/%s | "
                "pages=%s | evidence=%s | policy_number=%s",
                batch_number,
                len(batches),
                page_numbers,
                len(result.evidence),
                result.policy.policy_number,
            )

        merged_result = self._merge_results(batch_results)

        logger.info(
            "Batched policy extraction completed | "
            "batches=%s | evidence_count=%s",
            len(batches),
            len(merged_result.evidence),
        )

        return merged_result

    def _extract_batch(
        self,
        pages: list[dict],
    ) -> PolicyExtractionResult:
        """
        Extract policy fields from a single batch of pages.

        JSON is parsed and validated locally rather than relying on
        Groq's JSON response mode.
        """

        document_text = self._format_pages(pages)

        if not document_text.strip():
            raise ValueError("Extraction batch contains no text.")

        system_prompt = (
            SYSTEM_PROMPT
            + "\n\nEXPECTED JSON SCHEMA:\n"
            + json.dumps(self.response_schema, indent=2)
            + """

STRICT OUTPUT INSTRUCTIONS:
1. Return exactly one valid JSON object.
2. Do not use Markdown code fences.
3. Do not include explanations before or after the JSON.
4. Use exactly two top-level keys: "policy" and "evidence".
5. All object keys and string values must use double quotes.
6. Do not use trailing commas.
7. Do not return null for non-nullable categorical fields.
8. Use "unknown" for unknown categorical values.
9. Use null for unavailable optional values.
10. Evidence page numbers must match the original PDF page numbers.
"""
        )

        user_prompt = (
            "Extract insurance policy information from the following PDF pages.\n\n"

            "IMPORTANT BATCH PROCESSING RULES:\n"
            "1. These pages are only a portion of the complete PDF.\n"
            "2. Extract only information explicitly supported by these pages.\n"
            "3. Do not assume a missing field is absent from the entire document.\n"
            "4. Return null for optional fields that cannot be established "
            "from this batch.\n"
            "5. Do not guess values based on numeric patterns or nearby labels.\n"
            "6. Preserve the original PDF page numbers in evidence.\n\n"

            "POLICY NUMBER RULES:\n"
            "1. Extract policy_number only when an explicit Policy No. "
            "or Policy Number label is present.\n"
            "2. Never substitute Proposal No., Invoice No., Customer ID, "
            "UIN, EIA No., or barcode values.\n"
            "3. Do not extract an unlabeled number from the page header "
            "as a policy number.\n"
            "4. If this batch does not contain a clearly labelled policy "
            "number, return null for policy_number.\n"
            "5. The evidence must identify the actual Policy No. label "
            "and its associated number on the same page.\n\n"

            "Extract only the fields supported by these pages. "
            "Return one valid JSON object matching the supplied schema.\n\n"

            f"{document_text}"
        )

        try:
            logger.info(
                "Sending extraction request to Groq | pages=%s | model=%s",
                [page["page_number"] for page in pages],
                self.model,
            )

            # Intentionally not using response_format=json_object.

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                temperature=0.1,
                max_completion_tokens=2048,
                reasoning_effort="low",
            )

            message = completion.choices[0].message

            if message.refusal:
                raise ValueError("Groq refused the extraction request.")

            if not message.content or not message.content.strip():
                reasoning = getattr(message, "reasoning", None)

                logger.error(
                    "Groq returned empty content | "
                    "finish_reason=%s | reasoning_length=%s | usage=%s",
                    completion.choices[0].finish_reason,
                    len(reasoning) if reasoning else 0,
                    completion.usage.model_dump() if completion.usage else None,
                )

                raise ValueError(
                    "Groq returned an empty response. "
                    f"Finish reason: {completion.choices[0].finish_reason}. "
                    "Check the backend logs for completion diagnostics."
                )

            response_data = self._parse_json_response(message.content)

            if "policy" not in response_data or "evidence" not in response_data:
                raise ValueError(
                    "Groq response must contain 'policy' and 'evidence' keys."
                )

            self._normalize_categorical_defaults(response_data)

            result = PolicyExtractionResult.model_validate(response_data)

            # Evidence must only reference pages included in this batch.
            allowed_pages = {
                page["page_number"]
                for page in pages
            }

            invalid_evidence = [
                item.page_number
                for item in result.evidence
                if item.page_number not in allowed_pages
            ]

            if invalid_evidence:
                raise ValueError(
                    "Groq returned evidence for pages outside the current "
                    f"batch: {invalid_evidence}"
                )

            logger.info(
                "Groq batch extraction successful | pages=%s | "
                "evidence=%s | policy_number=%s",
                sorted(allowed_pages),
                len(result.evidence),
                result.policy.policy_number,
            )

            return result

        except ValidationError:
            logger.exception(
                "Groq response failed Pydantic validation | pages=%s",
                [page["page_number"] for page in pages],
            )
            raise

        except Exception:
            logger.exception(
                "Groq batch extraction failed | pages=%s | model=%s",
                [page["page_number"] for page in pages],
                self.model,
            )
            raise

    @staticmethod
    def _parse_json_response(content: str) -> dict:
        """
        Parse JSON returned by the model.

        Handles responses accidentally wrapped in Markdown fences.
        """

        content = content.strip()

        if content.startswith("```"):
            lines = content.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            content = "\n".join(lines).strip()

        try:
            result = json.loads(content)

        except json.JSONDecodeError as exc:
            logger.error(
                "Groq returned malformed JSON | error=%s | line=%s | column=%s",
                exc.msg,
                exc.lineno,
                exc.colno,
            )

            raise ValueError(
                "Groq returned malformed JSON. "
                f"Parsing failed at line {exc.lineno}, column {exc.colno}."
            ) from exc

        if not isinstance(result, dict):
            raise ValueError("Expected a JSON object from Groq.")

        return result

    @staticmethod
    def _normalize_categorical_defaults(response_data: dict) -> None:
        """
        Normalize null values for categorical fields that do not allow null.
        """

        policy_data = response_data.get("policy")

        if not isinstance(policy_data, dict):
            return

        if policy_data.get("policy_type") is None:
            policy_data["policy_type"] = "unknown"

        vehicle_data = policy_data.get("vehicle")

        if isinstance(vehicle_data, dict):
            if vehicle_data.get("vehicle_category") is None:
                vehicle_data["vehicle_category"] = "unknown"

        insurer_data = policy_data.get("insurer")

        if isinstance(insurer_data, dict):
            if insurer_data.get("business_type") is None:
                insurer_data["business_type"] = "unknown"

    def _merge_results(
        self,
        results: list[PolicyExtractionResult],
    ) -> PolicyExtractionResult:
        """
        Merge partial extraction results.

        Null values do not overwrite existing values.
        Unknown values do not overwrite known values.
        Conflicting non-null values raise an error.
        Evidence from every batch is retained.
        """

        if not results:
            raise ValueError("No extraction results available to merge.")

        merged_policy = results[0].policy.model_dump(mode="json")

        evidence_items = list(results[0].evidence)

        for result in results[1:]:

            incoming_policy = result.policy.model_dump(mode="json")

            self._merge_dicts(
                target=merged_policy,
                incoming=incoming_policy,
                path="policy",
            )

            evidence_items.extend(result.evidence)

        # Remove duplicate evidence while preserving order.
        unique_evidence = []
        seen_evidence = set()

        for item in evidence_items:

            key = (
                item.field_path,
                item.page_number,
                item.quote,
            )

            if key not in seen_evidence:
                seen_evidence.add(key)
                unique_evidence.append(item)

        return PolicyExtractionResult.model_validate(
            {
                "policy": merged_policy,
                "evidence": [
                    item.model_dump()
                    for item in unique_evidence
                ],
            }
        )

    def _merge_dicts(
        self,
        target: dict,
        incoming: dict,
        path: str,
    ) -> None:
        """
        Recursively merge partial extraction results.

        Rules:
        - None does not overwrite an existing value.
        - Unknown categorical values do not overwrite known values.
        - Known values replace unknown values.
        - Conflicting known values raise an error.
        """

        unknown_values = {
            "unknown",
            "none",
            "null",
            "",
        }

        for key, incoming_value in incoming.items():

            current_path = f"{path}.{key}"

            # Ignore missing values.
            if incoming_value is None:
                continue

            # If the target does not have a value, use the incoming value.
            if key not in target or target[key] is None:
                target[key] = incoming_value
                continue

            existing_value = target[key]

            # Recursively merge nested objects.
            if isinstance(existing_value, dict) and isinstance(
                incoming_value, dict
            ):
                self._merge_dicts(
                    target=existing_value,
                    incoming=incoming_value,
                    path=current_path,
                )
                continue

            # Treat unknown categorical values as missing information.
            existing_is_unknown = (
                isinstance(existing_value, str)
                and existing_value.strip().lower() in unknown_values
            )

            incoming_is_unknown = (
                isinstance(incoming_value, str)
                and incoming_value.strip().lower() in unknown_values
            )

            if incoming_is_unknown:
                continue

            if existing_is_unknown:
                target[key] = incoming_value
                continue

            # Two different known values require investigation.
            if existing_value != incoming_value:
                raise ValueError(
                    f"Conflicting extraction values for {current_path}: "
                    f"{existing_value!r} versus {incoming_value!r}. "
                    "Both batches returned known but different values."
                )

    @staticmethod
    def _format_pages(pages: list[dict]) -> str:
        """
        Format pages while preserving their original PDF page numbers.
        """

        return "\n\n".join(
            f"--- PAGE {page['page_number']} ---\n{page['text']}"
            for page in pages
            if page.get("text")
        )
