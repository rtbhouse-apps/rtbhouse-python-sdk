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

First, create ``config.py`` file with your api token: ::

    API_TOKEN = "your_api_token_here"


Set up virtualenv and install requirements: ::

    $ pip install rtbhouse_sdk tabulate


.. code-block:: python

    from datetime import date, timedelta
    from operator import attrgetter

    from rtbhouse_sdk.client import ApiTokenAuth, Client
    from rtbhouse_sdk.schema import CountConvention, StatsGroupBy, StatsMetric
    from tabulate import tabulate

    from config import API_TOKEN

    if __name__ == "__main__":
        with Client(auth=ApiTokenAuth(API_TOKEN)) as api:
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


Authentication methods
----------------------

The SDK supports several authentication methods.

API Token Auth (recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

API token authentication using ``ApiTokenAuth``.

.. code-block:: python

    from rtbhouse_sdk.client import ApiTokenAuth, Client

    auth = ApiTokenAuth("your_api_token")

    with Client(auth=auth) as api:
        info = api.get_user_info()

.. code-block:: python

    from rtbhouse_sdk.client import ApiTokenAuth, AsyncClient

    auth = ApiTokenAuth("your_api_token")

    async with AsyncClient(auth=auth) as api:
        info = await api.get_user_info()

.. note::

    API tokens have a limited lifetime and must be periodically rotated and actively used
    to prevent expiration. To handle this automatically, use the utilities provided in the
    `Managed API Token Authentication`_ section.

Managed API Token Authentication
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For automatic token lifecycle management, use ``ApiTokenManager`` / ``AsyncApiTokenManager`` as authentication classes.

These classes support **per-request token resolution** and allow the token to be stored
in a **persistent storage backend**.

When used with a storage backend, the SDK can:

- **rotate the token** automatically when it enters the rotation window and overwrite the stored token with the new one
- keep the token valid without manual maintenance

Rotation eligibility is checked **on every request**, which means that for typical integrations
with regular traffic, you can configure the token once and let the SDK manage it automatically.

For integrations that run infrequently and might miss the rotation window, the same mechanism
can be triggered via **CLI commands** ( check the CLI section below ), allowing token refresh or rotation to be scheduled
using tools like ``cron``.

API Token Storage Backends
^^^^^^^^^^^^^^^^^^^^^^^^^^

JSON File Storage (recommended)
"""""""""""""""""""""""""""""""

Persist tokens on disk using a JSON file. Can be initialized programmatically
via ``ApiTokenManager.configure()`` or by using the ``init-json`` CLI command.

Classes: ``JsonFileApiTokenStorage``, ``AsyncJsonFileApiTokenStorage``

Sync example:

.. code-block:: python

    from rtbhouse_sdk.api_tokens import ApiTokenManager, JsonFileApiTokenStorage
    from rtbhouse_sdk.client import Client

    storage = JsonFileApiTokenStorage()
    auth = ApiTokenManager(storage)

    with Client(auth=auth) as api:
        info = api.get_user_info()

Async example:

.. code-block:: python

    from rtbhouse_sdk.api_tokens import AsyncApiTokenManager, AsyncJsonFileApiTokenStorage
    from rtbhouse_sdk.client import AsyncClient

    storage = AsyncJsonFileApiTokenStorage()
    auth = AsyncApiTokenManager(storage)

    async with AsyncClient(auth=auth) as api:
        info = await api.get_user_info()

In-Memory Storage
"""""""""""""""""

For simple scenarios where true persistence is not required.

Classes: ``InMemoryApiTokenStorage``, ``AsyncInMemoryApiTokenStorage``

.. code-block:: python

    from rtbhouse_sdk.api_tokens import ApiTokenManager, InMemoryApiTokenStorage
    from rtbhouse_sdk.client import Client

    storage = InMemoryApiTokenStorage()
    manager = ApiTokenManager(storage)
    manager.configure("your_api_token")  # fetches token details and saves to storage

    with Client(auth=manager) as api:
        info = api.get_user_info()

Custom Storage Backend
""""""""""""""""""""""

You can implement your own storage backend by subclassing ``ApiTokenStorage`` (sync)
or ``AsyncApiTokenStorage`` (async). Each backend must implement three methods:

- ``lock()`` — a context manager ensuring exclusive access to the storage
- ``load()`` — load and return the current ``ApiToken``
- ``save(api_token)`` — persist the given ``ApiToken``

CLI for API Tokens
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A CLI interface is available to manage API tokens from the command line: ::

    $ python -m rtbhouse_sdk.api_tokens <command> [options]

``init-json``
"""""""""""""

Initialize JSON token storage. The token can be provided via **stdin**: ::

    $ python -m rtbhouse_sdk.api_tokens init-json <<< "$API_TOKEN"
    $ python -m rtbhouse_sdk.api_tokens init-json < token.txt
    $ python -m rtbhouse_sdk.api_tokens init-json

``keep-alive-json``
"""""""""""""""""""

Keep alive a token stored in JSON file storage. This command refreshes the token's
last activity timestamp and optionally rotates the token if it is in the rotation window: ::

    $ python -m rtbhouse_sdk.api_tokens keep-alive-json

Basic Auth
^^^^^^^^^^

Username and password authentication using ``BasicAuth``.

.. code-block:: python

    from rtbhouse_sdk.client import BasicAuth, Client

    auth = BasicAuth(username="jdoe", password="abcd1234")

    with Client(auth=auth) as api:
        info = api.get_user_info()

Basic Token Auth
^^^^^^^^^^^^^^^^

Token-based authentication using ``BasicTokenAuth``.

.. code-block:: python

    from rtbhouse_sdk.client import BasicTokenAuth, Client

    auth = BasicTokenAuth("your_basic_token")

    with Client(auth=auth) as api:
        info = api.get_user_info()

License
-------

`MIT <http://opensource.org/licenses/MIT/>`_
