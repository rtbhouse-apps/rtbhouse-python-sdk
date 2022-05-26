from datetime import date

import pytest
import respx
from httpx import Response

from rtbhouse_sdk.client import (
    API_BASE_URL,
    API_VERSION,
    ApiException,
    ApiRateLimitException,
    Client,
    CountConvention,
    DeviceType,
    GroupBy,
    Metric,
    SubcampaignsFilter,
    UserSegment,
)

DAY_FROM = "2020-09-01"
DAY_TO = "2020-09-01"

BASE_URL = f"{API_BASE_URL}/{API_VERSION}"


@pytest.fixture()
def api():
    with Client.get_client("test", "test") as client:
        yield client


@pytest.fixture(autouse=True)
def mock_outgoing_requests():
    with respx.mock() as mock:
        yield mock


@pytest.fixture()
def mocked_response(mock_outgoing_requests):
    yield mock_outgoing_requests


def test_validate_response_raises_error_on_too_old_api_version(api):
    response = Response(410)
    newest_version = int(API_VERSION.strip("v")) + 2
    response.headers["X-Current-Api-Version"] = f"v{newest_version}"

    with pytest.raises(ApiException) as cm:
        api.validate_response(response)

    assert cm.value.message.startswith("Unsupported api version")


def test_validate_response_warns_on_not_the_newest_api_version(api):
    response = Response(200)
    newest_version = f'v{int(API_VERSION.strip("v")) + 1}'
    response.headers["X-Current-Api-Version"] = newest_version

    with pytest.warns(Warning) as cm:
        api.validate_response(response)

    msg = (
        f"Used api version ({API_VERSION}) is outdated, use newest version ({newest_version}) "
        f"by updating rtbhouse_sdk package."
    )
    assert str(cm[0].message) == msg


def test_validate_response_raises_error_on_resource_usage_limit_reached(api):
    header = ";".join(
        [
            "WORKER_TIME-3600=11.78/10000000",
            "DB_QUERY_TIME-3600=4.62/500",
            "DB_QUERY_TIME-86400=17.995/5000",
        ]
    )
    response = Response(429)
    response.headers["X-Resource-Usage"] = header

    with pytest.raises(ApiRateLimitException) as cm:
        api.validate_response(response)

    data = cm.value.limits
    assert data["WORKER_TIME"]["3600"]["10000000"] == 11.78
    assert data["DB_QUERY_TIME"]["3600"]["500"] == 4.62
    assert data["DB_QUERY_TIME"]["86400"]["5000"] == 17.995


def test_get_user_info(api, mocked_response, user_info_response):
    mocked_response.get(f"{BASE_URL}/user/info").respond(200, json=user_info_response)

    data = api.get_user_info()

    assert data.hash_id == "hid"


def test_get_advertisers(api, mocked_response, advertisers_response):
    mocked_response.get(f"{BASE_URL}/advertisers").respond(200, json=advertisers_response)

    (advertiser,) = api.get_advertisers()

    assert advertiser.name == "Adv"


def test_get_advertiser(api, adv_hash, mocked_response, advertiser_response):
    mocked_response.get(f"{BASE_URL}/advertisers/{adv_hash}").respond(200, json=advertiser_response)

    advertiser = api.get_advertiser(adv_hash)

    assert advertiser.name == "Adv"


def test_get_invoicing_data(api, adv_hash, mocked_response, invoice_data_response):
    mocked_response.get(f"{BASE_URL}/advertisers/{adv_hash}/client").respond(200, json=invoice_data_response)

    invoice_data = api.get_invoicing_data(adv_hash)

    assert invoice_data.company_name == "Ltd"


def test_get_offer_categories(api, adv_hash, mocked_response, offer_categories_response):
    mocked_response.get(f"{BASE_URL}/advertisers/{adv_hash}/offer-categories").respond(
        200, json=offer_categories_response
    )

    (offer_cat,) = api.get_offer_categories(adv_hash)

    assert offer_cat.name == "full cat"


def test_get_offers(api, adv_hash, mocked_response, offers_response):
    mocked_response.get(f"{BASE_URL}/advertisers/{adv_hash}/offers").respond(200, json=offers_response)

    (offer,) = api.get_offers(adv_hash)

    assert offer.full_name == "FN"
    assert offer.images[0].width == "700"


def test_get_advertiser_campaigns(api, adv_hash, mocked_response, advertiser_campaigns_response):
    mocked_response.get(f"{BASE_URL}/advertisers/{adv_hash}/campaigns").respond(200, json=advertiser_campaigns_response)

    (campaign,) = api.get_advertiser_campaigns(adv_hash)

    assert campaign.name == "Campaign"


def test_get_billing(api, adv_hash, mocked_response, billing_response):
    mocked_response.get(f"{BASE_URL}/advertisers/{adv_hash}/billing").respond(200, json=billing_response)

    billing = api.get_billing(adv_hash, DAY_FROM, DAY_TO)

    (bill,) = billing.bills
    assert billing.initial_balance == -100
    assert bill.day == date(2020, 11, 25)


