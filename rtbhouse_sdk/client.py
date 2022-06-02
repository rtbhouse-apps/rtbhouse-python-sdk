"""Contains definitions of standard (sync) client as well as async client."""
import dataclasses
import warnings
from datetime import date
from types import TracebackType
from typing import Any, Dict, Generator, List, Optional, Type, Union

import httpx

from . import __version__ as sdk_version
from . import schema
from .exceptions import (
    ApiException,
    ApiRateLimitException,
    ApiRequestException,
    ApiVersionMismatch,
)

API_BASE_URL = "https://api.panel.rtbhouse.com"
API_VERSION = "v5"

DEFAULT_TIMEOUT = 60.0
MAX_CURSOR_ROWS_LIMIT = 10000


class HttpxBasicTokenAuth(httpx.Auth):
    """Basic token auth backend."""

    def __init__(self, token: str):
        self._token = token

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers["Authorization"] = f"Token {self._token}"
        yield request


@dataclasses.dataclass
class BasicAuth:
    username: str
    password: str

    @property
    def httpx_auth_backend(self) -> httpx.Auth:
        return httpx.BasicAuth(self.username, self.password)


@dataclasses.dataclass
class BasicTokenAuth:
    token: str

    @property
    def httpx_auth_backend(self) -> httpx.Auth:
        return HttpxBasicTokenAuth(self.token)


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

    def __init__(self, auth: Union[BasicAuth, BasicTokenAuth], timeout_in_seconds: float = DEFAULT_TIMEOUT):
        self._httpx_client = httpx.Client(
            base_url=f"{API_BASE_URL}/{API_VERSION}",
            auth=Client.choose_auth_backend(auth),
            headers=Client.construct_headers(),
            timeout=timeout_in_seconds,
        )

    def close(self) -> None:
        self._httpx_client.close()

    def __enter__(self) -> "Client":
        self._httpx_client.__enter__()
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        traceback: TracebackType,
    ) -> None:
        self._httpx_client.__exit__(exc_type, exc_value, traceback)

    @staticmethod
    def choose_auth_backend(auth: Union[BasicAuth, BasicTokenAuth]) -> httpx.Auth:
        if not isinstance(auth, (BasicAuth, BasicTokenAuth)):
            raise ValueError("Unknown auth method")
        return auth.httpx_auth_backend

    @staticmethod
    def construct_headers() -> Dict[str, str]:
        return {
            "user-agent": f"rtbhouse-python-sdk/{sdk_version}",
        }

    @staticmethod
    def validate_response(response: httpx.Response) -> None:
        if response.status_code == 410:
            newest_version = response.headers.get("X-Current-Api-Version")
            raise ApiVersionMismatch(
                f"Unsupported api version ({API_VERSION}), use newest version ({newest_version}) "
                f"by updating rtbhouse_sdk package."
            )

        if response.status_code == 429:
            raise ApiRateLimitException(response)

        current_version = response.headers.get("X-Current-Api-Version")
        if current_version is not None and current_version != API_VERSION:
            warnings.warn(
                f"Used api version ({API_VERSION}) is outdated, use newest version ({current_version}) "
                f"by updating rtbhouse_sdk package."
            )

        if response.is_error:
            raise ApiRequestException(response)

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        response = self._httpx_client.get(path, params=params)
        Client.validate_response(response)
        try:
            resp_json = response.json()
            return resp_json["data"]
        except (ValueError, KeyError) as exc:
            raise ApiException("Invalid response format") from exc

    def get_user_info(self) -> schema.UserInfo:
        data = self._get("/user/info")
        return schema.UserInfo(**data)

    def get_advertisers(self) -> List[schema.Advertiser]:
        data = self._get("/advertisers")
        return [schema.Advertiser(**adv) for adv in data]

    def get_advertiser(self, adv_hash: str) -> schema.Advertiser:
        data = self._get(f"/advertisers/{adv_hash}")
        return schema.Advertiser(**data)

    def get_invoicing_data(self, adv_hash: str) -> schema.InvoiceData:
        data = self._get(f"/advertisers/{adv_hash}/client")
        return schema.InvoiceData(**data["invoicing"])

    def get_offer_categories(self, adv_hash: str) -> List[schema.Category]:
        data = self._get(f"/advertisers/{adv_hash}/offer-categories")
        return [schema.Category(**cat) for cat in data]

    def get_offers(self, adv_hash: str) -> List[schema.Offer]:
        data = self._get(f"/advertisers/{adv_hash}/offers")
        return [schema.Offer(**offer) for offer in data]

    def get_advertiser_campaigns(self, adv_hash: str) -> List[schema.Campaign]:
        data = self._get(f"/advertisers/{adv_hash}/campaigns")
        return [schema.Campaign(**camp) for camp in data]

    def get_billing(
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
    ) -> schema.Billing:
        data = self._get(f"/advertisers/{adv_hash}/billing", {"dayFrom": day_from, "dayTo": day_to})
        return schema.Billing(**data)

    def get_rtb_creatives(
        self,
        adv_hash: str,
        subcampaigns: Union[None, List[str], schema.SubcampaignsFilter] = None,
        active_only: Optional[bool] = None,
    ) -> List[schema.Creative]:
        params = self.create_rtb_creatives_params(subcampaigns, active_only)
        data = self._get(f"/advertisers/{adv_hash}/rtb-creatives", params=params)
        return [schema.Creative(**cr) for cr in data]

    @staticmethod
    def create_rtb_creatives_params(
        subcampaigns: Union[None, List[str], schema.SubcampaignsFilter] = None,
        active_only: Optional[bool] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if subcampaigns:
            if isinstance(subcampaigns, schema.SubcampaignsFilter):
                params["subcampaigns"] = subcampaigns.value
            elif isinstance(subcampaigns, (list, tuple, set)):
                params["subcampaigns"] = "-".join(str(sub) for sub in subcampaigns)
        if active_only is not None:
            params["activeOnly"] = active_only

        return params

    def get_rtb_conversions(
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
        convention_type: schema.CountConvention = schema.CountConvention.ATTRIBUTED_POST_CLICK,
    ) -> List[schema.Conversion]:
        rows = self._get_from_cursor(
            f"/advertisers/{adv_hash}/conversions",
            params={
                "dayFrom": day_from,
                "dayTo": day_to,
                "countConvention": convention_type.value,
            },
        )
        return [schema.Conversion(**conv) for conv in rows]

    def _get_from_cursor(self, path: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        request_params = {
            "limit": MAX_CURSOR_ROWS_LIMIT,
        }
        request_params.update(params or {})

        result = []
        while True:
            resp_data = self._get(path, params=request_params)
            result += resp_data["rows"]
            next_cursor = resp_data["nextCursor"]
            if next_cursor is None:
                break
            request_params["nextCursor"] = next_cursor

        return result

    def get_rtb_stats(  # pylint: disable=too-many-arguments
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
        group_by: List[schema.GroupBy],
        metrics: List[schema.Metric],
        count_convention: Optional[schema.CountConvention] = None,
        subcampaigns: Optional[List[str]] = None,
        user_segments: Optional[List[schema.UserSegment]] = None,
        device_types: Optional[List[schema.DeviceType]] = None,
    ) -> List[Dict[str, Any]]:
        params = self.create_rtb_stats_params(
            day_from, day_to, group_by, metrics, count_convention, subcampaigns, user_segments, device_types
        )

        return list(self._get(f"/advertisers/{adv_hash}/rtb-stats", params))

    @staticmethod
    def create_rtb_stats_params(  # pylint: disable=too-many-arguments
        day_from: date,
        day_to: date,
        group_by: List[schema.GroupBy],
        metrics: List[schema.Metric],
        count_convention: Optional[schema.CountConvention] = None,
        subcampaigns: Optional[List[str]] = None,
        user_segments: Optional[List[schema.UserSegment]] = None,
        device_types: Optional[List[schema.DeviceType]] = None,
    ) -> Dict[str, Any]:
        params = {
            "dayFrom": day_from,
            "dayTo": day_to,
            "groupBy": "-".join(group_by),
            "metrics": "-".join(metrics),
        }
        if count_convention is not None:
            params["countConvention"] = count_convention.value
        if subcampaigns is not None:
            params["subcampaigns"] = subcampaigns
        if user_segments is not None:
            params["userSegments"] = "-".join(us.value for us in user_segments)
        if device_types is not None:
            params["deviceTypes"] = "-".join(dt.value for dt in device_types)

        return params

    def get_summary_stats(  # pylint: disable=too-many-arguments
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
        group_by: List[schema.GroupBy],
        metrics: List[schema.Metric],
        count_convention: Optional[schema.CountConvention] = None,
        subcampaigns: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        params = self.create_summary_stats_params(day_from, day_to, group_by, metrics, count_convention, subcampaigns)

        return list(self._get(f"/advertisers/{adv_hash}/summary-stats", params))

    @staticmethod
    def create_summary_stats_params(  # pylint: disable=too-many-arguments
        day_from: date,
        day_to: date,
        group_by: List[schema.GroupBy],
        metrics: List[schema.Metric],
        count_convention: Optional[schema.CountConvention] = None,
        subcampaigns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        params = {
            "dayFrom": day_from,
            "dayTo": day_to,
            "groupBy": "-".join(gb.value for gb in group_by),
            "metrics": "-".join(m.value for m in metrics),
        }
        if count_convention is not None:
            params["countConvention"] = count_convention
        if subcampaigns is not None:
            params["subcampaigns"] = subcampaigns

        return params


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

    def __init__(self, auth: Union[BasicAuth, BasicTokenAuth], timeout_in_seconds: float = DEFAULT_TIMEOUT) -> None:
        self._httpx_client = httpx.AsyncClient(
            base_url=f"{API_BASE_URL}/{API_VERSION}",
            auth=Client.choose_auth_backend(auth),
            headers=Client.construct_headers(),
            timeout=timeout_in_seconds,
        )

    async def close(self) -> None:
        await self._httpx_client.aclose()

    async def __aenter__(self) -> "AsyncClient":
        await self._httpx_client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        traceback: TracebackType,
    ) -> None:
        await self._httpx_client.__aexit__(exc_type, exc_value, traceback)

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        response = await self._httpx_client.get(path, params=params)
        Client.validate_response(response)
        try:
            resp_json = response.json()
            return resp_json["data"]
        except (ValueError, KeyError) as exc:
            raise ApiException("Invalid response format") from exc

    async def get_user_info(self) -> schema.UserInfo:
        data = await self._get("/user/info")
        return schema.UserInfo(**data)

    async def get_advertisers(self) -> List[schema.Advertiser]:
        data = await self._get("/advertisers")
        return [schema.Advertiser(**adv) for adv in data]

    async def get_advertiser(self, adv_hash: str) -> schema.Advertiser:
        data = await self._get(f"/advertisers/{adv_hash}")
        return schema.Advertiser(**data)

    async def get_invoicing_data(self, adv_hash: str) -> schema.InvoiceData:
        data = await self._get(f"/advertisers/{adv_hash}/client")
        return schema.InvoiceData(**data["invoicing"])

    async def get_offer_categories(self, adv_hash: str) -> List[schema.Category]:
        data = await self._get(f"/advertisers/{adv_hash}/offer-categories")
        return [schema.Category(**cat) for cat in data]

    async def get_offers(self, adv_hash: str) -> List[schema.Offer]:
        data = await self._get(f"/advertisers/{adv_hash}/offers")
        return [schema.Offer(**offer) for offer in data]

    async def get_advertiser_campaigns(self, adv_hash: str) -> List[schema.Campaign]:
        data = await self._get(f"/advertisers/{adv_hash}/campaigns")
        return [schema.Campaign(**camp) for camp in data]

    async def get_billing(
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
    ) -> schema.Billing:
        data = await self._get(f"/advertisers/{adv_hash}/billing", {"dayFrom": day_from, "dayTo": day_to})
        return schema.Billing(**data)

    async def get_rtb_creatives(
        self,
        adv_hash: str,
        subcampaigns: Union[None, List[str], schema.SubcampaignsFilter] = None,
        active_only: Optional[bool] = None,
    ) -> List[schema.Creative]:
        params = Client.create_rtb_creatives_params(subcampaigns, active_only)
        data = await self._get(f"/advertisers/{adv_hash}/rtb-creatives", params=params)
        return [schema.Creative(**cr) for cr in data]

    async def get_rtb_conversions(
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
        convention_type: schema.CountConvention = schema.CountConvention.ATTRIBUTED_POST_CLICK,
    ) -> List[schema.Conversion]:
        rows = await self._get_from_cursor(
            f"/advertisers/{adv_hash}/conversions",
            params={
                "dayFrom": day_from,
                "dayTo": day_to,
                "countConvention": convention_type.value,
            },
        )
        return [schema.Conversion(**conv) for conv in rows]

    async def _get_from_cursor(self, path: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        request_params = {
            "limit": MAX_CURSOR_ROWS_LIMIT,
        }
        request_params.update(params or {})

        result = []
        while True:
            resp_data = await self._get(path, params=request_params)
            result += resp_data["rows"]
            next_cursor = resp_data["nextCursor"]
            if next_cursor is None:
                break
            request_params["nextCursor"] = next_cursor

        return result

    async def get_rtb_stats(  # pylint: disable=too-many-arguments
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
        group_by: List[schema.GroupBy],
        metrics: List[schema.Metric],
        count_convention: Optional[schema.CountConvention] = None,
        subcampaigns: Optional[List[str]] = None,
        user_segments: Optional[List[schema.UserSegment]] = None,
        device_types: Optional[List[schema.DeviceType]] = None,
    ) -> List[Dict[str, Any]]:
        params = Client.create_rtb_stats_params(
            day_from, day_to, group_by, metrics, count_convention, subcampaigns, user_segments, device_types
        )

        return list(await self._get(f"/advertisers/{adv_hash}/rtb-stats", params))

    async def get_summary_stats(  # pylint: disable=too-many-arguments
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
        group_by: List[schema.GroupBy],
        metrics: List[schema.Metric],
        count_convention: Optional[schema.CountConvention] = None,
        subcampaigns: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        params = Client.create_summary_stats_params(day_from, day_to, group_by, metrics, count_convention, subcampaigns)

        return list(await self._get(f"/advertisers/{adv_hash}/summary-stats", params))
