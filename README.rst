RTB House SDK
=============

Overview
--------

This library provides an easy-to-use Python interface to RTB House API. It allows you to read and manage your campaigns settings, browse offers, download statistics etc.

API docs: https://api.panel.rtbhouse.com/api/docs

Installation
------------

RTB House SDK can be installed with `pip <https://pip.pypa.io/>`_: ::

    $ pip install rtbhouse_sdk


Usage example
-------------

Let's write a script which fetches campaign stats (imps, clicks, postclicks) and shows the result as a table (using ``tabulate`` library).

First set up virtualenv and install requirements: ::

    $ pip install rtbhouse_sdk tabulate

Create an API token in the RTB House Clients Panel (https://panel.rtbhouse.com/user/api-tokens) and copy it to a safe place.

Now you can initialize the API token in local file storage. Paste your API token in prompt after running the command below: ::

    $ python -m rtbhouse_sdk.api_tokens init-json
    Paste your token: PASTE_YOUR_TOKEN_HERE

The authentication token is now ready to use. As long as you use it with the client frequently enough, the SDK will keep the token valid and rotate it automatically (for details see API Token Authentication below):

.. code-block:: python

    from datetime import date, timedelta
    from operator import attrgetter

    from rtbhouse_sdk.api_tokens import ApiTokenManager, JsonFileApiTokenStorage
    from rtbhouse_sdk.client import Client
    from rtbhouse_sdk.schema import CountConvention, StatsGroupBy, StatsMetric
    from tabulate import tabulate

    if __name__ == "__main__":
        storage = JsonFileApiTokenStorage()
        auth = ApiTokenManager(storage)

        with Client(auth=auth) as api:
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

API Token Authentication
^^^^^^^^^^^^^^^^^^^^^^^^

API Tokens provide a secure and manageable way to grant programmatic access without using a login and password. This allows you to connect your integrations to the API, without specific user credentials.

API tokens have a limited lifetime and must be periodically rotated and actively used to prevent expiration. For more details on the API token lifecycle, see the ``LEARN MORE`` link in the Clients Panel API Tokens section.

For automatic token lifecycle management, use ``ApiTokenManager`` / ``AsyncApiTokenManager`` as authentication classes.

These classes support per-request token resolution and allow the token to be stored/retrieved with a storage backend. Currently, for production use, SDK provides a JSON file storage backend.

When used with a storage backend, the SDK can:

- rotate the token automatically when it enters the rotation window and overwrite the stored token with the new one
- keep the token valid without manual maintenance

Rotation eligibility is checked on every request, which means that for typical integrations with regular traffic, you can configure the token once and let the SDK manage it automatically.

For integrations that do not make requests frequently enough to trigger automatic rotation during the rotation window (e.g. at least once a day), use the ``keep-alive-json`` CLI command (see `CLI for API Tokens` below) scheduled with ``cron`` or a similar tool.

CLI for API Tokens
^^^^^^^^^^^^^^^^^^

A CLI interface is available to manage API tokens from the command line: ::

    $ python -m rtbhouse_sdk.api_tokens <command> [options]

``init-json``
"""""""""""""

Initialize JSON file storage with API Token.

First create your API token in the Clients Panel (https://panel.rtbhouse.com/user/api-tokens).

Then provide the token via stdin or interactively when prompted: ::

    $ python -m rtbhouse_sdk.api_tokens init-json
    Paste your token: PASTE_YOUR_TOKEN_HERE
    $ python -m rtbhouse_sdk.api_tokens init-json <<< "$API_TOKEN"
    $ python -m rtbhouse_sdk.api_tokens init-json < token.txt
    $ python -m rtbhouse_sdk.api_tokens init-json --path /custom/path/to/token.json
    

``keep-alive-json``
"""""""""""""""""""

Keep alive a token stored in JSON file storage.

This command refreshes the token's last activity timestamp and optionally rotates the token, if it is in the rotation window.

While you can run this command manually whenever needed, it is recommended to schedule it to run periodically at least once a day, to ensure the token remains active and does not expire: ::
    
    $ python -m rtbhouse_sdk.api_tokens keep-alive-json
    $ python -m rtbhouse_sdk.api_tokens keep-alive-json --skip-auto-rotate
    $ python -m rtbhouse_sdk.api_tokens keep-alive-json --path /custom/path/to/token.json

API Token Storage Backends
^^^^^^^^^^^^^^^^^^^^^^^^^^

Storage backends are responsible for persisting API tokens.

Storage backends must be initialized before use. API token manager classes provide a ``configure(token)`` method to initialize the token programmatically. This method will fetch the token details and save them to storage.

JSON File Storage
"""""""""""""""""

Persist tokens on disk using a JSON file. Use sync ``JsonFileApiTokenStorage`` or async ``AsyncJsonFileApiTokenStorage`` classes.

Storage can be initialized by ``manager.configure(token)`` method call or by using the ``init-json`` CLI command.

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

Use sync ``InMemoryApiTokenStorage`` or async ``AsyncInMemoryApiTokenStorage`` classes.

.. code-block:: python

    from rtbhouse_sdk.api_tokens import ApiTokenManager, InMemoryApiTokenStorage
    from rtbhouse_sdk.client import Client

    storage = InMemoryApiTokenStorage(None)
    manager = ApiTokenManager(storage)
    manager.configure("your_api_token")  # fetches token details and saves to storage

    with Client(auth=manager) as api:
        info = api.get_user_info()

Custom Storage Backend
""""""""""""""""""""""

You can implement your own storage backend by subclassing ``ApiTokenStorage`` (sync) or ``AsyncApiTokenStorage`` (async). Each backend must implement three methods:

- ``acquire_exclusive_for_update()`` — a context manager ensuring exclusive access to the storage
- ``load()`` — load and return the current ``ApiToken``
- ``save(api_token)`` — persist the given ``ApiToken``


API Token Auth (without automatic rotation and storage management)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``ApiTokenAuth`` if you want to authenticate with a fixed API token without automatic rotation or storage management.

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
