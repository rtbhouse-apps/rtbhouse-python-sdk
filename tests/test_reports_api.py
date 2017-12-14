import unittest

from config import USERNAME, PASSWORD
from rtbhouse_sdk.reports_api import ReportsApiSession, ConversionType

DAY_FROM = '2017-11-01'
DAY_TO = '2017-11-02'

shared_fixtures = {
    'advertiser': None
}


class TestReportsApi(unittest.TestCase):
    def setUp(self):
        self.api = ReportsApiSession(USERNAME, PASSWORD)

    @property
    def adv_hash(self):
        if shared_fixtures['advertiser']:
            return shared_fixtures['advertiser']['hash']

        advertisers = self.api.get_advertisers()
        self.assertGreater(len(advertisers), 0)
        first_adv = advertisers[0]
        self.assertIn('hash', first_adv)
        self.assertIn('name', first_adv)
        self.assertIn('status', first_adv)

        shared_fixtures['advertiser'] = first_adv
        return shared_fixtures['advertiser']['hash']

    def test_get_user_info(self):
        data = self.api.get_user_info()
        self.assertIn('username', data)
        self.assertIn('email', data)

    def test_get_advertiser(self):
        advertiser = self.api.get_advertiser(self.adv_hash)
        self.assertIn('hash', advertiser)
        self.assertIn('name', advertiser)
        self.assertIn('status', advertiser)

    def test_get_invoicing_data(self):
        inv_data = self.api.get_invoicing_data(self.adv_hash)
        self.assertIn('contact', inv_data)

    def test_get_offer_categories(self):
        offer_cat = self.api.get_offer_categories(self.adv_hash)
        self.assertGreater(len(offer_cat), 0)
        first_cat = offer_cat[0]
        self.assertIn('name', first_cat)
        self.assertIn('identifier', first_cat)

    def test_get_offers(self):
        offers = self.api.get_offers(self.adv_hash)
        self.assertGreater(len(offers), 0)
        first_offer = offers[0]
        self.assertIn('name', first_offer)
        self.assertIn('identifier', first_offer)

    def test_get_advertiser_campaigns(self):
        campaigns = self.api.get_advertiser_campaigns(self.adv_hash)
        self.assertGreater(len(campaigns), 0)
        first_camp = campaigns[0]
        self.assertIn('hash', first_camp)
        self.assertIn('name', first_camp)

    # def test_get_billing(self):
    #     billing = self.api.get_billing(self.adv_hash, DAY_FROM, DAY_TO)

    def test_get_campaign_stats_total(self):
        total_stats = self.api.get_campaign_stats_total(self.adv_hash, DAY_FROM, DAY_TO, 'day')
        self.assertGreater(len(total_stats), 0)
        first_row = total_stats[0]
        self.assertIn('day', first_row)
        self.assertIn('impsCount', first_row)
        self.assertIn('clicksCount', first_row)

    # RTB

    def test_get_rtb_creatives(self):
        rtb_creatives = self.api.get_rtb_creatives(self.adv_hash)
        self.assertGreater(len(rtb_creatives), 0)
        first_row = rtb_creatives[0]
        self.assertIn('hash', first_row)
        self.assertIn('status', first_row)
        self.assertIn('previewUrl', first_row)

    def test_get_rtb_campaign_stats(self):
        rtb_stats = self.api.get_rtb_campaign_stats(self.adv_hash, DAY_FROM, DAY_TO, 'day')
        self.assertGreater(len(rtb_stats), 0)
        first_row = rtb_stats[0]
        self.assertIn('day', first_row)
        self.assertIn('impsCount', first_row)
        self.assertIn('clicksCount', first_row)

    def test_get_rtb_conversions(self):
        rtb_conversions = self.api.get_rtb_conversions(self.adv_hash, DAY_FROM, DAY_TO, ConversionType.POST_CLICK)
        self.assertGreater(len(rtb_conversions), 0)
        first_row = rtb_conversions[0]
        self.assertIn('conversionType', first_row)
        self.assertIn('conversionValue', first_row)
        self.assertIn('conversionIdentifier', first_row)

    def test_get_rtb_deduplicated_conversions(self):
        rtb_conversions = self.api.get_rtb_conversions(self.adv_hash, DAY_FROM, DAY_TO, ConversionType.DEDUPLICATED)
        self.assertGreater(len(rtb_conversions), 0)
        first_row = rtb_conversions[0]
        self.assertIn('conversionType', first_row)
        self.assertIn('conversionValue', first_row)
        self.assertIn('conversionIdentifier', first_row)

    def test_get_rtb_category_stats(self):
        rtb_category_stats = self.api.get_rtb_category_stats(self.adv_hash, DAY_FROM, DAY_TO)
        self.assertGreater(len(rtb_category_stats), 0)
        first_row = rtb_category_stats[0]
        self.assertIn('categoryId', first_row)
        self.assertIn('impsCount', first_row)
        self.assertIn('clicksCount', first_row)

    def test_get_rtb_creative_stats(self):
        rtb_creative_stats = self.api.get_rtb_creative_stats(self.adv_hash, DAY_FROM, DAY_TO)
        self.assertGreater(len(rtb_creative_stats), 0)
        first_row = rtb_creative_stats[0]
        self.assertIn('creativeId', first_row)
        self.assertIn('impsCount', first_row)
        self.assertIn('clicksCount', first_row)

    def test_get_rtb_device_stats(self):
        rtb_device_stats = self.api.get_rtb_device_stats(self.adv_hash, DAY_FROM, DAY_TO)
        self.assertGreater(len(rtb_device_stats), 0)
        first_row = rtb_device_stats[0]
        self.assertIn('deviceType', first_row)
        self.assertIn('impsCount', first_row)
        self.assertIn('clicksCount', first_row)

    def test_get_rtb_country_stats(self):
        rtb_country_stats = self.api.get_rtb_country_stats(self.adv_hash, DAY_FROM, DAY_TO)
        self.assertGreater(len(rtb_country_stats), 0)
        first_row = rtb_country_stats[0]
        self.assertIn('country', first_row)
        self.assertIn('impsCount', first_row)
        self.assertIn('clicksCount', first_row)

    # DPA

    def test_get_dpa_creatives(self):
        dpa_creatives = self.api.get_dpa_creatives(self.adv_hash)
        self.assertGreater(len(dpa_creatives), 0)
        first_row = dpa_creatives[0]
        self.assertIn('adFormat', first_row)
        self.assertIn('iframe', first_row)

    def test_get_dpa_campaign_stats(self):
        dpa_stats = self.api.get_dpa_campaign_stats(self.adv_hash, DAY_FROM, DAY_TO, 'day')
        self.assertGreater(len(dpa_stats), 0)
        first_row = dpa_stats[0]
        self.assertIn('day', first_row)
        self.assertIn('impsCount', first_row)
        self.assertIn('clicksCount', first_row)

    def test_get_dpa_conversions(self):
        dpa_conversions = self.api.get_dpa_conversions(self.adv_hash, DAY_FROM, DAY_TO)
        self.assertGreater(len(dpa_conversions), 0)
        first_row = dpa_conversions[0]
        self.assertIn('conversionValue', first_row)
        self.assertIn('conversionIdentifier', first_row)


if __name__ == '__main__':
    unittest.main()
