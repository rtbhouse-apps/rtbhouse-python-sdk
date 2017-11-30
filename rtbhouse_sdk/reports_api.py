import requests

API_BASE_URL = "https://panel.rtbhouse.com/api"


class ConversionType:
    POST_CLICK = 'POST_CLICK'
    POST_VIEW = 'POST_VIEW'


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
        except:
            self.message = '{} ({})'.format(res.reason, str(res.status_code))


class ReportsApiSession:
    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._session = None

    @property
    def session(self):
        if not self._session:
            self._session = self._create_session()

        return self._session

    def _create_session(self):
        res = requests.post(API_BASE_URL + '/auth/login', json={'login': self._username, 'password': self._password})
        if not res.ok:
            raise ReportsApiRequestException(res)

        return res.cookies.get('session')

    def _get_data(self, res):
        if not res.ok:
            raise ReportsApiRequestException(res)

        try:
            res_json = res.json()
            return res_json.get('data') or {}
        except Exception:
            raise ReportsApiException('Invalid response format')

    def _get(self, path, params=None):
        res = requests.get(API_BASE_URL + path, cookies={'session': self.session}, params=params)
        return self._get_data(res)

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

    def get_campaign_stats_total(self, adv_hash, day_from, day_to, group_by):
        return self._get('/advertisers/' + adv_hash + '/campaign-stats-merged', {
            'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by
        })

    # RTB

    def get_rtb_creatives(self, adv_hash):
        return self._get('/advertisers/' + adv_hash + '/creatives')

    def get_rtb_campaign_stats(self, adv_hash, day_from, day_to, group_by):
        return self._get('/advertisers/' + adv_hash + '/campaign-stats', {
            'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by
        })

    def get_rtb_conversions(self, adv_hash, day_from, day_to, conversion_type=None):
        params = {'dayFrom': day_from, 'dayTo': day_to}
        if conversion_type:
            params['conversionType'] = conversion_type
        return self._get('/advertisers/' + adv_hash + '/conversions', params)

    def get_rtb_category_stats(self, adv_hash, day_from, day_to, group_by='categoryId'):
        return self._get('/advertisers/' + adv_hash + '/category-stats', {
            'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by
        })

    def get_rtb_creative_stats(self, adv_hash, day_from, day_to, group_by='creativeId'):
        return self._get('/advertisers/' + adv_hash + '/creative-stats', {
            'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by
        })

    def get_rtb_device_stats(self, adv_hash, day_from, day_to, group_by='deviceType'):
        return self._get('/advertisers/' + adv_hash + '/device-stats', {
            'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by
        })

    def get_rtb_country_stats(self, adv_hash, day_from, day_to, group_by='country'):
        return self._get('/advertisers/' + adv_hash + '/country-stats', {
            'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by
        })

    # DPA

    def get_dpa_creatives(self, adv_hash):
        return self._get('/advertisers/' + adv_hash + '/dpa/creatives')

    def get_dpa_campaign_stats(self, adv_hash, day_from, day_to, group_by):
        return self._get('/advertisers/' + adv_hash + '/dpa/campaign-stats', {
            'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by
        })

    def get_dpa_conversions(self, adv_hash, day_from, day_to):
        return self._get('/advertisers/' + adv_hash + '/dpa/conversions', {
            'dayFrom': day_from, 'dayTo': day_to
        })