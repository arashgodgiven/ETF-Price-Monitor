import pytest


@pytest.mark.integration
class TestHealthEndpoint:
    async def test_health_returns_200(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

    async def test_health_status_is_ok(self, client):
        response = await client.get("/api/v1/health")
        assert response.json()["status"] == "ok"

    async def test_health_db_is_reachable(self, client):
        response = await client.get("/api/v1/health")
        assert response.json()["db"] == "ok"

    async def test_health_returns_version(self, client):
        response = await client.get("/api/v1/health")
        assert "version" in response.json()

    async def test_health_returns_environment(self, client):
        response = await client.get("/api/v1/health")
        assert "environment" in response.json()

    async def test_health_response_schema(self, client):
        response = await client.get("/api/v1/health")
        body = response.json()
        assert set(body.keys()) >= {"status", "db", "version", "environment"}