import os
from datetime import datetime
from typing import AsyncGenerator

import pandas as pd
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://etf_user:etf_password@localhost:5432/etf_monitor_test",
)

TEST_DATABASE_URL_SYNC = TEST_DATABASE_URL.replace("+asyncpg", "")

os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.main import create_app

def _setup_db():
    engine = create_engine(TEST_DATABASE_URL_SYNC)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS etf_constituents CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS etfs CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS prices CASCADE"))
        conn.execute(text("""
            CREATE TABLE prices (
                date        DATE          NOT NULL,
                stock_name  TEXT          NOT NULL,
                close_price NUMERIC(12,4) NOT NULL,
                PRIMARY KEY (date, stock_name)
            )
        """))
        conn.execute(text("""
            CREATE TABLE etfs (
                id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id  UUID        NOT NULL,
                name        TEXT        NOT NULL,
                uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """))
        conn.execute(text("""
            CREATE TABLE etf_constituents (
                etf_id     UUID         NOT NULL REFERENCES etfs(id) ON DELETE CASCADE,
                stock_name TEXT         NOT NULL,
                weight     NUMERIC(8,6) NOT NULL,
                PRIMARY KEY (etf_id, stock_name)
            )
        """))

        prices_csv = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "db", "prices.csv"
        )
        df = pd.read_csv(prices_csv)
        rows = []
        for _, row in df.iterrows():
            for col in df.columns[1:]:
                rows.append({
                    "date": datetime.strptime(row["DATE"], "%Y-%m-%d").date(),
                    "stock_name": col,
                    "close_price": float(row[col]),
                })
        conn.execute(
            text(
                "INSERT INTO prices (date, stock_name, close_price) "
                "VALUES (:date, :stock_name, :close_price) "
                "ON CONFLICT DO NOTHING"
            ),
            rows,
        )
    engine.dispose()
    print("✓ Test DB ready")


_setup_db()

_async_engine = create_async_engine(TEST_DATABASE_URL, echo=False)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    async with _async_engine.begin() as conn:
        await conn.execute(text("DELETE FROM etfs"))