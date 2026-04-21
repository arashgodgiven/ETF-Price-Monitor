import pytest
from app.core.exceptions import InvalidCSVError
from app.services.etf_service import ETFService
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import MagicMock


def make_service() -> ETFService:
    mock_db = MagicMock(spec=AsyncSession)
    return ETFService(mock_db)


def make_csv(content: str) -> bytes:
    return content.strip().encode()


@pytest.mark.unit
class TestValidCSV:
    def test_valid_csv_returns_dataframe(self):
        svc = make_service()
        df = svc._parse_and_validate_csv(
            make_csv("name,weight\nA,0.5\nB,0.3\nZ,0.2"), "ETF1.csv"
        )
        assert list(df.columns) == ["name", "weight"]
        assert len(df) == 3

    def test_valid_csv_preserves_weights(self):
        svc = make_service()
        df = svc._parse_and_validate_csv(
            make_csv("name,weight\nA,0.097\nB,0.155"), "ETF1.csv"
        )
        assert abs(df.iloc[0]["weight"] - 0.097) < 1e-6
        assert abs(df.iloc[1]["weight"] - 0.155) < 1e-6

    def test_valid_csv_single_constituent(self):
        svc = make_service()
        df = svc._parse_and_validate_csv(
            make_csv("name,weight\nA,1.0"), "ETF1.csv"
        )
        assert len(df) == 1

    def test_extra_columns_are_ignored(self):
        svc = make_service()
        df = svc._parse_and_validate_csv(
            make_csv("name,weight,sector,country\nA,0.5,Tech,US\nB,0.5,Finance,CA"),
            "ETF1.csv",
        )
        assert list(df.columns) == ["name", "weight"]

    def test_whitespace_in_column_names_stripped(self):
        svc = make_service()
        df = svc._parse_and_validate_csv(
            make_csv("  name  ,  weight  \nA,0.5\nB,0.5"), "ETF1.csv"
        )
        assert "name" in df.columns
        assert "weight" in df.columns

    def test_column_names_case_insensitive(self):
        svc = make_service()
        df = svc._parse_and_validate_csv(
            make_csv("NAME,WEIGHT\nA,0.5\nB,0.5"), "ETF1.csv"
        )
        assert list(df.columns) == ["name", "weight"]

    def test_mixed_case_column_names(self):
        svc = make_service()
        df = svc._parse_and_validate_csv(
            make_csv("Name,Weight\nA,0.5\nB,0.5"), "ETF1.csv"
        )
        assert list(df.columns) == ["name", "weight"]


@pytest.mark.unit
class TestMissingColumns:
    def test_missing_weight_column(self):
        svc = make_service()
        with pytest.raises(InvalidCSVError, match="missing required columns"):
            svc._parse_and_validate_csv(
                make_csv("name\nA\nB"), "ETF1.csv"
            )

    def test_missing_name_column(self):
        svc = make_service()
        with pytest.raises(InvalidCSVError, match="missing required columns"):
            svc._parse_and_validate_csv(
                make_csv("weight\n0.5\n0.5"), "ETF1.csv"
            )

    def test_missing_both_columns(self):
        svc = make_service()
        with pytest.raises(InvalidCSVError, match="missing required columns"):
            svc._parse_and_validate_csv(
                make_csv("ticker,allocation\nA,0.5"), "ETF1.csv"
            )

    def test_empty_file(self):
        svc = make_service()
        with pytest.raises(InvalidCSVError):
            svc._parse_and_validate_csv(b"", "ETF1.csv")

    def test_headers_only_no_data_rows(self):
        svc = make_service()
        with pytest.raises(InvalidCSVError, match="no data rows"):
            svc._parse_and_validate_csv(
                make_csv("name,weight"), "ETF1.csv"
            )


