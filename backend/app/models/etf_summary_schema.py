from uuid import UUID
from pydantic import BaseModel
from app.models.constituent_schema import ConstituentSchema


class ETFSummarySchema(BaseModel):
    id: UUID
    name: str
    constituents: list[ConstituentSchema]

    model_config = {"from_attributes": True}