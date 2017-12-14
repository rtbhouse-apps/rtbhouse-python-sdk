from operator import itemgetter
from itertools import groupby

rtb_costs_types = ['CLICKS', 'IMPS', 'POST_CLICKS', 'POST_VIEWS', 'POST_CLICKS_REJECTIONS', 'POST_VIEWS_REJECTIONS']
dpa_costs_types = ['DPA_CLICKS', 'DPA_LAST_CLICKS']

def _combine(bills):
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


def _group_by_days(billing, operation_name, position):
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


def squash(billing, initial_balance=0):
    rtb_costs = _group_by_days(list(filter(lambda x: x['type'] in rtb_costs_types, billing)),
                                   'Cost of campaign', 2)
    dpa_costs = _group_by_days(list(filter(lambda x: x['type'] in dpa_costs_types, billing)),
                                   'Cost of FB DPA campaign', 3)
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
            filter(lambda x: x['credit'] != 0 or x['debit'] != 0, _combine(rtb_costs + dpa_costs + other)),
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
