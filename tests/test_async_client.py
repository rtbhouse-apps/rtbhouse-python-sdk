"""Tests for async client."""
# pylint: disable=too-many-arguments
from datetime import date
from typing import Any, AsyncIterator, Dict

import pytest
import pytest_asyncio
import respx
from httpx import Response

from rtbhouse_sdk.client import AsyncClient, BasicAuth
from rtbhouse_sdk.schema import GroupBy, Metric


@pytest_asyncio.fixture(name="api")
async def api_client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(auth=BasicAuth("test", "test")) as cli:
        yield cli


@pytest.mark.asyncio
async def test_client_close() -> None:
    cli = AsyncClient(auth=BasicAuth("test", "test"))
    await cli.close()


@pytest.mark.asyncio
async def test_client_as_context_manager() -> None:
    async with AsyncClient(auth=BasicAuth("test", "test")):
        pass


@pytest.mark.asyncio
async def test_get_user_info(
    api: AsyncClient, base_url: str, mocked_response: respx.MockRouter, user_info_response: Dict[str, Any]
) -> None:
    mocked_response.get(f"{base_url}/user/info").respond(200, json=user_info_response)

    data = await api.get_user_info()

    assert data.hash_id == "hid"


@pytest.mark.asyncio
async def test_get_advertisers(
    api: AsyncClient, base_url: str, mocked_response: respx.MockRouter, advertisers_response: Dict[str, Any]
) -> None:
    mocked_response.get(f"{base_url}/advertisers").respond(200, json=advertisers_response)

    (advertiser,) = await api.get_advertisers()

    assert advertiser.name == "Adv"


@pytest.mark.asyncio
async def test_get_advertiser(
    api: AsyncClient,
    base_url: str,
    adv_hash: str,
    mocked_response: respx.MockRouter,
    advertiser_response: Dict[str, Any],
) -> None:
    mocked_response.get(f"{base_url}/advertisers/{adv_hash}").respond(200, json=advertiser_response)

    advertiser = await api.get_advertiser(adv_hash)

    assert advertiser.name == "Adv"


@pytest.mark.asyncio
async def test_get_invoicing_data(
    api: AsyncClient,
    base_url: str,
    adv_hash: str,
    mocked_response: respx.MockRouter,
    invoice_data_response: Dict[str, Any],
) -> None:
    mocked_response.get(f"{base_url}/advertisers/{adv_hash}/client").respond(200, json=invoice_data_response)

    invoice_data = await api.get_invoicing_data(adv_hash)

    assert invoice_data.company_name == "Ltd"


@pytest.mark.asyncio
async def test_get_offer_categories(
    api: AsyncClient,
    base_url: str,
    adv_hash: str,
    mocked_response: respx.MockRouter,
    offer_categories_response: Dict[str, Any],
) -> None:
    mocked_response.get(f"{base_url}/advertisers/{adv_hash}/offer-categories").respond(
        200, json=offer_categories_response
    )

    (offer_cat,) = await api.get_offer_categories(adv_hash)

    assert offer_cat.name == "full cat"


@pytest.mark.asyncio
async def test_get_offers(
    api: AsyncClient, base_url: str, adv_hash: str, mocked_response: respx.MockRouter, offers_response: Dict[str, Any]
) -> None:
    mocked_response.get(f"{base_url}/advertisers/{adv_hash}/offers").respond(200, json=offers_response)

    (offer,) = await api.get_offers(adv_hash)

    assert offer.full_name == "FN"
    assert offer.images[0].width == "700"


@pytest.mark.asyncio
async def test_get_advertiser_campaigns(
    api: AsyncClient,
    base_url: str,
    adv_hash: str,
    mocked_response: respx.MockRouter,
    advertiser_campaigns_response: Dict[str, Any],
) -> None:
    mocked_response.get(f"{base_url}/advertisers/{adv_hash}/campaigns").respond(200, json=advertiser_campaigns_response)

    (campaign,) = await api.get_advertiser_campaigns(adv_hash)

    assert campaign.name == "Campaign"


