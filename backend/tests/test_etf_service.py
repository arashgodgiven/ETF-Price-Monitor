import pytest

from app.core.exceptions import InvalidCSVError
from app.services.etf_service import ETFService


def make_csv(content: str) -> bytes:
    return content.strip().encode()


class TestCSVValidation:

    def _parse(self, content: str):
        """Call the private parser directly — no DB needed."""
        svc = ETFService(db=None)
        return svc._parse_and_validate_csv(make_csv(content), "test.csv")

    def test_valid_csv(self):
        df = self._parse("name,weight\nA,0.5\nB,0.5")
        assert len(df) == 2
        assert list(df.columns) == ["name", "weight"]

    def test_missing_weight_column(self):
        with pytest.raises(InvalidCSVError, match="missing required columns"):
            self._parse("name\nA\nB")

    def test_missing_name_column(self):
        with pytest.raises(InvalidCSVError, match="missing required columns"):
            self._parse("weight\n0.5\n0.5")

    def test_empty_csv(self):
        with pytest.raises(InvalidCSVError, match="no data rows"):
            self._parse("name,weight")

    def test_non_numeric_weight(self):
        with pytest.raises(InvalidCSVError, match="non-numeric"):
            self._parse("name,weight\nA,abc\nB,0.5")

    def test_weight_out_of_range(self):
        with pytest.raises(InvalidCSVError, match="between 0"):
            self._parse("name,weight\nA,1.5\nB,0.5")

    def test_null_values(self):
        with pytest.raises(InvalidCSVError, match="null values"):
            self._parse("name,weight\n,0.5\nB,0.3")

    def test_column_names_are_case_insensitive(self):
        df = self._parse("Name,Weight\nA,0.5\nB,0.5")
        assert "name" in df.columns
        assert "weight" in df.columns
