"""Projects as real, working units: list/detail reflect real counts, and
linking a github_repo is a real, persisted PATCH - not a UI-only toggle."""


def _login(client, settings):
    client.post("/v1/auth/login", json={"secret": settings.dashboard_secret})


def test_list_projects_requires_auth(client):
    response = client.get("/v1/projects")
    assert response.status_code == 401


def test_list_projects_includes_seeded_project_with_real_counts(client, settings, seeded_project):
    _login(client, settings)
    response = client.get("/v1/projects")
    assert response.status_code == 200
    items = response.json()["items"]
    match = next((p for p in items if p["id"] == str(seeded_project["project_id"])), None)
    assert match is not None
    assert match["agent_count"] == 1
    assert match["github_repo"] is None


def test_patch_project_links_and_unlinks_github_repo(client, settings, seeded_project):
    _login(client, settings)
    project_id = str(seeded_project["project_id"])

    response = client.patch(f"/v1/projects/{project_id}", json={"github_repo": "octocat/hello-world"})
    assert response.status_code == 200
    assert response.json()["github_repo"] == "octocat/hello-world"

    detail = client.get(f"/v1/projects/{project_id}")
    assert detail.status_code == 200
    assert detail.json()["github_repo"] == "octocat/hello-world"

    unlink = client.patch(f"/v1/projects/{project_id}", json={"github_repo": None})
    assert unlink.status_code == 200
    assert unlink.json()["github_repo"] is None


def test_patch_project_rejects_malformed_repo(client, settings, seeded_project):
    _login(client, settings)
    project_id = str(seeded_project["project_id"])
    response = client.patch(f"/v1/projects/{project_id}", json={"github_repo": "not-a-valid-repo"})
    assert response.status_code == 400


def test_get_project_404_for_unknown_id(client, settings):
    _login(client, settings)
    response = client.get("/v1/projects/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
