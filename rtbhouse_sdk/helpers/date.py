import datetime

def fill_missing_days(data, template, day_from=None, day_to=None):
    existing_dates = []

    for row in data:
        existing_dates.append(datetime.datetime.strptime(row['day'], '%Y-%m-%d').date())

    max_date = datetime.datetime.strptime(day_from, '%Y-%m-%d').date() if day_from is not None else max(existing_dates)
    min_date = datetime.datetime.strptime(day_to, '%Y-%m-%d').date() if day_to is not None else min(existing_dates)

    dates_in_range = [datetime.date.fromordinal(i) for i in range(min_date.toordinal(), max_date.toordinal() + 1)]

    for day in dates_in_range:
        if day not in existing_dates:
            t = template.copy()
            t['day'] = day.strftime('%Y-%m-%d')
            data.append(t)

    return sorted(data, key=lambda k: (k['day']))
