import warnings
from requests import request
from . import __version__ as sdk_version


API_BASE_URL = "https://api.panel.rtbhouse.com"
API_VERSION = 'v1'
DEFAULT_TIMEOUT = 60


class Conversions:
    POST_VIEW = 'POST_VIEW'
    ATTRIBUTED_POST_CLICK = 'ATTRIBUTED'
    ALL_POST_CLICK = 'ALL_POST_CLICK'


class UserSegment:
    VISITORS = 'VISITORS'
    SHOPPERS = 'SHOPPERS'
    BUYERS = 'BUYERS'


class DeviceType:
    PC = 'PC'
    MOBILE = 'MOBILE'
    PHONE = 'PHONE'
    TABLET = 'TABLET'
    TV = 'TV'
    GAME_CONSOLE = 'GAME_CONSOLE'
    OTHER = 'OTHER'
    UNKNOWN = 'UNKNOWN'


class ReportsApiException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class ReportsApiRequestException(ReportsApiException):
    message = 'Unexpected error'
    app_code = 'UNKNOWN'
    errors = {}

    def __init__(self, res):
        try:
            self._res_data = res.json()
            self.message = self._res_data.get('message')
            self.app_code = self._res_data.get('appCode')
            self.errors = self._res_data.get('errors')
        except Exception:
            self.message = '{} ({})'.format(res.reason, str(res.status_code))


