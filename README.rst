RTB House SDK
=============

Overview
--------

This library provides an easy-to-use Python interface to RTB House API. It allows you to read and manage you campaigns settings, browse offers, download statistics etc.

API docs: https://api.panel.rtbhouse.com/api/docs

Installation
------------

RTB House SDK can be installed with `pip <https://pip.pypa.io/>`_: ::

    $ pip install rtbhouse_sdk


Usage example
-------------

Let's write a script which fetches campaign stats (imps, clicks, postclicks) and shows the result as a table (using ``tabulate`` library).

First, create ``config.py`` file with your credentials: ::

    USERNAME = 'jdoe'
    PASSWORD = 'abcd1234'


Set up virtualenv and install requirements: ::

    $ pip install rtbhouse_sdk tabulate


.. code-block:: python

    from datetime import date, timedelta
    from operator import attrgetter

    from rtbhouse_sdk.client import BasicAuth, Client
    from rtbhouse_sdk.schema import CountConvention, StatsGroupBy, StatsMetric
    from tabulate import tabulate

    from config import PASSWORD, USERNAME

    if __name__ == "__main__":
        with Client(auth=BasicAuth(USERNAME, PASSWORD)) as api:
            advertisers = api.get_advertisers()
            day_to = date.today()
            day_from = day_to - timedelta(days=30)
            group_by = [StatsGroupBy.DAY]
            metrics = [
                StatsMetric.IMPS_COUNT,
                StatsMetric.CLICKS_COUNT,
                StatsMetric.CAMPAIGN_COST,
                StatsMetric.CONVERSIONS_COUNT,
                StatsMetric.CTR
            ]
            stats = api.get_rtb_stats(
                advertisers[0].hash,
                day_from,
                day_to,
                group_by,
                metrics,
                count_convention=CountConvention.ATTRIBUTED_POST_CLICK,
            )
        columns = group_by + metrics
        data_frame = [
            [getattr(row, c.name.lower()) for c in columns]
            for row in reversed(sorted(stats, key=attrgetter("day")))
        ]
        print(tabulate(data_frame, headers=columns))


License
-------

`MIT <http://opensource.org/licenses/MIT/>`_