def test_get_rtb_creatives(api, adv_hash, mocked_response, rtb_creatives_response):
    mocked_response.get(f"{BASE_URL}/advertisers/{adv_hash}/rtb-creatives").respond(200, json=rtb_creatives_response)

    (rtb_creative,) = api.get_rtb_creatives(adv_hash)

    assert dict(mocked_response.calls[0].request.url.params) == {}
    assert rtb_creative.hash == "hash"
    assert len(rtb_creative.previews) == 1


@pytest.mark.parametrize(
    "subcampaigns,active_only,params",
    [
        (
            ["abc", "def"],
            True,
            {
                "subcampaigns": "abc-def",
                "activeOnly": "true",
            },
        ),
        (
            SubcampaignsFilter.ACTIVE,
            False,
            {
                "subcampaigns": "ACTIVE",
                "activeOnly": "false",
            },
        ),
        (
            SubcampaignsFilter.ANY,
            None,
            {
                "subcampaigns": "ANY",
            },
        ),
    ],
)
def test_get_rtb_creatives_with_extra_params(api, adv_hash, mocked_response, subcampaigns, active_only, params):
    mocked_response.get(f"{BASE_URL}/advertisers/{adv_hash}/rtb-creatives").respond(
        200, json={"status": "ok", "data": []}
    )

    api.get_rtb_creatives(adv_hash, subcampaigns=subcampaigns, active_only=active_only)

    assert dict(mocked_response.calls[0].request.url.params) == params


def test_get_rtb_conversions(
    api, adv_hash, mocked_response, conversions_with_next_cursor_response, conversions_without_next_cursor_response
):
    mocked_response.get(f"{BASE_URL}/advertisers/{adv_hash}/conversions").mock(
        side_effect=[
            Response(200, json=conversions_with_next_cursor_response),
            Response(200, json=conversions_without_next_cursor_response),
        ]
    )

    conversions = api.get_rtb_conversions(adv_hash, DAY_FROM, DAY_TO)

    call1, call2 = mocked_response.calls
    assert set(call1.request.url.params.keys()) == {"dayFrom", "dayTo", "countConvention", "limit"}
    assert set(call2.request.url.params.keys()) == {"dayFrom", "dayTo", "countConvention", "limit", "nextCursor"}
    assert len(conversions) == 2
    assert conversions[0].conversion_hash == "chash"


def test_get_rtb_stats(api, adv_hash, mocked_response):
    mocked_response.get(f"{BASE_URL}/advertisers/{adv_hash}/rtb-stats").respond(
        200,
        json={"status": "ok", "data": [{"day": "2022-01-01", "advertiser": "xyz", "campaignCost": 51.0}]},
    )

    (stats,) = api.get_rtb_stats(
        adv_hash,
        DAY_FROM,
        DAY_TO,
        [GroupBy.ADVERTISER, GroupBy.DAY],
        [Metric.CAMPAIGN_COST, Metric.CR],
    )

    assert dict(mocked_response.calls[0].request.url.params) == {
        "dayFrom": "2020-09-01",
        "dayTo": "2020-09-01",
        "groupBy": "advertiser-day",
        "metrics": "campaign_cost-cr",
    }
    assert stats["advertiser"] == "xyz"


@pytest.mark.parametrize(
    "param,query_param,value,query_value",
    [
        ("count_convention", "countConvention", CountConvention.ATTRIBUTED_POST_CLICK, "ATTRIBUTED"),
        ("subcampaigns", "subcampaigns", "hash", "hash"),
        ("user_segments", "userSegments", [UserSegment.BUYERS, UserSegment.SHOPPERS], "BUYERS-SHOPPERS"),
        ("device_types", "deviceTypes", [DeviceType.PC, DeviceType.MOBILE], "PC-MOBILE"),
    ],
)
def test_get_rtb_stats_extra_params(api, adv_hash, mocked_response, param, query_param, value, query_value):
    mocked_response.get(f"{BASE_URL}/advertisers/{adv_hash}/rtb-stats").respond(
        200,
        json={"status": "ok", "data": []},
    )

    extra_params = {param: value}
    api.get_rtb_stats(adv_hash, DAY_FROM, DAY_TO, ["advertiser"], ["campaignCost"], **extra_params)

    assert mocked_response.calls[0].request.url.params[query_param] == query_value


def test_get_summary_stats(api, adv_hash, mocked_response):
    mocked_response.get(f"{BASE_URL}/advertisers/{adv_hash}/summary-stats").respond(
        200,
        json={"status": "ok", "data": [{"day": "2022-01-01", "advertiser": "xyz", "campaignCost": 108.0}]},
    )

    (stats,) = api.get_summary_stats(
        adv_hash,
        DAY_FROM,
        DAY_TO,
        [GroupBy.ADVERTISER, GroupBy.DAY],
        [Metric.CAMPAIGN_COST, Metric.CR],
    )

    assert dict(mocked_response.calls[0].request.url.params) == {
        "dayFrom": "2020-09-01",
        "dayTo": "2020-09-01",
        "groupBy": "advertiser-day",
        "metrics": "campaign_cost-cr",
    }
    assert stats["advertiser"] == "xyz"
