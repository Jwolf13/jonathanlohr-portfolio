from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """All ORM models inherit from this class to register with SQLAlchemy's metadata."""
    pass
