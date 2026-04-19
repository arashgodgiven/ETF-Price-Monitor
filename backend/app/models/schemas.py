from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

class ConstituentSchema(BaseModel):
	stock_name: str
	weight: float
	lastest_price: float | None = None

	model_config = {"from_attributes": True}

class PricePointSchema(BaseModel):
	date: date
	price: float

class TopHoldingSchema(BaseModel):
	stock_name: str
	weight: float
	latest_price: float
	holding_size: float

class ETFSummarySchema(BaseModel):
	id: UUID
	name: str
	constituents: list[ConstituentSchema]

	model_config = {"from_attributes": True}

class ETFPriceHistorySchema(BaseModel):
	etf_id: UUID
	etf_name: str
	series: list[PricePointSchema]

class ETFPriceHistorySchema(BaseModel):
    etf_id: UUID
    etf_name: str
    series: list[PricePointSchema]

class ETFTopHoldingsSchema(BaseModel):
    etf_id: UUID
    etf_name: str
    as_of_date: date
    holdings: list[TopHoldingSchema]
		
class HealthSchema(BaseModel):
    status: str
    version: str
    environment: str
    db: str
