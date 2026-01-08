# v15.0.0
- [breaking change] dropped support for python 3.9 (which is end-of-life), please use python 3.10+

# v14.0.0
- [breaking change] dropped support for python 3.8 (which is end-of-life), please use python 3.9+
- added support for python 3.12 and 3.13

# v13.0.0
- [breaking change] current `viewability` metric has been renamed to `ssp_viewability`. We are leaving compatibility layer in the api until 2024-12-31.
- added audio related metrics: `audio_complete_listens`, `ecpl`, `acr`.
- added viewability related metrics: `viewability_measurability`, `viewability_viewability`, `evcpm`.
- added visits related metrics: `visits_count`, `cpvisit`.

# v12.0.0
- [breaking change] Stats (`schema.Stats`, returned from `get_rtb_stats` and `get_summary_stats`) metrics: `imps_count`, `clicks_count`, `conversions_count`, `video_complete_views` are now represented as float type, to reflect actual api responses. Fractional metrics may appear in certain scenarios, eg. for custom grouping and/or as a result of manual adjustment.

# v11.1.0
- Added `utc_offset_hours` parameter for `get_rtb_stats` and `get_summary_stats`

# v11.0.0
- Added support for Pydantic v2
- [breaking change] `cookie_hash`, `last_click_time` and `last_impression_time` fields in `Conversion` schema are now nullable
- [breaking change] fixed naming convention compliance for fields in schemas: `rateCardId` (`UserInfo`) is now `rate_card_id` and `customProperties` (`Offer`) is now `custom_properties`

