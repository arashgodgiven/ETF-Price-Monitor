from contextlib import asynccontextmanager

from fastapi  import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import get_settings
from app.core.database import engine
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.routers import etf, health

configure_logging()
logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
	logger.info(
		"Starting ETF Monitor API",
		extra={"environment": settings.environment, "version": settings.app_version},
	)
	async with engine.connect() as conn:
		from sqlalchemy import text
		await conn.execute(text("SELECT 1"))
	logger.info("Database connection verified.")

	yield

	logger.info("Shutting down! Disposing DB connection pool.")
	await engine.dispose()


def create_app() -> FastAPI:
	app = FastAPI(
		title=settings.app_name,
		version=settings.app_version,
		docs_url="/api/docs",
		redoc_url="/api/redoc",
		oopenapi_url="/api/openapi.json",
		lifespan=lifespan,
	)

	app.add_middleware(
		CORSMiddleware,
		allow_origins=settings.allowed_origins,
		allow_credentials=True,
		allow_methods=["GET", "POST", "DELETE"],
		allow_headers=["*"], ## Check if OK
	)
	app.add_middleware(GZipMiddleware, minimum_size=1000)

	register_exception_handlers(app)

	app.include_router(health.router, prefix="/api/v1")
	app.include_router(etf.router, prefix="/api/v1")

	return app


app = create_app()