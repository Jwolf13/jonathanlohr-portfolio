import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/apexbench",
)

engine = create_engine(DATABASE_URL)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """Yield a database session for a single request, then close it."""
    db: Session = SessionLocal()

    # ── transaction boundary begins ──────────────────────────────────────
    try:
        yield db
        db.commit()  # commit if the handler returned without raising   
    except Exception:
        db.rollback()  # rollback if the handler raised an exception
        raise
    finally:
        # ── transaction boundary ends ─────────────────────────────────────
        db.close()
