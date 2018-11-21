
adv_hash represents advertiser hash (string type, can be obtained from
list returned by the get_advertisers() method or directly from panel URL)


ReportsApiSession.get_user_info()
Method with no arguments, returning the username and email of the current API user.

ReportsApiSession.get_advertisers()
Method with no arguments, returning a Python list of elements representing advertisers
that the current API user has access to.

ReportsApiSession.get_advertiser(adv_hash)
Method with one argument adv_hash representing advertiser hash.
Returns Python dictionary containing advertiser campaign details including rate cards.

ReportsApiSession.get_invoicing_data(adv_hash)
Method with one argument adv_hash representing advertiser hash.
Returns Python dictionary containing invoicing data.

ReportsApiSession.get_offer_categories(adv_hash)
Method with one argument adv_hash representing advertiser hash.
Returns a Python list containing advertiser category details, including number
of active offers within each of the categories.

ReportsApiSession.get_offers(adv_hash)
Method with one argument adv_hash representing advertiser hash.
Returns a Python list containing first 1000 offers with their details as specified
by the feed.

ReportsApiSession.get_advertiser_campaigns(adv_hash)
Method with one argument adv_hash representing advertiser hash.
Returns a Python list of advertiser campaigns and subcampaigns.

ReportsApiSession.get_billing(adv_hash, day_from, day_to)
Method with three arguments: adv_hash, day_from, day_to
representing advertiser hash and
date ranges limiting data being returned. day_from and day_to must be of string type
and format 'dd-mm-yyyy'. Returns a Python dictionary containing billing information.


ReportsApiSession.get_campaign_stats_total(adv_hash, day_from, day_to, group_by)
Method with four arguments: adv_hash, day_from, day_to and group_by
representing advertiser hash and
date ranges limiting data being returned. day_from and day_to must be of string type
and format 'dd-mm-yyyy'. The group_by argument must be of string type and be one of the
following: 'day', 'month', 'year', 'campaign'

# RTB

ReportsApiSession.get_rtb_creatives(adv_hash):
Method with one argument adv_hash representing advertiser hash. Returns a list
of dictionaries containing details of creatives used in the campaign.

ReportsApiSession.get_rtb_campaign_stats(adv_hash, day_from, day_to, group_by)
Method with four arguments: adv_hash, day_from, day_to and group_by
representing advertiser hash and
date ranges limiting data being returned. day_from and day_to must be of string type
and format 'dd-mm-yyyy'. The group_by argument must be of string type and be one of the
following: 'day', 'month', 'year', 'userSegment', 'campaign'



ReportsApiSession.get_rtb_conversions(adv_hash, day_from, day_to, convention_type=None)
Method with four arguments: adv_hash, day_from, day_to and convention_type
representing advertiser hash and date ranges limiting data being returned. day_from and day_to must be of string type
and format 'dd-mm-yyyy'. The convention_type argument must be of string or None type and be one of the
following:
None (which is default, equals to leaving this argument empty) – will return a list of all attributed post click conversions and all post view conversions. Is roughly equivalent to merging results of calling this method with POST_CLICK and POST_VIEW arguments.
POST_CLICK – returns a list of all attributed post click conversions.
POST_VIEW – returns a list of all post view conversions
deduplicated – returns a list of all conversions, that were deduplicated.


ReportsApiSession.get_rtb_category_stats(adv_hash, day_from, day_to, group_by='categoryId')
Method with four arguments: adv_hash, day_from, day_to and group_by
representing advertiser hash and
date ranges limiting data being returned. day_from and day_to must be of string type
and format 'dd-mm-yyyy'. The group_by argument defaults to 'categoryId' and as such
there is no need to specify this argument. get_rtb_category_stats(adv_hash, day_from, day_to)
is enough. Returns campaign statistics grouped by categories specified in the feed.


ReportsApiSession.get_rtb_creative_stats(adv_hash, day_from, day_to, group_by='creativeId')
Method with four arguments: adv_hash, day_from, day_to and group_by
representing advertiser hash and
date ranges limiting data being returned. day_from and day_to must be of string type
and format 'dd-mm-yyyy'. The group_by argument defaults to 'creativeId' and as such
there is no need to specify this argument. get_rtb_creative_stats(adv_hash, day_from, day_to)
is enough. Returns campaign statistics grouped by creatives/banners.


ReportsApiSession.get_rtb_device_stats(adv_hash, day_from, day_to, group_by='deviceType')
Method with four arguments: adv_hash, day_from, day_to and group_by
representing advertiser hash and
date ranges limiting data being returned. day_from and day_to must be of string type
and format 'dd-mm-yyyy'. The group_by argument defaults to 'deviceType' and as such
there is no need to specify this argument. get_rtb_device_stats(adv_hash, day_from, day_to)
is enough. Returns campaign statistics grouped by device type.

ReportsApiSession.get_rtb_country_stats(adv_hash, day_from, day_to, group_by='country')
Method with four arguments: adv_hash, day_from, day_to and group_by
representing advertiser hash and
date ranges limiting data being returned. day_from and day_to must be of string type
and format 'dd-mm-yyyy'. The group_by argument defaults to 'country' and as such
there is no need to specify this argument. get_rtb_country_stats(adv_hash, day_from, day_to)
is enough. Returns campaign statistics grouped by country.

# DPA

ReportsApiSession.get_dpa_creatives(adv_hash)

Method with one argument: adv_hash representing advertiser hash
(string type, can be obtained from list returned by the get_advertisers()
method or directly from panel URL). Returns a list containing details of
Facebook DPA banners.

ReportsApiSession.get_dpa_campaign_stats(adv_hash, day_from, day_to, group_by)
Method with four arguments: adv_hash, day_from, day_to and group_by
representing advertiser hash and
date ranges limiting data being returned. day_from and day_to must be of string type
and format 'dd-mm-yyyy'. The group_by argument must be of string type and be one of the
following: 'day', 'month', 'year', 'placement'. Returns a list of Python dictionaries
containing data on DPA campaigns.

ReportsApiSession.get_dpa_conversions(self, adv_hash, day_from, day_to)
Method with three arguments: adv_hash, day_from, day_to
representing advertiser hash and
date ranges limiting data being returned. day_from and day_to must be of string type
and format 'dd-mm-yyyy'. Returns a Python dictionary containing billing information.


