from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from kosma_api.config import get_settings

settings = get_settings()

# Conservative pool: Supabase's free-tier direct connection limit is small, and
# this process isn't the only thing that talks to it during local dev (seed
# scripts, ad-hoc verification queries). pool_recycle avoids handing out
# connections the server may have quietly dropped after sitting idle.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=2,
    pool_recycle=300,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
