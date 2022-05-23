from datetime import date

import pytest
import responses
from requests import Response

from rtbhouse_sdk.client import (
    API_BASE_URL,
    API_VERSION,
    ApiException,
    ApiRateLimitException,
    Client,
    Conversions,
    DeviceType,
    UserSegment,
)

DAY_FROM = "2020-09-01"
DAY_TO = "2020-09-01"

BASE_URL = f"{API_BASE_URL}/{API_VERSION}"


@pytest.fixture()
def api():
    return Client("test", "test")


@pytest.fixture()
def adv_hash(api):
    return "advhash"


@pytest.fixture(autouse=True)
def mock_outgoing_requests():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture()
def mocked_response(mock_outgoing_requests):
    yield mock_outgoing_requests


def test_raise_error_on_too_old_api_version(api):
    response = Response()
    newest_version = int(API_VERSION.strip("v")) + 2
    response.status_code = 410
    response.headers["X-Current-Api-Version"] = f"v{newest_version}"

    with pytest.raises(ApiException) as cm:
        api._validate_response(response)

    assert cm.value.message.startswith("Unsupported api version")


def test_warn_on_not_the_newest_api_version(api):
    response = Response()
    newest_version = f'v{int(API_VERSION.strip("v")) + 1}'
    response.status_code = 200
    response.headers["X-Current-Api-Version"] = newest_version

    with pytest.warns(Warning) as cm:
        api._validate_response(response)

    msg = f"Used api version ({API_VERSION}) is outdated, use newest version ({newest_version}) by updating rtbhouse_sdk package."
    assert str(cm[0].message) == msg


def test_raise_error_on_resource_usage_limit_reached(api):
    header = ";".join(
        [
            "WORKER_TIME-3600=11.78/10000000",
            "DB_QUERY_TIME-3600=4.62/500",
            "DB_QUERY_TIME-86400=17.995/5000",
        ]
    )
    response = Response()
    response.status_code = 429
    response.headers["X-Resource-Usage"] = header

    with pytest.raises(ApiRateLimitException) as cm:
        api._validate_response(response)

    data = cm.value.limits
    assert data["WORKER_TIME"]["3600"]["10000000"] == 11.78
    assert data["DB_QUERY_TIME"]["3600"]["500"] == 4.62
    assert data["DB_QUERY_TIME"]["86400"]["5000"] == 17.995


def test_get_user_info(api, mocked_response):
    mocked_response.get(
        f"{BASE_URL}/user/info",
        json={
            "status": "ok",
            "data": {
                "hashId": "hid",
                "login": "john",
                "email": "em",
                "isClientUser": True,
                "isDemoUser": False,
                "isForceLoggedIn": False,
                "permissions": ["abc"],
                "countConvention": None,
            },
        },
    )
    data = api.get_user_info()

    assert data.hash_id == "hid"


def test_get_advertisers(api, mocked_response):
    mocked_response.get(
        f"{BASE_URL}/advertisers",
        json={
            "status": "ok",
            "data": [
                {
                    "hash": "hash",
                    "status": "ACTIVE",
                    "name": "Adv",
                    "currency": "USD",
                    "url": "url",
                    "createdAt": "2020-10-15T12:58:19.509985+00:00",
                    "features": {"enabled": ["abc"]},
                    "properties": {"key": "val"},
                }
            ],
        },
    )

    (advertiser,) = api.get_advertisers()

    assert advertiser.name == "Adv"


def test_get_advertiser(api, adv_hash, mocked_response):
    mocked_response.get(
        f"{BASE_URL}/advertisers/{adv_hash}",
        json={
            "data": {
                "hash": "hash",
                "status": "ACTIVE",
                "name": "Adv",
                "currency": "USD",
                "url": "url",
                "createdAt": "2020-10-15T12:58:19.509985+00:00",
                "properties": {"key": "val"},
                "version": "2020-10-15T12:58:19.509985+00:00",
                "feedIdentifier": "xyz",
                "country": "US",
            }
        },
    )

    advertiser = api.get_advertiser(adv_hash)

    assert advertiser.name == "Adv"


