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
    pool_size=8,
    max_overflow=4,
    pool_recycle=300,
    # Supabase's transaction-mode pooler (port 6543) hands out physical
    # connections that get reused across different clients between
    # transactions, so a server-side prepared statement from one client can
    # collide with another's - disabling statement preparation avoids
    # "prepared statement already exists" errors under that pooling mode.
    # Deployed hosts (e.g. Railway) go through the pooler because its direct
    # connection only resolves over IPv6, which many cloud networks don't
    # route; local dev can use either.
    connect_args={"prepare_threshold": None},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
