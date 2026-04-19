import logging
import sys
from pythonjsonlogger import jsonlogger

from app.config import get_settings


def configure_logging() -> None:

	settings = get_settings()

	log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

	handler = logging.StreamHandler(sys.stdout)

	if settings.is_production:
		formatter = jsonlogger.JsonFormatter(
			fmt="%(ascctime)s %(name)s %(levelname)s %(message)s",
			datefmt="%Y-%m-%dT%H:%M:%S",
		)
	else:
		formatter = logging.Formatter(
			fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
		)

	handler.setFormatter(formatter)

	root_logger = logging.getLogger()
	root_logger.handlers.clear()
	root_logger.addHandler(handler)
	root_logger.setLevel(log_level)

	logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
	logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
	return logging.getLogger(name)
