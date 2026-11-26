
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

CURRENT INSURER:
- The current insurer is the company issuing the policy being extracted.
- Identify it from the policy header, certificate, or issuing company details.
- Do not use the previous insurer as the current insurer.
- A company mentioned alongside "Previous Policy No.", "Previous Policy",
  or previous policy details belongs to the previous insurer.
- Do not identify an insurer based only on its occurrence in the document.
- Use the issuing insurer's name exactly as printed in the document.

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

POLICY TYPE:
- Identify whether the policy is comprehensive, standalone OD,
  or standalone TP based on the actual coverage described.
- Do not infer policy type from the document title alone.
- If coverage cannot be established confidently, return "unknown".

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
- Return valid JSON only.
- Follow the supplied PolicyExtractionResult schema exactly.
- Do not include Markdown, explanations, comments, or additional keys.
"""



class PolicyExtractionService:

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

        # Generate the expected schema directly from our Pydantic model.
        self.response_schema = PolicyExtractionResult.model_json_schema()

        logger.info(
            "PolicyExtractionService initialized | provider=groq | model=%s",
            self.model,
        )

    def extract(self, pages: list[dict]) -> PolicyExtractionResult:

        if not pages:
            raise ValueError("No PDF pages supplied for extraction.")

        document_text = self._format_pages(pages)

        if not document_text.strip():
            raise ValueError("PDF contains no extractable text.")

        logger.info(
            "Starting policy extraction | provider=groq | model=%s | pages=%s",
            self.model,
            len(pages),
        )

        system_prompt = (
            SYSTEM_PROMPT
            + "\n\nExpected JSON Schema:\n"
            + json.dumps(self.response_schema, indent=2)
            + "\n\nThe top-level keys must be exactly 'policy' and 'evidence'."
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": (
                            "Extract the policy information from this document:\n\n"
                            f"{document_text}"
                        ),
                    },
                ],
                response_format={
                    "type": "json_object",
                },
                temperature=0.1,
            )

            message = completion.choices[0].message

            if message.refusal:
                logger.warning(
                    "Groq refused policy extraction | model=%s",
                    self.model,
                )
                raise ValueError("Groq refused the extraction request.")

            if not message.content:
                raise ValueError("Groq returned an empty response.")

            logger.info(
                "Groq response received | model=%s",
                self.model,
            )

            # Validate the JSON response against our Pydantic contract.
            try:
                result = PolicyExtractionResult.model_validate_json(
                    message.content
                )

            except ValidationError as exc:

                # Log structure and validation errors, not policy content.
                try:
                    response_data = json.loads(message.content)

                    response_keys = (
                        list(response_data.keys())
                        if isinstance(response_data, dict)
                        else []
                    )

                except json.JSONDecodeError:
                    response_keys = []

                logger.error(
                    "Groq response schema validation failed | "
                    "top_level_keys=%s | validation_errors=%s",
                    response_keys,
                    exc.errors(include_input=False),
                )

                raise

            logger.info(
                "Policy extraction completed successfully | "
                "evidence_count=%s",
                len(result.evidence),
            )

            return result

        except ValidationError:
            logger.exception(
                "Groq returned invalid policy extraction structure"
            )
            raise

        except Exception:
            logger.exception(
                "Groq policy extraction failed | model=%s",
                self.model,
            )
            raise

    @staticmethod
    def _format_pages(pages: list[dict]) -> str:

        return "\n\n".join(
            f"--- PAGE {page['page_number']} ---\n{page['text']}"
            for page in pages
            if page.get("text")
        )
