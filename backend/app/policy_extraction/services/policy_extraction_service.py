
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

Rules:
1. Extract only information explicitly supported by the document.
2. Never invent, assume, or guess missing values.
3. If a value is missing or unclear, return null or the schema's unknown value.
4. Do not calculate vehicle age or derive missing dates.
5. Preserve insurer and vehicle names as written in the document.
6. Identify policy type only when supported by policy wording.
7. Extract premium components separately.
8. Do not confuse total premium with own damage or third-party premium.
9. Do not interpret commission or brokerage rates as customer premium.
10. For every extracted value, provide evidence:
    - Exact field path from the PolicyDetails schema.
    - PDF page number.
    - A short supporting quotation copied from the supplied text.
11. Do not provide evidence for values that are unknown or null.
12. If current and previous insurer are the same, do not independently
    assume renewal unless the policy document supports it.

Important:
- Return only valid JSON.
- Follow the supplied JSON schema exactly.
- Use the exact field names from the schema.
- Do not convert snake_case fields to camelCase.
- Do not add alternative field names.
- Do not omit required top-level fields.
- Do not include Markdown code fences or explanations.
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
