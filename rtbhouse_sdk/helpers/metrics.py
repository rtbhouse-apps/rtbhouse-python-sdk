stats_row_countable_defaults = {
  'allPostclicksCount': 0, 'allPostclicksValue': 0,
  'attributedPostclicksCount': 0, 'attributedPostclicksCost': 0, 'attributedPostclicksValue': 0,
  'attributedPostviewsCount': 0, 'attributedPostviewsCost': 0, 'attributedPostviewsValue': 0,
  'clicksCount': 0, 'clicksCost': 0, 'impsCount': 0, 'impsCost': 0
}

class CountConventionType:
    POST_VIEW = 'POST_VIEW'
    ATTRIBUTED = 'ATTRIBUTED'
    ALL_POST_CLICK = 'ALL_POST_CLICK'

def calculate_convention_metrics(row, count_convention, NA=0):
    total_cost = row['impsCost'] + row['clicksCost'] + row['attributedPostviewsCost'] + row['attributedPostclicksCost']

    conversions_count = NA
    conversions_value = NA

    if count_convention == CountConventionType.POST_VIEW:
        conversions_count = row.get('attributedPostviewsCount', NA)
        conversions_value = row.get('attributedPostviewsValue', NA)
    elif count_convention == CountConventionType.ATTRIBUTED:
        conversions_count = row.get('attributedPostclicksCount', NA)
        conversions_value = row.get('attributedPostclicksValue', NA)
    elif count_convention == CountConventionType.ALL_POST_CLICK:
        conversions_count = row.get('allPostclicksCount', NA)
        conversions_value = row.get('allPostclicksValue', NA)

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
        imps=row['impsCount'], clicks=row['clicksCount'],
        ctr=clickthrough_rate, campaignCost=total_cost, conversionsCount=conversions_count,
        conversionsRate=conversions_rate, cpc=cost_per_click, ecc=effective_cost_of_conversion,
        roas=return_on_advertiser_spending, conversionsValue=conversions_value
    )

def calculate_deduplication_metrics(row, NA=0):
    deduplication_rate = 1 - row['attributedPostclicksCount'] / row['allPostclicksCount'] if row['allPostclicksCount'] > 0 else NA
    deduplication_value_rate = 1 - row['attributedPostclicksValue'] / row['allPostclicksValue'] if row['allPostclicksValue'] > 0 else NA

    return dict(
        deduplicationRate=deduplication_rate,
        deduplicationValueRate=deduplication_value_rate
    )
