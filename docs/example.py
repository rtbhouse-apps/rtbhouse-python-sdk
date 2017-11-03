from operator import itemgetter

from tabulate import tabulate

from config import USERNAME, PASSWORD
from rtbhouse_sdk.reports_api import ReportsApiSession

if __name__ == '__main__':
    api = ReportsApiSession(USERNAME, PASSWORD)
    advertisers = api.get_advertisers()
    stats = api.get_rtb_campaign_stats(advertisers[0]['hash'], '2017-10-01', '2017-10-31', 'day')
    columns = ['day', 'impsCount', 'clicksCount', 'attributedPostclicksCount', 'attributedPostclicksValue']
    data_frame = [[row[c] for c in columns] for row in reversed(sorted(stats, key=itemgetter('day')))]
    print(tabulate(data_frame, headers=columns))