@pytest.mark.unit
class TestWeightValidation:
    def test_weight_zero_is_rejected(self):
        svc = make_service()
        with pytest.raises(InvalidCSVError, match="between 0"):
            svc._parse_and_validate_csv(
                make_csv("name,weight\nA,0.0\nB,0.5"), "ETF1.csv"
            )

    def test_weight_negative_is_rejected(self):
        svc = make_service()
        with pytest.raises(InvalidCSVError, match="between 0"):
            svc._parse_and_validate_csv(
                make_csv("name,weight\nA,-0.1\nB,0.5"), "ETF1.csv"
            )

    def test_weight_greater_than_one_rejected(self):
        svc = make_service()
        with pytest.raises(InvalidCSVError, match="between 0"):
            svc._parse_and_validate_csv(
                make_csv("name,weight\nA,1.1\nB,0.5"), "ETF1.csv"
            )

    def test_weight_exactly_one_accepted(self):
        svc = make_service()
        df = svc._parse_and_validate_csv(
            make_csv("name,weight\nA,1.0"), "ETF1.csv"
        )
        assert len(df) == 1

    def test_weight_very_small_positive_accepted(self):
        svc = make_service()
        df = svc._parse_and_validate_csv(
            make_csv("name,weight\nA,0.001\nB,0.999"), "ETF1.csv"
        )
        assert len(df) == 2

    def test_non_numeric_weight_rejected(self):
        svc = make_service()
        with pytest.raises(InvalidCSVError, match="non-numeric"):
            svc._parse_and_validate_csv(
                make_csv("name,weight\nA,high\nB,0.5"), "ETF1.csv"
            )

    def test_empty_weight_rejected(self):
        svc = make_service()
        with pytest.raises(InvalidCSVError):
            svc._parse_and_validate_csv(
                make_csv("name,weight\nA,\nB,0.5"), "ETF1.csv"
            )

    def test_weights_do_not_need_to_sum_to_one(self):
        svc = make_service()
        df = svc._parse_and_validate_csv(
            make_csv("name,weight\nA,0.3\nB,0.3\nZ,0.3"), "ETF1.csv"
        )
        assert len(df) == 3


@pytest.mark.unit
class TestNullValues:
    def test_null_weight_rejected(self):
        svc = make_service()
        with pytest.raises(InvalidCSVError, match="null"):
            svc._parse_and_validate_csv(
                make_csv("name,weight\nA,\nB,0.5"), "ETF1.csv"
            )

    def test_null_name_rejected(self):
        svc = make_service()
        with pytest.raises(InvalidCSVError, match="null"):
            svc._parse_and_validate_csv(
                make_csv("name,weight\n,0.5\nB,0.5"), "ETF1.csv"
            )


@pytest.mark.unit
class TestStockNameValidation:
    def test_stock_name_too_long_rejected(self):
        svc = make_service()
        long_name = "A" * 21
        with pytest.raises(InvalidCSVError, match="characters or fewer"):
            svc._parse_and_validate_csv(
                make_csv(f"name,weight\n{long_name},0.5"), "ETF1.csv"
            )

    def test_stock_name_exactly_20_chars_accepted(self):
        svc = make_service()
        name_20 = "A" * 20
        df = svc._parse_and_validate_csv(
            make_csv(f"name,weight\n{name_20},0.5"), "ETF1.csv"
        )
        assert len(df) == 1

    def test_multiple_too_long_names_reported(self):
        svc = make_service()
        long_a = "A" * 21
        long_b = "B" * 22
        with pytest.raises(InvalidCSVError, match="characters or fewer"):
            svc._parse_and_validate_csv(
                make_csv(f"name,weight\n{long_a},0.5\n{long_b},0.5"), "ETF1.csv"
            )


@pytest.mark.unit
class TestMalformedCSV:
    def test_completely_invalid_file_content(self):
        svc = make_service()
        with pytest.raises(InvalidCSVError):
            svc._parse_and_validate_csv(b"\x00\x01\x02\x03", "ETF1.csv")

    def test_json_file_rejected(self):
        svc = make_service()
        with pytest.raises(InvalidCSVError):
            svc._parse_and_validate_csv(
                b'{"name": "A", "weight": 0.5}', "ETF1.csv"
            )