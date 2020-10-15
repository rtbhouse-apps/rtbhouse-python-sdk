from requests import Response
from pytest import fixture, raises, warns

from config import USERNAME, PASSWORD
from rtbhouse_sdk.reports_api import (
    ReportsApiSession, UserSegment, Conversions, API_VERSION,
    ReportsApiException, ReportsApiRateLimitException,
)

DAY_FROM = '2020-09-01'
DAY_TO = '2020-09-01'

DPA_DAY_FROM = '2019-05-09'
DPA_DAY_TO = '2019-05-09'

# pylint: disable=redefined-outer-name


@fixture(scope='module')
def api():
    return ReportsApiSession(USERNAME, PASSWORD)


@fixture(scope='module')
def adv_hash(api):
    advertisers = api.get_advertisers()

    assert advertisers
    first_adv = advertisers[0]
    assert 'hash' in first_adv
    assert 'name' in first_adv
    assert 'status' in first_adv

    return first_adv['hash']


@fixture(scope='module')
def account_hash(api, adv_hash):
    dpa_accounts = api.get_dpa_accounts(adv_hash)

    assert dpa_accounts
    first_account = dpa_accounts[0]
    assert 'hash' in first_account
    assert 'name' in first_account

    return first_account['hash']


def test_raise_error_on_too_old_api_version(api):
    response = Response()
    newest_version = 'v{}'.format(int(API_VERSION.strip('v')) + 2)
    response.status_code = 410
    response.headers['X-Current-Api-Version'] = newest_version

    with raises(ReportsApiException) as cm:
        api._validate_response(response)  # pylint: disable=protected-access

    msg = 'Unsupported api version ({}), use newest version ({}) by updating rtbhouse_sdk package.' \
        .format(API_VERSION, newest_version)
    assert cm.value.message == msg


def test_raises_warning_on_not_the_newest_api_version(api):
    response = Response()
    newest_version = 'v{}'.format(int(API_VERSION.strip('v')) + 1)
    response.status_code = 200
    response.headers['X-Current-Api-Version'] = newest_version

    with warns(Warning) as cm:
        api._validate_response(response)  # pylint: disable=protected-access

    msg = 'Used api version ({}) is outdated, use newest version ({}) by updating ' \
        'rtbhouse_sdk package.'.format(API_VERSION, newest_version)
    assert str(cm[0].message) == msg


def test_parse_resource_usage_header():
    header = ';'.join([
        'WORKER_TIME-3600=11.78/10000000',
        'DB_QUERY_TIME-3600=4.62/500',
        'DB_QUERY_TIME-86400=17.995/5000',
    ])

    data = ReportsApiSession.parse_resource_usage_header(header)

    assert data['WORKER_TIME']['3600']['10000000'] == 11.78
    assert data['DB_QUERY_TIME']['3600']['500'] == 4.62
    assert data['DB_QUERY_TIME']['86400']['5000'] == 17.995


def test_parse_resource_usage_header_invalid_structure():
    assert ReportsApiSession.parse_resource_usage_header(None) == {}
    assert ReportsApiSession.parse_resource_usage_header(';') == {}
    assert ReportsApiSession.parse_resource_usage_header('asd;qwe121=-/') == {}
    assert ReportsApiSession.parse_resource_usage_header(
        'WORKER_TIME-3600=asd/10000000') == {}
    assert ReportsApiSession.parse_resource_usage_header(
        'WORKER_TIME-3600=asd10000000') == {}
    assert ReportsApiSession.parse_resource_usage_header(
        'WORKER_TIME3600asd10000000') == {}


def test_raises_error_on_resource_usage_limit_reached(api):
    header = ';'.join([
        'WORKER_TIME-3600=11.78/10000000',
        'DB_QUERY_TIME-3600=4.62/500',
        'DB_QUERY_TIME-86400=17.995/5000',
    ])
    response = Response()
    response.status_code = 429
    response.headers['X-Resource-Usage'] = header

    with raises(ReportsApiRateLimitException) as cm:
        api._validate_response(response)  # pylint: disable=protected-access

    data = cm.value.limits
    assert data['WORKER_TIME']['3600']['10000000'] == 11.78
    assert data['DB_QUERY_TIME']['3600']['500'] == 4.62
    assert data['DB_QUERY_TIME']['86400']['5000'] == 17.995


