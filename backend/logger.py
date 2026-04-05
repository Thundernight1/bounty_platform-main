"""
Structured logging configuration using structlog.
Provides consistent, JSON-formatted logs for production environments.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

import structlog
from structlog.processors import JSONRenderer, TimeStamper
from structlog.stdlib import add_log_level, add_logger_name


def configure_logging(log_level: str = None) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  Defaults to LOG_LEVEL env var or INFO
    """
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level),
    )

    # Shared processors for both development and production
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        add_log_level,
        add_logger_name,
        TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Production: JSON output for machine parsing
    if os.getenv("APP_ENV", "development").lower() == "production":
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            JSONRenderer(),
        ]
    # Development: Human-readable console output
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__ of the calling module)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


# Context manager for adding temporary context to logs
class LogContext:
    """
    Context manager for adding temporary context to structured logs.

    Usage:
        with LogContext(user_id="123", request_id="abc"):
            logger.info("processing request")
    """

    def __init__(self, **kwargs: Any):
        self.kwargs = kwargs
        self.token = None

    def __enter__(self):
        self.token = structlog.contextvars.bind_contextvars(**self.kwargs)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        structlog.contextvars.unbind_contextvars(*self.kwargs.keys())


# Initialize logging on module import
configure_logging()
