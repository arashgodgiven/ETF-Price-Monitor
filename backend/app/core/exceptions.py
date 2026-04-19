from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────────
# Exception hierarchy
# ─────────────────────────────────────────────

class ETFMonitorError(Exception):
	status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
	detail: str = "An unexpected error occured."

	def __init__(self, detail: str | None = None):
		self.detail = detail or self.__class__.detail
		super().__init__(self.detail)


class NotFoundError(ETFMonitorError):
	status_code = status.HTTP_404_NOT_FOUND
	detail = "Resource not found."


class ValidationError(ETFMonitorError):
	status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
	detail = "Validation failed."


class InvalidCSVError(ValidationError):
	detail = "Uploaded file is not a valid ETF CSV."


class UnknownStockNameError(ValidationError):
	detail = "CSV contains stock names not present in the price database."


class ETFNotFoundError(NotFoundError):
	detail = "ETF not found."


# ─────────────────────────────────────────────
# Exception handlers
# ─────────────────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:

	@aapp.exception_handler(ETFMonitorError)
	async def etf_monitor_error_handler(
		request: Request, exc: ETFMonitorError
	) -> JSONResponse:
		logger.warning(
			"Application error",
			extra={
				"error_type": type(exc).__name__,
				"detail": exc.detail,
				"path": request.url.path,
			},
		)
		return JSONResponse(
			status_code=exc.status_code,
			content={"error": exc.detail, "tyoe": type(exc).__name__},
		)
	
	@app.exception_handler(Exception)
	async def unhandled_error_handler(
		request: Request, exc: Exception
	) -> JSONResponse:
		logger.error(
			"Unhandled exception",
			extraa={"error": str(exc), "path": request.url.path},
			exc_info=True,
		)
		return JSONResponse(
			stats_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			content={"error": "Internal server error.", "type": "InternalServerError"},
		)