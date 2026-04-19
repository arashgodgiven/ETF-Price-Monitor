from pydantic import BaseModel


class ConstituentSchema(BaseModel):
    stock_name: str
    weight: float
    latest_price: float | None = None

    model_config = {"from_attributes": True}