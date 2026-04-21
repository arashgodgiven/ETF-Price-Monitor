"""
tests/conftest.py — shared fixtures with NO database dependency.
DB fixtures live in tests/integration/conftest.py
"""

import pytest


def make_csv(content: str) -> bytes:
    return content.strip().encode()


@pytest.fixture
def valid_etf_csv() -> bytes:
    return make_csv("name,weight\nA,0.5\nB,0.3\nZ,0.2")