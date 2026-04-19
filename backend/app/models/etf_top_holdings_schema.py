from datetime import date
from uuid import UUID
from pydantic import BaseModel
from app.models.top_holding_schema import TopHoldingSchema


class ETFTopHoldingsSchema(BaseModel):
    etf_id: UUID
    etf_name: str
    as_of_date: date
    holdings: list[TopHoldingSchema]