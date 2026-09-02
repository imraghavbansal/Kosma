"""GitHub OAuth as a second login method alongside the shared dashboard secret
(see kosma_api/auth.py). Scoping decision (2026-09-02): a user who signs in
here gets a real account (kosma_api.models.User) and a real session, but
explores the same shared seeded demo data every session does - this is NOT
per-user data isolation. Building that properly means re-scoping every
existing endpoint (traces, agents, change-proposals, ...) by tenant, which is
genuine V2-scale work (see PRODUCT-SPEC.md's original single-tenant
decision). What's real here: the OAuth handshake, the user record, and the
session - not fabricated, just intentionally narrow in what it unlocks."""

import secrets

import httpx
from fastapi import APIRouter, Cookie, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from kosma_api.auth import create_session_token
from kosma_api.config import get_settings
from kosma_api.db.session import SessionLocal
from kosma_api.models.user import User

router = APIRouter(prefix="/v1/auth/github", tags=["auth"])
settings = get_settings()

STATE_COOKIE_NAME = "kosma_oauth_state"
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


@router.get("/login")
def github_login(response: Response) -> RedirectResponse:
    if not settings.github_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured on this deployment",
        )
    state = secrets.token_urlsafe(24)
    authorize_url = (
        f"{GITHUB_AUTHORIZE_URL}?client_id={settings.github_client_id}"
        f"&redirect_uri={settings.github_oauth_redirect_uri}"
        f"&scope=read:user%20user:email%20public_repo&state={state}"
    )
    redirect = RedirectResponse(authorize_url)
    redirect.set_cookie(
        key=STATE_COOKIE_NAME,
        value=state,
        httponly=True,
        samesite="lax",
        secure=settings.environment != "local",
        max_age=600,
    )
    return redirect


@router.get("/callback")
def github_callback(
    code: str = Query(...),
    state: str = Query(...),
    oauth_state_cookie: str | None = Cookie(default=None, alias=STATE_COOKIE_NAME),
) -> RedirectResponse:
    if oauth_state_cookie is None or state != oauth_state_cookie:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    token_response = httpx.post(
        GITHUB_TOKEN_URL,
        data={
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "code": code,
            "redirect_uri": settings.github_oauth_redirect_uri,
        },
        headers={"Accept": "application/json"},
        timeout=15,
    )
    token_response.raise_for_status()
    access_token = token_response.json().get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub did not return a token")

    auth_headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    profile = httpx.get(GITHUB_USER_URL, headers=auth_headers, timeout=15).json()

    email = profile.get("email")
    if not email:
        emails = httpx.get(GITHUB_EMAILS_URL, headers=auth_headers, timeout=15).json()
        primary = next((e for e in emails if e.get("primary")), None)
        email = primary["email"] if primary else None

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.github_id == str(profile["id"])))
        if user is None:
            user = User(
                github_id=str(profile["id"]),
                github_username=profile["login"],
                display_name=profile.get("name"),
                email=email,
                avatar_url=profile.get("avatar_url"),
                github_access_token=access_token,
            )
            db.add(user)
        else:
            user.github_username = profile["login"]
            user.display_name = profile.get("name")
            user.email = email
            user.avatar_url = profile.get("avatar_url")
            user.github_access_token = access_token
        db.commit()
        db.refresh(user)
        user_id = str(user.id)
    finally:
        db.close()

    redirect = RedirectResponse(f"{settings.frontend_url}/dashboard")
    redirect.delete_cookie(STATE_COOKIE_NAME)
    redirect.set_cookie(
        key=settings.session_cookie_name,
        value=create_session_token(user_id=user_id),
        httponly=True,
        samesite="lax",
        secure=settings.environment != "local",
        max_age=60 * 60 * 24 * 7,
    )
    return redirect
