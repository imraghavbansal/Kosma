from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel

from traceos_api.auth import create_session_token, verify_dashboard_secret
from traceos_api.config import get_settings

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
