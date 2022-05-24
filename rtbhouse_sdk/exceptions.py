from typing import Dict


class ApiException(Exception):
    def __init__(self, message):
        super(ApiException, self).__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class ApiRequestException(ApiException):
    message = "Unexpected error"
    app_code = "UNKNOWN"
    errors = {}

    def __init__(self, response):
        self.raw_response = response
        try:
            self._res_data = response.json()
        except ValueError:
            message = f"{response.reason_phrase} ({response.status_code})"
        else:
            self.app_code = self._res_data.get("appCode")
            self.errors = self._res_data.get("errors")
            message = self._res_data.get("message")

        super(ApiRequestException, self).__init__(message)


class ApiRateLimitException(ApiRequestException):
    message = "Resource usage limits reached"

    def __init__(self, response):
        super(ApiRateLimitException, self).__init__(response)
        self.limits = parse_resource_usage_header(response.headers.get("X-Resource-Usage"))


def parse_resource_usage_header(header) -> Dict:
    """parse string like WORKER_TIME-3600=11.7/10000000;DB_QUERY_TIME-21600=4.62/2000 into dict"""
    if not header:
        return {}
    result = {}
    try:
        for line in header.split(";"):
            right, left = line.split("=")
            metric, time_span = right.split("-")
            used, limit = left.split("/")
            result.setdefault(metric, {}).setdefault(time_span, {})[limit] = float(used)
    except ValueError:
        return {}
    return result
