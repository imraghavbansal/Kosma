"""GitHub App webhook receiver - the P2 "GitHub PR integration" from
PRODUCT-SPEC.md. On a pull_request event for a repo linked to a Kosma
project (Project.github_repo), posts that project's most recent change
verdict as a real PR comment.

What this deliberately does NOT do: guess which files in a diff constitute
"an AI change" and run a fresh analysis from the diff alone - that's a real,
unsolved classification problem (what counts as a prompt/config change is
repo-specific), not something to fake. Instead it surfaces the verdict from
the most recent change proposal already analyzed for that project - real,
already-computed evidence, not a new fabrication triggered by the diff.

Setup (you do this in GitHub's UI, not via this app):
1. https://github.com/settings/apps/new -> create a GitHub App
   - Webhook URL: https://<your-api>/v1/github/webhook
   - Webhook secret: generate one, save it
   - Permissions: Pull requests (Read & write), Metadata (Read-only)
   - Subscribe to events: Pull request
2. Generate a private key (downloads a .pem) - set GITHUB_APP_PRIVATE_KEY to
   its full contents
3. Set GITHUB_APP_ID (shown on the app's settings page) and
   GITHUB_APP_WEBHOOK_SECRET
4. Install the app on the repo(s) you want it to comment on
5. Link that repo to a Kosma project: PATCH /v1/projects/{id} {"github_repo": "owner/name"}
"""

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from kosma_api.config import get_settings
from kosma_api.db.session import SessionLocal
from kosma_api.github_app import generate_app_jwt, get_installation_token, post_pr_comment, verify_webhook_signature
from kosma_api.models.change_proposal import ChangeProposal
from kosma_api.models.impact_report import ImpactReport
from kosma_api.models.project import Project

router = APIRouter(prefix="/v1/github", tags=["github-app"])
settings = get_settings()

HANDLED_ACTIONS = {"opened", "synchronize", "reopened"}


def _verdict_comment_body(project: Project, db: Session) -> str:
    latest = db.scalar(
        select(ChangeProposal)
        .where(ChangeProposal.project_id == project.id)
        .order_by(ChangeProposal.created_at.desc())
        .limit(1)
    )
    if latest is None:
        return (
            "**Kosma** - this repo is linked to a Kosma project, but no change has "
            "been proposed and analyzed yet. Propose one from the dashboard to get "
            "a Blast Radius Diff and verdict here on future PRs."
        )

    report = db.scalar(select(ImpactReport).where(ImpactReport.change_proposal_id == latest.id))
    if report is None:
        return (
            f"**Kosma** - the most recent change proposal (\"{latest.description or latest.id}\") "
            "hasn't been analyzed yet. Run Analyze on it from the dashboard."
        )

    icon = {"SHIP": "\U0001F7E2", "MODIFY": "\U0001F7E1", "BLOCK": "\U0001F534", "INSUFFICIENT_EVIDENCE": "⚪"}
    rec = report.recommendation.value if hasattr(report.recommendation, "value") else str(report.recommendation)
    lines = [
        f"### {icon.get(rec, '')} Kosma verdict: {rec.replace('_', ' ')}",
        "",
        f"Most recent analyzed change: **{latest.description or latest.id}**",
        f"Confidence: {report.confidence * 100:.0f}% · Replayed against {report.sample_size} historical executions",
        "",
        report.evidence_basis,
        "",
        f"**Next action:** {report.recommended_next_action}",
    ]
    return "\n".join(lines)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def github_webhook(request: Request) -> dict:
    if not (settings.github_app_id and settings.github_app_private_key and settings.github_app_webhook_secret):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The GitHub App integration is not configured on this deployment",
        )

    raw_body = await request.body()
    signature = request.headers.get("x-hub-signature-256")
    if not verify_webhook_signature(raw_body, signature, settings.github_app_webhook_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    event = request.headers.get("x-github-event")
    payload = await request.json()

    if event != "pull_request" or payload.get("action") not in HANDLED_ACTIONS:
        return {"status": "ignored"}

    repo_full_name = payload["repository"]["full_name"]
    pr_number = payload["pull_request"]["number"]
    installation_id = payload.get("installation", {}).get("id")
    if installation_id is None:
        return {"status": "ignored", "reason": "no installation id on payload"}

    db = SessionLocal()
    try:
        project = db.scalar(select(Project).where(Project.github_repo == repo_full_name))
        if project is None:
            return {"status": "ignored", "reason": f"{repo_full_name} is not linked to any Kosma project"}

        body = _verdict_comment_body(project, db)
    finally:
        db.close()

    app_jwt = generate_app_jwt(settings.github_app_id, settings.github_app_private_key)
    installation_token = get_installation_token(installation_id, app_jwt)
    post_pr_comment(installation_token, repo_full_name, pr_number, body)

    return {"status": "commented", "repo": repo_full_name, "pr": pr_number}
