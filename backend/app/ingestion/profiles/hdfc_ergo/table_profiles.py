
from app.ingestion.core.profile_models import PDFTableProfile


COMMISSION_TABLE = PDFTableProfile(
    table_id="private_car_commission_rates",
    page_numbers=(1,),
    table_type="commission_grid",
    product_line="private_car",
    description=(
        "HDFC ERGO private car commission rates by zone, "
        "product type, fuel category, NCB category and GWP slab."
    ),
    extraction_method="table",
    header_keywords=(
        "GWP",
        "PACKAGE",
        "SAOD",
        "PETROL",
        "NON PETROL",
    ),
)


ZONE_MAPPING_TABLE = PDFTableProfile(
    table_id="private_car_zone_mappings",
    page_numbers=(1, 2),
    table_type="rto_mapping",
    product_line="private_car",
    description=(
        "Geographical mapping of states and locations "
        "to HDFC ERGO private car zones."
    ),
    extraction_method="table",
    header_keywords=(
        "ZONE 1",
        "ZONE 2",
        "STATE",
        "LOCATION",
    ),
)


PDF_TABLE_PROFILES = {
    COMMISSION_TABLE.table_id: COMMISSION_TABLE,
    ZONE_MAPPING_TABLE.table_id: ZONE_MAPPING_TABLE,
}
