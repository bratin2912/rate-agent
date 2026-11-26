
from app.ingestion.core.profile_models import SourceProfile
from app.ingestion.profiles.godigit.sheet_profiles import SHEET_PROFILES


PROFILE = SourceProfile(
    source_id="godigit_mar_2026",
    publisher="Go Digit",
    version="March 2026",
    file_type="xlsx",
    sheets=SHEET_PROFILES,
)
