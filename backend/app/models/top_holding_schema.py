from pydantic import BaseModel


class TopHoldingSchema(BaseModel):
    stock_name: str
    weight: float
    latest_price: float
    holding_size: float