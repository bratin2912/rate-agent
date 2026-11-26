
from app.database.base import Base
from app.database.connection import engine

# Import models so SQLAlchemy registers their tables.
from app.models.policy import PolicyDocument, PolicyAnalysis  # noqa: F401


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
