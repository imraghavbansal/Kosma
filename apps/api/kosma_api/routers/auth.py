from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from kosma_api.auth import create_session_token, get_current_user_id, require_dashboard_session, verify_dashboard_secret
from kosma_api.config import get_settings
from kosma_api.db.session import get_db
from kosma_api.models.user import User

router = APIRouter(prefix="/v1/auth", tags=["auth"])
settings = get_settings()


class LoginRequest(BaseModel):
    secret: str


@router.post("/login")
def login(body: LoginRequest, response: Response) -> dict:
    if not verify_dashboard_secret(body.secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid secret")
    token = create_session_token()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.environment != "local",
        max_age=60 * 60 * 24 * 7,
    )
    return {"status": "ok"}


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(key=settings.session_cookie_name)
    return {"status": "ok"}


@router.get("/me", dependencies=[Depends(require_dashboard_session)])
def me(
    user_id: str | None = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> dict:
    if user_id is None:
        return {"authenticated": True, "user": None}
    user = db.get(User, user_id)
    if user is None:
        return {"authenticated": True, "user": None}
    return {
        "authenticated": True,
        "user": {
            "github_username": user.github_username,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
        },
    }
