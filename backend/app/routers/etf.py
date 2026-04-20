import uuid
from datetime import date

from fastapi import APIRouter, Cookie, Depends, File, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import get_db_session
from app.core.exceptions import InvalidCSVError
from app.core.logging import get_logger
from app.models import(
		ETFPriceHistorySchema,
    ETFSummarySchema,
    ETFTopHoldingsSchema,
)
from app.services.etf_service import ETFService

router = APIRouter(prefix="/etf", tags=["ETF"])
logger = get_logger(__name__)
settings = get_settings()

SESSION_COOKIE = "etf_session_id"


def get_or_create_session(
    response: Response,
    session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> uuid.UUID:
	if session_id:
		try:
			return uuid.UUID(session_id)
		except ValueError:
			pass

	new_id = uuid.uuid4()
	response.set_cookie(
		key=SESSION_COOKIE,
    value=str(new_id),
    httponly=True,
    samesite="none",
    secure=True,
    max_age=60 * 60 * 24 * 30,
	)
	return new_id
	

@router.post(
	"/upload",
	response_model=ETFSummarySchema,
	status_code=status.HTTP_201_CREATED,
	summary="Upload an ETF CSV file",
)
async def upload_etf(
	file: UploadFile = File(...),
	session_id: uuid.UUID = Depends(get_or_create_session),
	db: AsyncSession = Depends(get_db_session),
) -> ETFSummarySchema:
	if not file.filename or not file.filename.lower().endswith(".csv"):
		raise InvalidCSVError("Only .csv files are accepted.")
	
	contents = await file.read()
	if len(contents) > settings.max_upload_size_bytes:
		raise InvalidCSVError(
			f"File exceeds maximum size of {settings.max_upload_size_bytes // 1024} KB."
		)
	
	service = ETFService(db)
	return await service.upload_etf(
		file_bytes=contents,
		filename=file.filename,
		session_id=session_id,
	)


@router.get(
	"/session",
	response_model=list[ETFSummarySchema],
	summary="Get all ETFs uplloaded in the current session",
)
async def get_session_etfs(
	session_id: uuid.UUID = Depends(get_or_create_session),
	db: AsyncSession = Depends(get_db_session),
) -> list[ETFSummarySchema]:
	service = ETFService(db)
	return await service.get_session_etfs(session_id)
	

@router.get(
	"/{etf_id}",
	response_model=ETFSummarySchema,
	summary="Get ETF summary with constituents and latest prices",
)
async def get_etf_summary(
	etf_id: uuid.UUID,
	db: AsyncSession = Depends(get_db_session),
) -> ETFSummarySchema:
	service = ETFService(db)
	return await service.get_etf_summary(etf_id)


@router.get(
	"/{etf_id}/price-history",
	response_model=ETFPriceHistorySchema,
	summary="Get reconstructed ETF price time series",
)
async def get_price_history(
	etf_id: uuid.UUID,
	date_from: date | None = None,
	date_to: date | None = None,
	db: AsyncSession = Depends(get_db_session),
) -> ETFPriceHistorySchema:
	service = ETFService(db)
	return await service.get_price_history(etf_id, date_from, date_to)


@router.get(
	"/{etf_id}/top-holdings",
	response_model=ETFTopHoldingsSchema,
	summary="Get top N holdings by holding size",
)
async def get_top_holdings(
	etf_id: uuid.UUID,
	limit: int = 5,
	db: AsyncSession = Depends(get_db_session),
) -> ETFTopHoldingsSchema:
	if limit < 1 or limit > 20:
		raise InvalidCSVError("limit must be between 1 and 20.")
	service = ETFService(db)
	return await service.get_top_holdings(etf_id, limit)


@router.delete(
    "/{etf_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an ETF from the current session",
)
async def delete_etf(
    etf_id: uuid.UUID,
    session_id: uuid.UUID = Depends(get_or_create_session),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    service = ETFService(db)
    await service.delete_etf(etf_id, session_id)


@router.get(
    "/stock/{stock_name}/price-history",
    response_model=ETFPriceHistorySchema,
    summary="Get price history for a single stock",
)
async def get_stock_price_history(
    stock_name: str,
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> ETFPriceHistorySchema:
    service = ETFService(db)
    return await service.get_stock_price_history(
        stock_name, date_from, date_to
    )