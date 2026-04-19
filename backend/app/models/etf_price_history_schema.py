from datetime import date
from uuid import UUID
from pydantic import BaseModel
from app.models.price_point_schema import PricePointSchema


class ETFPriceHistorySchema(BaseModel):
    etf_id: UUID
    etf_name: str
    series: list[PricePointSchema]