import requests
from rtbhouse_sdk.helpers.billing import squash
from rtbhouse_sdk.helpers.metrics import calculate_convention_metrics, stats_row_countable_defaults, CountConventionType, ConversionType
from rtbhouse_sdk.helpers.date import fill_missing_days

API_BASE_URL = "https://panel.rtbhouse.com/api"

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
        billing = self._get('/advertisers/' + adv_hash + '/billing', {
            'dayFrom': day_from, 'dayTo': day_to
        })

        return squash(billing['operations'], billing['initialBalance'])

    def get_campaign_stats_total(self, adv_hash, day_from, day_to, group_by='day', convention_type=CountConventionType.ATTRIBUTED):
        stats = self._get('/advertisers/' + adv_hash + '/campaign-stats-merged', {
            'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by
        })

        data = self._convert_stats(stats, convention_type, group_by)

        return data

    # RTB

    def get_rtb_creatives(self, adv_hash):
        return self._get('/advertisers/' + adv_hash + '/creatives')

    def get_rtb_campaign_stats(self, adv_hash, day_from, day_to, group_by='day', convention_type=CountConventionType.ATTRIBUTED):
        stats = self._get('/advertisers/' + adv_hash + '/campaign-stats', {
            'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by
        })

        return self._convert_stats(stats, convention_type, group_by)

    def get_rtb_conversions(self, adv_hash, day_from, day_to, convention_type=CountConventionType.ATTRIBUTED):
        if convention_type == CountConventionType.ALL_POST_CLICK:
            deduplicated_stats = self._get('/advertisers/' + adv_hash + '/deduplicated-conversions', {
                'dayFrom': day_from, 'dayTo': day_to
            })
        else:
            deduplicated_stats = []

        if convention_type == CountConventionType.ATTRIBUTED or convention_type == CountConventionType.ALL_POST_CLICK:
            stats = self._get('/advertisers/' + adv_hash + '/conversions', {
                'dayFrom': day_from, 'dayTo': day_to, 'conversionType': ConversionType.POST_CLICK
            })
        else:
            # CountConventionType.POST_VIEW
            stats = self._get('/advertisers/' + adv_hash + '/conversions', {
                'dayFrom': day_from, 'dayTo': day_to, 'conversionType': ConversionType.POST_VIEW
            })

        new_stats = []

        for row in deduplicated_stats + stats:
            row['conversionType'] = convention_type
            new_stats.append(row)

        return new_stats

    def get_rtb_category_stats(self, adv_hash, day_from, day_to, group_by='categoryId', convention_type=CountConventionType.ATTRIBUTED):
        stats = self._get('/advertisers/' + adv_hash + '/category-stats', {
            'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by
        })

        data = self._convert_stats(stats, convention_type, group_by)
        categories = self.get_offer_categories(adv_hash)

        for row in data:
            row['category'] = next((x['name'] for x in categories if x['categoryId'] == row['categoryId']), None)

        return data

    def get_rtb_creative_stats(self, adv_hash, day_from, day_to, group_by='creativeId', convention_type=CountConventionType.ATTRIBUTED):
        stats = self._get('/advertisers/' + adv_hash + '/creative-stats', {
            'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by
        })

        return self._convert_stats(stats, convention_type, group_by)

    def get_rtb_device_stats(self, adv_hash, day_from, day_to, group_by='deviceType', convention_type=CountConventionType.ATTRIBUTED):
        stats = self._get('/advertisers/' + adv_hash + '/device-stats', {
            'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by
        })

        return self._convert_stats(stats, convention_type, group_by)

    def get_rtb_country_stats(self, adv_hash, day_from, day_to, group_by='country', convention_type=CountConventionType.ATTRIBUTED):
        stats = self._get('/advertisers/' + adv_hash + '/country-stats', {
            'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by
        })

        return self._convert_stats(stats, convention_type, group_by)

    # DPA

    def get_dpa_creatives(self, adv_hash):
        return self._get('/advertisers/' + adv_hash + '/dpa/creatives')

    def get_dpa_campaign_stats(self, adv_hash, day_from, day_to, group_by='day', convention_type=CountConventionType.ATTRIBUTED):
        stats = self._get('/advertisers/' + adv_hash + '/dpa/campaign-stats', {
            'dayFrom': day_from, 'dayTo': day_to, 'groupBy': group_by
        })

        return self._convert_stats(stats, convention_type, group_by)

    def get_dpa_conversions(self, adv_hash, day_from, day_to):
        return self._get('/advertisers/' + adv_hash + '/dpa/conversions', {
            'dayFrom': day_from, 'dayTo': day_to
        })

    def _convert_stats(self, stats, convention_type, group_by):
        data = fill_missing_days(stats, stats_row_countable_defaults) if group_by == 'day' else stats
        new_stats = []

        for row in data:
            metrics = calculate_convention_metrics(row, convention_type)

            if group_by == 'day':
                metrics['day'] = row['day']
            elif group_by == 'deviceType':
                metrics['deviceType'] = row['deviceType']
            elif group_by == 'creativeId':
                metrics['creativeId'] = row['creativeId']
                metrics['hash'] = row['hash']
                metrics['offersNumber'] = row.get('offersNumber', 0)
                metrics['height'] = row.get('height', 0)
                metrics['width'] = row.get('width', 0)
                metrics['name'] = row.get('name', '')
                metrics['createdAt'] = row.get('createdAt')
                metrics['updatedAt'] = row.get('updatedAt')
            elif group_by == 'country':
                metrics['country'] = row.get('country')
            elif group_by == 'categoryId':
                metrics['categoryId'] = row['categoryId']
            elif group_by == 'placement':
                metrics['placement'] = row['placement']

            new_stats.append(metrics)

        return new_stats
