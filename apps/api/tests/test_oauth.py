"""Covers the GitHub-OAuth-adjacent auth surface that doesn't require a real
GitHub round-trip: session encoding/decoding with a user_id, and /v1/auth/me
for both session kinds. The actual OAuth handshake (redirect, code exchange)
needs a live GitHub app and is exercised manually, not here."""

from kosma_api.auth import create_session_token
from kosma_api.models.user import User


def test_shared_secret_session_has_no_user_id(client, settings):
    client.post("/v1/auth/login", json={"secret": settings.dashboard_secret})
    response = client.get("/v1/auth/me")
    assert response.status_code == 200
    body = response.json()
    assert body["authenticated"] is True
    assert body["user"] is None


def test_me_requires_authentication(client):
    response = client.get("/v1/auth/me")
    assert response.status_code == 401


def test_github_session_token_round_trips_user_id(client, db_session, settings):
    user = User(
        github_id="12345",
        github_username="octocat",
        display_name="The Octocat",
        email="octocat@example.com",
        avatar_url="https://example.com/avatar.png",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_session_token(user_id=str(user.id))
    client.cookies.set(settings.session_cookie_name, token)

    response = client.get("/v1/auth/me")
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["github_username"] == "octocat"
    assert body["user"]["display_name"] == "The Octocat"

    db_session.delete(user)
    db_session.commit()


def test_github_login_without_configured_client_id_returns_503(client):
    response = client.get("/v1/auth/github/login", follow_redirects=False)
    # local test env has no GITHUB_CLIENT_ID set - must fail loudly, not
    # silently redirect somewhere broken
    assert response.status_code == 503
