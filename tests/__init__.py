"""Common data for tests."""
from datetime import date

from rtbhouse_sdk.client import API_BASE_URL, API_VERSION

BASE_URL = f"{API_BASE_URL}/{API_VERSION}"

DAY_FROM = date(2020, 9, 1)
DAY_TO = date(2020, 9, 1)
