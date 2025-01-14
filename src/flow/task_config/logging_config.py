import logging
import logging.config
from typing import Any, Dict

try:
    from pythonjsonlogger import jsonlogger  # type: ignore

    if jsonlogger:  # Temporarily added to avoid flake8 errors.
        JSON_LOGGER_AVAILABLE = True
except ImportError:
    JSON_LOGGER_AVAILABLE = False

LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console_json": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "level": "INFO",
        },
        "console_standard": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "INFO",
        },
    },
    "loggers": {
        "config_parser": {
            "handlers": (
                ["console_json"] if JSON_LOGGER_AVAILABLE else ["console_standard"]
            ),
            "level": "INFO",
            "propagate": False,
        },
    },
}


def setup_logging() -> None:
    """Configures logging from the LOGGING_CONFIG dictionary."""
    logging.config.dictConfig(LOGGING_CONFIG)
