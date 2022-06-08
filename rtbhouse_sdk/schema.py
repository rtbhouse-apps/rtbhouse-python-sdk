"""Schemas and enums for API data."""
# pylint: disable=no-name-in-module
# pylint: disable=too-few-public-methods
from datetime import date, datetime
from enum import Enum
from functools import partial
from typing import Any, Dict, List, Optional

from inflection import camelize
from pydantic import BaseModel

to_camel_case = partial(camelize, uppercase_first_letter=False)


class CountConvention(str, Enum):
    """Holds possible values of count convention parameter."""

    ATTRIBUTED_POST_CLICK = "ATTRIBUTED"
    ATTRIBUTED_POST_VIEW = "POST_VIEW"
    ALL_POST_CLICK = "ALL_POST_CLICK"
    ALL_CONVERSIONS = "ALL_CONVERSIONS"


class UserSegment(str, Enum):
    """Holds possible values of user segment parameter."""

    VISITORS = "VISITORS"
    SHOPPERS = "SHOPPERS"
    BUYERS = "BUYERS"
    NEW = "NEW"


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

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

    ADVERTISER = "advertiser"
    CAMPAIGN = "subcampaign"
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
    VIEWABILITY = "viewability"
    USER_FREQUENCY = "userFrequency"
    USER_REACH = "userReach"


class SubcampaignsFilter(str, Enum):
    """Holds possible values of subcampaigns parameter."""

    ALL = "ALL"
    ANY = "ANY"
    ACTIVE = "ACTIVE"


class CamelcasedBaseModel(BaseModel):
    class Config:
        alias_generator = to_camel_case


class UserInfo(CamelcasedBaseModel):
    hash_id: str
    login: str
    email: str
    is_client_user: bool
    permissions: List[str]


class Advertiser(CamelcasedBaseModel):
    hash: str
    status: str
    name: str
    currency: str
    url: str
    created_at: datetime
    properties: Dict[str, Any]


class Campaign(CamelcasedBaseModel):
    hash: str
    name: str
    creative_ids: List[int]
    status: str
    updated_at: Optional[datetime]
    rateCardId: str
    is_editable: bool
    advertiser_limits: Optional[Dict[str, Optional[str]]]


class InvoiceData(BaseModel):
    vat_number: str
    company_name: str
    street1: str
    street2: Optional[str]
    postal_code: str
    city: str
    country: str
    email: str


class Category(CamelcasedBaseModel):
    category_id: str
    identifier: str
    name: str
    active_offers_number: int


class Image(CamelcasedBaseModel):
    width: str
    height: str
    url: str
    added: str
    hash: str


class Offer(CamelcasedBaseModel):
    url: str
    full_name: str
    identifier: str
    id: str
    images: List[Image]
    name: str
    price: float
    category_name: str
    customProperties: Dict[str, str]
    updated_at: str
    status: str


class Bill(CamelcasedBaseModel):
    day: date
    operation: str
    position: int
    credit: float
    debit: float
    balance: float
    record_number: int


class Billing(CamelcasedBaseModel):
    initial_balance: float
    bills: List[Bill]


class CreativePreview(CamelcasedBaseModel):
    width: int
    height: int
    offers_number: int
    preview_url: str


class Creative(CamelcasedBaseModel):
    hash: str
    previews: List[CreativePreview]


class Conversion(CamelcasedBaseModel):
    conversion_identifier: str
    conversion_hash: str
    conversion_class: Optional[str]
    conversion_value: float
    commission_value: float
    cookie_hash: str
    conversion_time: datetime
    last_click_time: datetime
    last_impression_time: datetime


class Stats(CamelcasedBaseModel):
    # from GroupBy
    day: Optional[date]
    week: Optional[str]
    month: Optional[str]
    year: Optional[str]
    advertiser: Optional[str]
    subcampaign: Optional[str]
    subcampaign_hash: Optional[str]
    user_segment: Optional[str]
    device_type: Optional[str]
    creative: Optional[str]
    category: Optional[str]
    category_name: Optional[str]
    country: Optional[str]
    placement: Optional[str]

    # from Metric
    campaign_cost: Optional[float]
    imps_count: Optional[int]
    ecpm: Optional[float]
    clicks_count: Optional[int]
    ecpc: Optional[float]
    ctr: Optional[float]
    conversions_count: Optional[int]
    ecpa: Optional[float]
    cr: Optional[float]
    conversions_value: Optional[float]
    roas: Optional[float]
    ecps: Optional[float]
    video_complete_views: Optional[int]
    ecpv: Optional[float]
    vcr: Optional[float]
    viewability: Optional[float]
    user_frequency: Optional[float]
    user_reach: Optional[float]

    class Config:
        alias_generator = to_camel_case