def test_get_invoicing_data(api, adv_hash, mocked_response):
    mocked_response.get(
        f"{BASE_URL}/advertisers/{adv_hash}/client",
        json={
            "status": "ok",
            "data": {
                "invoicing": {
                    "vat_number": "123",
                    "company_name": "Ltd",
                    "street1": "St",
                    "postal_code": "321",
                    "city": "Rotterdam",
                    "country": "Netherlands",
                    "email": "em",
                },
            },
        },
    )

    invoice_data = api.get_invoicing_data(adv_hash)

    assert invoice_data.company_name == "Ltd"


def test_get_offer_categories(api, adv_hash, mocked_response):
    mocked_response.get(
        f"{BASE_URL}/advertisers/{adv_hash}/offer-categories",
        json={
            "status": "ok",
            "data": [
                {
                    "categoryId": "123",
                    "identifier": "id56",
                    "name": "full cat",
                    "activeOffersNumber": 0,
                }
            ],
        },
    )

    (offer_cat,) = api.get_offer_categories(adv_hash)

    assert offer_cat.name == "full cat"


def test_get_offers(api, adv_hash, mocked_response):
    mocked_response.get(
        f"{BASE_URL}/advertisers/{adv_hash}/offers",
        json={
            "data": [
                {
                    "url": "url",
                    "fullName": "FN",
                    "identifier": "ident",
                    "id": "id",
                    "images": [
                        {
                            "added": "123",
                            "width": "700",
                            "height": "800",
                            "url": "url",
                            "hash": "hash",
                        }
                    ],
                    "name": "name",
                    "price": 99.99,
                    "categoryName": "cat",
                    "customProperties": {"prop": "val"},
                    "updatedAt": "2020-10-15T22:26:49.511000+00:00",
                    "status": "ACTIVE",
                }
            ]
        },
    )

    (offer,) = api.get_offers(adv_hash)

    assert offer.full_name == "FN"
    assert offer.images[0].width == "700"


def test_get_advertiser_campaigns(api, adv_hash, mocked_response):
    mocked_response.get(
        f"{BASE_URL}/advertisers/{adv_hash}/campaigns",
        json={
            "status": "ok",
            "data": [
                {
                    "hash": "hash",
                    "name": "Campaign",
                    "creativeIds": [543],
                    "status": "PAUSED",
                    "updatedAt": "2020-10-15T08:53:15.940369+00:00",
                    "rateCardId": "E76",
                    "isEditable": True,
                    "advertiserLimits": {"budgetDaily": 1, "budgetMonthly": 10},
                }
            ],
        },
    )

    (campaign,) = api.get_advertiser_campaigns(adv_hash)

    assert campaign.name == "Campaign"


def test_get_billing(api, adv_hash, mocked_response):
    mocked_response.get(
        f"{BASE_URL}/advertisers/{adv_hash}/billing",
        json={
            "status": "ok",
            "data": {
                "initialBalance": -100,
                "bills": [
                    {
                        "day": "2020-11-25",
                        "operation": "Cost of campaign",
                        "position": 2,
                        "credit": 0,
                        "debit": -102,
                        "balance": -200,
                        "recordNumber": 1,
                    }
                ],
            },
        },
    )

    billing = api.get_billing(adv_hash, DAY_FROM, DAY_TO)
    (bill,) = billing.bills

    assert billing.initial_balance == -100
    assert bill.day == date(2020, 11, 25)


def test_get_rtb_creatives(api, adv_hash, mocked_response):
    mocked_response.get(
        f"{BASE_URL}/advertisers/{adv_hash}/rtb-creatives",
        json={
            "status": "ok",
            "data": [
                {
                    "hash": "hash",
                    "status": "ACTIVE",
                    "previews": [
                        {
                            "width": 300,
                            "height": 200,
                            "offersNumber": 4,
                            "previewUrl": "url",
                        }
                    ],
                }
            ],
        },
    )

    (rtb_creative,) = api.get_rtb_creatives(adv_hash)
    assert mocked_response.calls[0].request.params == {}
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
                "activeOnly": "True",
            },
        ),
        (
            "ACTIVE",
            False,
            {
                "subcampaigns": "ACTIVE",
                "activeOnly": "False",
            },
        ),
        (
            "ANY",
            None,
            {
                "subcampaigns": "ANY",
            },
        ),
    ],
)
def test_get_rtb_creatives_with_extra_params(api, adv_hash, mocked_response, subcampaigns, active_only, params):
    mocked_response.get(f"{BASE_URL}/advertisers/{adv_hash}/rtb-creatives", json={"status": "ok", "data": []})

    api.get_rtb_creatives(adv_hash, subcampaigns=subcampaigns, active_only=active_only)

    assert mocked_response.calls[0].request.params == params


