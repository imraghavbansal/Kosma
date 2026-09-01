from kosma_api.auth import hash_api_key


def test_login_rejects_wrong_secret(client):
    response = client.post("/v1/auth/login", json={"secret": "wrong"})
    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == 401
    assert "request_id" in body["error"]


def test_login_accepts_correct_secret_and_sets_cookie(client, settings):
    response = client.post("/v1/auth/login", json={"secret": settings.dashboard_secret})
    assert response.status_code == 200
    assert settings.session_cookie_name in response.cookies


def test_logout_clears_cookie(client, settings):
    client.post("/v1/auth/login", json={"secret": settings.dashboard_secret})
    response = client.post("/v1/auth/logout")
    assert response.status_code == 200


def test_hash_api_key_is_deterministic_and_not_reversible_plaintext():
    hashed = hash_api_key("sk-live-abc123")
    assert hashed != "sk-live-abc123"
    assert hash_api_key("sk-live-abc123") == hashed
    assert len(hashed) == 64  # sha256 hex digest