# v10.1.0
- Removed [inflection](https://pypi.org/project/inflection/) from the project dependencies
- Added `camelize` and `underscore` helper functions

# v10.0.0
- Dropped support for python 3.7 (which is reaching end-of-life), please use python 3.8.1+, v9 branch with python 3.7 compatibility will be updated until 2023-06-27
- Added support for python 3.11
- Unfrozen httpx, httpcore has been fixed

# v9.0.1
- Freeze httpx in version 0.23.0, as 0.23.1 uses bugged httpcore 0.16.x (see https://github.com/encode/httpcore/issues/621)

# v9.0.0
This version introduces breaking changes. Please see the migration guide below on how to migrate from older versions.

## Changes
- Drop support for Python 2
- Split `reports_api` module into `client`, `exceptions`, `schema` modules
- Rename `ReportsApiSession` to `Client` and change its constructor arguments
- Remove `Reports` prefix from exception names
- Return objects with well-defined fields instead of dicts
- Use proper enums for parameters instead of string values
- Add type annotations
- Add token authentication method
- Add asynchronous client

## Migration

### Python compatibility
Python 2 is no longer supported, please use Python 3.7+.

### Authentication
For example, previous code creating API client instance:
```python
from rtbhouse_sdk.reports_api import ReportsApiSession
api = ReportsApiSession(username="myuser", password="mypassword")
```

Now should look like this:
```python
from rtbhouse_sdk.client import BasicAuth, Client
api = Client(auth=BasicAuth(username="myuser", password="mypassword"))
```

Additionally, it is now possible to authenticate with a token:
```python
from rtbhouse_sdk.client import BasicTokenAuth, Client
api = Client(auth=BasicTokenAuth(token="mytoken"))
```

### Clients
Now SDK offers both synchronous and asynchronous clients to work with. They have the same set of endpoints.

It is recommended to close the session using `close()` method. For convenience there is also a context manager that takes care of that.

Usage example with sync client:
```python
from rtbhouse_sdk.client import BasicTokenAuth, Client

auth = BasicTokenAuth(token='mytoken')

# using close
api = Client(auth=auth)
info = api.get_user_info()
api.close()

# or using context manager
with Client(auth=auth) as api:
    info = api.get_user_info()
```

Usage example with async client:
```python
from rtbhouse_sdk.client import BasicTokenAuth, AsyncClient

auth = BasicTokenAuth(token='mytoken')

# using close
api = AsyncClient(auth=auth)
info = await api.get_user_info()
await api.close()

# or using context manager
async with AsyncClient(auth=auth) as api:
    info = await api.get_user_info()
```

### Result data
Each endpoint method returns data in form of [Pydantic model](https://pydantic-docs.helpmanual.io/usage/models/).

If you wish to access the data as a dict, you can call `dict()` method on the resulting object.

For example, previous code fetching user info:
```python
info = api.get_user_info()
print(info['isClientUser'])
```

Now should look like:
```python
# recommended way
info = api.get_user_info()
print(info.is_client_user)

# alternative way using dict with camelCase keys
# (same as in the code for previous SDK version)
info = api.get_user_info().dict(by_alias=True)
print(info['isClientUser'])

# alternative way using dict with snake_case keys
info = api.get_user_info().dict()
print(info['is_client_user'])
```

### Query params
Instead of plain strings there are now enums which should be used for query filters.
Moreover, `date` objects should be used for `day_from` and `day_to` parameters.

For example, previous code fetching stats:
```python
from rtbhouse_sdk.reports_api import ReportsApiSession

api = ReportsApiSession(username="myuser", password="mypassword")
results = api.get_rtb_stats(
    adv_hash="myadvertiser",
    day_from="2022-06-01",
    day_to="2022-06-30",
    group_by=["subcampaign", "userSegment"],
    metrics=["clicksCount"]
)
for row in results:
    print(row["subcampaign"] + " - " + row["userSegment"] + ": " + str(row["clicksCount"]))
```

Now should look like this:
```python
from datetime import date
from rtbhouse_sdk.client import Client, BasicAuth
from rtbhouse_sdk.schema import StatsGroupBy, StatsMetric

api = Client(auth=BasicAuth(username="myuser", password="mypassword"))
results = api.get_rtb_stats(
    adv_hash="myadvertiser",
    day_from=date(2022, 6, 1),
    day_to=date(2022, 6, 30),
    group_by=[StatsGroupBy.SUBCAMPAIGN, StatsGroupBy.USER_SEGMENT],
    metrics=[StatsMetric.CLICKS_COUNT]
)
for row in results:
    print(row.subcampaign + " - " + row.user_segment + ": " + str(row.clicks_count))
api.close()
```

### Other changes
- `get_rtb_conversions` is now a generator function (previously it returned list)


# v8.1.0
Dependencies bump
Support for Python 3.10
Drop support for python 3.5 and 3.6

# v8.0.0
Remove `get_dpa_accounts`, `get_dpa_stats`, `get_dpa_conversions` functions

# v7.1.0
Update build tooling, added poetry
Apply lint fixes
Drop support for Python 3.3 and Python 3.4


# v7.0.0
Remove `get_dpa_creatives` function


# v6.0.2
Update usage example in README.rst


# v6.0.1
Restored support for python 2.7


# v6.0.0
This version adapts to latest api v5 changes.
See API docs: https://panel.rtbhouse.com/api/docs for details.

For now, three methods - `get_rtb_stats` (for RTB only), `get_dpa_stats` (for DPA only) and `get_summary_stats` (for RTB + DPA) shares similar parameters and output:
```
get_(rtb|dpa|summary)_stats(
    adv_hash,  # Advertiser hash. No changes.
    day_from,  # Date range start (inclusive). No changes for RTB. For DPA this parameter is now obligatory (was not in the past).
    day_to,  # Date range end (inclusive). No changes for RTB. For DPA this parameter is now obligatory (was not in the past).
    group_by,  # Iterable (eg. list, set) of grouping columns. Refer to api docs for list of possible values. No changes for RTB. For DPA this now accepts list instead of single value.
    metrics,  # Iterable (eg. list, set) of value columns. Refer to api docs for list of possible values. This parameter was newly added.
    count_convention,  # (Optional) Conversions counting convention. Changes: Defaults to None; This parameter must only be set if at least one conversions related metric is selected.
    subcampaigns,  # (Optional) Subcampaigns filter. No changes.
    user_segments,  # (Optional, RTB only) User segments filter. No changes.
    device_types,  # (Optional, RTB only) Device types filter. No changes.
    placement,  # (Optional, DPA only). Placement filter. No changes.
) -> [{
    "grouping field 1 name": "grouping field 1 value 1",  # No changes
    "grouping field N name": "grouping field N value 1",  # No changes
    "grouping field X details": "grouping field X details values",  # No changes
    "metric 1 name": "metric field 1 value",  # Changes: now only metrics requested by `metrics` parameter are returned
}]
```

`get_dpa_campaign_stats` was removed, use `get_dpa_stats` instead.

`include_dpa` in `get_rtb_stats` is no longer supported, use `get_summary_stats` instead.

A few new metrics were added, refer to docs (as above) for details.

A few metrics changed their names. `ecc` was renamed to `ecpa`, `cpc` was renamed to `ecpc`.

`count_convention` parameter is now not needed if no conversions related metrics are requested.


# v5.0.0
This version adapts to latest api v4 changes.

`get_rtb_creatives` now provides faster results with different output:
Refer to `https://panel.rtbhouse.com/api/docs` - `GET /advertisers/{hash}/rtb-creatives` for details


# v4.1.0
Add python 2.7 support


# v4.0.0
This version adapts to latest api v3. changes.

Multiple stats loading functions: `get_campaign_stats_total`, `get_rtb_campaign_stats`, `get_rtb_category_stats`, `get_rtb_creative_stats`, `get_rtb_device_stats`, `get_rtb_country_stats`, `get_rtb_creative_country_stats` are now replaced with single `get_rtb_stats` method, see below.
- `campaign` in `group_by` is renamed to `subcampaign`.
- `categoryId` grouping is renamed to `category`. In output `categoryId` is removed, `category` now contains category identifier (previously name) and new field `categoryName` is added.
- `creativeId` grouping is renamed to `creative`. In output `hash` is renamed to `creative`. All creative details are prefixed with `creative` (`creativeName`, `creativeWidth`, `creativeCreatedAt`).
- `conversionsRate` in output is renamed to `cr`.
- Indeterminate values (ex. ctr when there are no imps and clicks) are now `null` / `None`, previously `0`.

For example:
- `get_rtb_campaign_stats` equals to `get_rtb_stats`, with default `group_by` set to `{'day'}`.
- `get_campaign_stats_total` equals to `get_rtb_stats`, with default `group_by` set to `{'day'}` and `includeDpa` set to `True`.
- `get_rtb_category_stats` equals to `get_rtb_stats` with `group_by` set to `{'category'}`.
- `get_rtb_creative_stats` equals to `get_rtb_stats` with `group_by` set to `{'creative'}`.
- `get_rtb_device_stats` equals to `get_rtb_stats` with `group_by` set to `{'deviceType'}`.
- `get_rtb_country_stats` equals to `get_rtb_stats` with `group_by` set to `{'country'}`.
- `get_rtb_creative_country_stats` equals to `get_rtb_stats` with `group_by` set to `{'creative', 'country'}`.