def test_get_rtb_conversions(api, adv_hash, mocked_response):
    conv_data = {
        "conversionTime": "2020-01-02T21:51:57.686000+00:00",
        "conversionIdentifier": "226",
        "conversionHash": "chash",
        "conversionClass": None,
        "cookieHash": "hash",
        "conversionValue": 13.3,
        "commissionValue": 3.0,
        "lastClickTime": "2020-01-02T21:35:06.279000+00:00",
        "lastImpressionTime": "2020-01-02T21:38:13.346000+00:00",
    }
    mocked_response.get(
        f"{BASE_URL}/advertisers/{adv_hash}/conversions",
        json={
            "status": "ok",
            "data": {
                "rows": [conv_data],
                "nextCursor": "123",
                "total": 1,
            },
        },
    )
    mocked_response.get(
        f"{BASE_URL}/advertisers/{adv_hash}/conversions",
        json={
            "status": "ok",
            "data": {
                "rows": [conv_data],
                "nextCursor": None,
                "total": 1,
            },
        },
    )

    conversions = api.get_rtb_conversions(adv_hash, DAY_FROM, DAY_TO)
    call1, call2 = mocked_response.calls
    assert set(call1.request.params.keys()) == {"dayFrom", "dayTo", "countConvention", "limit"}
    assert set(call2.request.params.keys()) == {"dayFrom", "dayTo", "countConvention", "limit", "nextCursor"}
    assert len(conversions) == 2
    assert conversions[0].conversion_hash == "chash"


def test_get_rtb_stats(api, adv_hash, mocked_response):
    mocked_response.get(
        f"{BASE_URL}/advertisers/{adv_hash}/rtb-stats",
        json={"status": "ok", "data": [{"day": "2022-01-01", "advertiser": "xyz", "campaignCost": 51.0}]},
    )

    (stats,) = api.get_rtb_stats(
        adv_hash,
        DAY_FROM,
        DAY_TO,
        ["advertiser", "day"],
        ["campaignCost", "cr"],
    )

    assert mocked_response.calls[0].request.params == {
        "dayFrom": "2020-09-01",
        "dayTo": "2020-09-01",
        "groupBy": "advertiser-day",
        "metrics": "campaignCost-cr",
    }
    assert stats["advertiser"] == "xyz"


@pytest.mark.parametrize(
    "param,query_param,value,query_value",
    [
        ("count_convention", "countConvention", Conversions.ATTRIBUTED_POST_CLICK, "ATTRIBUTED"),
        ("subcampaigns", "subcampaigns", "hash", "hash"),
        ("user_segments", "userSegments", [UserSegment.BUYERS, UserSegment.SHOPPERS], "BUYERS-SHOPPERS"),
        ("device_types", "deviceTypes", [DeviceType.PC, DeviceType.MOBILE], "PC-MOBILE"),
    ],
)
def test_get_rtb_stats_extra_params(api, adv_hash, mocked_response, param, query_param, value, query_value):
    mocked_response.get(
        f"{BASE_URL}/advertisers/{adv_hash}/rtb-stats",
        json={"status": "ok", "data": []},
    )

    extra_params = {param: value}
    api.get_rtb_stats(adv_hash, DAY_FROM, DAY_TO, ["advertiser"], ["campaignCost"], **extra_params)

    assert mocked_response.calls[0].request.params[query_param] == query_value


def test_get_summary_stats(api, adv_hash, mocked_response):
    mocked_response.get(
        f"{BASE_URL}/advertisers/{adv_hash}/summary-stats",
        json={"status": "ok", "data": [{"day": "2022-01-01", "advertiser": "xyz", "campaignCost": 108.0}]},
    )

    (stats,) = api.get_summary_stats(
        adv_hash,
        DAY_FROM,
        DAY_TO,
        ["advertiser", "day"],
        ["campaignCost", "cr"],
    )

    assert mocked_response.calls[0].request.params == {
        "dayFrom": "2020-09-01",
        "dayTo": "2020-09-01",
        "groupBy": "advertiser-day",
        "metrics": "campaignCost-cr",
    }
    assert stats["advertiser"] == "xyz"
