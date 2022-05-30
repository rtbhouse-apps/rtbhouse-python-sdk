"""Definitions of exceptions used in SDK."""
from typing import Any, Dict


class ApiException(Exception):
    """Base API Exception."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class ApiVersionMismatch(ApiException):
    """Indicates SDK version is behind API version and needs to be updated."""


class ApiRequestException(ApiException):
    """Indicates there's something wrong with request."""

    message = "Unexpected error"
    app_code = "UNKNOWN"
    errors: Dict[str, Any] = {}

    def __init__(self, response):
        self.raw_response = response
        try:
            self._response_data = response.json()
        except ValueError:
            message = f"{response.reason_phrase} ({response.status_code})"
        else:
            self.app_code = self._response_data.get("appCode")
            self.errors = self._response_data.get("errors")
            message = self._response_data.get("message")

        super().__init__(message)


class ApiRateLimitException(ApiRequestException):
    """Indicates that rate limit was exceeded."""

    message = "Resource usage limits reached"

    def __init__(self, response):
        super().__init__(response)
        self.limits = parse_resource_usage_header(response.headers.get("X-Resource-Usage"))


def parse_resource_usage_header(header) -> Dict:
    """parse string like WORKER_TIME-3600=11.7/10000000;DB_QUERY_TIME-21600=4.62/2000 into dict"""
    if not header:
        return {}
    result: Dict[str, Dict[str, Dict[str, float]]] = {}
    try:
        for line in header.split(";"):
            right, left = line.split("=")
            metric, time_span = right.split("-")
            used, limit = left.split("/")
            result.setdefault(metric, {}).setdefault(time_span, {})[limit] = float(used)
    except ValueError:
        return {}
    return result
