def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "A API está saudável.",
        "result": {"status": "ok"},
    }
