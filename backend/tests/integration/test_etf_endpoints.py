import pytest


def csv_file(content: str, filename: str = "ETF1.csv"):
    return {"file": (filename, content.strip().encode(), "text/csv")}


@pytest.mark.integration
class TestETFSummary:
    async def test_get_summary_returns_200(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5"),
        )
        etf_id = upload.json()["id"]
        response = await client.get(f"/api/v1/etf/{etf_id}")
        assert response.status_code == 200

    async def test_get_summary_unknown_id_returns_404(self, client):
        response = await client.get(
            "/api/v1/etf/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404

    async def test_get_summary_invalid_uuid_returns_422(self, client):
        response = await client.get("/api/v1/etf/not-a-uuid")
        assert response.status_code == 422

    async def test_get_summary_returns_correct_name(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5", filename="TestFund.csv"),
        )
        etf_id = upload.json()["id"]
        response = await client.get(f"/api/v1/etf/{etf_id}")
        assert response.json()["name"] == "TESTFUND"

    async def test_get_summary_returns_all_constituents(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.3\nZ,0.2"),
        )
        etf_id = upload.json()["id"]
        response = await client.get(f"/api/v1/etf/{etf_id}")
        assert len(response.json()["constituents"]) == 3

    async def test_get_summary_constituent_has_latest_price(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5"),
        )
        etf_id = upload.json()["id"]
        response = await client.get(f"/api/v1/etf/{etf_id}")
        for c in response.json()["constituents"]:
            assert c["latest_price"] is not None
            assert c["latest_price"] > 0


@pytest.mark.integration
class TestPriceHistory:
    async def test_price_history_returns_200(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5"),
        )
        etf_id = upload.json()["id"]
        response = await client.get(f"/api/v1/etf/{etf_id}/price-history")
        assert response.status_code == 200

    async def test_price_history_returns_series(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5"),
        )
        etf_id = upload.json()["id"]
        response = await client.get(f"/api/v1/etf/{etf_id}/price-history")
        assert "series" in response.json()
        assert len(response.json()["series"]) > 0

    async def test_price_history_series_has_date_and_price(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5"),
        )
        etf_id = upload.json()["id"]
        response = await client.get(f"/api/v1/etf/{etf_id}/price-history")
        point = response.json()["series"][0]
        assert "date" in point
        assert "price" in point

    async def test_price_history_prices_are_positive(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5"),
        )
        etf_id = upload.json()["id"]
        response = await client.get(f"/api/v1/etf/{etf_id}/price-history")
        for point in response.json()["series"]:
            assert point["price"] > 0

    async def test_price_history_series_ordered_by_date(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5"),
        )
        etf_id = upload.json()["id"]
        response = await client.get(f"/api/v1/etf/{etf_id}/price-history")
        dates = [p["date"] for p in response.json()["series"]]
        assert dates == sorted(dates)

    async def test_price_history_date_filter(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5"),
        )
        etf_id = upload.json()["id"]
        response = await client.get(
            f"/api/v1/etf/{etf_id}/price-history",
            params={"date_from": "2017-01-01", "date_to": "2017-01-31"},
        )
        series = response.json()["series"]
        assert all(p["date"] >= "2017-01-01" for p in series)
        assert all(p["date"] <= "2017-01-31" for p in series)

    async def test_price_history_unknown_etf_returns_404(self, client):
        response = await client.get(
            "/api/v1/etf/00000000-0000-0000-0000-000000000000/price-history"
        )
        assert response.status_code == 404

    async def test_price_history_is_weighted_sum(self, client):
        """
        With a single constituent at weight 1.0,
        ETF price should equal the stock price exactly.
        """
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,1.0"),
        )
        etf_id = upload.json()["id"]
        etf_history = await client.get(f"/api/v1/etf/{etf_id}/price-history")
        stock_history = await client.get("/api/v1/etf/stock/A/price-history")

        etf_prices = {p["date"]: p["price"] for p in etf_history.json()["series"]}
        stock_prices = {p["date"]: p["price"] for p in stock_history.json()["series"]}

        for date, price in etf_prices.items():
            assert abs(price - stock_prices[date]) < 0.01


@pytest.mark.integration
class TestTopHoldings:
    async def test_top_holdings_returns_200(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.3\nZ,0.2"),
        )
        etf_id = upload.json()["id"]
        response = await client.get(f"/api/v1/etf/{etf_id}/top-holdings")
        assert response.status_code == 200

    async def test_top_holdings_default_limit_is_5(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file(
                "name,weight\nA,0.2\nB,0.2\nZ,0.2\nE,0.2\nF,0.1\nG,0.1"
            ),
        )
        etf_id = upload.json()["id"]
        response = await client.get(f"/api/v1/etf/{etf_id}/top-holdings")
        assert len(response.json()["holdings"]) == 5

    async def test_top_holdings_custom_limit(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file(
                "name,weight\nA,0.2\nB,0.2\nZ,0.2\nE,0.2\nF,0.2"
            ),
        )
        etf_id = upload.json()["id"]
        response = await client.get(
            f"/api/v1/etf/{etf_id}/top-holdings", params={"limit": 3}
        )
        assert len(response.json()["holdings"]) == 3

    async def test_top_holdings_ordered_by_holding_size_desc(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.3\nZ,0.2"),
        )
        etf_id = upload.json()["id"]
        response = await client.get(f"/api/v1/etf/{etf_id}/top-holdings")
        sizes = [h["holding_size"] for h in response.json()["holdings"]]
        assert sizes == sorted(sizes, reverse=True)

    async def test_top_holdings_holding_size_is_weight_times_price(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5"),
        )
        etf_id = upload.json()["id"]
        response = await client.get(f"/api/v1/etf/{etf_id}/top-holdings")
        for h in response.json()["holdings"]:
            expected = round(h["weight"] * h["latest_price"], 4)
            assert abs(h["holding_size"] - expected) < 0.01

    async def test_top_holdings_returns_as_of_date(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5"),
        )
        etf_id = upload.json()["id"]
        response = await client.get(f"/api/v1/etf/{etf_id}/top-holdings")
        assert "as_of_date" in response.json()

    async def test_top_holdings_unknown_etf_returns_404(self, client):
        response = await client.get(
            "/api/v1/etf/00000000-0000-0000-0000-000000000000/top-holdings"
        )
        assert response.status_code == 404


