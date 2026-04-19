from pydantic import BaseModel


class HealthSchema(BaseModel):
    status: str
    version: str
    environment: str
    db: str