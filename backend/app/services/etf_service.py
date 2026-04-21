import io
import uuid
import asyncio
from functools import partial

from datetime import date

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ETFNotFoundError,
    InvalidCSVError,
    UnknownStockNameError,
)
from app.core.logging import get_logger
from app.models import (
    ConstituentSchema,
    ETFPriceHistorySchema,
    ETFSummarySchema,
    ETFTopHoldingsSchema,
    PricePointSchema,
    TopHoldingSchema,
)
from app.repositories.etf_repository import ETFRepository

logger = get_logger(__name__)

REQUIRED_COLUMNS = {"name", "weight"}


class ETFService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = ETFRepository(db)

    # ─────────────────────────────────────────
    # Upload
    # ─────────────────────────────────────────

    async def upload_etf(
        self,
        file_bytes: bytes,
        filename: str,
        session_id: uuid.UUID,
    ) -> ETFSummarySchema:
        loop = asyncio.get_running_loop()
        df = await loop.run_in_executor(
            None,
            partial(self._parse_and_validate_csv, file_bytes, filename)
        )

        stock_names = df["name"].str.upper().tolist()

        known_stock_names = await self._repo.get_known_stock_names()
        unknown = set(stock_names) - known_stock_names
        if unknown:
            raise UnknownStockNameError(
                f"Stock names not found in price database: {sorted(unknown)}"
            )

        etf_name = filename.rsplit(".", 1)[0].upper()
        MAX_ETF_NAME_LENGTH = 50
        if len(etf_name) > MAX_ETF_NAME_LENGTH:
            raise InvalidCSVError(
                f"ETF name must be {MAX_ETF_NAME_LENGTH} characters or fewer. "
                f"Got: '{etf_name}' ({len(etf_name)} characters). "
                f"Please rename your file."
            )

        etf_id = uuid.uuid4()
        await self._repo.insert_etf(etf_id, session_id, etf_name)
        await self._repo.insert_constituents(
            etf_id,
            [
                {
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
    # Summary
    # ─────────────────────────────────────────

    async def get_etf_summary(self, etf_id: uuid.UUID) -> ETFSummarySchema:
        row = await self._repo.get_etf_by_id(etf_id)
        if not row:
            raise ETFNotFoundError(f"ETF {etf_id} not found.")

        constituents = await self._repo.get_constituents_with_latest_price(etf_id)

        return ETFSummarySchema(
            id=row["id"],
            name=row["name"],
            constituents=[
                ConstituentSchema(
                    stock_name=c["stock_name"],
                    weight=float(c["weight"]),
                    latest_price=float(c["latest_price"]) if c["latest_price"] else None,
                )
                for c in constituents
            ],
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
        row = await self._repo.get_etf_by_id(etf_id)
        if not row:
            raise ETFNotFoundError(f"ETF {etf_id} not found.")

        rows = await self._repo.get_price_history(etf_id, date_from, date_to)

        return ETFPriceHistorySchema(
            etf_id=etf_id,
            etf_name=row["name"],
            series=[
                PricePointSchema(
                    date=r["date"],
                    price=round(float(r["etf_price"]), 4),
                )
                for r in rows
            ],
        )

    # ─────────────────────────────────────────
    # Top holdings
    # ─────────────────────────────────────────

    async def get_top_holdings(
        self, etf_id: uuid.UUID, limit: int = 5
    ) -> ETFTopHoldingsSchema:
        row = await self._repo.get_etf_by_id(etf_id)
        if not row:
            raise ETFNotFoundError(f"ETF {etf_id} not found.")

        rows = await self._repo.get_top_holdings(etf_id, limit)
        as_of = rows[0]["as_of_date"] if rows else date.today()

        return ETFTopHoldingsSchema(
            etf_id=etf_id,
            etf_name=row["name"],
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

    async def get_session_etfs(
        self, session_id: uuid.UUID
    ) -> list[ETFSummarySchema]:
        rows = await self._repo.get_etfs_by_session(session_id)
        return [
            await self.get_etf_summary(uuid.UUID(str(r["id"])))
            for r in rows
        ]

    # ─────────────────────────────────────────
    # Private — CSV validation
    # ─────────────────────────────────────────

    def _parse_and_validate_csv(
        self, file_bytes: bytes, filename: str
    ) -> pd.DataFrame:
        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
        except Exception as exc:
            raise InvalidCSVError(f"Could not parse CSV: {exc}") from exc

        df.columns = [c.strip().lower() for c in df.columns]

        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise InvalidCSVError(
                f"CSV missing required columns: {sorted(missing)}. "
                f"Expected: {sorted(REQUIRED_COLUMNS)}"
            )

        if df.empty:
            raise InvalidCSVError("CSV contains no data rows.")

        if df["weight"].isnull().any() or df["name"].isnull().any():
            raise InvalidCSVError(
                "CSV contains null values in 'name' or 'weight'."
            )

        df["weight"] = pd.to_numeric(df["weight"], errors="coerce")
        if df["weight"].isnull().any():
            raise InvalidCSVError(
                "'weight' column contains non-numeric values."
            )

        invalid_weights = df[(df["weight"] <= 0) | (df["weight"] > 1)]
        if not invalid_weights.empty:
            raise InvalidCSVError(
                "All weights must be between 0 (exclusive) and 1 (inclusive)."
            )

        MAX_STOCK_NAME_LENGTH = 20
        too_long = df[df["name"].str.len() > MAX_STOCK_NAME_LENGTH]["name"].tolist()
        if too_long:
            raise InvalidCSVError(
                f"Stock names must be {MAX_STOCK_NAME_LENGTH} characters or fewer. "
                f"Found: {too_long}"
            )

        return df[["name", "weight"]].copy()
    
    # ─────────────────────────────────────────
    # Delete ETF
    # ─────────────────────────────────────────

    async def delete_etf(
        self, etf_id: uuid.UUID, session_id: uuid.UUID
    ) -> None:
        deleted = await self._repo.delete_etf(etf_id, session_id)
        if not deleted:
            raise ETFNotFoundError(
                f"ETF {etf_id} not found or does not belong to this session."
            )
        logger.info(
            "ETF deleted",
            extra={"etf_id": str(etf_id)},
        )

    # ─────────────────────────────────────────
    # Get Stock Price History
    # ─────────────────────────────────────────

    async def get_stock_price_history(
        self,
        stock_name: str,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> ETFPriceHistorySchema:
        rows = await self._repo.get_stock_price_history(
            stock_name, date_from, date_to
        )
        return ETFPriceHistorySchema(
            etf_id=uuid.uuid4(),  # placeholder — not an ETF
            etf_name=stock_name,
            series=[
                PricePointSchema(
                    date=r["date"],
                    price=round(float(r["close_price"]), 4),
                )
                for r in rows
            ],
        )