"""POST /v1/agents/{id}/configs: the actual missing piece behind "Propose a
Change" - a fresh self-serve project starts with only its baseline config,
and without this endpoint there is no way to ever create a candidate."""


def _login(client, settings):
    client.post("/v1/auth/login", json={"secret": settings.dashboard_secret})


def test_create_config_requires_auth(client, seeded_project):
    response = client.post(
        f"/v1/agents/{seeded_project['agent_id']}/configs",
        json={"kind": "prompt", "version_label": "v2"},
    )
    assert response.status_code == 401


def test_create_config_returns_it_and_lists_it_on_the_agent(client, settings, seeded_project):
    _login(client, settings)
    create = client.post(
        f"/v1/agents/{seeded_project['agent_id']}/configs",
        json={
            "kind": "prompt",
            "version_label": "v2-concise",
            "prompt_text": "Be extra concise.",
            "model_provider": "mock",
            "model_name": "mock-v1",
        },
    )
    assert create.status_code == 201
    body = create.json()
    assert body["version_label"] == "v2-concise"
    assert body["is_baseline"] is False
    assert body["agent_id"] == str(seeded_project["agent_id"])

    listed = client.get("/v1/agents")
    assert listed.status_code == 200
    agent = next(a for a in listed.json()["items"] if a["id"] == str(seeded_project["agent_id"]))
    labels = [c["version_label"] for c in agent["configs"]]
    assert "v2-concise" in labels


def test_create_config_rejects_unknown_agent(client, settings):
    import uuid

    _login(client, settings)
    response = client.post(
        f"/v1/agents/{uuid.uuid4()}/configs",
        json={"kind": "prompt", "version_label": "v2"},
    )
    assert response.status_code == 404


def test_create_config_rejects_invalid_kind(client, settings, seeded_project):
    _login(client, settings)
    response = client.post(
        f"/v1/agents/{seeded_project['agent_id']}/configs",
        json={"kind": "not-a-real-kind", "version_label": "v2"},
    )
    assert response.status_code == 400


def test_create_config_rejects_blank_version_label(client, settings, seeded_project):
    _login(client, settings)
    response = client.post(
        f"/v1/agents/{seeded_project['agent_id']}/configs",
        json={"kind": "prompt", "version_label": "   "},
    )
    assert response.status_code == 400
