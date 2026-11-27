
from app.ingestion.core.profile_models import SourceProfile
from app.ingestion.profiles.hdfc_ergo.table_profiles import (
    PDF_TABLE_PROFILES,
)


PROFILE = SourceProfile(
    source_id="hdfc_ergo_private_car_feb_2025",
    publisher="HDFC ERGO",
    version="2025-02-01",
    file_type="pdf",
    tables=PDF_TABLE_PROFILES,
)