def test_get_user_info(api):
    data = api.get_user_info()

    assert 'username' in data
    assert 'email' in data


def test_get_advertiser(api, adv_hash):
    advertiser = api.get_advertiser(adv_hash)

    assert 'hash' in advertiser
    assert 'name' in advertiser
    assert 'status' in advertiser


def test_get_invoicing_data(api, adv_hash):
    inv_data = api.get_invoicing_data(adv_hash)

    assert 'invoicing' in inv_data


def test_get_offer_categories(api, adv_hash):
    offer_cat = api.get_offer_categories(adv_hash)

    assert offer_cat
    first_cat = offer_cat[0]
    assert 'name' in first_cat
    assert 'identifier' in first_cat


def test_get_offers(api, adv_hash):
    offers = api.get_offers(adv_hash)

    assert offers
    first_offer = offers[0]
    assert 'name' in first_offer
    assert 'identifier' in first_offer


def test_get_advertiser_campaigns(api, adv_hash):
    campaigns = api.get_advertiser_campaigns(adv_hash)

    assert campaigns
    first_camp = campaigns[0]
    assert 'hash' in first_camp
    assert 'name' in first_camp


def test_get_billing(api, adv_hash):
    billing = api.get_billing(adv_hash, DAY_FROM, DAY_TO)

    assert billing['bills']
    first_bill = billing['bills'][0]
    assert 'credit' in first_bill
    assert 'debit' in first_bill
    assert 'balance' in first_bill
    assert 'operation' in first_bill
    assert 'position' in first_bill
    assert 'recordNumber' in first_bill
    assert 'day' in first_bill


# RTB

def test_get_rtb_creatives(api, adv_hash):
    rtb_creatives = api.get_rtb_creatives(adv_hash)

    assert rtb_creatives
    rtb_creative = rtb_creatives[0]
    assert 'hash' in rtb_creative
    assert 'status' in rtb_creative
    assert 'previews' in rtb_creative
    assert rtb_creative['previews']
    preview = rtb_creative['previews'][0]
    assert 'width' in preview
    assert 'height' in preview
    assert 'offersNumber' in preview
    assert 'previewUrl' in preview


def _validate_get_rtb_dpa_summary_stats_response(stats, required_fields):
    assert len(stats) > 0
    stat = stats[0]

    for required_field in required_fields:
        assert required_field in stat


def test_get_rtb_stats1(api, adv_hash):
    _validate_get_rtb_dpa_summary_stats_response(
        api.get_rtb_stats(
            adv_hash,
            DAY_FROM, DAY_TO,
            {'day', 'subcampaign'},
            {'impsCount', 'clicksCount'},
            None,
            user_segments={UserSegment.BUYERS}
        ),
        {'day', 'subcampaign', 'subcampaignHash', 'impsCount', 'clicksCount'}
    )


def test_get_rtb_stats2(api, adv_hash):
    _validate_get_rtb_dpa_summary_stats_response(
        api.get_rtb_stats(
            adv_hash,
            DAY_FROM, DAY_TO,
            {'day', 'subcampaign'},
            {'impsCount', 'clicksCount', 'conversionsCount'},
            Conversions.ATTRIBUTED_POST_CLICK,
        ),
        {'day', 'subcampaign', 'subcampaignHash', 'impsCount', 'clicksCount', 'conversionsCount'}
    )


def test_get_rtb_stats3(api, adv_hash):
    _validate_get_rtb_dpa_summary_stats_response(
        api.get_rtb_stats(
            adv_hash,
            DAY_FROM, DAY_TO,
            {'day', 'userSegment'},
            {'cr'},
            Conversions.POST_VIEW,
        ),
        {'day', 'userSegment', 'cr'}
    )


def test_get_rtb_stats4(api, adv_hash):
    _validate_get_rtb_dpa_summary_stats_response(
        api.get_rtb_stats(
            adv_hash,
            DAY_FROM, DAY_TO,
            {'day', 'deviceType'},
            {'impsCount', 'clicksCount'},
            None,
        ),
        {'day', 'deviceType', 'impsCount', 'clicksCount'}
    )


def test_get_rtb_stats5(api, adv_hash):
    _validate_get_rtb_dpa_summary_stats_response(
        api.get_rtb_stats(
            adv_hash,
            DAY_FROM, DAY_TO,
            {'day', 'creative'},
            {'impsCount', 'clicksCount'},
            None,
        ),
        {'day', 'creative', 'creativeName', 'creativeType', 'impsCount', 'clicksCount'}
    )


