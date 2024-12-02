"""Contains definitions of standard (sync) client as well as async client."""

# pylint: disable=too-many-arguments
import dataclasses
import warnings
from collections.abc import AsyncIterable, Generator, Iterable
from datetime import date, timedelta
from json import JSONDecodeError
from types import TracebackType
from typing import Any, Optional, Union

import httpx

from . import __version__ as sdk_version
from . import schema
from .exceptions import (
    ApiException,
    ApiRateLimitException,
    ApiRequestException,
    ApiVersionMismatchException,
    ErrorDetails,
)

API_BASE_URL = "https://api.panel.rtbhouse.com"
API_VERSION = "v5"

DEFAULT_TIMEOUT = timedelta(seconds=60.0)
MAX_CURSOR_ROWS = 10000


@dataclasses.dataclass
class BasicAuth:
    username: str
    password: str


@dataclasses.dataclass
class BasicTokenAuth:
    token: str


class Client:
    """
    A standard synchronous API client.

    The simplest way is to use it like:
    ```
    cli = Client(...)
    info = cli.get_user_info()
    adv = cli.get_advertiser(hash)
    cli.close()
    ```

    It's also possible to use it as context manager:
    ```
    with Client(...) as cli:
        info = cli.get_user_info()
        adv = cli.get_advertiser(hash)
    ```
    """

    def __init__(
        self,
        auth: Union[BasicAuth, BasicTokenAuth],
        timeout: timedelta = DEFAULT_TIMEOUT,
    ):
        self._httpx_client = httpx.Client(
            base_url=build_base_url(),
            auth=_choose_auth_backend(auth),
            headers=_build_headers(),
            timeout=timeout.total_seconds(),
        )

    def close(self) -> None:
        self._httpx_client.close()

    def __enter__(self) -> "Client":
        self._httpx_client.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        traceback: TracebackType,
    ) -> None:
        self._httpx_client.__exit__(exc_type, exc_value, traceback)

    def _get(self, path: str, params: Optional[dict[str, Any]] = None) -> Any:
        response = self._httpx_client.get(path, params=params)
        _validate_response(response)
        try:
            resp_json = response.json()
            return resp_json["data"]
        except (ValueError, KeyError) as exc:
            raise ApiException("Invalid response format") from exc

    def _get_dict(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        data = self._get(path, params)
        if not isinstance(data, dict):
            raise ValueError("Result is not a dict")
        return data

    def _get_list_of_dicts(self, path: str, params: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        data = self._get(path, params)
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError("Result is not a list of dicts")
        return data

    def _get_list_of_dicts_from_cursor(self, path: str, params: dict[str, Any]) -> Iterable[dict[str, Any]]:
        request_params = {
            "limit": MAX_CURSOR_ROWS,
        }
        request_params.update(params or {})

        while True:
            resp_data = self._get_dict(path, params=request_params)
            yield from resp_data["rows"]
            next_cursor = resp_data["nextCursor"]
            if next_cursor is None:
                break
            request_params["nextCursor"] = next_cursor

    def get_user_info(self) -> schema.UserInfo:
        data = self._get_dict("/user/info")
        return schema.UserInfo(**data)

    def get_advertisers(self) -> list[schema.Advertiser]:
        data = self._get_list_of_dicts("/advertisers")
        return [schema.Advertiser(**adv) for adv in data]

    def get_advertiser(self, adv_hash: str) -> schema.Advertiser:
        data = self._get_dict(f"/advertisers/{adv_hash}")
        return schema.Advertiser(**data)

    def get_invoicing_data(self, adv_hash: str) -> schema.InvoiceData:
        data = self._get_dict(f"/advertisers/{adv_hash}/client")
        return schema.InvoiceData(**data["invoicing"])

    def get_offer_categories(self, adv_hash: str) -> list[schema.Category]:
        data = self._get_list_of_dicts(f"/advertisers/{adv_hash}/offer-categories")
        return [schema.Category(**cat) for cat in data]

    def get_offers(self, adv_hash: str) -> list[schema.Offer]:
        data = self._get_list_of_dicts(f"/advertisers/{adv_hash}/offers")
        return [schema.Offer(**offer) for offer in data]

    def get_advertiser_campaigns(self, adv_hash: str) -> list[schema.Campaign]:
        data = self._get_list_of_dicts(f"/advertisers/{adv_hash}/campaigns")
        return [schema.Campaign(**camp) for camp in data]

    def get_billing(
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
    ) -> schema.Billing:
        data = self._get_dict(f"/advertisers/{adv_hash}/billing", {"dayFrom": day_from, "dayTo": day_to})
        return schema.Billing(**data)

    def get_rtb_creatives(
        self,
        adv_hash: str,
        subcampaigns: Union[None, list[str], schema.SubcampaignsFilter] = None,
        active_only: Optional[bool] = None,
    ) -> list[schema.Creative]:
        params = _build_rtb_creatives_params(subcampaigns, active_only)
        data = self._get_list_of_dicts(f"/advertisers/{adv_hash}/rtb-creatives", params=params)
        return [schema.Creative(**cr) for cr in data]

    def get_rtb_conversions(
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
        convention_type: schema.CountConvention = schema.CountConvention.ATTRIBUTED_POST_CLICK,
    ) -> Iterable[schema.Conversion]:
        rows = self._get_list_of_dicts_from_cursor(
            f"/advertisers/{adv_hash}/conversions",
            params={
                "dayFrom": day_from,
                "dayTo": day_to,
                "countConvention": convention_type.value,
            },
        )
        for conv in rows:
            yield schema.Conversion(**conv)

    def get_rtb_stats(
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
        group_by: list[schema.StatsGroupBy],
        metrics: list[schema.StatsMetric],
        count_convention: Optional[schema.CountConvention] = None,
        utc_offset_hours: int = 0,
        subcampaigns: Optional[list[str]] = None,
        user_segments: Optional[list[schema.UserSegment]] = None,
        device_types: Optional[list[schema.DeviceType]] = None,
    ) -> list[schema.Stats]:
        params = _build_rtb_stats_params(
            day_from,
            day_to,
            group_by,
            metrics,
            count_convention,
            utc_offset_hours,
            subcampaigns,
            user_segments,
            device_types,
        )

        data = self._get_list_of_dicts(f"/advertisers/{adv_hash}/rtb-stats", params)
        return [schema.Stats(**st) for st in data]

    def get_summary_stats(
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
        group_by: list[schema.StatsGroupBy],
        metrics: list[schema.StatsMetric],
        count_convention: Optional[schema.CountConvention] = None,
        utc_offset_hours: int = 0,
        subcampaigns: Optional[list[str]] = None,
    ) -> list[schema.Stats]:
        params = _build_summary_stats_params(
            day_from, day_to, group_by, metrics, count_convention, utc_offset_hours, subcampaigns
        )

        data = self._get_list_of_dicts(f"/advertisers/{adv_hash}/summary-stats", params)
        return [schema.Stats(**st) for st in data]


class AsyncClient:
    """
    An asynchronous API client.

    Usage is the same as with synchronous client with the only difference of `await` keyword.
    ```
    cli = AsyncClient(...)
    info = await cli.get_user_info()
    await cli.close()
    ```
    """

    def __init__(
        self,
        auth: Union[BasicAuth, BasicTokenAuth],
        timeout: timedelta = DEFAULT_TIMEOUT,
    ) -> None:
        self._httpx_client = httpx.AsyncClient(
            base_url=build_base_url(),
            auth=_choose_auth_backend(auth),
            headers=_build_headers(),
            timeout=timeout.total_seconds(),
        )

    async def close(self) -> None:
        await self._httpx_client.aclose()

    async def __aenter__(self) -> "AsyncClient":
        await self._httpx_client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        traceback: TracebackType,
    ) -> None:
        await self._httpx_client.__aexit__(exc_type, exc_value, traceback)

    async def _get(self, path: str, params: Optional[dict[str, Any]] = None) -> Any:
        response = await self._httpx_client.get(path, params=params)
        _validate_response(response)
        try:
            resp_json = response.json()
            return resp_json["data"]
        except (ValueError, KeyError) as exc:
            raise ApiException("Invalid response format") from exc

    async def _get_dict(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        data = await self._get(path, params)
        if not isinstance(data, dict):
            raise ValueError("Result is not a dict")
        return data

    async def _get_list_of_dicts(self, path: str, params: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        data = await self._get(path, params)
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError("Result is not of a list of dicts")
        return data

    async def _get_list_of_dicts_from_cursor(self, path: str, params: dict[str, Any]) -> AsyncIterable[dict[str, Any]]:
        request_params = {
            "limit": MAX_CURSOR_ROWS,
        }
        request_params.update(params or {})

        while True:
            resp_data = await self._get_dict(path, params=request_params)
            for row in resp_data["rows"]:
                yield row
            next_cursor = resp_data["nextCursor"]
            if next_cursor is None:
                break
            request_params["nextCursor"] = next_cursor

    async def get_user_info(self) -> schema.UserInfo:
        data = await self._get_dict("/user/info")
        return schema.UserInfo(**data)

    async def get_advertisers(self) -> list[schema.Advertiser]:
        data = await self._get_list_of_dicts("/advertisers")
        return [schema.Advertiser(**adv) for adv in data]

    async def get_advertiser(self, adv_hash: str) -> schema.Advertiser:
        data = await self._get_dict(f"/advertisers/{adv_hash}")
        return schema.Advertiser(**data)

    async def get_invoicing_data(self, adv_hash: str) -> schema.InvoiceData:
        data = await self._get_dict(f"/advertisers/{adv_hash}/client")
        return schema.InvoiceData(**data["invoicing"])

    async def get_offer_categories(self, adv_hash: str) -> list[schema.Category]:
        data = await self._get_list_of_dicts(f"/advertisers/{adv_hash}/offer-categories")
        return [schema.Category(**cat) for cat in data]

    async def get_offers(self, adv_hash: str) -> list[schema.Offer]:
        data = await self._get_list_of_dicts(f"/advertisers/{adv_hash}/offers")
        return [schema.Offer(**offer) for offer in data]

    async def get_advertiser_campaigns(self, adv_hash: str) -> list[schema.Campaign]:
        data = await self._get_list_of_dicts(f"/advertisers/{adv_hash}/campaigns")
        return [schema.Campaign(**camp) for camp in data]

    async def get_billing(
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
    ) -> schema.Billing:
        data = await self._get_dict(f"/advertisers/{adv_hash}/billing", {"dayFrom": day_from, "dayTo": day_to})
        return schema.Billing(**data)

    async def get_rtb_creatives(
        self,
        adv_hash: str,
        subcampaigns: Union[None, list[str], schema.SubcampaignsFilter] = None,
        active_only: Optional[bool] = None,
    ) -> list[schema.Creative]:
        params = _build_rtb_creatives_params(subcampaigns, active_only)
        data = await self._get_list_of_dicts(f"/advertisers/{adv_hash}/rtb-creatives", params=params)
        return [schema.Creative(**cr) for cr in data]

    async def get_rtb_conversions(
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
        convention_type: schema.CountConvention = schema.CountConvention.ATTRIBUTED_POST_CLICK,
    ) -> AsyncIterable[schema.Conversion]:
        rows = self._get_list_of_dicts_from_cursor(
            f"/advertisers/{adv_hash}/conversions",
            params={
                "dayFrom": day_from,
                "dayTo": day_to,
                "countConvention": convention_type.value,
            },
        )
        async for conv in rows:
            yield schema.Conversion(**conv)

    async def get_rtb_stats(
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
        group_by: list[schema.StatsGroupBy],
        metrics: list[schema.StatsMetric],
        count_convention: Optional[schema.CountConvention] = None,
        utc_offset_hours: int = 0,
        subcampaigns: Optional[list[str]] = None,
        user_segments: Optional[list[schema.UserSegment]] = None,
        device_types: Optional[list[schema.DeviceType]] = None,
    ) -> list[schema.Stats]:
        params = _build_rtb_stats_params(
            day_from,
            day_to,
            group_by,
            metrics,
            count_convention,
            utc_offset_hours,
            subcampaigns,
            user_segments,
            device_types,
        )

        data = await self._get_list_of_dicts(f"/advertisers/{adv_hash}/rtb-stats", params)
        return [schema.Stats(**st) for st in data]

    async def get_summary_stats(
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
        group_by: list[schema.StatsGroupBy],
        metrics: list[schema.StatsMetric],
        count_convention: Optional[schema.CountConvention] = None,
        utc_offset_hours: int = 0,
        subcampaigns: Optional[list[str]] = None,
    ) -> list[schema.Stats]:
        params = _build_summary_stats_params(
            day_from, day_to, group_by, metrics, count_convention, utc_offset_hours, subcampaigns
        )

        data = await self._get_list_of_dicts(f"/advertisers/{adv_hash}/summary-stats", params)
        return [schema.Stats(**st) for st in data]


class _HttpxBasicTokenAuth(httpx.Auth):
    """Basic token auth backend."""

    def __init__(self, token: str):
        self._token = token

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers["Authorization"] = f"Token {self._token}"
        yield request


def build_base_url() -> str:
    return f"{API_BASE_URL}/{API_VERSION}"


def _build_headers() -> dict[str, str]:
    return {
        "user-agent": f"rtbhouse-python-sdk/{sdk_version}",
    }


def _choose_auth_backend(auth: Union[BasicAuth, BasicTokenAuth]) -> httpx.Auth:
    if isinstance(auth, BasicAuth):
        return httpx.BasicAuth(auth.username, auth.password)
    if isinstance(auth, BasicTokenAuth):
        return _HttpxBasicTokenAuth(auth.token)
    raise ValueError("Unknown auth method")


def _validate_response(response: httpx.Response) -> None:
    try:
        response_data = response.json()
    except JSONDecodeError:
        error_details = None
    else:
        error_details = ErrorDetails(
            app_code=response_data.get("appCode"),
            errors=response_data.get("errors"),
            message=response_data.get("message"),
        )

    if response.status_code == 410:
        newest_version = response.headers.get("X-Current-Api-Version")
        raise ApiVersionMismatchException(
            f"Unsupported api version ({API_VERSION}), use newest version ({newest_version}) "
            f"by updating rtbhouse_sdk package."
        )

    if response.status_code == 429:
        raise ApiRateLimitException(
            "Resource usage limits reached",
            details=error_details,
            usage_header=response.headers.get("X-Resource-Usage"),
        )

    if response.is_error:
        raise ApiRequestException(
            error_details.message if error_details else "Unexpected error",
            details=error_details,
        )

    current_version = response.headers.get("X-Current-Api-Version")
    if current_version is not None and current_version != API_VERSION:
        warnings.warn(
            f"Used api version ({API_VERSION}) is outdated, use newest version ({current_version}) "
            f"by updating rtbhouse_sdk package."
        )


def _build_rtb_creatives_params(
    subcampaigns: Union[None, list[str], schema.SubcampaignsFilter] = None,
    active_only: Optional[bool] = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if subcampaigns:
        if isinstance(subcampaigns, schema.SubcampaignsFilter):
            params["subcampaigns"] = subcampaigns.value
        elif isinstance(subcampaigns, (list, tuple, set)):
            params["subcampaigns"] = "-".join(str(sub) for sub in subcampaigns)
    if active_only is not None:
        params["activeOnly"] = active_only

    return params


def _build_rtb_stats_params(
    day_from: date,
    day_to: date,
    group_by: list[schema.StatsGroupBy],
    metrics: list[schema.StatsMetric],
    count_convention: Optional[schema.CountConvention] = None,
    utc_offset_hours: int = 0,
    subcampaigns: Optional[list[str]] = None,
    user_segments: Optional[list[schema.UserSegment]] = None,
    device_types: Optional[list[schema.DeviceType]] = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "dayFrom": day_from,
        "dayTo": day_to,
        "groupBy": "-".join(gb.value for gb in group_by),
        "metrics": "-".join(m.value for m in metrics),
    }
    if count_convention is not None:
        params["countConvention"] = count_convention.value
    if utc_offset_hours != 0:
        params["utcOffsetHours"] = utc_offset_hours
    if subcampaigns is not None:
        params["subcampaigns"] = "-".join(str(sub) for sub in subcampaigns)
    if user_segments is not None:
        params["userSegments"] = "-".join(us.value for us in user_segments)
    if device_types is not None:
        params["deviceTypes"] = "-".join(dt.value for dt in device_types)

    return params


def _build_summary_stats_params(
    day_from: date,
    day_to: date,
    group_by: list[schema.StatsGroupBy],
    metrics: list[schema.StatsMetric],
    count_convention: Optional[schema.CountConvention] = None,
    utc_offset_hours: int = 0,
    subcampaigns: Optional[list[str]] = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "dayFrom": day_from,
        "dayTo": day_to,
        "groupBy": "-".join(gb.value for gb in group_by),
        "metrics": "-".join(m.value for m in metrics),
    }
    if count_convention is not None:
        params["countConvention"] = count_convention.value
    if utc_offset_hours != 0:
        params["utcOffsetHours"] = utc_offset_hours
    if subcampaigns is not None:
        params["subcampaigns"] = "-".join(str(sub) for sub in subcampaigns)

    return params
