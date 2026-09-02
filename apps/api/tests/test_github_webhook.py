"""GitHub PR bot: real webhook signature verification, real GitHub App JWT
auth, real PR comment posting - GitHub's own API calls mocked here (no
network, no real GitHub App needed to run these), but exercising the actual
crypto and request logic that runs in production."""

import hashlib
import hmac
import json

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from kosma_api.github_app import generate_app_jwt, verify_webhook_signature
from kosma_api.models.project import Project


def test_generate_app_jwt_is_a_valid_signed_rs256_token():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    token = generate_app_jwt("test-app-id", private_pem)
    decoded = jwt.decode(token, public_pem, algorithms=["RS256"])
    assert decoded["iss"] == "test-app-id"
    assert decoded["exp"] > decoded["iat"]


def test_verify_webhook_signature_accepts_valid_hmac():
    secret = "test-webhook-secret"
    body = b'{"action": "opened"}'
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(body, expected, secret) is True


def test_verify_webhook_signature_rejects_wrong_signature():
    secret = "test-webhook-secret"
    body = b'{"action": "opened"}'
    assert verify_webhook_signature(body, "sha256=deadbeef", secret) is False


def test_verify_webhook_signature_rejects_missing_header():
    assert verify_webhook_signature(b"{}", None, "secret") is False


def test_verify_webhook_signature_rejects_tampered_body():
    secret = "test-webhook-secret"
    original = b'{"action": "opened"}'
    signature = "sha256=" + hmac.new(secret.encode(), original, hashlib.sha256).hexdigest()
    tampered = b'{"action": "closed"}'
    assert verify_webhook_signature(tampered, signature, secret) is False


def test_webhook_rejects_bad_signature(client, monkeypatch):
    import kosma_api.routers.github_webhook as webhook_module

    monkeypatch.setattr(webhook_module.settings, "github_app_id", "123")
    monkeypatch.setattr(webhook_module.settings, "github_app_private_key", "fake-key")
    monkeypatch.setattr(webhook_module.settings, "github_app_webhook_secret", "correct-secret")

    response = client.post(
        "/v1/github/webhook",
        json={"action": "opened"},
        headers={"x-hub-signature-256": "sha256=wrong", "x-github-event": "pull_request"},
    )
    assert response.status_code == 401


def test_webhook_returns_503_when_unconfigured(client, monkeypatch):
    import kosma_api.routers.github_webhook as webhook_module

    monkeypatch.setattr(webhook_module.settings, "github_app_id", "")
    response = client.post("/v1/github/webhook", json={"action": "opened"})
    assert response.status_code == 503


def test_webhook_ignores_unlinked_repo(client, monkeypatch):
    import kosma_api.routers.github_webhook as webhook_module

    secret = "test-webhook-secret"
    monkeypatch.setattr(webhook_module.settings, "github_app_id", "123")
    monkeypatch.setattr(webhook_module.settings, "github_app_private_key", "fake-key")
    monkeypatch.setattr(webhook_module.settings, "github_app_webhook_secret", secret)

    body = {
        "action": "opened",
        "repository": {"full_name": "someone/not-linked-anywhere"},
        "pull_request": {"number": 7},
        "installation": {"id": 999},
    }
    raw = json.dumps(body).encode()
    signature = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()

    response = client.post(
        "/v1/github/webhook",
        content=raw,
        headers={
            "content-type": "application/json",
            "x-hub-signature-256": signature,
            "x-github-event": "pull_request",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_webhook_posts_real_verdict_comment_for_linked_repo(client, monkeypatch, db_session, seeded_project):
    import kosma_api.routers.github_webhook as webhook_module

    secret = "test-webhook-secret"
    monkeypatch.setattr(webhook_module.settings, "github_app_id", "123")
    monkeypatch.setattr(webhook_module.settings, "github_app_private_key", "fake-key")
    monkeypatch.setattr(webhook_module.settings, "github_app_webhook_secret", secret)

    project = db_session.get(Project, seeded_project["project_id"])
    project.github_repo = "acme/webhook-test-repo"
    db_session.commit()

    posted = {}

    def fake_jwt(app_id, private_key):
        return "fake-app-jwt"

    def fake_installation_token(installation_id, app_jwt):
        assert app_jwt == "fake-app-jwt"
        return "fake-installation-token"

    def fake_post_comment(token, repo_full_name, pr_number, body):
        posted["token"] = token
        posted["repo"] = repo_full_name
        posted["pr_number"] = pr_number
        posted["body"] = body

    monkeypatch.setattr(webhook_module, "generate_app_jwt", fake_jwt)
    monkeypatch.setattr(webhook_module, "get_installation_token", fake_installation_token)
    monkeypatch.setattr(webhook_module, "post_pr_comment", fake_post_comment)

    body = {
        "action": "opened",
        "repository": {"full_name": "acme/webhook-test-repo"},
        "pull_request": {"number": 42},
        "installation": {"id": 555},
    }
    raw = json.dumps(body).encode()
    signature = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()

    response = client.post(
        "/v1/github/webhook",
        content=raw,
        headers={
            "content-type": "application/json",
            "x-hub-signature-256": signature,
            "x-github-event": "pull_request",
        },
    )
    assert response.status_code == 200
    body_json = response.json()
    assert body_json["status"] == "commented"
    assert posted["repo"] == "acme/webhook-test-repo"
    assert posted["pr_number"] == 42
    assert posted["token"] == "fake-installation-token"
    assert "Kosma" in posted["body"]
    # no change proposed yet for this project - the comment should say so honestly
    assert "no change has been proposed" in posted["body"]

    project.github_repo = None
    db_session.commit()
