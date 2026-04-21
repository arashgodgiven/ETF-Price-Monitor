import pytest


def csv_file(content: str, filename: str = "ETF1.csv"):
    return {"file": (filename, content.strip().encode(), "text/csv")}


@pytest.mark.integration
class TestSessionEndpoint:
    async def test_empty_session_returns_empty_list(self, client):
        response = await client.get("/api/v1/etf/session")
        assert response.status_code == 200
        assert response.json() == []

    async def test_session_contains_uploaded_etf(self, client):
        await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5"),
        )
        response = await client.get("/api/v1/etf/session")
        assert len(response.json()) == 1

    async def test_session_contains_multiple_uploaded_etfs(self, client):
        await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5", filename="ETF1.csv"),
        )
        await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.3\nZ,0.7", filename="ETF2.csv"),
        )
        response = await client.get("/api/v1/etf/session")
        assert len(response.json()) == 2

    async def test_session_etf_has_correct_name(self, client):
        await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5", filename="MyFund.csv"),
        )
        response = await client.get("/api/v1/etf/session")
        assert response.json()[0]["name"] == "MYFUND"

    async def test_session_etf_has_constituents(self, client):
        await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.3\nZ,0.2"),
        )
        response = await client.get("/api/v1/etf/session")
        assert len(response.json()[0]["constituents"]) == 3