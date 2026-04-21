import pytest


def csv_file(content: str, filename: str = "ETF1.csv"):
    return {"file": (filename, content.strip().encode(), "text/csv")}


@pytest.mark.integration
class TestUploadSuccess:
    async def test_upload_returns_201(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.3\nZ,0.2"),
        )
        assert response.status_code == 201

    async def test_upload_returns_etf_id(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.3\nZ,0.2"),
        )
        body = response.json()
        assert "id" in body
        assert len(body["id"]) == 36  # UUID format

    async def test_upload_returns_etf_name_from_filename(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5", filename="MyETF.csv"),
        )
        assert response.json()["name"] == "MYETF"

    async def test_upload_returns_constituents(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.3\nZ,0.2"),
        )
        constituents = response.json()["constituents"]
        assert len(constituents) == 3

    async def test_upload_constituent_has_correct_fields(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5"),
        )
        c = response.json()["constituents"][0]
        assert "stock_name" in c
        assert "weight" in c
        assert "latest_price" in c

    async def test_upload_constituent_weight_matches_csv(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.097\nB,0.155\nZ,0.748"),
        )
        constituents = {
            c["stock_name"]: c["weight"]
            for c in response.json()["constituents"]
        }
        assert abs(constituents["A"] - 0.097) < 1e-4

    async def test_upload_sets_session_cookie(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5"),
        )
        assert "etf_session_id" in response.cookies

    async def test_upload_etf_name_is_uppercased(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5", filename="myetf.csv"),
        )
        assert response.json()["name"] == "MYETF"

    async def test_upload_stock_names_are_uppercased(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\na,0.5\nb,0.5"),
        )
        stock_names = [c["stock_name"] for c in response.json()["constituents"]]
        assert all(s.isupper() for s in stock_names)

    async def test_upload_with_extra_csv_columns(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight,sector\nA,0.5,Tech\nB,0.5,Finance"),
        )
        assert response.status_code == 201

    async def test_upload_multiple_etfs_same_session(self, client):
        await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5", filename="ETF1.csv"),
        )
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.3\nZ,0.7", filename="ETF2.csv"),
        )
        assert response.status_code == 201


@pytest.mark.integration
class TestUploadValidationErrors:
    async def test_upload_missing_weight_column_returns_422(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name\nA\nB"),
        )
        assert response.status_code == 422

    async def test_upload_missing_name_column_returns_422(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("weight\n0.5\n0.5"),
        )
        assert response.status_code == 422

    async def test_upload_empty_csv_returns_422(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight"),
        )
        assert response.status_code == 422

    async def test_upload_unknown_ticker_returns_422(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nZZZZZZZZ,0.5\nYYYYYYYY,0.5"),
        )
        assert response.status_code == 422

    async def test_upload_unknown_ticker_error_message(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nZZZZZZZZ,0.5"),
        )
        assert "ZZZZZZZZ" in response.json()["detail"]

    async def test_upload_weight_greater_than_one_returns_422(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,1.5\nB,0.5"),
        )
        assert response.status_code == 422

    async def test_upload_weight_zero_returns_422(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.0\nB,0.5"),
        )
        assert response.status_code == 422

    async def test_upload_negative_weight_returns_422(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,-0.1\nB,0.5"),
        )
        assert response.status_code == 422

    async def test_upload_non_numeric_weight_returns_422(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,high\nB,0.5"),
        )
        assert response.status_code == 422

    async def test_upload_null_name_returns_422(self, client):
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\n,0.5\nB,0.5"),
        )
        assert response.status_code == 422

    async def test_upload_stock_name_too_long_returns_422(self, client):
        long_name = "A" * 21
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file(f"name,weight\n{long_name},0.5"),
        )
        assert response.status_code == 422

    async def test_upload_etf_name_too_long_returns_422(self, client):
        long_filename = "A" * 51 + ".csv"
        response = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5", filename=long_filename),
        )
        assert response.status_code == 422

    async def test_upload_no_file_returns_422(self, client):
        response = await client.post("/api/v1/etf/upload")
        assert response.status_code == 422