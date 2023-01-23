"""Tests for async client."""
# pylint: disable=too-many-arguments
from datetime import date
from typing import Any, AsyncIterator, Dict

import pytest
import respx
from httpx import Response

from rtbhouse_sdk.client import AsyncClient, BasicAuth
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
async def api_client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(auth=BasicAuth("test", "test")) as cli:
        yield cli


async def test_client_close() -> None:
    cli = AsyncClient(auth=BasicAuth("test", "test"))
    await cli.close()


async def test_client_as_context_manager() -> None:
    async with AsyncClient(auth=BasicAuth("test", "test")):
        pass


async def test_get_user_info(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    user_info_response: Dict[str, Any],
) -> None:
    api_mock.get("/user/info").respond(200, json=user_info_response)

    data = await api.get_user_info()

    assert data.hash_id == "hid"


async def test_get_advertisers(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    advertisers_response: Dict[str, Any],
) -> None:
    api_mock.get("/advertisers").respond(200, json=advertisers_response)

    (advertiser,) = await api.get_advertisers()

    assert advertiser.name == "Adv"


async def test_get_advertiser(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    advertiser_response: Dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}").respond(200, json=advertiser_response)

    advertiser = await api.get_advertiser(adv_hash)

    assert advertiser.name == "Adv"


async def test_get_invoicing_data(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    invoice_data_response: Dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/client").respond(200, json=invoice_data_response)

    invoice_data = await api.get_invoicing_data(adv_hash)

    assert invoice_data.company_name == "Ltd"


async def test_get_offer_categories(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    offer_categories_response: Dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/offer-categories").respond(200, json=offer_categories_response)

    (offer_cat,) = await api.get_offer_categories(adv_hash)

    assert offer_cat.name == "full cat"


async def test_get_offers(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    offers_response: Dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/offers").respond(200, json=offers_response)

    (offer,) = await api.get_offers(adv_hash)

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
async def test_get_offers_with_extra_params(
    api: AsyncClient, api_mock: respx.MockRouter, adv_hash: str, param: str, value: Any, query_value: Any
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/offers").respond(200, json={"status": "ok", "data": []})

    extra_params = {param: value}
    await api.get_offers(adv_hash=adv_hash, **extra_params)

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


async def test_get_advertiser_campaigns(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    advertiser_campaigns_response: Dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/campaigns").respond(200, json=advertiser_campaigns_response)

    (campaign,) = await api.get_advertiser_campaigns(adv_hash)

    assert campaign.name == "Campaign"

    (call,) = api_mock.calls
    assert dict(call.request.url.params) == {}


@pytest.mark.parametrize(
    "param,value,query_value",
    [
        ("exclude_archived", True, "true"),
    ],
)
async def test_get_advertiser_campaigns_with_extra_params(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    param: str,
    value: Any,
    query_value: Any,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/campaigns").respond(200, json={"status": "ok", "data": []})

    extra_params = {param: value}
    await api.get_advertiser_campaigns(adv_hash=adv_hash, **extra_params)

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


async def test_get_billing(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
    billing_response: Dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/billing").respond(200, json=billing_response)

    billing = await api.get_billing(adv_hash, day_from, day_to)

    (bill,) = billing.bills
    assert billing.initial_balance == -100
    assert bill.day == date(2020, 11, 25)


async def test_get_rtb_creatives(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    rtb_creatives_response: Dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/rtb-creatives").respond(200, json=rtb_creatives_response)

    (rtb_creative,) = await api.get_rtb_creatives(adv_hash)

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
async def test_get_rtb_creatives_with_extra_params(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    param: str,
    value: Any,
    query_value: Any,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/rtb-creatives").respond(200, json={"status": "ok", "data": []})

    extra_params = {param: value}
    await api.get_rtb_creatives(adv_hash=adv_hash, **extra_params)

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


async def test_get_rtb_conversions(
    api: AsyncClient,
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

    conversions = []
    async for conv in api.get_rtb_conversions(adv_hash, day_from, day_to):
        conversions.append(conv)

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
async def test_get_rtb_conversions_with_extra_params(
    api: AsyncClient,
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
    conversions = []
    async for conv in api.get_rtb_conversions(adv_hash, day_from, day_to, **extra_params):
        conversions.append(conv)

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


async def test_get_rtb_stats(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/rtb-stats").respond(
        200,
        json={"status": "ok", "data": [{"day": "2022-01-01", "advertiser": "xyz", "campaignCost": 51.0}]},
    )

    (stats,) = await api.get_rtb_stats(
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
    ],
)
async def test_get_rtb_stats_extra_params(
    api: AsyncClient,
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

    await api.get_rtb_stats(
        adv_hash, day_from, day_to, [StatsGroupBy.ADVERTISER], [StatsMetric.CAMPAIGN_COST], **extra_params
    )

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


async def test_get_summary_stats(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/summary-stats").respond(
        200,
        json={"status": "ok", "data": [{"day": "2022-01-01", "advertiser": "xyz", "campaignCost": 108.0}]},
    )

    (stats,) = await api.get_summary_stats(
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
async def test_get_summary_stats_extra_params(
    api: AsyncClient,
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
    await api.get_summary_stats(
        adv_hash,
        day_from,
        day_to,
        [StatsGroupBy.ADVERTISER, StatsGroupBy.DAY],
        [StatsMetric.CAMPAIGN_COST, StatsMetric.CR],
        **extra_params,
    )

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


async def test_advertisers_summary_stats(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    day_from: date,
    day_to: date,
) -> None:
    api_mock.get("/advertisers-summary-stats").respond(
        200,
        json={
            "status": "ok",
            "data": [{"day": "2022-01-01", "advertiser": "xyz", "campaignCost": 108.0, "clickCount": 231}],
        },
    )

    (stats,) = await api.get_advertisers_summary_stats(
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
async def test_get_advertisers_summary_stats_extra_params(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    day_from: date,
    day_to: date,
    param: str,
    value: Any,
    query_value: str,
) -> None:
    api_mock.get("/advertisers-summary-stats").respond(
        200,
        json={"status": "ok", "data": []},
    )
    extra_params = {param: value}
    await api.get_advertisers_summary_stats(
        CampaignType.PERFORMANCE,
        day_from,
        day_to,
        [StatsGroupBy.DAY, StatsGroupBy.ADVERTISER],
        [StatsMetric.CAMPAIGN_COST, StatsMetric.CLICKS_COUNT],
        **extra_params,
    )

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


async def test_last_seen_tags_stats(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/last-seen-tags-stats").respond(
        200,
        json={"status": "ok", "data": [{"lastTagHour": "123-456", "impsCount": 123, "clicksCount": 456}]},
    )

    (stats,) = await api.get_last_seen_tags_stats(
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
async def test_last_seen_tags_stats_with_extra_params(
    api: AsyncClient,
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
    await api.get_last_seen_tags_stats(
        adv_hash,
        day_from,
        day_to,
        **extra_params,
    )

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


async def test_win_rate_stats(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/win-rate-stats").respond(
        200,
        json={"status": "ok", "data": [{"day": "2020-09-01", "won": 123, "total": 12345}]},
    )

    (stats,) = await api.get_win_rate_stats(
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
async def test_win_rate_stats_with_extra_params(
    api: AsyncClient,
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
    await api.get_win_rate_stats(
        adv_hash,
        day_from,
        day_to,
        **extra_params,
    )

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


async def test_top_hosts_stats(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/top-hosts-stats").respond(
        200,
        json={"status": "ok", "data": [{"host": "xyz", "value": 123}]},
    )

    (stats,) = await api.get_top_hosts_stats(
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
async def test_top_hosts_stats_with_extra_params(
    api: AsyncClient,
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
    await api.get_top_hosts_stats(
        adv_hash,
        day_from,
        day_to,
        TopStatsRankedBy.CLICKS,
        **extra_params,
    )

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


async def test_top_in_apps_stats(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/top-in-apps-stats").respond(
        200,
        json={"status": "ok", "data": [{"appName": "name", "value": 123}]},
    )

    (stats,) = await api.get_top_in_apps_stats(
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
async def test_top_in_apps_stats_with_extra_params(
    api: AsyncClient,
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
    await api.get_top_in_apps_stats(
        adv_hash,
        day_from,
        day_to,
        TopStatsRankedBy.CLICKS,
        **extra_params,
    )

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value


async def test_rtb_deduplication_stats_stats(
    api: AsyncClient,
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

    (stats,) = await api.get_rtb_deduplication_stats(
        adv_hash, day_from, day_to, [StatsGroupBy.QUARTER, StatsGroupBy.DAY]
    )

    (call,) = api_mock.calls
    assert dict(call.request.url.params) == {"dayFrom": "2020-09-01", "dayTo": "2020-09-01", "groupBy": "quarter-day"}
    assert str(stats.day) == "2020-09-01"


@pytest.mark.parametrize(
    "param,value,query_value",
    [
        ("subcampaigns", ["hash1", "hash2"], "hash1-hash2"),
    ],
)
async def test_rtb_deduplication_stats_with_extra_params(
    api: AsyncClient,
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
    await api.get_rtb_deduplication_stats(
        adv_hash,
        day_from,
        day_to,
        [StatsGroupBy.DAY],
        **extra_params,
    )

    (call,) = api_mock.calls
    assert call.request.url.params[to_camel_case(param)] == query_value
