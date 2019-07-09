import warnings
from requests import request
from . import __version__ as sdk_version


API_BASE_URL = "https://api.panel.rtbhouse.com"
API_VERSION = 'v2'
DEFAULT_TIMEOUT = 60
MAX_CURSOR_ROWS_LIMIT = 10000


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
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class ReportsApiRequestException(ReportsApiException):
    message = 'Unexpected error'
    app_code = 'UNKNOWN'
    errors = {}

    def __init__(self, res):
        self.raw_response = res
        try:
            self._res_data = res.json()
        except Exception:
            message = '{} ({})'.format(res.reason, str(res.status_code))
        else:
            self.app_code = self._res_data.get('appCode')
            self.errors = self._res_data.get('errors')
            message = self._res_data.get('message')

        super().__init__(message)


class ReportsApiRateLimitException(ReportsApiRequestException):
    message = 'Resource usage limits reached'

    def __init__(self, res):
        super().__init__(res)
        self.limits = ReportsApiSession.parse_resource_usage_header(
            res.headers.get('X-Resource-Usage'))


class ReportsApiSession:
    def __init__(self, username, password, timeout=DEFAULT_TIMEOUT):
        self._username = username
        self._password = password
        self._timeout = timeout

    @staticmethod
    def parse_resource_usage_header(header):
        '''parse string like WORKER_TIME-3600=11.7/10000000;DB_QUERY_TIME-21600=4.62/2000 into dict
        '''
        if not header:
            return {}
        result = {}
        try:
            for line in header.split(';'):
                right, left = line.split('=')
                metric, time_span = right.split('-')
                used, limit = left.split('/')
                result.setdefault(metric, {}).setdefault(
                    time_span, {})[limit] = float(used)
        except ValueError:
            return {}
        return result

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

        if res.status_code == 429:
            raise ReportsApiRateLimitException(res)

        raise ReportsApiRequestException(res)

    def _make_request(self, method, path, *args, **kwargs):
        base_url = '{}/{}'.format(API_BASE_URL, API_VERSION)
        kwargs['timeout'] = self._timeout
        kwargs.setdefault('headers', {})[
            'user-agent'] = 'rtbhouse-python-sdk/{}'.format(sdk_version)

        res = request(method, base_url + path, *args, **kwargs)
        self._validate_response(res)
        return res

    def _get(self, path, params=None):
        res = self._make_request('get', path, auth=(
            self._username, self._password), params=params)
        try:
            res_json = res.json()
            return res_json.get('data') or {}
        except Exception:
            raise ReportsApiException('Invalid response format')

    def _get_from_cursor(self, path, params=None):
        res = self._get(
            path, params={**params, 'limit': MAX_CURSOR_ROWS_LIMIT})
        rows = res['rows']

        while res['nextCursor']:
            res = self._get(
                path, params={'nextCursor': res['nextCursor'], 'limit': MAX_CURSOR_ROWS_LIMIT})
            rows.extend(res['rows'])

        return rows

    def _map_stats_params(self, params):
        if 'groupBy' in params and isinstance(params['groupBy'], list):
            params['groupBy'] = '-'.join(params['groupBy'])
        return params

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

    def get_campaign_stats_total(self, adv_hash, day_from, day_to, group_by=None,
                                 convention_type=Conversions.ATTRIBUTED_POST_CLICK):
        if group_by is None:
            group_by = ['day']

        params = self._map_stats_params({
            'dayFrom': day_from,
            'dayTo': day_to,
            'groupBy': group_by,
            'countConvention': convention_type,
        })
        url = '/advertisers/{}/campaign-stats-merged'.format(adv_hash)

        return self._get(url, params)

    # RTB

    def get_rtb_creatives(self, adv_hash):
        return self._get('/advertisers/' + adv_hash + '/creatives')

    def get_rtb_campaign_stats(self, adv_hash, day_from, day_to, group_by=None,
                               convention_type=Conversions.ATTRIBUTED_POST_CLICK, user_segment=None,
                               campaign_hash=None):
        if group_by is None:
            group_by = ['day']

        params = {
            'dayFrom': day_from,
            'dayTo': day_to,
            'groupBy': group_by,
            'countConvention': convention_type,
        }
        if user_segment is not None:
            params['userSegment'] = user_segment
        if campaign_hash is not None:
            params['campaigns'] = campaign_hash
        params = self._map_stats_params(params)
        url = '/advertisers/{}/campaign-stats'.format(adv_hash)

        return self._get(url, params)

    def get_rtb_conversions(self, adv_hash, day_from, day_to, convention_type=Conversions.ATTRIBUTED_POST_CLICK):

        return self._get_from_cursor('/advertisers/' + adv_hash + '/conversions', {
            'dayFrom': day_from, 'dayTo': day_to, 'countConvention': convention_type
        })

    def get_rtb_category_stats(self, adv_hash, day_from, day_to, group_by=None,
                               convention_type=Conversions.ATTRIBUTED_POST_CLICK, user_segment=None):
        if group_by is None:
            group_by = ['categoryId']

        params = {
            'dayFrom': day_from,
            'dayTo': day_to,
            'groupBy': group_by,
            'countConvention': convention_type,
        }
        if user_segment is not None:
            params['userSegment'] = user_segment
        params = self._map_stats_params(params)
        url = '/advertisers/{}/category-stats'.format(adv_hash)

        return self._get(url, params)

    def get_rtb_creative_stats(self, adv_hash, day_from, day_to, group_by=None,
                               convention_type=Conversions.ATTRIBUTED_POST_CLICK, user_segment=None):
        if group_by is None:
            group_by = ['creativeId']

        params = {
            'dayFrom': day_from,
            'dayTo': day_to,
            'groupBy': group_by,
            'countConvention': convention_type,
        }
        if user_segment is not None:
            params['userSegment'] = user_segment
        params = self._map_stats_params(params)
        url = '/advertisers/{}/creative-stats'.format(adv_hash)

        return self._get(url, params)

    def get_rtb_device_stats(self, adv_hash, day_from, day_to, group_by=None,
                             convention_type=Conversions.ATTRIBUTED_POST_CLICK,
                             device_type=None, campaign_hash=None):
        if group_by is None:
            group_by = ['deviceType']

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
        params = self._map_stats_params(params)
        url = '/advertisers/{}/device-stats'.format(adv_hash)

        return self._get(url, params)

    def get_rtb_country_stats(self, adv_hash, day_from, day_to, group_by=None,
                              convention_type=Conversions.ATTRIBUTED_POST_CLICK, user_segment=None):
        if group_by is None:
            group_by = ['country']

        params = {
            'dayFrom': day_from,
            'dayTo': day_to,
            'groupBy': group_by,
            'countConvention': convention_type,
        }
        if user_segment is not None:
            params['userSegment'] = user_segment
        params = self._map_stats_params(params)
        url = '/advertisers/{}/country-stats'.format(adv_hash)

        return self._get(url, params)

    def get_rtb_creative_country_stats(self, adv_hash, day_from, day_to, group_by=None,
                                       convention_type=Conversions.ATTRIBUTED_POST_CLICK, user_segment=None):
        if group_by is None:
            group_by = ['creativeId', 'country']

        params = {
            'dayFrom': day_from,
            'dayTo': day_to,
            'groupBy': group_by,
            'countConvention': convention_type,
        }
        if user_segment is not None:
            params['userSegment'] = user_segment
        params = self._map_stats_params(params)
        url = '/advertisers/{}/creative-country-stats'.format(adv_hash)

        return self._get(url, params)

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
