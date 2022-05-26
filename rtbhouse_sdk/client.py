import contextlib
import warnings
from datetime import date
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

import httpx

from . import __version__ as sdk_version
from . import schema
from .exceptions import ApiException, ApiRateLimitException, ApiRequestException

API_BASE_URL = "https://api.panel.rtbhouse.com"
API_VERSION = "v5"

DEFAULT_TIMEOUT = 60
MAX_CURSOR_ROWS_LIMIT = 10000


class CountConvention(str, Enum):
    ATTRIBUTED_POST_CLICK = "ATTRIBUTED"
    ATTRIBUTED_POST_VIEW = "POST_VIEW"
    ALL_POST_CLICK = "ALL_POST_CLICK"
    ALL_CONVERSIONS = "ALL_CONVERSIONS"


class UserSegment(str, Enum):
    VISITORS = "VISITORS"
    SHOPPERS = "SHOPPERS"
    BUYERS = "BUYERS"
    NEW = "NEW"


class DeviceType(str, Enum):
    PC = "PC"
    MOBILE = "MOBILE"
    PHONE = "PHONE"
    TABLET = "TABLET"
    TV = "TV"
    GAME_CONSOLE = "GAME_CONSOLE"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class GroupBy(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

    ADVERTISER = "advertiser"
    CAMPAIGN = "subcampaign"
    USER_SEGMENT = "user_segment"
    DEVICE_TYPE = "device_type"
    CREATIVE = "creative"
    CATEGORY = "category"
    COUNTRY = "country"
    PLACEMENT = "placement"


class Metric(str, Enum):
    CAMPAIGN_COST = "campaign_cost"
    IMPS_COUNT = "imps_count"
    ECPM = "ecpm"
    CLICKS_COUNT = "clicks_count"
    ECPC = "ecpc"
    CTR = "ctr"
    CONVERSIONS_COUNT = "conversions_count"
    ECPA = "ecpa"
    CR = "cr"
    CONVERSIONS_VALUE = "conversions_value"
    ROAS = "roas"
    ECPS = "ecps"
    VIDEO_COMPLETE_VIEWS = "video_complete_views"
    ECPV = "ecpv"
    VCR = "vcr"
    VIEWABILITY = "viewability"
    USER_FREQUENCY = "user_frequency"
    USER_REACH = "user_reach"


class Client:
    """
    A standard synchronous API client.

    The simplest way is to use it like:
    ```
    cli = Client(...)
    info = cli.get_user_info()
    adv = cli.get_advertiser(hash)
    ```
    This will however result in new http connection per each query.


    It's also possible to share underlying connection with consecutive queries using a context manager:
    ```
    with Client.get_client(...) as cli:
        info = cli.get_user_info()
        adv = cli.get_advertiser(hash)
    ```
    """

    def __init__(self, username, password, timeout=DEFAULT_TIMEOUT, httpx_client=None):
        self._username = username
        self._password = password
        self._timeout = timeout
        self._httpx_client = httpx_client

    @staticmethod
    @contextlib.contextmanager
    def get_client(username, password, timeout=DEFAULT_TIMEOUT):
        with httpx.Client() as httpx_cli:
            client = Client(username, password, timeout, httpx_cli)
            yield client
        client._httpx_client = None

    @contextlib.contextmanager
    def _get_httpx_client(self):
        if self._httpx_client:
            yield self._httpx_client
        else:
            with httpx.Client() as httpx_cli:
                yield httpx_cli

    def _validate_response(self, response):
        if response.status_code == 410:
            newest_version = response.headers.get("X-Current-Api-Version")
            raise ApiException(
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

        if response.status_code < 400:
            return

        raise ApiRequestException(response)

    def _make_request(self, method, path, *args, **kwargs):
        base_url = f"{API_BASE_URL}/{API_VERSION}"
        kwargs["timeout"] = self._timeout
        kwargs.setdefault("headers", {})["user-agent"] = f"rtbhouse-python-sdk/{sdk_version}"

        with self._get_httpx_client() as httpx_client:
            response = httpx_client.request(method, base_url + path, *args, **kwargs)
        self._validate_response(response)
        return response

    def _get(self, path, params=None) -> Dict:
        response = self._make_request("get", path, auth=(self._username, self._password), params=params)
        try:
            resp_json = response.json()
            return resp_json.get("data") or {}
        except (ValueError, KeyError):
            raise ApiException("Invalid response format")

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
        subcampaigns: Union[None, List[int], Literal["ALL", "ACTIVE"]] = None,
        active_only: Optional[bool] = None,
    ) -> List[schema.Creative]:
        params = self._create_rtb_creatives_params(subcampaigns, active_only)
        data = self._get(f"/advertisers/{adv_hash}/rtb-creatives", params=params)
        return [schema.Creative(**cr) for cr in data]

    def _create_rtb_creatives_params(
        self, subcampaigns: Union[None, List[int], Literal["ALL", "ACTIVE"]] = None, active_only: Optional[bool] = None
    ) -> Dict[str, Any]:
        params = {}
        if subcampaigns:
            if subcampaigns in ["ANY", "ACTIVE"]:
                params["subcampaigns"] = subcampaigns
            elif isinstance(subcampaigns, (list, tuple, set)):
                params["subcampaigns"] = "-".join(subcampaigns)
        if active_only is not None:
            params["activeOnly"] = active_only

        return params

    def get_rtb_conversions(
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
        convention_type=CountConvention.ATTRIBUTED_POST_CLICK,
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

    def _get_from_cursor(self, path, params=None) -> List[Dict]:
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
            else:
                request_params["nextCursor"] = next_cursor

        return result

    def get_rtb_stats(
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
        group_by: List[GroupBy],
        metrics: List[Metric],
        count_convention: Optional[CountConvention] = None,
        subcampaigns: Optional[List[str]] = None,
        user_segments: Optional[List[UserSegment]] = None,
        device_types: Optional[List[DeviceType]] = None,
    ):
        params = self._create_rtb_stats_params(
            day_from, day_to, group_by, metrics, count_convention, subcampaigns, user_segments, device_types
        )

        return self._get(f"/advertisers/{adv_hash}/rtb-stats", params)

    def _create_rtb_stats_params(
        self,
        day_from: date,
        day_to: date,
        group_by: List[GroupBy],
        metrics: List[Metric],
        count_convention: Optional[CountConvention] = None,
        subcampaigns: Optional[List[str]] = None,
        user_segments: Optional[List[UserSegment]] = None,
        device_types: Optional[List[DeviceType]] = None,
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

    def get_summary_stats(
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
        group_by: List[GroupBy],
        metrics: List[Metric],
        count_convention: Optional[CountConvention] = None,
        subcampaigns: Optional[List[int]] = None,
    ):
        params = self._create_summary_stats_params(day_from, day_to, group_by, metrics, count_convention, subcampaigns)

        return self._get(f"/advertisers/{adv_hash}/summary-stats", params)

    def _create_summary_stats_params(
        self,
        day_from: date,
        day_to: date,
        group_by: List[GroupBy],
        metrics: List[Metric],
        count_convention: Optional[CountConvention] = None,
        subcampaigns: Optional[List[int]] = None,
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


class AsyncClient(Client):
    """
    An asynchronous API client.

    Usage is the same as with synchronous client with the only difference of `await` keyword.
    ```
    cli = AsyncClient(...)
    info = await cli.get_user_info()
    ```
    """

    @staticmethod
    @contextlib.asynccontextmanager
    async def get_client(username, password, timeout=DEFAULT_TIMEOUT):
        async with httpx.AsyncClient() as httpx_cli:
            client = AsyncClient(username, password, timeout, httpx_cli)
            yield client
        client._httpx_client = None

    @contextlib.asynccontextmanager
    async def _get_httpx_client(self):
        if self._httpx_client:
            yield self._httpx_client
        else:
            async with httpx.AsyncClient() as httpx_cli:
                yield httpx_cli

    async def _make_request(self, method, path, *args, **kwargs):
        base_url = f"{API_BASE_URL}/{API_VERSION}"
        kwargs["timeout"] = self._timeout
        kwargs.setdefault("headers", {})["user-agent"] = f"rtbhouse-python-sdk/{sdk_version}"

        async with self._get_httpx_client() as cli:
            response = await cli.request(method, base_url + path, *args, **kwargs)
        self._validate_response(response)
        return response

    async def _get(self, path, params=None) -> Dict:
        response = await self._make_request("get", path, auth=(self._username, self._password), params=params)
        try:
            resp_json = response.json()
            return resp_json.get("data") or {}
        except (ValueError, KeyError):
            raise ApiException("Invalid response format")

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
        subcampaigns: Union[None, List[int], Literal["ALL", "ACTIVE"]] = None,
        active_only: Optional[bool] = None,
    ) -> List[schema.Creative]:
        params = self._create_rtb_creatives_params(subcampaigns, active_only)
        data = await self._get(f"/advertisers/{adv_hash}/rtb-creatives", params=params)
        return [schema.Creative(**cr) for cr in data]

    async def get_rtb_conversions(
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
        convention_type=CountConvention.ATTRIBUTED_POST_CLICK,
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

    async def _get_from_cursor(self, path, params=None) -> List[Dict]:
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
            else:
                request_params["nextCursor"] = next_cursor

        return result

    async def get_rtb_stats(
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
        group_by: List[GroupBy],
        metrics: List[Metric],
        count_convention: Optional[CountConvention] = None,
        subcampaigns: Optional[List[str]] = None,
        user_segments: Optional[List[UserSegment]] = None,
        device_types: Optional[List[DeviceType]] = None,
    ):
        params = self._create_rtb_stats_params(
            day_from, day_to, group_by, metrics, count_convention, subcampaigns, user_segments, device_types
        )

        return await self._get(f"/advertisers/{adv_hash}/rtb-stats", params)

    async def get_summary_stats(
        self,
        adv_hash: str,
        day_from: date,
        day_to: date,
        group_by: List[GroupBy],
        metrics: List[Metric],
        count_convention: Optional[CountConvention] = None,
        subcampaigns: Optional[List[int]] = None,
    ):
        params = self._create_summary_stats_params(day_from, day_to, group_by, metrics, count_convention, subcampaigns)

        return await self._get(f"/advertisers/{adv_hash}/summary-stats", params)
