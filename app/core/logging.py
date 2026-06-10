from __future__ import annotations

import logging
import sys
from pathlib import Path

import structlog

from app.core.config import get_settings


class AuditLogFilter(logging.Filter):
    """Allow only application audit events to be written to the JSON audit file."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.name.startswith("app.") or record.name == "streamlit_app"


def configure_logging() -> None:
    """Configure structured JSON logging to stdout and a local audit file."""
    settings = get_settings()
    _ensure_log_directory(settings.audit_log_path)

    timestamper = structlog.processors.TimeStamper(fmt="iso")
    pre_chain = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        timestamper,
    ]

    structlog.configure(
        processors=[
            *pre_chain,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=pre_chain,
    )

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(_build_stream_handler(formatter))
    root_logger.addHandler(_build_file_handler(settings.audit_log_path, formatter))


def get_logger(name: str):
    return structlog.get_logger(name)


def _ensure_log_directory(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)


def _build_stream_handler(
    formatter: structlog.stdlib.ProcessorFormatter,
) -> logging.StreamHandler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    return handler


def _build_file_handler(
    log_path: Path,
    formatter: structlog.stdlib.ProcessorFormatter,
) -> logging.FileHandler:
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(formatter)
    handler.addFilter(AuditLogFilter())
    return handler
