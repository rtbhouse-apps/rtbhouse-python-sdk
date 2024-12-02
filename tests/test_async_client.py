"""Tests for async client."""

# pylint: disable=too-many-arguments
from collections.abc import AsyncIterator
from datetime import date
from typing import Any

import pytest
import respx
from httpx import Response

from rtbhouse_sdk.client import AsyncClient, BasicAuth
from rtbhouse_sdk.schema import StatsGroupBy, StatsMetric


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
    user_info_response: dict[str, Any],
) -> None:
    api_mock.get("/user/info").respond(200, json=user_info_response)

    data = await api.get_user_info()

    assert data.hash_id == "hid"


async def test_get_advertisers(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    advertisers_response: dict[str, Any],
) -> None:
    api_mock.get("/advertisers").respond(200, json=advertisers_response)

    (advertiser,) = await api.get_advertisers()

    assert advertiser.name == "Adv"


async def test_get_advertiser(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    advertiser_response: dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}").respond(200, json=advertiser_response)

    advertiser = await api.get_advertiser(adv_hash)

    assert advertiser.name == "Adv"


async def test_get_invoicing_data(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    invoice_data_response: dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/client").respond(200, json=invoice_data_response)

    invoice_data = await api.get_invoicing_data(adv_hash)

    assert invoice_data.company_name == "Ltd"


async def test_get_offer_categories(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    offer_categories_response: dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/offer-categories").respond(200, json=offer_categories_response)

    (offer_cat,) = await api.get_offer_categories(adv_hash)

    assert offer_cat.name == "full cat"


async def test_get_offers(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    offers_response: dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/offers").respond(200, json=offers_response)

    (offer,) = await api.get_offers(adv_hash)

    assert offer.full_name == "FN"
    assert offer.images[0].width == "700"


async def test_get_advertiser_campaigns(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    advertiser_campaigns_response: dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/campaigns").respond(200, json=advertiser_campaigns_response)

    (campaign,) = await api.get_advertiser_campaigns(adv_hash)

    assert campaign.name == "Campaign"


async def test_get_billing(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
    billing_response: dict[str, Any],
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
    rtb_creatives_response: dict[str, Any],
) -> None:
    api_mock.get(f"/advertisers/{adv_hash}/rtb-creatives").respond(200, json=rtb_creatives_response)

    (rtb_creative,) = await api.get_rtb_creatives(adv_hash)

    (call,) = api_mock.calls
    assert dict(call.request.url.params) == {}
    assert rtb_creative.hash == "hash"
    assert len(rtb_creative.previews) == 1


async def test_get_rtb_conversions(
    api: AsyncClient,
    api_mock: respx.MockRouter,
    adv_hash: str,
    day_from: date,
    day_to: date,
    conversions_with_next_cursor_response: dict[str, Any],
    conversions_without_next_cursor_response: dict[str, Any],
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
        [StatsGroupBy.ADVERTISER, StatsGroupBy.DAY, StatsGroupBy.HOUR],
        [StatsMetric.CAMPAIGN_COST, StatsMetric.CR],
    )

    (call,) = api_mock.calls
    assert dict(call.request.url.params) == {
        "dayFrom": "2020-09-01",
        "dayTo": "2020-09-01",
        "groupBy": "advertiser-day-hour",
        "metrics": "campaignCost-cr",
    }
    assert stats.advertiser == "xyz"


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
