def test_public_stats_requires_no_auth(client):
    response = client.get("/v1/public/stats")
    assert response.status_code == 200
    body = response.json()
    assert "total_traces" in body
    assert "total_analyzed_changes" in body
    assert isinstance(body["total_traces"], int)
