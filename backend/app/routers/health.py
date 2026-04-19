from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import get_db_session
from app.models.schemas import HealthSchema

router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()


@router.get("", response_model=HealthSchema, summary="Service health check")
async def health(db: AsyncSession = Depends(get_db_session)) -> HealthSchema:
	db_status = "ok"
	try:
		await db.execute(text("SELECT 1"))
	except Exception:
		db_status = "unreachable"

	return HealthSchema(
		status="ok",
		version=settings.app_version,
		environment=settings.environment,
		db=db_status,
	)