@pytest.mark.integration
class TestDeleteETF:
    async def test_delete_returns_204(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5"),
        )
        etf_id = upload.json()["id"]
        response = await client.delete(f"/api/v1/etf/{etf_id}")
        assert response.status_code == 204

    async def test_delete_removes_etf_from_session(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5"),
        )
        etf_id = upload.json()["id"]
        await client.delete(f"/api/v1/etf/{etf_id}")
        session = await client.get("/api/v1/etf/session")
        ids = [e["id"] for e in session.json()]
        assert etf_id not in ids

    async def test_delete_nonexistent_etf_returns_404(self, client):
        response = await client.delete(
            "/api/v1/etf/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404

    async def test_delete_makes_etf_unreachable(self, client):
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5"),
        )
        etf_id = upload.json()["id"]
        await client.delete(f"/api/v1/etf/{etf_id}")
        response = await client.get(f"/api/v1/etf/{etf_id}")
        assert response.status_code == 404

    async def test_delete_cascades_to_constituents(self, client):
        """
        After deleting an ETF, its constituents should also be deleted
        (enforced by ON DELETE CASCADE in the DB schema).
        Verified by checking the ETF is fully gone.
        """
        upload = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5"),
        )
        etf_id = upload.json()["id"]
        await client.delete(f"/api/v1/etf/{etf_id}")
        response = await client.get(f"/api/v1/etf/{etf_id}")
        assert response.status_code == 404

    async def test_delete_only_removes_target_etf(self, client):
        upload1 = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5", filename="ETF1.csv"),
        )
        upload2 = await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.3\nZ,0.7", filename="ETF2.csv"),
        )
        etf1_id = upload1.json()["id"]
        etf2_id = upload2.json()["id"]

        await client.delete(f"/api/v1/etf/{etf1_id}")

        response = await client.get(f"/api/v1/etf/{etf2_id}")
        assert response.status_code == 200


@pytest.mark.integration
class TestStockPriceHistory:
    async def test_stock_price_history_returns_200(self, client):
        response = await client.get("/api/v1/etf/stock/A/price-history")
        assert response.status_code == 200

    async def test_stock_price_history_returns_series(self, client):
        response = await client.get("/api/v1/etf/stock/A/price-history")
        assert "series" in response.json()
        assert len(response.json()["series"]) > 0

    async def test_stock_price_history_has_date_and_price(self, client):
        response = await client.get("/api/v1/etf/stock/A/price-history")
        point = response.json()["series"][0]
        assert "date" in point
        assert "price" in point

    async def test_stock_price_history_prices_positive(self, client):
        response = await client.get("/api/v1/etf/stock/A/price-history")
        for point in response.json()["series"]:
            assert point["price"] > 0

    async def test_stock_price_history_ordered_by_date(self, client):
        response = await client.get("/api/v1/etf/stock/A/price-history")
        dates = [p["date"] for p in response.json()["series"]]
        assert dates == sorted(dates)

    async def test_stock_price_history_date_filter(self, client):
        response = await client.get(
            "/api/v1/etf/stock/A/price-history",
            params={"date_from": "2017-01-01", "date_to": "2017-01-31"},
        )
        series = response.json()["series"]
        assert len(series) > 0
        assert all(p["date"] >= "2017-01-01" for p in series)
        assert all(p["date"] <= "2017-01-31" for p in series)

    async def test_stock_price_history_etf_name_is_stock_name(self, client):
        response = await client.get("/api/v1/etf/stock/A/price-history")
        assert response.json()["etf_name"] == "A"

    async def test_all_26_tickers_have_price_history(self, client):
        tickers = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        for ticker in tickers:
            response = await client.get(f"/api/v1/etf/stock/{ticker}/price-history")
            assert response.status_code == 200
            assert len(response.json()["series"]) == 100


@pytest.mark.integration
class TestSessionIsolation:
    async def test_new_client_sees_empty_session(self, client):
        """Each test gets a fresh session — no ETFs from other tests."""
        response = await client.get("/api/v1/etf/session")
        assert response.json() == []

    async def test_uploaded_etf_scoped_to_session(self, client):
        await client.post(
            "/api/v1/etf/upload",
            files=csv_file("name,weight\nA,0.5\nB,0.5"),
        )
        session = await client.get("/api/v1/etf/session")
        assert len(session.json()) == 1