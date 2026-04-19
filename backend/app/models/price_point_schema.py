from datetime import date
from pydantic import BaseModel


class PricePointSchema(BaseModel):
    date: date
    price: float