# Import the base class to expose it for Alembic
from app.db.base_class import Base  # noqa

# Import all models here to register them with the Base.metadata
# This is crucial for Alembic's 'autogenerate' feature to detect schema changes.
from app.db.models.user import User  # noqa
