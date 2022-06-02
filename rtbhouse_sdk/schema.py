"""Schemas and enums for API data."""
# pylint: disable=no-name-in-module
# pylint: disable=too-few-public-methods
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


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


class GroupBy(str, Enum):
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


class Metric(str, Enum):
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


def to_camel_case(string: str) -> str:
    words = string.split("_")
    return words[0] + "".join(word.capitalize() for word in words[1:])


class UserInfo(BaseModel):
    hash_id: str
    login: str
    email: str
    is_client_user: bool
    permissions: List[str]

    class Config:
        alias_generator = to_camel_case


class Advertiser(BaseModel):
    hash: str
    status: str
    name: str
    currency: str
    url: str
    created_at: datetime
    properties: Dict[str, Any]

    class Config:
        alias_generator = to_camel_case


class Campaign(BaseModel):
    hash: str
    name: str
    creative_ids: List[int]
    status: str
    updated_at: Optional[datetime]
    rateCardId: str
    is_editable: bool
    advertiser_limits: Optional[Dict[str, Optional[str]]]

    class Config:
        alias_generator = to_camel_case


class InvoiceData(BaseModel):
    vat_number: str
    company_name: str
    street1: str
    street2: Optional[str]
    postal_code: str
    city: str
    country: str
    email: str


class Category(BaseModel):
    category_id: str
    identifier: str
    name: str
    active_offers_number: int

    class Config:
        alias_generator = to_camel_case


class Image(BaseModel):
    width: str
    height: str
    url: str
    added: str
    hash: str


class Offer(BaseModel):
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

    class Config:
        alias_generator = to_camel_case


class Bill(BaseModel):
    day: date
    operation: str
    position: int
    credit: float
    debit: float
    balance: float
    record_number: int

    class Config:
        alias_generator = to_camel_case


class Billing(BaseModel):
    initial_balance: float
    bills: List[Bill]

    class Config:
        alias_generator = to_camel_case


class CreativePreview(BaseModel):
    width: int
    height: int
    offers_number: int
    preview_url: str

    class Config:
        alias_generator = to_camel_case


class Creative(BaseModel):
    hash: str
    previews: List[CreativePreview]

    class Config:
        alias_generator = to_camel_case


class Conversion(BaseModel):
    conversion_identifier: str
    conversion_hash: str
    conversion_class: Optional[str]
    conversion_value: float
    commission_value: float
    cookie_hash: str
    conversion_time: datetime
    last_click_time: datetime
    last_impression_time: datetime

    class Config:
        alias_generator = to_camel_case
