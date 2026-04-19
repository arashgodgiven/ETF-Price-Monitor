import io
import uuid
from datetime import date

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ETFNotFoundError,
    InvalidCSVError,
    UnknownStockNameError,
)
from app.core.logging import get_logger
from app.models.schemas import (
    ConstituentSchema,
    ETFPriceHistorySchema,
    ETFSummarySchema,
    ETFTopHoldingsSchema,
    PricePointSchema,
    TopHoldingSchema,
)

logger = get_logger(__name__)

# ─────────────────────────────────────────────
# CSV validation constants
# ─────────────────────────────────────────────
REQUIRED_COLUMNS = {"name", "weight"}


class ETFService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ─────────────────────────────────────────
    # Upload
    # ─────────────────────────────────────────

    async def upload_etf(
        self,
        file_bytes: bytes,
        filename: str,
        session_id: uuid.UUID,
    ) -> ETFSummarySchema:
        """
        Parse, validate, and persist an uploaded ETF CSV.
        Returns the saved ETF with constituent latest prices attached.
        """
        df = self._parse_and_validate_csv(file_bytes, filename)
        stock_names = df["name"].str.upper().tolist()

        # Validate all stock names exist in the price DB
        known_stock_names = await self._get_known_stock_names()
        unknown = set(stock_names) - known_stock_names
        if unknown:
            raise UnknownStockNameError(
                f"Stock names not found in price database: {sorted(unknown)}"
            )

        # Derive ETF name from filename (strip extension)
        etf_name = filename.rsplit(".", 1)[0].upper()

        # Validate ETF name length
        MAX_ETF_NAME_LENGTH = 50
        if len(etf_name) > MAX_ETF_NAME_LENGTH:
            raise InvalidCSVError(
                f"ETF name derived from filename must be {MAX_ETF_NAME_LENGTH} "
                f"characters or fewer. Got: '{etf_name}' ({len(etf_name)} characters). "
                f"Please rename your file."
            )

        # Persist ETF + constituents in a single transaction
        etf_id = uuid.uuid4()
        await self._db.execute(
            text(
                "INSERT INTO etfs (id, session_id, name) VALUES (:id, :session_id, :name)"
            ),
            {"id": str(etf_id), "session_id": str(session_id), "name": etf_name},
        )
        await self._db.execute(
            text(
                "INSERT INTO etf_constituents (etf_id, stock_name, weight) "
                "VALUES (:etf_id, :stock_name, :weight)"
            ),
            [
                {
                    "etf_id": str(etf_id),
                    "stock_name": row["name"].upper(),
                    "weight": float(row["weight"]),
                }
                for _, row in df.iterrows()
            ],
        )

        logger.info(
            "ETF uploaded",
            extra={
                "etf_id": str(etf_id),
                "etf_name": etf_name,
                "constituents": len(df),
            },
        )

        return await self.get_etf_summary(etf_id)

    # ─────────────────────────────────────────
    # Summary (constituents + latest prices)
    # ─────────────────────────────────────────

    async def get_etf_summary(self, etf_id: uuid.UUID) -> ETFSummarySchema:
        result = await self._db.execute(
            text("SELECT id, name FROM etfs WHERE id = :id"),
            {"id": str(etf_id)},
        )
        row = result.mappings().first()
        if not row:
            raise ETFNotFoundError(f"ETF {etf_id} not found.")

        constituents = await self._get_constituents_with_latest_price(etf_id)

        return ETFSummarySchema(
            id=row["id"],
            name=row["name"],
            constituents=constituents,
        )

    # ─────────────────────────────────────────
    # Price history
    # ─────────────────────────────────────────

    async def get_price_history(
        self,
        etf_id: uuid.UUID,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> ETFPriceHistorySchema:
        """
        Reconstruct the ETF price time series as:
            ETF_price(t) = SUM(weight_i * price_i(t))
        using a single SQL query for efficiency.
        """
        etf_row = await self._get_etf_or_raise(etf_id)

        date_filter = ""
        params: dict = {"etf_id": str(etf_id)}
        if date_from:
            date_filter += " AND p.date >= :date_from"
            params["date_from"] = date_from
        if date_to:
            date_filter += " AND p.date <= :date_to"
            params["date_to"] = date_to

        query = text(f"""
            SELECT
                p.date,
                SUM(ec.weight * p.close_price) AS etf_price
            FROM etf_constituents ec
            JOIN prices p ON p.stock_name = ec.stock_name
            WHERE ec.etf_id = :etf_id
            {date_filter}
            GROUP BY p.date
            ORDER BY p.date ASC
        """)

        result = await self._db.execute(query, params)
        rows = result.mappings().all()

        return ETFPriceHistorySchema(
            etf_id=etf_id,
            etf_name=etf_row["name"],
            series=[
                PricePointSchema(date=r["date"], price=round(float(r["etf_price"]), 4))
                for r in rows
            ],
        )

    # ─────────────────────────────────────────
    # Top holdings
    # ─────────────────────────────────────────

    async def get_top_holdings(
        self, etf_id: uuid.UUID, limit: int = 5
    ) -> ETFTopHoldingsSchema:
        """
        Top N holdings by holding size = weight * latest_close_price.
        Latest close = most recent date in the prices table.
        """
        etf_row = await self._get_etf_or_raise(etf_id)

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
        rows = result.mappings().all()

        as_of = rows[0]["as_of_date"] if rows else date.today()

        return ETFTopHoldingsSchema(
            etf_id=etf_id,
            etf_name=etf_row["name"],
            as_of_date=as_of,
            holdings=[
                TopHoldingSchema(
                    stock_name=r["stock_name"],
                    weight=float(r["weight"]),
                    latest_price=float(r["latest_price"]),
                    holding_size=round(float(r["holding_size"]), 4),
                )
                for r in rows
            ],
        )

    # ─────────────────────────────────────────
    # Session ETFs
    # ─────────────────────────────────────────

    async def get_session_etfs(self, session_id: uuid.UUID) -> list[ETFSummarySchema]:
        result = await self._db.execute(
            text(
                "SELECT id FROM etfs WHERE session_id = :sid ORDER BY uploaded_at DESC"
            ),
            {"sid": str(session_id)},
        )
        etf_ids = [row["id"] for row in result.mappings().all()]
        return [await self.get_etf_summary(uuid.UUID(str(eid))) for eid in etf_ids]

    # ─────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────

    def _parse_and_validate_csv(self, file_bytes: bytes, filename: str) -> pd.DataFrame:
        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
        except Exception as exc:
            raise InvalidCSVError(f"Could not parse CSV: {exc}") from exc

        df.columns = [c.strip().lower() for c in df.columns]

        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise InvalidCSVError(
                f"CSV missing required columns: {sorted(missing)}. "
                f"Expected columns: {sorted(REQUIRED_COLUMNS)}"
            )

        if df.empty:
            raise InvalidCSVError("CSV contains no data rows.")

        if df["weight"].isnull().any() or df["name"].isnull().any():
            raise InvalidCSVError("CSV contains null values in 'name' or 'weight'.")

        df["weight"] = pd.to_numeric(df["weight"], errors="coerce")
        if df["weight"].isnull().any():
            raise InvalidCSVError("'weight' column contains non-numeric values.")

        invalid_weights = df[(df["weight"] <= 0) | (df["weight"] > 1)]
        if not invalid_weights.empty:
            raise InvalidCSVError("All weights must be between 0 (exclusive) and 1 (inclusive).")

        # Stock Name length validation
        MAX_STOCK_NAME_LENGTH = 20
        too_long = df[df["name"].str.len() > MAX_STOCK_NAME_LENGTH]["name"].tolist()
        if too_long:
            raise InvalidCSVError(
                f"Stock name symbols must be {MAX_STOCK_NAME_LENGTH} characters or fewer. "
                f"Found: {too_long}"
            )

        return df[["name", "weight"]].copy()

    async def _get_known_stock_names(self) -> set[str]:
        result = await self._db.execute(
            text("SELECT DISTINCT stock_name FROM prices")
        )
        return {row["stock_name"] for row in result.mappings().all()}

    async def _get_etf_or_raise(self, etf_id: uuid.UUID) -> dict:
        result = await self._db.execute(
            text("SELECT id, name FROM etfs WHERE id = :id"),
            {"id": str(etf_id)},
        )
        row = result.mappings().first()
        if not row:
            raise ETFNotFoundError(f"ETF {etf_id} not found.")
        return dict(row)

    async def _get_constituents_with_latest_price(
        self, etf_id: uuid.UUID
    ) -> list[ConstituentSchema]:
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
        return [
            ConstituentSchema(
                stock_name=r["stock_name"],
                weight=float(r["weight"]),
                latest_price=float(r["latest_price"]) if r["latest_price"] else None,
            )
            for r in result.mappings().all()
        ]