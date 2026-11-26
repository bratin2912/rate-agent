
import fitz
from pathlib import Path


class PDFReader:

    def extract_text(self, file_path: str) -> list[dict]:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"PDF not found: {file_path}"
            )

        pages = []

        with fitz.open(path) as document:
            for page_number, page in enumerate(document, start=1):
                text = page.get_text("text")

                pages.append({
                    "page_number": page_number,
                    "text": text.strip(),
                })

        return pages
