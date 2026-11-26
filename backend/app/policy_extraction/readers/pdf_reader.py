
from pathlib import Path

import fitz


class PDFReader:
    """Extract text from each page of a PDF document."""

    def extract_text(self, file_path: str) -> list[dict]:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError("Only PDF files are supported.")

        pages = []

        with fitz.open(path) as document:
            for page_number, page in enumerate(document, start=1):
                pages.append({
                    "page_number": page_number,
                    "text": page.get_text("text").strip(),
                })

        return pages
