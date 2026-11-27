from app.ingestion.core.registry import get_profile
from app.ingestion.readers.pdf_reader import PDFReader
from app.ingestion.extractors.pdf_table_extractor import PDFTableExtractor
from app.ingestion.normalizer import InsuranceDataNormalizer


PDF_PATH = (
    "data/raters/hdfc-ergo/feb-2025/"
    "Pvt Car New Grid Eff 1st Feb'25 (HDFC ergo) 1.pdf"
)


def main():
    profile = get_profile("hdfc_ergo_private_car_feb_2025")

    reader = PDFReader()
    normalizer = InsuranceDataNormalizer()

    source_metadata = {
        "source_id": profile.source_id,
        "publisher": profile.publisher,
        "version": profile.version,
        "original_filename": PDF_PATH.split("/")[-1],
    }

    for table_profile in profile.tables.values():
        extractor = PDFTableExtractor(reader, table_profile)
        extracted_table = extractor.extract(PDF_PATH)

        normalized_table = normalizer.normalize_pdf_table(
            extracted_table,
            source_metadata,
        )

        record_ids = [
            record.record_id
            for record in normalized_table.records
        ]

        print("\nTable:", normalized_table.table_id)
        print("Record count:", normalized_table.record_count)
        print("Unique IDs:", len(set(record_ids)))
        print("First record:", normalized_table.records[0].model_dump())


if __name__ == "__main__":
    main()
