from datetime import date, timedelta
from operator import itemgetter

from tabulate import tabulate

from config import PASSWORD, USERNAME
from rtbhouse_sdk.reports_api import ReportsApiSession

if __name__ == '__main__':
    api = ReportsApiSession(USERNAME, PASSWORD)
    advertisers = api.get_advertisers()
    day_to = date.today()
    day_from = day_to - timedelta(days=30)
    stats = api.get_rtb_stats(advertisers[0]['hash'], day_from, day_to, {'day'}, include_dpa=True)
    columns = ['day', 'impsCount', 'clicksCount', 'campaignCost', 'conversionsCount', 'conversionsValue', 'cr', 'ctr', 'cpc', 'ecc', 'roas']
    data_frame = [[row[c] for c in columns] for row in reversed(sorted(stats, key=itemgetter('day')))]
    print(tabulate(data_frame, headers=columns))
