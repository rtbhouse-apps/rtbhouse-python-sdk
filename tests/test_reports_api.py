import unittest

from config import USERNAME, PASSWORD
from rtbhouse_sdk.reports_api import ReportsApiSession, ConversionType

DAY_FROM = '2017-11-01'
DAY_TO = '2017-11-02'


class TestReportsApi(unittest.TestCase):
    def setUp(self):
        self.api = ReportsApiSession(USERNAME, PASSWORD)

    def test_user_info(self):
        data = self.api.get_user_info()
        self.assertIn('username', data)
        self.assertIn('email', data)

    def test_advertiser_campaigns(self):
        advertisers = self.api.get_advertisers()
        self.assertGreater(len(advertisers), 0)
        first_adv = advertisers[0]
        self.assertIn('hash', first_adv)
        self.assertIn('name', first_adv)
        self.assertIn('status', first_adv)

        adv_hash = first_adv['hash']

        advertiser = self.api.get_advertiser(adv_hash)
        self.assertIn('hash', advertiser)
        self.assertIn('name', advertiser)
        self.assertIn('status', advertiser)

        inv_data = self.api.get_invoicing_data(adv_hash)
        self.assertIn('contact', inv_data)

        offer_cat = self.api.get_offer_categories(adv_hash)
        self.assertGreater(len(offer_cat), 0)
        first_cat = offer_cat[0]
        self.assertIn('name', first_cat)
        self.assertIn('identifier', first_cat)

        offers = self.api.get_offers(adv_hash)
        self.assertGreater(len(offers), 0)
        first_offer = offers[0]
        self.assertIn('name', first_offer)
        self.assertIn('identifier', first_offer)

        campaigns = self.api.get_advertiser_campaigns(adv_hash)
        self.assertGreater(len(campaigns), 0)
        first_camp = campaigns[0]
        self.assertIn('hash', first_camp)
        self.assertIn('name', first_camp)

        billing = self.api.get_billing(adv_hash, DAY_FROM, DAY_TO)
        self.assertIn('operations', billing)
        self.assertGreater(len(billing['operations']), 0)
        first_row = billing['operations'][0]
        self.assertIn('day', first_row)
        self.assertIn('value', first_row)

        total_stats = self.api.get_campaign_stats_total(adv_hash, DAY_FROM, DAY_TO, 'day')
        self.assertGreater(len(total_stats), 0)
        first_row = total_stats[0]
        self.assertIn('day', first_row)
        self.assertIn('impsCount', first_row)
        self.assertIn('clicksCount', first_row)

        rtb_creatives = self.api.get_rtb_creatives(adv_hash)
        self.assertGreater(len(rtb_creatives), 0)
        first_row = rtb_creatives[0]
        self.assertIn('hash', first_row)
        self.assertIn('status', first_row)
        self.assertIn('previewUrl', first_row)

        rtb_stats = self.api.get_rtb_campaign_stats(adv_hash, DAY_FROM, DAY_TO, 'day')
        self.assertGreater(len(rtb_stats), 0)
        first_row = rtb_stats[0]
        self.assertIn('day', first_row)
        self.assertIn('impsCount', first_row)
        self.assertIn('clicksCount', first_row)

        rtb_conversions = self.api.get_rtb_conversions(adv_hash, DAY_FROM, DAY_TO, ConversionType.POST_CLICK)
        self.assertGreater(len(rtb_conversions), 0)
        first_row = rtb_conversions[0]
        self.assertIn('conversionType', first_row)
        self.assertIn('conversionValue', first_row)
        self.assertIn('conversionIdentifier', first_row)

        dpa_creatives = self.api.get_dpa_creatives(adv_hash)
        self.assertGreater(len(dpa_creatives), 0)
        first_row = dpa_creatives[0]
        self.assertIn('adFormat', first_row)
        self.assertIn('iframe', first_row)

        dpa_stats = self.api.get_dpa_campaign_stats(adv_hash, DAY_FROM, DAY_TO, 'day')
        self.assertGreater(len(dpa_stats), 0)
        first_row = dpa_stats[0]
        self.assertIn('day', first_row)
        self.assertIn('impsCount', first_row)
        self.assertIn('clicksCount', first_row)

        dpa_conversions = self.api.get_dpa_conversions(adv_hash, DAY_FROM, DAY_TO)
        self.assertGreater(len(dpa_conversions), 0)
        first_row = dpa_conversions[0]
        self.assertIn('conversionValue', first_row)
        self.assertIn('conversionIdentifier', first_row)


if __name__ == '__main__':
    unittest.main()