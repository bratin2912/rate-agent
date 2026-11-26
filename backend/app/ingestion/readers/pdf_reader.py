
from pathlib import Path
import subprocess

import pymupdf

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class PDFReader:
    """Extract text from native and scanned PDF documents."""

    OCR_LANGUAGE = "eng"
    OCR_DPI = 300
    MIN_NATIVE_TEXT_LENGTH = 20

    def extract_text(self, file_path: str) -> list[dict]:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError("Only PDF files are supported.")

        pages = []

        try:
            with pymupdf.open(path) as document:
                if document.is_encrypted:
                    raise ValueError("Encrypted PDFs are not supported.")

                for page_number, page in enumerate(document, start=1):
                    text = page.get_text("text").strip()
                    extraction_method = "native"

                    if len(text) < self.MIN_NATIVE_TEXT_LENGTH:
                        logger.info(
                            "Native text insufficient; running Tesseract OCR | page=%s",
                            page_number,
                        )

                        pixmap = page.get_pixmap(
                            dpi=self.OCR_DPI,
                            alpha=False,
                        )

                        image_bytes = pixmap.tobytes("png")

                        try:
                            result = subprocess.run(
                                [
                                    "tesseract",
                                    "stdin",
                                    "stdout",
                                    "-l",
                                    self.OCR_LANGUAGE,
                                ],
                                input=image_bytes,
                                capture_output=True,
                                check=True,
                            )

                            text = result.stdout.decode(
                                "utf-8",
                                errors="replace",
                            ).strip()

                            extraction_method = "ocr"

                        except FileNotFoundError as exc:
                            raise RuntimeError(
                                "Tesseract is not installed or not available in PATH."
                            ) from exc

                        except subprocess.CalledProcessError as exc:
                            logger.error(
                                "Tesseract failed | page=%s | error=%s",
                                page_number,
                                exc.stderr.decode(errors="replace"),
                            )
                            raise RuntimeError(
                                f"OCR failed on PDF page {page_number}."
                            ) from exc

                    logger.info(
                        "PDF page processed | page=%s | method=%s | characters=%s",
                        page_number,
                        extraction_method,
                        len(text),
                    )

                    pages.append({
                        "page_number": page_number,
                        "text": text,
                    })

        except pymupdf.FileDataError as exc:
            raise ValueError("Invalid or corrupted PDF file.") from exc

        if not pages:
            raise ValueError("PDF contains no pages.")

        return pages
