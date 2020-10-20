import warnings

from requests import request

from . import __version__ as sdk_version

API_BASE_URL = 'https://api.panel.rtbhouse.com'
API_VERSION = 'v5'

DEFAULT_TIMEOUT = 60
MAX_CURSOR_ROWS_LIMIT = 10000


class Conversions(object):
    POST_VIEW = 'POST_VIEW'
    ATTRIBUTED_POST_CLICK = 'ATTRIBUTED'
    ALL_POST_CLICK = 'ALL_POST_CLICK'


class UserSegment(object):
    VISITORS = 'VISITORS'
    SHOPPERS = 'SHOPPERS'
    BUYERS = 'BUYERS'
    NEW = 'NEW'


class DeviceType(object):
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
        super(ReportsApiException, self).__init__(message)
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

        super(ReportsApiRequestException, self).__init__(message)


class ReportsApiRateLimitException(ReportsApiRequestException):
    message = 'Resource usage limits reached'

    def __init__(self, res):
        super(ReportsApiRateLimitException, self).__init__(res)
        self.limits = ReportsApiSession.parse_resource_usage_header(
            res.headers.get('X-Resource-Usage'))


class ReportsApiSession(object):
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
        if newest_version is not None and newest_version != API_VERSION:
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
        kwargs.setdefault('headers', {})['user-agent'] = 'rtbhouse-python-sdk/{}'.format(sdk_version)

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
        req_params = {
            'limit': MAX_CURSOR_ROWS_LIMIT,
        }
        if params:
            req_params.update(params)

        res = self._get(path, params=params)
        rows = res['rows']

        while res['nextCursor']:
            req_params['nextCursor'] = res['nextCursor']
            res = self._get(path, params=params)
            rows.extend(res['rows'])

        return rows

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

    # RTB

    def get_rtb_creatives(self, adv_hash):
        return self._get('/advertisers/' + adv_hash + '/rtb-creatives')

    def get_rtb_stats(self, adv_hash, day_from, day_to, group_by, metrics, count_convention=None, subcampaigns=None, user_segments=None, device_types=None):
        params = {
            'dayFrom': day_from,
            'dayTo': day_to,
            'groupBy': '-'.join(group_by),
            'metrics': '-'.join(metrics),
        }
        if count_convention is not None:
            params['countConvention'] = count_convention
        if subcampaigns is not None:
            params['subcampaigns'] = subcampaigns
        if user_segments is not None:
            params['userSegments'] = '-'.join(user_segments)
        if device_types is not None:
            params['deviceTypes'] = '-'.join(device_types)

        return self._get('/advertisers/' + adv_hash + '/rtb-stats', params)

    def get_rtb_conversions(self, adv_hash, day_from, day_to, convention_type=Conversions.ATTRIBUTED_POST_CLICK):
        return self._get_from_cursor('/advertisers/' + adv_hash + '/conversions', {
            'dayFrom': day_from, 'dayTo': day_to, 'countConvention': convention_type
        })

    # DPA

    def get_dpa_accounts(self, adv_hash):
        return self._get('/advertisers/' + adv_hash + '/dpa/accounts')

    def get_dpa_creatives(self, account_hash):
        return self._get('/preview/dpa/' + account_hash)

    def get_dpa_stats(self, adv_hash, day_from, day_to, group_by, metrics, count_convention=None, subcampaigns=None, placement=None):
        params = {
            'dayFrom': day_from,
            'dayTo': day_to,
            'groupBy': '-'.join(group_by),
            'metrics': '-'.join(metrics),
        }
        if count_convention is not None:
            params['countConvention'] = count_convention
        if subcampaigns is not None:
            params['subcampaigns'] = subcampaigns
        if placement is not None:
            params['placement'] = '-'.join(placement)
        
        return self._get('/advertisers/' + adv_hash + '/dpa-stats', params)
        
    def get_dpa_conversions(self, adv_hash, day_from, day_to):
        return self._get('/advertisers/' + adv_hash + '/dpa/conversions', {
            'dayFrom': day_from, 'dayTo': day_to
        })

    # RTB + DPA
    def get_summary_stats(self, adv_hash, day_from, day_to, group_by, metrics, count_convention=None, subcampaigns=None):
        params = {
            'dayFrom': day_from,
            'dayTo': day_to,
            'groupBy': '-'.join(group_by),
            'metrics': '-'.join(metrics),
        }
        if count_convention is not None:
            params['countConvention'] = count_convention
        if subcampaigns is not None:
            params['subcampaigns'] = subcampaigns
        
        return self._get('/advertisers/' + adv_hash + '/summary-stats', params)
