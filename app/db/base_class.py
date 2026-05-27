from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Unified declarative base for all database models.
    Defined in a separate module to prevent circular dependency loops
    when models need to import the base class.
    """
    pass
