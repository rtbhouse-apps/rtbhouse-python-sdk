"""Definitions of exceptions used in SDK."""

import dataclasses
from typing import Any, Optional


@dataclasses.dataclass
class ErrorDetails:
    app_code: str
    message: str
    errors: Optional[dict[str, Any]]


class ApiException(Exception):
    """Base API Exception."""

    message: str
    error_details: Optional[ErrorDetails]

    def __init__(self, message: str, details: Optional[ErrorDetails] = None) -> None:
        super().__init__(message)
        self.message = message
        self.error_details = details

    def __str__(self) -> str:
        return self.message


class ApiVersionMismatchException(ApiException):
    """Indicates SDK version is behind API version and needs to be updated."""


class ApiRequestException(ApiException):
    """Indicates there's something wrong with request."""


class ApiRateLimitException(ApiRequestException):
    """Indicates that rate limit was exceeded."""

    limits: dict[str, dict[str, dict[str, float]]]

    def __init__(
        self,
        message: str,
        details: Optional[ErrorDetails],
        usage_header: Optional[str],
    ) -> None:
        super().__init__(message, details)
        self.limits = _parse_resource_usage_header(usage_header)


def _parse_resource_usage_header(header: Optional[str]) -> dict[str, dict[str, dict[str, float]]]:
    """parse string like WORKER_TIME-3600=11.7/10000000;BQ_TB_BILLED-21600=4.62/2000 into dict"""
    if not header:
        return {}
    result: dict[str, dict[str, dict[str, float]]] = {}
    try:
        for line in header.split(";"):
            right, left = line.split("=")
            metric, time_span = right.split("-")
            used, limit = left.split("/")
            result.setdefault(metric, {}).setdefault(time_span, {})[limit] = float(used)
    except ValueError:
        return {}
    return result
