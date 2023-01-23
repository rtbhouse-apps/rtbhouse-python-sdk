"""Tests for client."""
# pylint: disable=too-many-arguments
from datetime import date
from typing import Any, Dict, Iterator, List, Optional

import pytest
import respx
from httpx import Response

from rtbhouse_sdk.client import API_VERSION, BasicAuth, Client
from rtbhouse_sdk.exceptions import ApiRateLimitException, ApiVersionMismatchException
from rtbhouse_sdk.schema import (
    CampaignType,
    ConversionSortBy,
    CountConvention,
    DeviceType,
    DpaPlacement,
    SortDirection,
    StatsGroupBy,
    StatsMetric,
    SubcampaignsFilter,
    TopStatsRankedBy,
    UserSegment,
    to_camel_case,
)


@pytest.fixture(name="api")
def api_client() -> Iterator[Client]:
    with Client(auth=BasicAuth("test", "test")) as api:
        yield api


def test_client_close() -> None:
    cli = Client(auth=BasicAuth("test", "test"))
    cli.close()


def test_client_as_context_manager() -> None:
    with Client(auth=BasicAuth("test", "test")):
        pass


def test_validate_response_raises_error_on_too_old_api_version(api: Client, api_mock: respx.MockRouter) -> None:
    newest_version = int(API_VERSION.strip("v")) + 2
    api_mock.get("/example-endpoint").respond(410, headers={"X-Current-Api-Version": f"v{newest_version}"})

    with pytest.raises(ApiVersionMismatchException) as cm:
        api._get("/example-endpoint")  # pylint: disable=protected-access

    assert cm.value.message.startswith("Unsupported api version")


def test_validate_response_warns_on_not_the_newest_api_version(api: Client, api_mock: respx.MockRouter) -> None:
    newest_version = f'v{int(API_VERSION.strip("v")) + 1}'
    api_mock.get("/example-endpoint").respond(200, json={"data": {}}, headers={"X-Current-Api-Version": newest_version})

    with pytest.warns(Warning) as cm:
        api._get("/example-endpoint")  # pylint: disable=protected-access

    msg = (
        f"Used api version ({API_VERSION}) is outdated, use newest version ({newest_version}) "
        f"by updating rtbhouse_sdk package."
    )
    assert str(cm[0].message) == msg


def test_validate_response_raises_error_on_resource_usage_limit_reached(
    api: Client, api_mock: respx.MockRouter
) -> None:
    header = ";".join(
        [
            "WORKER_TIME-3600=11.78/10000000",
            "DB_QUERY_TIME-3600=4.62/500",
            "DB_QUERY_TIME-86400=17.995/5000",
        ]
    )
    api_mock.get("/example-endpoint").respond(429, headers={"X-Resource-Usage": header})

    with pytest.raises(ApiRateLimitException) as cm:
        api._get("/example-endpoint")  # pylint: disable=protected-access

    data = cm.value.limits
    assert data["WORKER_TIME"]["3600"]["10000000"] == 11.78
    assert data["DB_QUERY_TIME"]["3600"]["500"] == 4.62
    assert data["DB_QUERY_TIME"]["86400"]["5000"] == 17.995


def test_get_user_info(
    api: Client,
    api_mock: respx.MockRouter,
    user_info_response: Dict[str, Any],
) -> None:
    api_mock.get("/user/info").respond(200, json=user_info_response)

    data = api.get_user_info()

    assert data.hash_id == "hid"


def test_get_advertisers(
    api: Client,
    api_mock: respx.MockRouter,
    advertisers_response: Dict[str, Any],
) -> None:
    api_mock.get("/advertisers").respond(200, json=advertisers_response)

    (advertiser,) = api.get_advertisers()

    assert advertiser.name == "Adv"


def test_get_advertiser(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    advertiser_response: Dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}").respond(200, json=advertiser_response)

    advertiser = api.get_advertiser(adv_hash)

    assert advertiser.name == "Adv"