class ReportsApiSession:
    def __init__(self, username, password, timeout=DEFAULT_TIMEOUT):
        self._username = username
        self._password = password
        self._session = None
        self._timeout = timeout

    @property
    def session(self):
        if not self._session:
            self._session = self._create_session()

        return self._session

    def _validate_response(self, res):
        newest_version = res.headers.get('X-Current-Api-Version')
        if newest_version != API_VERSION:
            warnings.warn(
                'Used api version ({}) is outdated, use newest version ({}) by updating '
                'rtbhouse_sdk package.'.format(API_VERSION, newest_version))
        if res.ok:
            return

        if res.status_code == 410:
            raise ReportsApiException(
                'Unsupported api version ({}), use newest version ({}) by updating rtbhouse_sdk package.'
                .format(API_VERSION, res.headers.get('X-Current-Api-Version')))
        raise ReportsApiRequestException(res)

    def _make_request(self, method, path, *args, **kwargs):
        base_url = '{}/{}'.format(API_BASE_URL, API_VERSION)
        kwargs['timeout'] = self._timeout
        kwargs.setdefault('headers', {})['user-agent'] = 'rtbhouse-python-sdk/{}'.format(sdk_version)

        res = request(method, base_url + path, *args, **kwargs)
        self._validate_response(res)
        return res

    def _create_session(self):
        res = self._make_request('post', '/auth/login', json={'login': self._username, 'password': self._password})
        return res.cookies.get('session')

    def _get(self, path, params=None):
        res = self._make_request('get', path, cookies={'session': self.session}, params=params)
        try:
            res_json = res.json()
            return res_json.get('data') or {}
        except Exception:
            raise ReportsApiException('Invalid response format')

    def get_user_info(self):
        data = self._get('/user/info')
        return {
            'username': data.get('login'),
            'email': data.get('email'),
        }

    def get_advertisers(self):
        return self._get('/advertisers')

    def get_advertiser(self, adv_hash):
        return self._get('/advertisers/' + adv_hash)

    def get_invoicing_data(self, adv_hash):
        return self._get('/advertisers/' + adv_hash + '/client')

    def get_offer_categories(self, adv_hash):
        return self._get('/advertisers/' + adv_hash + '/offer-categories')

    def get_offers(self, adv_hash):
        return self._get('/advertisers/' + adv_hash + '/offers')

    def get_advertiser_campaigns(self, adv_hash):
        return self._get('/advertisers/' + adv_hash + '/campaigns')

    def get_billing(self, adv_hash, day_from, day_to):
        return self._get('/advertisers/' + adv_hash + '/billing', {
            'dayFrom': day_from, 'dayTo': day_to
        })

    def get_campaign_stats_total(self, adv_hash, day_from, day_to, group_by='day',
                                 convention_type=Conversions.ATTRIBUTED_POST_CLICK):
        return self._get('/advertisers/' + adv_hash + '/campaign-stats-merged', {
            'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by, 'countConvention': convention_type
        })

    # RTB

    def get_rtb_creatives(self, adv_hash):
        return self._get('/advertisers/' + adv_hash + '/creatives')

    def get_rtb_campaign_stats(self, adv_hash, day_from, day_to, group_by='day',
                               convention_type=Conversions.ATTRIBUTED_POST_CLICK, user_segment=None,
                               campaign_hash=None):
        params = {'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by, 'countConvention': convention_type}

        if user_segment is not None:
            params['userSegment'] = user_segment

        if campaign_hash is not None:
            params['campaigns'] = campaign_hash

        return self._get('/advertisers/' + adv_hash + '/campaign-stats', params)

    def get_rtb_conversions(self, adv_hash, day_from, day_to, convention_type=Conversions.ATTRIBUTED_POST_CLICK):

        return self._get('/advertisers/' + adv_hash + '/conversions', {
            'dayFrom': day_from, 'dayTo': day_to, 'conversionType': convention_type
        })

    def get_rtb_category_stats(self, adv_hash, day_from, day_to, group_by='categoryId',
                               convention_type=Conversions.ATTRIBUTED_POST_CLICK, user_segment=None):
        params = {'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by, 'countConvention': convention_type}

        if user_segment is not None:
            params['userSegment'] = user_segment

        return self._get('/advertisers/' + adv_hash + '/category-stats', params)

    def get_rtb_creative_stats(self, adv_hash, day_from, day_to, group_by='creativeId',
                               convention_type=Conversions.ATTRIBUTED_POST_CLICK, user_segment=None):
        params = {'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by, 'countConvention': convention_type}

        if user_segment is not None:
            params['userSegment'] = user_segment

        return self._get('/advertisers/' + adv_hash + '/creative-stats', params)

    def get_rtb_device_stats(self, adv_hash, day_from, day_to, group_by='deviceType',
                             convention_type=Conversions.ATTRIBUTED_POST_CLICK,
                             device_type=None, campaign_hash=None):
        params = {
            'dayFrom': day_from,
            'dayTo': day_to,
            'groupBy': group_by,
            'countConvention': convention_type
        }
        if device_type is not None:
            params['deviceType'] = device_type
        if campaign_hash is not None:
            params['campaigns'] = campaign_hash

        return self._get('/advertisers/' + adv_hash + '/device-stats', params)

    def get_rtb_country_stats(self, adv_hash, day_from, day_to, group_by='country',
                              convention_type=Conversions.ATTRIBUTED_POST_CLICK, user_segment=None):
        params = {'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by, 'countConvention': convention_type}

        if user_segment is not None:
            params['userSegment'] = user_segment

        return self._get('/advertisers/' + adv_hash + '/country-stats', params)

    # DPA

    def get_dpa_accounts(self, adv_hash):
        return self._get('/advertisers/' + adv_hash + '/dpa/accounts')

    def get_dpa_creatives(self, account_hash):
        return self._get('/preview/dpa/' + account_hash)

    def get_dpa_campaign_stats(self, adv_hash, day_from, day_to, group_by='day',
                               convention_type=Conversions.ATTRIBUTED_POST_CLICK):
        return self._get('/advertisers/' + adv_hash + '/dpa/campaign-stats', {
            'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by, 'countConvention': convention_type
        })

    def get_dpa_conversions(self, adv_hash, day_from, day_to):
        return self._get('/advertisers/' + adv_hash + '/dpa/conversions', {
            'dayFrom': day_from, 'dayTo': day_to
        })
