import unittest

from config import USERNAME, PASSWORD
from rtbhouse_sdk.reports_api import ReportsApiSession


class TestReportsApi(unittest.TestCase):

    def test_get_user_info(self):
        api = ReportsApiSession(USERNAME, PASSWORD)
        data = api.get_user_info()
        self.assertIn('username', data)
        self.assertIn('email', data)


if __name__ == '__main__':
    unittest.main()