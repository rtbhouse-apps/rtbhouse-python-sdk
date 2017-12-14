def calculate_convention_metrics(row, count_convention, NA=0):
    total_cost = row['impsCost'] + row['clicksCost'] + row['attributedPostviewsCost'] + row['attributedPostclicksCost']

    conversions_count = NA
    conversions_value = NA

    if count_convention == 'POST_VIEW':
        conversions_count = row['attributedPostviewsCount'] or NA
        conversions_value = row['attributedPostviewsValue'] or NA
    elif count_convention == 'ATTRIBUTED':
        conversions_count = row['attributedPostclicksCount'] or NA
        conversions_value = row['attributedPostclicksValue'] or NA
    elif count_convention == 'ALL_POST_CLICK':
        conversions_count = row['allPostclicksCount'] or NA
        conversions_value = row['allPostclicksValue'] or NA

    conversions_rate = conversions_count / row['clicksCount'] if row['clicksCount'] else NA

    # eCC
    effective_cost_of_conversion = total_cost / conversions_count if conversions_count else NA

    # CTR
    clickthrough_rate = row['clicksCount'] / row['impsCount'] if row['impsCount'] else NA

    # CPC
    cost_per_click = total_cost / row['clicksCount'] if row['clicksCount'] else NA

    # ROAS
    return_on_advertiser_spending = conversions_value / total_cost if total_cost > 0 else NA

    return dict(
        totalCost=total_cost, clickthroughRate=clickthrough_rate, costPerclick=cost_per_click,
        conversionsCount=conversions_count, conversionsRate=conversions_rate,
        conversionsValue=conversions_value, effectiveCostOfConversion=effective_cost_of_conversion,
        returnOnAdvertiserSpending=return_on_advertiser_spending
    )

def calculate_deduplication_metrics(row, NA=0):
    deduplication_rate = 1 - row['attributedPostclicksCount'] / row['allPostclicksCount'] if row['allPostclicksCount'] > 0 else NA
    deduplication_value_rate = 1 - row['attributedPostclicksValue'] / row['allPostclicksValue'] if row['allPostclicksValue'] > 0 else NA

    return dict(
        deduplicationRate=deduplication_rate,
        deduplicationValueRate=deduplication_value_rate
    )

def stats_summary_reduce(omit_keys, multiplier=1000):
    # not needed?
    pass


def calculate_summary_row(stats):
    omit_keys = ['clickthroughRate', 'conversionsRate', 'effectiveCostOfConversion', 'returnOnAdvertiserSpending']
    summary_row = stats # stats.reduce(statsSummaryReduce(omitKeys, {})

    clicktrough_rate = _avg_clicktrough_rate(summary_row)
    conversions_rate = _avg_conversions_rate(summary_row)
    effective_cost_of_conversion = _avg_effective_cost_of_conversion(summary_row)
    return_on_advertiser_spending = _avg_return_on_advertiser_spending(summary_row)

    summary_row.update({
        'clicktroughRate': clicktrough_rate,
        'conversionsRate': conversions_rate,
        'effectiveCostOfConversion': effective_cost_of_conversion,
        'returnOnAdvertiserSpending': return_on_advertiser_spending
    })

    return summary_row

def calculate_deduplication_stats_summary_row(stats):
    omit_keys = ['deduplicationRate', 'deduplicationValueRate']
    summary_row = stats # stats.reduce(statsSummaryReduce(omitKeys), {})

    deduplication_rate = _avg_deduplication_rate(summary_row)
    deduplication_value_rate = _avg_deduplication_value_rate(summary_row)

    summary_row.update({
        'deduplicationRate': deduplication_rate,
        'deduplicationValueRate': deduplication_value_rate
    })

    return summary_row

def _avg_clicktrough_rate(row):
    return row['clicksCount'] / row['impsCount'] if row['impsCount'] > 0 else 0

def _avg_conversions_rate(row):
    return row['conversionsCount'] / row['clicksCount'] if row['clicksCount'] > 0 else 0

def _avg_effective_cost_of_conversion(row):
    return row['totalCost'] / row['conversionsCount'] if row['conversionsCount'] > 0 else 0

def _avg_return_on_advertiser_spending(row):
    return row['conversionsValue'] / row['totalCost'] if row['totalCost'] > 0 else 0

def _avg_deduplication_rate(row):
    return 1 - row['attributedPostClicksCount'] / row['allPostClicksCount'] if row['allPostClicksCount'] > 0 else 0

def _avg_deduplication_value_rate(row):
    return 1 - row['attributedPostClicksValue'] / row['allPostClicksValue'] if row['allPostClicksValue'] > 0 else 0
