
import os

from openai import OpenAI

from backend.app.policy_extraction.schemas.policy import PolicyExtractionResult


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
"""


class PolicyExtractionService:
    def __init__(self, client: OpenAI | None = None):
        self.client = client or OpenAI()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def extract(self, pages: list[dict]) -> PolicyExtractionResult:
        if not pages:
            raise ValueError("No PDF pages supplied for extraction.")

        document_text = self._format_pages(pages)

        completion = self.client.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        "Extract the policy information from this document:\n\n"
                        f"{document_text}"
                    ),
                },
            ],
            response_format=PolicyExtractionResult,
        )

        message = completion.choices[0].message

        if message.refusal:
            raise ValueError(
                f"Policy extraction was refused: {message.refusal}"
            )

        if message.parsed is None:
            raise ValueError("The model did not return structured policy data.")

        return message.parsed

    @staticmethod
    def _format_pages(pages: list[dict]) -> str:
        return "\n\n".join(
            f"--- PAGE {page['page_number']} ---\n{page['text']}"
            for page in pages
            if page.get("text")
        )
