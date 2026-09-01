import hashlib
import hmac

from fastapi import Cookie, Depends, Header, HTTPException, status
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy import select
from sqlalchemy.orm import Session

from kosma_api.config import get_settings
from kosma_api.db.session import get_db
from kosma_api.models.project import Project

settings = get_settings()

SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7  # 7 days


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.session_secret_key, salt="kosma-dashboard-session")


def create_session_token() -> str:
    return _serializer().dumps({"authenticated": True})


def verify_dashboard_secret(secret: str) -> bool:
    return hmac.compare_digest(secret, settings.dashboard_secret)


def require_dashboard_session(
    session: str | None = Cookie(default=None, alias=settings.session_cookie_name),
) -> None:
    token = session
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        _serializer().loads(token, max_age=SESSION_MAX_AGE_SECONDS)
    except BadSignature as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session") from exc


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def require_project_api_key(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Project:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or malformed Authorization header"
        )
    api_key = authorization.removeprefix("Bearer ").strip()
    project = db.scalar(select(Project).where(Project.api_key_hash == hash_api_key(api_key)))
    if project is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return project