@pytest.mark.asyncio
async def test_get_billing(
    api: AsyncClient,
    base_url: str,
    adv_hash: str,
    day_from: date,
    day_to: date,
    mocked_response: respx.MockRouter,
    billing_response: Dict[str, Any],
) -> None:
    mocked_response.get(f"{base_url}/advertisers/{adv_hash}/billing").respond(200, json=billing_response)

    billing = await api.get_billing(adv_hash, day_from, day_to)

    (bill,) = billing.bills
    assert billing.initial_balance == -100
    assert bill.day == date(2020, 11, 25)


@pytest.mark.asyncio
async def test_get_rtb_creatives(
    api: AsyncClient,
    base_url: str,
    adv_hash: str,
    mocked_response: respx.MockRouter,
    rtb_creatives_response: Dict[str, Any],
) -> None:
    mocked_response.get(f"{base_url}/advertisers/{adv_hash}/rtb-creatives").respond(200, json=rtb_creatives_response)

    (rtb_creative,) = await api.get_rtb_creatives(adv_hash)

    assert dict(mocked_response.calls[0].request.url.params) == {}
    assert rtb_creative.hash == "hash"
    assert len(rtb_creative.previews) == 1


@pytest.mark.asyncio
async def test_get_rtb_conversions(
    api: AsyncClient,
    base_url: str,
    adv_hash: str,
    day_from: date,
    day_to: date,
    mocked_response: respx.MockRouter,
    conversions_with_next_cursor_response: Dict[str, Any],
    conversions_without_next_cursor_response: Dict[str, Any],
) -> None:
    mocked_response.get(f"{base_url}/advertisers/{adv_hash}/conversions").mock(
        side_effect=[
            Response(200, json=conversions_with_next_cursor_response),
            Response(200, json=conversions_without_next_cursor_response),
        ]
    )

    conversions = await api.get_rtb_conversions(adv_hash, day_from, day_to)

    assert len(conversions) == 2
    assert conversions[0].conversion_hash == "chash"


@pytest.mark.asyncio
async def test_get_rtb_stats(
    api: AsyncClient, base_url: str, adv_hash: str, day_from: date, day_to: date, mocked_response: respx.MockRouter
) -> None:
    mocked_response.get(f"{base_url}/advertisers/{adv_hash}/rtb-stats").respond(
        200,
        json={"status": "ok", "data": [{"day": "2022-01-01", "advertiser": "xyz", "campaignCost": 51.0}]},
    )

    (stats,) = await api.get_rtb_stats(
        adv_hash,
        day_from,
        day_to,
        [GroupBy.ADVERTISER, GroupBy.DAY],
        [Metric.CAMPAIGN_COST, Metric.CR],
    )

    assert dict(mocked_response.calls[0].request.url.params) == {
        "dayFrom": "2020-09-01",
        "dayTo": "2020-09-01",
        "groupBy": "advertiser-day",
        "metrics": "campaignCost-cr",
    }
    assert stats.advertiser == "xyz"


@pytest.mark.asyncio
async def test_get_summary_stats(
    api: AsyncClient, base_url: str, adv_hash: str, day_from: date, day_to: date, mocked_response: respx.MockRouter
) -> None:
    mocked_response.get(f"{base_url}/advertisers/{adv_hash}/summary-stats").respond(
        200,
        json={"status": "ok", "data": [{"day": "2022-01-01", "advertiser": "xyz", "campaignCost": 108.0}]},
    )

    (stats,) = await api.get_summary_stats(
        adv_hash,
        day_from,
        day_to,
        [GroupBy.ADVERTISER, GroupBy.DAY],
        [Metric.CAMPAIGN_COST, Metric.CR],
    )

    assert dict(mocked_response.calls[0].request.url.params) == {
        "dayFrom": "2020-09-01",
        "dayTo": "2020-09-01",
        "groupBy": "advertiser-day",
        "metrics": "campaignCost-cr",
    }
    assert stats.advertiser == "xyz"
