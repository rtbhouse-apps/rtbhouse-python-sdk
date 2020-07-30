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

# v4.1.0
Add python 2.7 support

# v5.0.0
This version adapts to latest api v4 changes.

`get_rtb_creatives` now provides faster results with different output:
Refer to `https://panel.rtbhouse.com/api/docs` - `GET /advertisers/{hash}/rtb-creatives` for details
