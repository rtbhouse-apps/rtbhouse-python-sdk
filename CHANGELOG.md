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
    "grouping field 1 name": "groping field 1 value 1",  # No changes
    "grouping field N name": "groping field N value 1",  # No changes
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
