
from app.ingestion.core.profile_models import SourceProfile

from app.ingestion.profiles.godigit.source import PROFILE as GODIGIT_PROFILE
from app.ingestion.profiles.hdfc_ergo.source import PROFILE as HDFC_ERGO_PROFILE


PROFILES: dict[str, SourceProfile] = {
    GODIGIT_PROFILE.source_id: GODIGIT_PROFILE,
    HDFC_ERGO_PROFILE.source_id: HDFC_ERGO_PROFILE,
}


def get_profile(source_id: str) -> SourceProfile:
    """
    Return the registered profile for a source.

    Raises:
        KeyError: If the source ID is not registered.
    """
    try:
        return PROFILES[source_id]
    except KeyError:
        raise KeyError(
            f"No source profile registered for: {source_id}"
        )


def register_profile(profile: SourceProfile) -> None:
    """
    Register a source profile.

    Raises:
        ValueError: If the source ID is already registered.
    """
    if profile.source_id in PROFILES:
        raise ValueError(
            f"Profile already registered: {profile.source_id}"
        )

    PROFILES[profile.source_id] = profile