def test_get_rtb_stats6(api, adv_hash):
    _validate_get_rtb_dpa_summary_stats_response(
        api.get_rtb_stats(
            adv_hash,
            DAY_FROM, DAY_TO,
            {'day', 'category'},
            {'impsCount', 'clicksCount', 'conversionsCount'},
            Conversions.ATTRIBUTED_POST_CLICK,
        ),
        {'day', 'category', 'categoryName', 'impsCount', 'clicksCount', 'conversionsCount'}
    )


def test_get_rtb_stats7(api, adv_hash):
    _validate_get_rtb_dpa_summary_stats_response(
        api.get_rtb_stats(
            adv_hash,
            DAY_FROM, DAY_TO,
            {'day', 'country'},
            {'impsCount', 'clicksCount'},
            None,
        ),
        {'day', 'country', 'impsCount', 'clicksCount'}
    )


def test_get_rtb_stats8(api, adv_hash):
    _validate_get_rtb_dpa_summary_stats_response(
        api.get_rtb_stats(
            adv_hash,
            DAY_FROM, DAY_TO,
            {'day', 'creative', 'country'},
            {'impsCount', 'clicksCount'},
            None,
        ),
        {'day', 'creative', 'country', 'impsCount', 'clicksCount'}
    )


def test_get_rtb_conversions(api, adv_hash):
    all_conversions = api.get_rtb_conversions(
        adv_hash, DAY_FROM, DAY_TO,
        Conversions.ALL_POST_CLICK,
    )
    assert all_conversions
    first_row = all_conversions[0]
    assert 'conversionValue' in first_row
    assert 'conversionIdentifier' in first_row

    attr_conversions = api.get_rtb_conversions(
        adv_hash, DAY_FROM, DAY_TO,
        Conversions.ATTRIBUTED_POST_CLICK,
    )
    assert attr_conversions
    attr_first_row = attr_conversions[0]
    assert 'conversionValue' in attr_first_row
    assert 'conversionIdentifier' in attr_first_row

    pv_conversions = api.get_rtb_conversions(
        adv_hash, DAY_FROM, DAY_TO,
        Conversions.POST_VIEW,
    )
    assert pv_conversions
    pv_first_row = pv_conversions[0]
    assert 'conversionValue' in pv_first_row
    assert 'conversionIdentifier' in pv_first_row


# DPA


def test_get_dpa_creatives(api, account_hash):
    dpa_creatives = api.get_dpa_creatives(account_hash)

    assert dpa_creatives
    first_row = dpa_creatives[0]
    assert 'adFormat' in first_row
    assert 'iframe' in first_row


def test_get_dpa_dpa_stats(api, adv_hash):
    dpa_stats = api.get_dpa_stats(
        adv_hash,
        DPA_DAY_FROM,
        DPA_DAY_TO,
        ['day'],
        ['impsCount', 'clicksCount'],
        None,
    )

    assert dpa_stats
    first_row = dpa_stats[0]
    assert 'day' in first_row
    assert 'impsCount' in first_row
    assert 'clicksCount' in first_row


def test_get_dpa_conversions(api, adv_hash):
    dpa_conversions = api.get_dpa_conversions(adv_hash, DPA_DAY_FROM, DPA_DAY_TO)

    assert dpa_conversions
    first_row = dpa_conversions[0]
    assert 'conversionValue' in first_row
    assert 'conversionIdentifier' in first_row


def test_get_summary_stats1(api, adv_hash):
    _validate_get_rtb_dpa_summary_stats_response(
        api.get_summary_stats(
            adv_hash,
            DAY_FROM, DAY_TO,
            {'day', 'subcampaign'},
            {'impsCount', 'clicksCount'},
            None,
        ),
        {'day', 'subcampaign', 'impsCount', 'clicksCount'}
    )


def test_get_summary_stats2(api, adv_hash):
    _validate_get_rtb_dpa_summary_stats_response(
        api.get_summary_stats(
            adv_hash,
            DAY_FROM, DAY_TO,
            {'day', 'subcampaign'},
            {'impsCount', 'clicksCount', 'conversionsCount'},
            Conversions.ATTRIBUTED_POST_CLICK,
        ),
        {'day', 'subcampaign', 'impsCount', 'clicksCount', 'conversionsCount'}
    )
