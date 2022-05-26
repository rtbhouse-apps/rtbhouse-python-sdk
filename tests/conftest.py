import copy

import pytest
import respx


@pytest.fixture()
def adv_hash():
    return "advhash"


@pytest.fixture(autouse=True)
def mocked_response():
    with respx.mock() as mock:  # pylint: disable=not-context-manager
        yield mock


@pytest.fixture
def user_info_response():
    return {
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
    }


@pytest.fixture
def advertisers_response():
    return {
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
    }


@pytest.fixture
def advertiser_response():
    return {
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
    }


@pytest.fixture
def invoice_data_response():
    return {
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
    }


@pytest.fixture
def offer_categories_response():
    return {
        "status": "ok",
        "data": [
            {
                "categoryId": "123",
                "identifier": "id56",
                "name": "full cat",
                "activeOffersNumber": 0,
            }
        ],
    }


@pytest.fixture
def offers_response():
    return {
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
    }


@pytest.fixture
def advertiser_campaigns_response():
    return {
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
    }


@pytest.fixture
def billing_response():
    return {
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
    }


@pytest.fixture
def rtb_creatives_response():
    return {
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
    }


@pytest.fixture(name="conversions_with_next_cursor_response")
def conversions_with_next_cursor_response_fixture():
    return {
        "status": "ok",
        "data": {
            "rows": [
                {
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
            ],
            "nextCursor": "123",
            "total": 1,
        },
    }


@pytest.fixture
def conversions_without_next_cursor_response(conversions_with_next_cursor_response):
    data = copy.deepcopy(conversions_with_next_cursor_response)
    data["data"]["nextCursor"] = None
    return data
