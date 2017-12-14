import requests
from operator import itemgetter
from itertools import groupby

API_BASE_URL = "https://panel.rtbhouse.com/api"

rtb_costs_types = ['CLICKS', 'IMPS', 'POST_CLICKS', 'POST_VIEWS', 'POST_CLICKS_REJECTIONS', 'POST_VIEWS_REJECTIONS']
dpa_costs_types = ['DPA_CLICKS', 'DPA_LAST_CLICKS']


def combineBilling(bills):
    result = []
    for record in bills:
        has_record = False
        for saved_record in result:
            if saved_record['day'] == record['day'] and saved_record['operation'] == record['operation']:
                has_record = True
                saved_record['debit'] += record['debit']
                saved_record['credit'] += record['credit']

        if not has_record:
            result.append(record)
    return result

def groupByDays(billing, operation_name, position):
    result = []
    for day, items in groupby(billing, key=itemgetter('day')):
        credit = 0
        debit = 0

        for item in items:
            v = item.get('value', 0)
            credit = credit + v if v > 0 else credit
            debit = debit + v if v < 0 else debit

        result.append(dict(
            day=day, operation=operation_name, position=position, credit=credit, debit=debit
        ))
    return result

def squashBilling(billing, initial_balance = 0):
    rtb_costs = groupByDays(list(filter(lambda x: x['type'] in rtb_costs_types, billing)), 'Cost of campaign', 2)
    dpa_costs = groupByDays(list(filter(lambda x: x['type'] in dpa_costs_types, billing)), 'Cost of FB DPA campaign', 3)
    other = list(
        map(lambda y: dict(
            day=y['day'],
            operation=y['description'] or y['type'].lower().title(),
            position=1,
            credit=y['value'] if y['value'] > 0 else 0,
            debit=y['value'] if y['value'] < 0 else 0
        ),
        filter(lambda x: x['type'] not in rtb_costs_types + dpa_costs_types, billing))
    )

    balance = initial_balance

    sorted_bills = list(
        sorted(
            filter(lambda x: x['credit'] != 0 or x['debit'] != 0, combineBilling(rtb_costs + dpa_costs + other)),
            key=lambda k: (k['day'], k['position'], k['operation'])
        )
    )

    result = []
    for i, bill in enumerate(sorted_bills):
        balance += bill['credit']
        balance += bill['debit']

        bill['balance'] = balance
        bill['recordNumber'] = i + 1
        result.append(bill)

    return result

class ConversionType:
    POST_CLICK = 'POST_CLICK'
    POST_VIEW = 'POST_VIEW'
    DEDUPLICATED = 'DEDUPLICATED'


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

        return squashBilling(billing['data']['operations'], billing['data']['initialBalance'])

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

        if conversion_type == ConversionType.DEDUPLICATED:

            deduplicated = self._get('/advertisers/' + adv_hash + '/deduplicated-conversions', {'dayFrom': day_from, 'dayTo': day_to})

            for conv in deduplicated:
                 conv['conversionType'] = ConversionType.DEDUPLICATED

            return deduplicated
        else:

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
