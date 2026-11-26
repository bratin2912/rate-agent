
from app.ingestion.core.profile_models import SourceProfile
from app.ingestion.profiles.godigit.source import PROFILE as GODIGIT_PROFILE


PROFILES: dict[str, SourceProfile] = {
    GODIGIT_PROFILE.source_id: GODIGIT_PROFILE,
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
    """
    if profile.source_id in PROFILES:
        raise ValueError(
            f"Profile already registered: {profile.source_id}"
        )

    PROFILES[profile.source_id] = profile
