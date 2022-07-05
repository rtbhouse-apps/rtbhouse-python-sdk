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

Breaking changes in version 9.0.0
-------------------------

This version introduced many breaking changes. Please see this guide on how to migrate from older versions.

Python compatibility
~~~~~~~~~~~~~~~~~~~~

Python2 is no longer supported. Please use Python3.7+.

Authentication
~~~~~~~~~~~~~~

Two authentication methods are available: basic auth and basic token auth

.. code-block:: python

    # previously
    from rtbhouse_sdk.reports_api import ReportsApiSession
    api = ReportsApiSession(username='myuser', password='mypassword')

    # currently
    from rtbhouse_sdk.client import BasicAuth, BasicTokenAuth, Client

    # with basic auth
    api = Client(auth=BasicAuth(username='myuser', password='mypassword'))
    # or with basic token auth
    api = Client(auth=BasicTokenAuth(token='mytoken'))

Result data
~~~~~~~~~~~

Each endpoint method returns data in form of `Pydantic model <https://pydantic-docs.helpmanual.io/usage/models/>`_.

In order to use dictionary just convert it using `dict()` method on resulting object.

.. code-block:: python

    # previously
    info = api.get_user_info()
    print(info['isClientUser']

    # currently
    # with a Pydantic model
    info = api.get_user_info()
    print(info.is_client_user)
    # or with a dict
    print(info.dict()['is_client_user'])

Clients
~~~~~~~

SDK offers synchronous and asynchronous clients to work with. They have the same set of endpoints.

It is recommended to close the session using `close()` method. For convenience there is also a context manager that takes care of that.

.. code-block:: python

    from rtbhouse_sdk.client import BasicTokenAuth, Client

    auth = BasicTokenAuth(token='mytoken')

    # using close
    api = Client(auth=auth)
    info = api.get_user_info()
    api.close()

    # or using context manager
    with Client(auth=auth) as api:
        info = api.get_user_info()

Same goes with async client.

.. code-block:: python

    from rtbhouse_sdk.client import BasicTokenAuth, AsyncClient

    auth = BasicTokenAuth(token='mytoken')

    # using close
    api = AsyncClient(auth=auth)
    info = await api.get_user_info()
    await api.close()

    # or using context manager
    async with AsyncClient(auth=auth) as api:
        info = await api.get_user_info()

Query params
~~~~~~~~~~~~

Another breaking change is how params are handled. Instead of plain strings there are now enums you can use for query parameters.

.. code-block:: python

    # previously
    from rtbhouse_sdk.reports_api import ReportsApiSession
    api = ReportsApiSession(username='myuser', password='mypassword')

    # currently
    from rtbhouse_sdk.client import BasicAuth, BasicTokenAuth, Client
    from rtbhouse_sdk.schema import StatsGroupBy, StatsMetric

    auth = BasicTokenAuth(token='mytoken')
    api = Client(auth=auth)
    api.get_rtb_stats(
        'adv_hash',
        day_from,
        day_to,
        [StatsGroupBy.ADVERTISER, StatsGroupBy.DAY],
        [StatsMetric.CAMPAIGN_COST, StatsMetric.CR],
    )

Other changes
~~~~~~~~~~~~~

- `get_rtb_conversions` is now a generator function
- SDK is now fully typed


License
-------

`MIT <http://opensource.org/licenses/MIT/>`_