def test_get_invoicing_data(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    invoice_data_response: Dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/client").respond(200, json=invoice_data_response)

    invoice_data = api.get_invoicing_data(adv_hash)

    assert invoice_data.company_name == "Ltd"


def test_get_offer_categories(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    offer_categories_response: Dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/offer-categories").respond(200, json=offer_categories_response)

    (offer_cat,) = api.get_offer_categories(adv_hash)

    assert offer_cat.name == "full cat"


def test_get_offers(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    offers_response: Dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/offers").respond(200, json=offers_response)

    (offer,) = api.get_offers(adv_hash)

    assert offer.full_name == "FN"
    assert offer.images[0].width == "700"

    (call,) = api_mock.calls
    assert dict(call.request.url.params) == {}


@pytest.mark.parametrize(
    "param,value,query_value",
    [
        ("name", "abc", "abc"),
        (
            "category_ids",
            [1, 2],
            "1,2",
        ),
        ("identifiers", ["def", "ghi"], "def,ghi"),
        ("limit", 100, "100"),
    ],
)
def test_get_offers_with_extra_params(
    api: Client, api_mock: respx.MockRouter, adv_hash: str, param: str, value: Any, query_value: Any
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/offers").respond(200, json={"status": "ok", "data": []})

    extra_params = {param: value}
    api.get_offers(adv_hash=adv_hash, **extra_params)

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


def test_get_advertiser_campaigns(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    advertiser_campaigns_response: Dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/campaigns").respond(200, json=advertiser_campaigns_response)

    (campaign,) = api.get_advertiser_campaigns(adv_hash)
    assert campaign.name == "Campaign"

    (call,) = api_mock.calls
    assert dict(call.request.url.params) == {}


@pytest.mark.parametrize(
    "param,value,query_value",
    [
        ("exclude_archived", True, "true"),
    ],
)
def test_get_advertiser_campaigns_with_extra_params(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    param: str,
    value: Any,
    query_value: Any,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/campaigns").respond(200, json={"status": "ok", "data": []})

    extra_params = {param: value}
    api.get_advertiser_campaigns(adv_hash=adv_hash, **extra_params)

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


def test_get_billing(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
    billing_response: Dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/billing").respond(200, json=billing_response)

    billing = api.get_billing(adv_hash, day_from, day_to)

    (bill,) = billing.bills
    assert billing.initial_balance == -100
    assert bill.day == date(2020, 11, 25)


def test_get_rtb_creatives(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    rtb_creatives_response: Dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/rtb-creatives").respond(200, json=rtb_creatives_response)

    (rtb_creative,) = api.get_rtb_creatives(adv_hash)

    (call,) = api_mock.calls
    assert dict(call.request.url.params) == {}
    assert rtb_creative.hash == "hash"
    assert len(rtb_creative.previews) == 1

    (call,) = api_mock.calls
    assert dict(call.request.url.params) == {}


@pytest.mark.parametrize(
    "param,value,query_value",
    [
        ("subcampaigns", ["hash1", "hash2"], "hash1-hash2"),
        ("subcampaigns", SubcampaignsFilter.ACTIVE, "ACTIVE"),
        (
            "active_only",
            True,
            "true",
        ),
    ],
)
def test_get_rtb_creatives_with_extra_params(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    param: str,
    value: Any,
    query_value: Any,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/rtb-creatives").respond(200, json={"status": "ok", "data": []})

    extra_params = {param: value}
    api.get_rtb_creatives(adv_hash=adv_hash, **extra_params)

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


def test_get_rtb_conversions(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
    conversions_with_next_cursor_response: Dict[str, Any],
    conversions_without_next_cursor_response: Dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/conversions").mock(
        side_effect=[
            Response(200, json=conversions_with_next_cursor_response),
            Response(200, json=conversions_without_next_cursor_response),
        ]
    )

    conversions = list(api.get_rtb_conversions(adv_hash, day_from, day_to))

    call1, call2 = api_mock.calls
    assert set(call1.request.url.params.keys()) == {"dayFrom", "dayTo", "countConvention", "limit"}
    assert set(call2.request.url.params.keys()) == {"dayFrom", "dayTo", "countConvention", "limit", "nextCursor"}
    assert len(conversions) == 6
    assert conversions[0].conversion_hash == "chash"


@pytest.mark.parametrize(
    "param,value,query_value",
    [
        ("limit", 100, "100"),
        ("count_convention", CountConvention.ALL_CONVERSIONS, "ALL_CONVERSIONS"),
        ("subcampaigns", ["hash1", "hash2"], "hash1-hash2"),
        ("conversion_identifier", "ghi", "ghi"),
        ("sort_by", ConversionSortBy.COMISSION_VALUE, "commissionValue"),
        ("sort_direction", SortDirection.DESC, "DESC"),
    ],
)
def test_get_rtb_conversions_with_extra_params(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
    param: str,
    value: Any,
    query_value: Any,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/conversions").mock(
        side_effect=[Response(200, json={"status": "ok", "data": {"rows": [], "nextCursor": None}})]
    )

    extra_params = {param: value}
    list(api.get_rtb_conversions(adv_hash=adv_hash, day_from=day_from, day_to=day_to, **extra_params))

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


def test_get_rtb_stats(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/rtb-stats").respond(
        200,
        json={"status": "ok", "data": [{"day": "2022-01-01", "advertiser": "xyz", "campaignCost": 51.0}]},
    )

    (stats,) = api.get_rtb_stats(
        adv_hash,
        day_from,
        day_to,
        [StatsGroupBy.ADVERTISER, StatsGroupBy.DAY],
        [StatsMetric.CAMPAIGN_COST, StatsMetric.CR],
    )

    (call,) = api_mock.calls
    assert dict(call.request.url.params) == {
        "dayFrom": "2020-09-01",
        "dayTo": "2020-09-01",
        "groupBy": "advertiser-day",
        "metrics": "campaignCost-cr",
    }
    assert stats.advertiser == "xyz"
    assert stats.campaign_cost == 51.0

    (call,) = api_mock.calls
    assert dict(call.request.url.params) == {
        "dayFrom": "2020-09-01",
        "dayTo": "2020-09-01",
        "groupBy": "advertiser-day",
        "metrics": "campaignCost-cr",
    }


@pytest.mark.parametrize(
    "param,value,query_value",
    [
        ("count_convention", CountConvention.ATTRIBUTED_POST_CLICK, "ATTRIBUTED"),
        ("subcampaigns", ["hash1", "hash2"], "hash1-hash2"),
        ("user_segments", [UserSegment.BUYERS, UserSegment.SHOPPERS], "BUYERS-SHOPPERS"),
        ("device_types", DeviceType.PC, "PC"),
    ],
)
def test_get_rtb_stats_extra_params(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
    param: str,
    value: Any,
    query_value: str,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/rtb-stats").respond(
        200,
        json={"status": "ok", "data": []},
    )

    extra_params = {param: value}

    api.get_rtb_stats(
        adv_hash, day_from, day_to, [StatsGroupBy.ADVERTISER], [StatsMetric.CAMPAIGN_COST], **extra_params
    )

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


def test_get_summary_stats(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/summary-stats").respond(
        200,
        json={"status": "ok", "data": [{"day": "2022-01-01", "advertiser": "xyz", "campaignCost": 108.0}]},
    )

    (stats,) = api.get_summary_stats(
        adv_hash,
        day_from,
        day_to,
        [StatsGroupBy.ADVERTISER, StatsGroupBy.DAY],
        [StatsMetric.CAMPAIGN_COST, StatsMetric.CR],
    )

    (call,) = api_mock.calls
    assert dict(call.request.url.params) == {
        "dayFrom": "2020-09-01",
        "dayTo": "2020-09-01",
        "groupBy": "advertiser-day",
        "metrics": "campaignCost-cr",
    }
    assert stats.advertiser == "xyz"


@pytest.mark.parametrize(
    "param,value,query_value",
    [
        ("count_convention", CountConvention.ATTRIBUTED_POST_CLICK, "ATTRIBUTED"),
        ("subcampaigns", ["hash1", "hash2"], "hash1-hash2"),
        ("user_segments", [UserSegment.BUYERS, UserSegment.SHOPPERS], "BUYERS-SHOPPERS"),
        ("device_types", DeviceType.PC, "PC"),
        ("placement", DpaPlacement.DESKTOP, "DESKTOP"),
    ],
)
def test_get_summary_stats_extra_params(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
    param: str,
    value: Any,
    query_value: str,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/summary-stats").respond(
        200,
        json={"status": "ok", "data": []},
    )

    extra_params = {param: value}
    api.get_summary_stats(
        adv_hash,
        day_from,
        day_to,
        [StatsGroupBy.ADVERTISER, StatsGroupBy.DAY],
        [StatsMetric.CAMPAIGN_COST, StatsMetric.CR],
        **extra_params,
    )

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


def test_advertisers_summary_stats(
    api: Client,
    api_mock: respx.MockRouter,
    day_from: date,
    day_to: date,
) -> None:
    api_mock.get(f"/advertisers-summary-stats").respond(
        200,
        json={
            "status": "ok",
            "data": [{"day": "2022-01-01", "advertiser": "xyz", "campaignCost": 108.0, "clickCount": 231}],
        },
    )

    (stats,) = api.get_advertisers_summary_stats(
        CampaignType.PERFORMANCE,
        day_from,
        day_to,
        [StatsGroupBy.DAY, StatsGroupBy.ADVERTISER],
        [StatsMetric.CAMPAIGN_COST, StatsMetric.CLICKS_COUNT],
    )

    (call,) = api_mock.calls
    assert dict(call.request.url.params) == {
        "campaignType": "PERFORMANCE",
        "dayFrom": "2020-09-01",
        "dayTo": "2020-09-01",
        "groupBy": "day-advertiser",
        "metrics": "campaignCost-clicksCount",
    }
    assert stats.advertiser == "xyz"


@pytest.mark.parametrize(
    "param,value,query_value",
    [
        ("advertisers", ["advhash1", "advhash2"], "advhash1,advhash2"),
        ("count_convention", CountConvention.ATTRIBUTED_POST_CLICK, "ATTRIBUTED"),
        ("currency", "USD", "USD"),
        ("subcampaigns", ["hash1", "hash2"], "hash1-hash2"),
        ("user_segments", [UserSegment.BUYERS, UserSegment.SHOPPERS], "BUYERS-SHOPPERS"),
        ("device_types", DeviceType.PC, "PC"),
        ("placement", DpaPlacement.DESKTOP, "DESKTOP"),
    ],
)
def test_get_advertisers_summary_stats_extra_params(
    api: Client,
    api_mock: respx.MockRouter,
    day_from: date,
    day_to: date,
    param: str,
    value: Any,
    query_value: str,
) -> None:
    api_mock.get(f"/advertisers-summary-stats").respond(
        200,
        json={"status": "ok", "data": []},
    )
    extra_params = {param: value}
    api.get_advertisers_summary_stats(
        CampaignType.PERFORMANCE,
        day_from,
        day_to,
        [StatsGroupBy.DAY, StatsGroupBy.ADVERTISER],
        [StatsMetric.CAMPAIGN_COST, StatsMetric.CLICKS_COUNT],
        **extra_params,
    )

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


def test_last_seen_tags_stats(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/last-seen-tags-stats").respond(
        200,
        json={"status": "ok", "data": [{"lastTagHour": "123-456", "impsCount": 123, "clicksCount": 456}]},
    )

    (stats,) = api.get_last_seen_tags_stats(
        adv_hash,
        day_from,
        day_to,
    )

    (call,) = api_mock.calls
    assert dict(call.request.url.params) == {"dayFrom": "2020-09-01", "dayTo": "2020-09-01"}
    assert stats.last_tag_hour == "123-456"


@pytest.mark.parametrize(
    "param,value,query_value",
    [
        ("subcampaigns", ["hash1", "hash2"], "hash1-hash2"),
    ],
)
def test_last_seen_tags_stats_with_extra_params(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
    param: str,
    value: Any,
    query_value: str,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/last-seen-tags-stats").respond(
        200,
        json={"status": "ok", "data": []},
    )

    extra_params = {param: value}
    api.get_last_seen_tags_stats(
        adv_hash,
        day_from,
        day_to,
        **extra_params,
    )

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


def test_win_rate_stats(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/win-rate-stats").respond(
        200,
        json={"status": "ok", "data": [{"day": "2020-09-01", "won": 123, "total": 12345}]},
    )

    (stats,) = api.get_win_rate_stats(
        adv_hash,
        day_from,
        day_to,
    )

    (call,) = api_mock.calls
    assert dict(call.request.url.params) == {"dayFrom": "2020-09-01", "dayTo": "2020-09-01"}
    assert str(stats.day) == "2020-09-01"


@pytest.mark.parametrize(
    "param,value,query_value",
    [
        ("subcampaigns", ["hash1", "hash2"], "hash1-hash2"),
    ],
)
def test_win_rate_stats_with_extra_params(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
    param: str,
    value: Any,
    query_value: str,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/win-rate-stats").respond(200, json={"status": "ok", "data": []})

    extra_params = {param: value}
    api.get_win_rate_stats(
        adv_hash,
        day_from,
        day_to,
        **extra_params,
    )

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


def test_top_hosts_stats(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/top-hosts-stats").respond(
        200,
        json={"status": "ok", "data": [{"host": "xyz", "value": 123}]},
    )

    (stats,) = api.get_top_hosts_stats(
        adv_hash,
        day_from,
        day_to,
        TopStatsRankedBy.CLICKS,
    )

    (call,) = api_mock.calls
    assert dict(call.request.url.params) == {"dayFrom": "2020-09-01", "dayTo": "2020-09-01", "rankedBy": "CLICKS"}
    assert stats.host == "xyz"


@pytest.mark.parametrize(
    "param,value,query_value",
    [
        ("subcampaigns", ["hash1", "hash2"], "hash1-hash2"),
    ],
)
def test_top_hosts_stats_with_extra_params(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
    param: str,
    value: Any,
    query_value: str,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/top-hosts-stats").respond(200, json={"status": "ok", "data": []})

    extra_params = {param: value}
    api.get_top_hosts_stats(
        adv_hash,
        day_from,
        day_to,
        TopStatsRankedBy.CLICKS,
        **extra_params,
    )

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


def test_top_in_apps_stats(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/top-in-apps-stats").respond(
        200,
        json={"status": "ok", "data": [{"appName": "name", "value": 123}]},
    )

    (stats,) = api.get_top_in_apps_stats(
        adv_hash,
        day_from,
        day_to,
        TopStatsRankedBy.CLICKS,
    )

    (call,) = api_mock.calls
    assert dict(call.request.url.params) == {"dayFrom": "2020-09-01", "dayTo": "2020-09-01", "rankedBy": "CLICKS"}
    assert stats.app_name == "name"


@pytest.mark.parametrize(
    "param,value,query_value",
    [
        ("subcampaigns", ["hash1", "hash2"], "hash1-hash2"),
    ],
)
def test_top_in_apps_stats_with_extra_params(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
    param: str,
    value: Any,
    query_value: str,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/top-in-apps-stats").respond(200, json={"status": "ok", "data": []})

    extra_params = {param: value}
    api.get_top_in_apps_stats(
        adv_hash,
        day_from,
        day_to,
        TopStatsRankedBy.CLICKS,
        **extra_params,
    )

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


def test_rtb_deduplication_stats_stats(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/rtb-deduplication-stats").respond(
        200,
        json={
            "status": "ok",
            "data": [
                {
                    "quarter": "01 (2023)",
                    "day": "2020-09-01",
                    "clicksCount": 111,
                    "impsCount": 222,
                    "attributedConversionsCount": 333,
                    "allConversionsCount": 444,
                    "countDecuplicationRate": 555.55,
                    "attributedConversionsValue": 666.66,
                    "allConversionsValue": 777.7,
                    "valueDeduplicationRate": 0.888,
                }
            ],
        },
    )

    (stats,) = api.get_rtb_deduplication_stats(adv_hash, day_from, day_to, [StatsGroupBy.QUARTER, StatsGroupBy.DAY])

    (call,) = api_mock.calls
    assert dict(call.request.url.params) == {"dayFrom": "2020-09-01", "dayTo": "2020-09-01", "groupBy": "quarter-day"}
    assert str(stats.day) == "2020-09-01"


@pytest.mark.parametrize(
    "param,value,query_value",
    [
        ("subcampaigns", ["hash1", "hash2"], "hash1-hash2"),
    ],
)
def test_rtb_deduplication_stats_with_extra_params(
    api: Client,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
    param: str,
    value: Any,
    query_value: str,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/rtb-deduplication-stats").respond(200, json={"status": "ok", "data": []})

    extra_params = {param: value}
    api.get_rtb_deduplication_stats(
        adv_hash,
        day_from,
        day_to,
        [StatsGroupBy.DAY],
        **extra_params,
    )

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value
