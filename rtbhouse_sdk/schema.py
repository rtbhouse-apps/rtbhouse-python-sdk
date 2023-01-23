"""Schemas and enums for API data."""
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


class DpaPlacement(str, Enum):
    """Holds possible values of placement parameter."""

    MOBILE = "MOBILE"
    DESKTOP = "DESKTOP"
    OTHER = "OTHER"
    DESKTOP_RIGHT_HAND_COLUMN = "DESKTOP_RIGHT_HAND_COLUMN"
    UNKNOWN = "UNKNOWN"


class StatsGroupBy(str, Enum):
    """Holds possible values of group by parameter."""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
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
    VIEWABILITY = "viewability"
    USER_FREQUENCY = "userFrequency"
    USER_REACH = "userReach"


class CampaignType(str, Enum):
    """Holds possible values of subcampaigns parameter."""

    PERFORMANCE = "PERFORMANCE"
    BRANDING = "BRANDING"


class SubcampaignsFilter(str, Enum):
    """Holds possible values of subcampaigns parameter."""

    ANY = "ANY"
    ACTIVE = "ACTIVE"


class CamelizedBaseModel(BaseModel):
    class Config:
        alias_generator = to_camel_case


class UserInfo(CamelizedBaseModel):
    hash_id: str
    login: str
    email: str
    is_client_user: bool
    permissions: List[str]


class AdvertiserListElement(CamelizedBaseModel):
    hash: str
    status: str
    name: str
    currency: str
    url: str
    created_at: datetime
    features: Dict[str, Any]
    properties: Dict[str, Any]


class Advertiser(CamelizedBaseModel):
    hash: str
    status: str
    name: str
    currency: str
    url: str
    created_at: datetime
    features: Dict[str, Any]
    properties: Dict[str, Any]
    feed_identifier: str
    country: str


class Campaign(CamelizedBaseModel):
    hash: str
    name: str
    creative_ids: List[int]
    status: str
    updated_at: Optional[datetime]
    rate_card_id: str
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
    images: List[Image]
    currency: str
    name: str
    price: float
    category_name: str
    custom_properties: Dict[str, str]
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
    bills: List[Bill]


class CreativePreview(CamelizedBaseModel):
    width: int
    height: int
    offers_number: int
    preview_url: str


class Creative(CamelizedBaseModel):
    hash: str
    status: str
    previews: List[CreativePreview]


class ConversionSortBy(str, Enum):
    """Holds possible values of sortBy parameter."""

    CONVERSION_TYPE = "conversionTime"
    CONVERSION_VALUE = "conversionValue"
    COMISSION_VALUE = "commissionValue"
    LAST_CLICK_TIME = "lastClickTime"
    LAST_IMPRESSION_TIME = "lastImpressionTime"


class SortDirection(str, Enum):
    """Holds possible values of sortDirection parameter."""

    DESC = "DESC"
    ASC = "ASC"


class Conversion(CamelizedBaseModel):
    conversion_identifier: str
    conversion_hash: str
    conversion_class: Optional[str]
    conversion_value: float
    commission_value: float
    cookie_hash: str
    conversion_time: datetime
    last_click_time: datetime
    last_impression_time: datetime


class RateCardBidding(CamelizedBaseModel):
    visitors: Optional[float]
    shoppers: Optional[float]
    buyers: Optional[float]


class CategoryRateCardBidding(CamelizedBaseModel):
    cpc: Optional[float]


class CategoryRateCard(CamelizedBaseModel):
    categoryId: Optional[str]
    visitors_rate_card: CategoryRateCardBidding
    shoppers_rate_card: CategoryRateCardBidding
    buyers_rate_card: CategoryRateCardBidding


class InvoiceRateCard(CamelizedBaseModel):
    id: str
    cpc: RateCardBidding
    cpm: RateCardBidding
    cpa_post_click: RateCardBidding
    cpa_post_view: RateCardBidding
    cps_post_click: RateCardBidding
    cps_post_view: RateCardBidding
    category_rate_cards: List[CategoryRateCard]


class Stats(CamelizedBaseModel):
    # from GroupBy
    day: Optional[date]
    week: Optional[str]
    month: Optional[str]
    quarter: Optional[str]
    year: Optional[str]
    advertiser: Optional[str]
    subcampaign: Optional[str]
    subcampaign_hash: Optional[str]
    user_segment: Optional[str]
    device_types: Optional[str]
    creative: Optional[str]
    category: Optional[str]
    category_name: Optional[str]
    country: Optional[str]
    placement: Optional[str]
    device_type: Optional[str]

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


class LastSeenTagsStats(CamelizedBaseModel):
    last_tag_hour: Optional[str]
    imps_count: Optional[float]
    clicks_count: Optional[float]


class WinRateStats(CamelizedBaseModel):
    day: Optional[date]
    won: Optional[float]
    total: Optional[float]


class TopStatsRankedBy(str, Enum):
    """Holds possible values of rankedBy parameter."""

    IMPS = "IMPS"
    CLICKS = "CLICKS"


class TopHostsStats(CamelizedBaseModel):
    host: Optional[str]
    value: Optional[float]


class TopInAppsStats(CamelizedBaseModel):
    app_name: Optional[str]
    value: Optional[float]


class DeduplicationStats(CamelizedBaseModel):
    # from GroupBy
    day: Optional[date]
    week: Optional[str]
    month: Optional[str]
    quarter: Optional[str]
    year: Optional[str]
    subcampaign_hash: Optional[str]
    user_segment: Optional[str]

    # from Metric
    imps_count: Optional[int]
    clicks_count: Optional[int]

    # from Deduplication Stats
    attributed_conversions_count: Optional[float]
    all_conversions_count: Optional[float]
    count_decuplication_rate: Optional[float]
    attributed_conversions_value: Optional[float]
    all_conversions_value: Optional[float]
    value_deduplication_rate: Optional[float]
