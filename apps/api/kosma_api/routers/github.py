"""Real GitHub activity for a signed-in user - their actual public repos,
commits, and pull requests, fetched live from the GitHub API with the access
token captured during OAuth (see routers/oauth.py). No synthetic data: if the
user has no repos, or GitHub is slow/unreachable, we return an empty/error
state rather than making something up."""

from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from kosma_api.auth import get_current_user_id, require_dashboard_session
from kosma_api.db.session import get_db
from kosma_api.models.user import User

router = APIRouter(prefix="/v1/github", tags=["github"])

GITHUB_API = "https://api.github.com"


def _get_authenticated_user(db: Session, user_id: str | None) -> User:
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="GitHub activity is only available for GitHub-authenticated sessions",
        )
    user = db.get(User, user_id)
    if user is None or not user.github_access_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No linked GitHub account")
    return user


@router.get("/repos", dependencies=[Depends(require_dashboard_session)])
def list_repos(
    db: Session = Depends(get_db),
    user_id: str | None = Depends(get_current_user_id),
) -> dict:
    user = _get_authenticated_user(db, user_id)
    headers = {"Authorization": f"Bearer {user.github_access_token}", "Accept": "application/vnd.github+json"}
    try:
        resp = httpx.get(
            f"{GITHUB_API}/user/repos",
            headers=headers,
            params={"sort": "pushed", "per_page": 10, "affiliation": "owner,collaborator"},
            timeout=15,
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not reach GitHub") from exc

    repos = [
        {
            "name": r["full_name"],
            "description": r.get("description"),
            "url": r["html_url"],
            "stars": r["stargazers_count"],
            "language": r.get("language"),
            "pushed_at": r["pushed_at"],
            "private": r["private"],
        }
        for r in resp.json()
    ]
    return {"items": repos}


@router.get("/activity", dependencies=[Depends(require_dashboard_session)])
def recent_activity(
    db: Session = Depends(get_db),
    user_id: str | None = Depends(get_current_user_id),
) -> dict:
    """Recent commits and open PRs across the user's most recently pushed
    repos - real GitHub data, capped to keep this endpoint fast."""
    user = _get_authenticated_user(db, user_id)
    headers = {"Authorization": f"Bearer {user.github_access_token}", "Accept": "application/vnd.github+json"}

    try:
        repos_resp = httpx.get(
            f"{GITHUB_API}/user/repos",
            headers=headers,
            params={"sort": "pushed", "per_page": 4, "affiliation": "owner,collaborator"},
            timeout=15,
        )
        repos_resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not reach GitHub") from exc

    repos = repos_resp.json()
    commits: list[dict] = []
    pulls: list[dict] = []

    with httpx.Client(headers=headers, timeout=10) as client:
        for repo in repos:
            full_name = repo["full_name"]
            try:
                c_resp = client.get(f"{GITHUB_API}/repos/{full_name}/commits", params={"per_page": 3})
                if c_resp.status_code == 200:
                    for c in c_resp.json():
                        commits.append(
                            {
                                "repo": full_name,
                                "sha": c["sha"][:7],
                                "message": c["commit"]["message"].split("\n")[0],
                                "author": (c.get("author") or {}).get("login") or c["commit"]["author"]["name"],
                                "url": c["html_url"],
                                "date": c["commit"]["author"]["date"],
                            }
                        )
            except httpx.HTTPError:
                continue

            try:
                p_resp = client.get(
                    f"{GITHUB_API}/repos/{full_name}/pulls",
                    params={"state": "all", "per_page": 3, "sort": "updated", "direction": "desc"},
                )
                if p_resp.status_code == 200:
                    for p in p_resp.json():
                        pulls.append(
                            {
                                "repo": full_name,
                                "number": p["number"],
                                "title": p["title"],
                                "state": "merged" if p.get("merged_at") else p["state"],
                                "author": p["user"]["login"],
                                "url": p["html_url"],
                                "updated_at": p["updated_at"],
                            }
                        )
            except httpx.HTTPError:
                continue

    commits.sort(key=lambda c: c["date"], reverse=True)
    pulls.sort(key=lambda p: p["updated_at"], reverse=True)

    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "commits": commits[:8],
        "pull_requests": pulls[:6],
    }
