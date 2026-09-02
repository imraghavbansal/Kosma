"""GitHub activity endpoints require a GitHub-authenticated session with a
linked access token - real API calls to github.com are exercised manually,
not here (no network calls in tests)."""

from kosma_api.auth import create_session_token
from kosma_api.models.user import User


def test_repos_requires_authentication(client):
    response = client.get("/v1/github/repos")
    assert response.status_code == 401


def test_repos_forbidden_for_shared_secret_session(client, settings):
    client.post("/v1/auth/login", json={"secret": settings.dashboard_secret})
    response = client.get("/v1/github/repos")
    assert response.status_code == 403


def test_activity_forbidden_without_linked_github_token(client, db_session, settings):
    user = User(
        github_id="99999",
        github_username="notoken",
        github_access_token=None,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_session_token(user_id=str(user.id))
    client.cookies.set(settings.session_cookie_name, token)

    response = client.get("/v1/github/activity")
    assert response.status_code == 403

    db_session.delete(user)
    db_session.commit()
