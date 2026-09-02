"""Real GitHub App authentication and PR commenting - the mechanics behind
"KOSMA posts SHIP/MODIFY/BLOCK to the PR" (see routers/github_webhook.py).
Separate from routers/oauth.py's GitHub OAuth App: that authenticates a
person logging into Kosma; this authenticates Kosma itself acting on a
repo it's been installed into, via a signed JWT exchanged for a short-lived
installation token - the standard GitHub App auth flow, implemented for
real (RS256 JWT via PyJWT, real token exchange, real comment POST)."""

import hashlib
import hmac
import time

import httpx
import jwt

GITHUB_API = "https://api.github.com"


def verify_webhook_signature(payload: bytes, signature_header: str | None, secret: str) -> bool:
    """Constant-time HMAC-SHA256 check against X-Hub-Signature-256 - without
    this, anyone could POST a fake webhook and get Kosma to post fabricated
    verdicts to a PR under its name."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def generate_app_jwt(app_id: str, private_key: str) -> str:
    """A short-lived (10 min) RS256-signed JWT identifying the GitHub App
    itself - the first step of GitHub App auth, exchanged for a
    per-installation token by get_installation_token below."""
    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + 600, "iss": app_id}
    return jwt.encode(payload, private_key, algorithm="RS256")


def get_installation_token(installation_id: int, app_jwt: str) -> str:
    resp = httpx.post(
        f"{GITHUB_API}/app/installations/{installation_id}/access_tokens",
        headers={"Authorization": f"Bearer {app_jwt}", "Accept": "application/vnd.github+json"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["token"]


def post_pr_comment(installation_token: str, repo_full_name: str, pr_number: int, body: str) -> None:
    resp = httpx.post(
        f"{GITHUB_API}/repos/{repo_full_name}/issues/{pr_number}/comments",
        headers={
            "Authorization": f"Bearer {installation_token}",
            "Accept": "application/vnd.github+json",
        },
        json={"body": body},
        timeout=15,
    )
    resp.raise_for_status()
