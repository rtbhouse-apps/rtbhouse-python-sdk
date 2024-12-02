"""Schemas and enums for API data."""

# pylint: disable=too-few-public-methods
from datetime import date, datetime
from enum import Enum
from functools import partial
from typing import Any, Optional

from pydantic import BaseModel

from ._utils import PYDANTIC_V1, camelize

if not PYDANTIC_V1:
    from pydantic import ConfigDict


to_camel_case = partial(
    camelize,
    uppercase_first_letter=False,
)


class CountConvention(str, Enum):
    """Holds possible values of count convention parameter."""

    ATTRIBUTED_POST_CLICK = "ATTRIBUTED"
    ATTRIBUTED_POST_VIEW = "POST_VIEW"
    ALL_POST_CLICK = "ALL_POST_CLICK"
    ALL_CONVERSIONS = "ALL_CONVERSIONS"


class UserSegment(str, Enum):
    """Holds possible values of user segment parameter."""

    NEW = "NEW"
    VISITORS = "VISITORS"
    SHOPPERS = "SHOPPERS"
    BUYERS = "BUYERS"


class DeviceType(str, Enum):
    """Holds possible values of device type parameter."""

    PC = "PC"
    MOBILE = "MOBILE"
    PHONE = "PHONE"
    TABLET = "TABLET"
    TV = "TV"
    GAME_CONSOLE = "GAME_CONSOLE"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class StatsGroupBy(str, Enum):
    """Holds possible values of group by parameter."""

    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

    ADVERTISER = "advertiser"
    SUBCAMPAIGN = "subcampaign"
    USER_SEGMENT = "userSegment"
    DEVICE_TYPE = "deviceType"
    CREATIVE = "creative"
    CATEGORY = "category"
    COUNTRY = "country"
    PLACEMENT = "placement"


class StatsMetric(str, Enum):
    """Holds possible values of metric parameter."""

    CAMPAIGN_COST = "campaignCost"
    IMPS_COUNT = "impsCount"
    ECPM = "ecpm"
    CLICKS_COUNT = "clicksCount"
    ECPC = "ecpc"
    CTR = "ctr"
    CONVERSIONS_COUNT = "conversionsCount"
    ECPA = "ecpa"
    CR = "cr"
    CONVERSIONS_VALUE = "conversionsValue"
    ROAS = "roas"
    ECPS = "ecps"
    VIDEO_COMPLETE_VIEWS = "videoCompleteViews"
    ECPV = "ecpv"
    VCR = "vcr"
    AUDIO_COMPLETE_LISTENS = "audioCompleteListens"
    ECPL = "ecpl"
    ACR = "acr"
    VIEWABILITY_MEASURABILITY = "viewabilityMeasurability"
    VIEWABILITY_VIEWABILITY = "viewabilityViewability"
    EVCPM = "evcpm"
    SSP_VIEWABILITY = "sspViewability"
    VISITS_COUNT = "visitsCount"
    CPVISIT = "cpvisit"
    USER_FREQUENCY = "userFrequency"
    USER_REACH = "userReach"


class SubcampaignsFilter(str, Enum):
    """Holds possible values of subcampaigns parameter."""

    ANY = "ANY"
    ACTIVE = "ACTIVE"


class CamelizedBaseModel(BaseModel):
    if PYDANTIC_V1:

        class Config:
            alias_generator = to_camel_case

    else:
        model_config = ConfigDict(  # pylint: disable=possibly-used-before-assignment  # pyright: ignore
            alias_generator=to_camel_case,
        )


class UserInfo(CamelizedBaseModel):
    hash_id: str
    login: str
    email: str
    is_client_user: bool
    permissions: list[str]


class Advertiser(CamelizedBaseModel):
    hash: str
    status: str
    name: str
    currency: str
    url: str
    created_at: datetime
    properties: dict[str, Any]


class Campaign(CamelizedBaseModel):
    hash: str
    name: str
    creative_ids: list[int]
    status: str
    updated_at: Optional[datetime]
    rate_card_id: str
    is_editable: bool
    advertiser_limits: Optional[dict[str, Optional[int]]] = None


class InvoiceData(BaseModel):
    vat_number: str
    company_name: str
    street1: str
    street2: Optional[str] = None
    postal_code: str
    city: str
    country: str
    email: str


class Category(CamelizedBaseModel):
    category_id: str
    identifier: str
    name: str
    active_offers_number: int


class Image(CamelizedBaseModel):
    width: str
    height: str
    url: str
    added: str
    hash: str


class Offer(CamelizedBaseModel):
    url: str
    full_name: str
    identifier: str
    id: str
    images: list[Image]
    name: str
    price: float
    category_name: str
    custom_properties: dict[str, str]
    updated_at: str
    status: str


class Bill(CamelizedBaseModel):
    day: date
    operation: str
    position: int
    credit: float
    debit: float
    balance: float
    record_number: int


class Billing(CamelizedBaseModel):
    initial_balance: float
    bills: list[Bill]


class CreativePreview(CamelizedBaseModel):
    width: int
    height: int
    offers_number: int
    preview_url: str


class Creative(CamelizedBaseModel):
    hash: str
    previews: list[CreativePreview]


class Conversion(CamelizedBaseModel):
    conversion_identifier: str
    conversion_hash: str
    conversion_class: Optional[str]
    conversion_value: float
    commission_value: float
    cookie_hash: Optional[str]
    conversion_time: datetime
    last_click_time: Optional[datetime]
    last_impression_time: Optional[datetime]


class Stats(CamelizedBaseModel):
    # from GroupBy
    hour: Optional[int] = None
    day: Optional[date] = None
    week: Optional[str] = None
    month: Optional[str] = None
    year: Optional[str] = None
    advertiser: Optional[str] = None
    subcampaign: Optional[str] = None
    subcampaign_hash: Optional[str] = None
    user_segment: Optional[str] = None
    device_type: Optional[str] = None
    creative: Optional[str] = None
    category: Optional[str] = None
    category_name: Optional[str] = None
    country: Optional[str] = None
    placement: Optional[str] = None

    # from Metric
    campaign_cost: Optional[float] = None
    imps_count: Optional[float] = None
    ecpm: Optional[float] = None
    clicks_count: Optional[float] = None
    ecpc: Optional[float] = None
    ctr: Optional[float] = None
    conversions_count: Optional[float] = None
    ecpa: Optional[float] = None
    cr: Optional[float] = None
    conversions_value: Optional[float] = None
    roas: Optional[float] = None
    ecps: Optional[float] = None
    video_complete_views: Optional[float] = None
    ecpv: Optional[float] = None
    vcr: Optional[float] = None
    audio_complete_listens: Optional[float] = None
    ecpl: Optional[float] = None
    acr: Optional[float] = None
    viewability_measurability: Optional[float] = None
    viewability_viewability: Optional[float] = None
    evcpm: Optional[float] = None
    ssp_viewability: Optional[float] = None
    visits_count: Optional[float] = None
    cpvisit: Optional[float] = None
    user_frequency: Optional[float] = None
    user_reach: Optional[float] = None
