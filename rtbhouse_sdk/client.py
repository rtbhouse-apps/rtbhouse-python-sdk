import warnings
from typing import Dict, List, Optional

import httpx

from . import __version__ as sdk_version
from . import schema
from .exceptions import ApiException, ApiRateLimitException, ApiRequestException

API_BASE_URL = "https://api.panel.rtbhouse.com"
API_VERSION = "v5"

DEFAULT_TIMEOUT = 60
MAX_CURSOR_ROWS_LIMIT = 10000


class Conversions:
    POST_VIEW = "POST_VIEW"
    ATTRIBUTED_POST_CLICK = "ATTRIBUTED"
    ALL_POST_CLICK = "ALL_POST_CLICK"


class UserSegment:
    VISITORS = "VISITORS"
    SHOPPERS = "SHOPPERS"
    BUYERS = "BUYERS"
    NEW = "NEW"


class DeviceType:
    PC = "PC"
    MOBILE = "MOBILE"
    PHONE = "PHONE"
    TABLET = "TABLET"
    TV = "TV"
    GAME_CONSOLE = "GAME_CONSOLE"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class GroupBy:
    day = "day"
    week = "week"
    month = "month"
    year = "year"
    advertiser = "advertiser"
    subcampaign = "subcampaign"
    user_segment = "userSegment"
    device_type = "deviceType"
    creative = "creative"
    category = "category"
    country = "country"


class Metrics:
    campaign_cost = "campaignCost"
    imps_count = "impsCount"
    ecpm = "ecpm"
    clicks_count = "clicksCount"
    ecpc = "ecpc"
    ctr = "ctr"
    conversions_count = "conversionsCount"
    ecpa = "ecpa"
    cr = "cr"
    conversions_value = "conversionsValue"
    roas = "roas"
    ecps = "ecps"
    video_complete_views = "videoCompleteViews"
    ecpv = "ecpv"
    vcr = "vcr"
    viewability = "viewability"
    user_frequency = "userFrequency"
    user_reach = "userReach"


class Client:
    def __init__(self, username, password, timeout=DEFAULT_TIMEOUT):
        self._username = username
        self._password = password
        self._timeout = timeout

    def _validate_response(self, response):
        if response.status_code == 410:
            newest_version = response.headers.get("X-Current-Api-Version")
            raise ApiException(
                f"Unsupported api version ({API_VERSION}), use newest version ({newest_version}) "
                f"by updating rtbhouse_python_sdk package."
            )

        if response.status_code == 429:
            raise ApiRateLimitException(response)

        current_version = response.headers.get("X-Current-Api-Version")
        if current_version is not None and current_version != API_VERSION:
            warnings.warn(
                f"Used api version ({API_VERSION}) is outdated, use newest version ({current_version}) "
                f"by updating rtbhouse_python_sdk package."
            )

        if response.status_code < 400:
            return

        raise ApiRequestException(response)

    def _make_request(self, method, path, *args, **kwargs):
        base_url = f"{API_BASE_URL}/{API_VERSION}"
        kwargs["timeout"] = self._timeout
        kwargs.setdefault("headers", {})["user-agent"] = f"rtbhouse-python-sdk/{sdk_version}"

        with httpx.Client() as cli:
            response = cli.get(base_url + path, *args, **kwargs)
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

    def get_advertiser(self, adv_hash) -> schema.Advertiser:
        data = self._get(f"/advertisers/{adv_hash}")
        return schema.Advertiser(**data)

    def get_invoicing_data(self, adv_hash) -> schema.InvoiceData:
        data = self._get(f"/advertisers/{adv_hash}/client")
        return schema.InvoiceData(**data["invoicing"])

    def get_offer_categories(self, adv_hash) -> List[schema.Category]:
        data = self._get(f"/advertisers/{adv_hash}/offer-categories")
        return [schema.Category(**cat) for cat in data]

    def get_offers(self, adv_hash) -> List[schema.Offer]:
        data = self._get(f"/advertisers/{adv_hash}/offers")
        return [schema.Offer(**offer) for offer in data]

    def get_advertiser_campaigns(self, adv_hash) -> List[schema.Campaign]:
        data = self._get(f"/advertisers/{adv_hash}/campaigns")
        return [schema.Campaign(**camp) for camp in data]

    def get_billing(self, adv_hash, day_from, day_to) -> schema.Billing:
        data = self._get(f"/advertisers/{adv_hash}/billing", {"dayFrom": day_from, "dayTo": day_to})
        return schema.Billing(**data)

    def get_rtb_creatives(
        self, adv_hash, subcampaigns=None, active_only: Optional[bool] = None
    ) -> List[schema.Creative]:
        params = {}
        if subcampaigns:
            if subcampaigns in ["ANY", "ACTIVE"]:
                params["subcampaigns"] = subcampaigns
            elif isinstance(subcampaigns, (list, tuple, set)):
                params["subcampaigns"] = "-".join(subcampaigns)
        if active_only is not None:
            params["activeOnly"] = active_only
        data = self._get(f"/advertisers/{adv_hash}/rtb-creatives", params=params)
        return [schema.Creative(**cr) for cr in data]

    def get_rtb_conversions(
        self, adv_hash, day_from, day_to, convention_type=Conversions.ATTRIBUTED_POST_CLICK
    ) -> List[schema.Conversion]:
        rows = self._get_from_cursor(
            f"/advertisers/{adv_hash}/conversions",
            params={
                "dayFrom": day_from,
                "dayTo": day_to,
                "countConvention": convention_type,
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
        adv_hash,
        day_from,
        day_to,
        group_by,
        metrics,
        count_convention=None,
        subcampaigns=None,
        user_segments=None,
        device_types=None,
    ):
        params = {
            "dayFrom": day_from,
            "dayTo": day_to,
            "groupBy": "-".join(group_by),
            "metrics": "-".join(metrics),
        }
        if count_convention is not None:
            params["countConvention"] = count_convention
        if subcampaigns is not None:
            params["subcampaigns"] = subcampaigns
        if user_segments is not None:
            params["userSegments"] = "-".join(user_segments)
        if device_types is not None:
            params["deviceTypes"] = "-".join(device_types)

        return self._get(f"/advertisers/{adv_hash}/rtb-stats", params)

    def get_summary_stats(
        self, adv_hash, day_from, day_to, group_by, metrics, count_convention=None, subcampaigns=None
    ):
        params = {
            "dayFrom": day_from,
            "dayTo": day_to,
            "groupBy": "-".join(group_by),
            "metrics": "-".join(metrics),
        }
        if count_convention is not None:
            params["countConvention"] = count_convention
        if subcampaigns is not None:
            params["subcampaigns"] = subcampaigns

        return self._get(f"/advertisers/{adv_hash}/summary-stats", params)
