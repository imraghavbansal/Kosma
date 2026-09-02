"""Projects as real, working units: list/detail reflect real counts, and
linking a github_repo is a real, persisted PATCH - not a UI-only toggle."""

import uuid


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


def test_create_project_returns_a_working_api_key(client, settings, db_session):
    _login(client, settings)
    response = client.post("/v1/projects", json={"name": "real-onboarding-test"})
    assert response.status_code == 201
    body = response.json()
    assert body["api_key"].startswith("kosma_live_")
    assert body["agent_id"]
    assert body["agent_config_id"]

    # the returned key must actually authenticate a real trace ingest
    ingest = client.post(
        "/v1/traces",
        headers={"Authorization": f"Bearer {body['api_key']}"},
        json={
            "trace_ref": "onboarding-smoke-test-1",
            "agent_id": body["agent_id"],
            "agent_config_id": body["agent_config_id"],
            "input_text": "hello",
            "status": "completed",
            "success": True,
            "latency_ms": 10,
            "input_tokens": 5,
            "output_tokens": 5,
            "spans": [],
        },
    )
    assert ingest.status_code == 202

    from kosma_api.models.organization import Organization
    from kosma_api.models.project import Project

    project = db_session.get(Project, uuid.UUID(body["id"]))
    org_id = project.organization_id
    db_session.delete(project)
    db_session.commit()
    org = db_session.get(Organization, org_id)
    if org is not None:
        db_session.delete(org)
        db_session.commit()


def test_create_project_rejects_blank_name(client, settings):
    _login(client, settings)
    response = client.post("/v1/projects", json={"name": "   "})
    assert response.status_code == 400


def test_regenerate_key_invalidates_old_key_and_issues_a_working_new_one(client, settings, db_session):
    _login(client, settings)
    create = client.post("/v1/projects", json={"name": "regen-key-test"})
    body = create.json()
    old_key = body["api_key"]

    regen = client.post(f"/v1/projects/{body['id']}/regenerate-key")
    assert regen.status_code == 200
    new_key = regen.json()["api_key"]
    assert new_key != old_key

    # old key no longer authenticates
    old_ingest = client.post(
        "/v1/traces",
        headers={"Authorization": f"Bearer {old_key}"},
        json={
            "trace_ref": "regen-test-old-key",
            "agent_id": body["agent_id"],
            "agent_config_id": body["agent_config_id"],
            "input_text": "hi",
        },
    )
    assert old_ingest.status_code == 401

    # new key does
    new_ingest = client.post(
        "/v1/traces",
        headers={"Authorization": f"Bearer {new_key}"},
        json={
            "trace_ref": "regen-test-new-key",
            "agent_id": body["agent_id"],
            "agent_config_id": body["agent_config_id"],
            "input_text": "hi",
        },
    )
    assert new_ingest.status_code == 202

    from kosma_api.models.organization import Organization
    from kosma_api.models.project import Project

    project = db_session.get(Project, uuid.UUID(body["id"]))
    org_id = project.organization_id
    db_session.delete(project)
    db_session.commit()
    org = db_session.get(Organization, org_id)
    if org is not None:
        db_session.delete(org)
        db_session.commit()
