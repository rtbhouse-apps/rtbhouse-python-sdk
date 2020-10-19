from datetime import date, timedelta
from operator import itemgetter

from rtbhouse_sdk.reports_api import Conversions, ReportsApiSession
from tabulate import tabulate

from config import PASSWORD, USERNAME

if __name__ == '__main__':
    api = ReportsApiSession(USERNAME, PASSWORD)
    advertisers = api.get_advertisers()
    day_to = date.today()
    day_from = day_to - timedelta(days=30)
    group_by = ['day']
    metrics = ['impsCount', 'clicksCount', 'campaignCost', 'conversionsCount', 'conversionsValue', 'cr', 'ctr', 'ecpa']
    stats = api.get_rtb_stats(advertisers[0]['hash'], day_from, day_to, group_by, metrics, count_convention=Conversions.ATTRIBUTED_POST_CLICK)
    columns = group_by + metrics
    data_frame = [[row[c] for c in columns] for row in reversed(sorted(stats, key=itemgetter('day')))]
    print(tabulate(data_frame, headers=columns))
