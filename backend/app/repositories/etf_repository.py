import uuid
from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger

logger = get_logger(__name__)


class ETFRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_known_stock_names(self) -> set[str]:
        result = await self._db.execute(
            text("SELECT DISTINCT stock_name FROM prices")
        )
        return {row["stock_name"] for row in result.mappings().all()}


    async def insert_etf(
        self,
        etf_id: uuid.UUID,
        session_id: uuid.UUID,
        name: str,
    ) -> None:
        await self._db.execute(
            text(
                "INSERT INTO etfs (id, session_id, name) "
                "VALUES (:id, :session_id, :name)"
            ),
            {"id": str(etf_id), "session_id": str(session_id), "name": name},
        )


    async def insert_constituents(
        self,
        etf_id: uuid.UUID,
        constituents: list[dict],
    ) -> None:
        await self._db.execute(
            text(
                "INSERT INTO etf_constituents (etf_id, stock_name, weight) "
                "VALUES (:etf_id, :stock_name, :weight)"
            ),
            [
                {
                    "etf_id": str(etf_id),
                    "stock_name": c["stock_name"],
                    "weight": c["weight"],
                }
                for c in constituents
            ],
        )


    async def get_etf_by_id(self, etf_id: uuid.UUID) -> dict | None:
        result = await self._db.execute(
            text("SELECT id, name FROM etfs WHERE id = :id"),
            {"id": str(etf_id)},
        )
        row = result.mappings().first()
        return dict(row) if row else None


    async def get_etfs_by_session(self, session_id: uuid.UUID) -> list[dict]:
        result = await self._db.execute(
            text(
                "SELECT id FROM etfs "
                "WHERE session_id = :sid "
                "ORDER BY uploaded_at DESC"
            ),
            {"sid": str(session_id)},
        )
        return [dict(row) for row in result.mappings().all()]


    async def get_constituents_with_latest_price(
        self, etf_id: uuid.UUID
    ) -> list[dict]:
        result = await self._db.execute(
            text("""
                WITH latest AS (
                    SELECT stock_name, close_price
                    FROM prices
                    WHERE date = (SELECT MAX(date) FROM prices)
                )
                SELECT
                    ec.stock_name,
                    ec.weight,
                    l.close_price AS latest_price
                FROM etf_constituents ec
                LEFT JOIN latest l ON l.stock_name = ec.stock_name
                WHERE ec.etf_id = :etf_id
                ORDER BY ec.stock_name
            """),
            {"etf_id": str(etf_id)},
        )
        return [dict(row) for row in result.mappings().all()]


    async def get_price_history(
        self,
        etf_id: uuid.UUID,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[dict]:
        date_filter = ""
        params: dict = {"etf_id": str(etf_id)}
        if date_from:
            date_filter += " AND p.date >= :date_from"
            params["date_from"] = date_from
        if date_to:
            date_filter += " AND p.date <= :date_to"
            params["date_to"] = date_to

        result = await self._db.execute(
            text(f"""
                SELECT
                    p.date,
                    SUM(ec.weight * p.close_price) AS etf_price
                FROM etf_constituents ec
                JOIN prices p ON p.stock_name = ec.stock_name
                WHERE ec.etf_id = :etf_id
                {date_filter}
                GROUP BY p.date
                ORDER BY p.date ASC
            """),
            params,
        )
        return [dict(row) for row in result.mappings().all()]


    async def get_top_holdings(
        self, etf_id: uuid.UUID, limit: int = 5
    ) -> list[dict]:
        result = await self._db.execute(
            text("""
                WITH latest AS (
                    SELECT stock_name, close_price, date
                    FROM prices
                    WHERE date = (SELECT MAX(date) FROM prices)
                )
                SELECT
                    ec.stock_name,
                    ec.weight,
                    l.close_price       AS latest_price,
                    l.date              AS as_of_date,
                    ec.weight * l.close_price AS holding_size
                FROM etf_constituents ec
                JOIN latest l ON l.stock_name = ec.stock_name
                WHERE ec.etf_id = :etf_id
                ORDER BY holding_size DESC
                LIMIT :limit
            """),
            {"etf_id": str(etf_id), "limit": limit},
        )
        return [dict(row) for row in result.mappings().all()]
    

    async def delete_etf(self, etf_id: uuid.UUID, session_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            text(
                "DELETE FROM etfs WHERE id = :id AND session_id = :session_id "
                "RETURNING id"
            ),
            {"id": str(etf_id), "session_id": str(session_id)},
        )
        return result.first() is not None
    

    async def get_stock_price_history(
        self,
        stock_name: str,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[dict]:
        date_filter = ""
        params: dict = {"stock_name": stock_name}
        if date_from:
            date_filter += " AND date >= :date_from"
            params["date_from"] = date_from
        if date_to:
            date_filter += " AND date <= :date_to"
            params["date_to"] = date_to

        result = await self._db.execute(
            text(f"""
                SELECT date, close_price
                FROM prices
                WHERE stock_name = :stock_name
                {date_filter}
                ORDER BY date ASC
            """),
            params,
        )
        return [dict(row) for row in result.mappings().all()]