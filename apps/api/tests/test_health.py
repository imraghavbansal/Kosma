def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_response_carries_request_id_header(client):
    response = client.get("/health")
    assert "x-request-id" in response.headers
