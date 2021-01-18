RTB House SDK
=============

Overview
--------

This library provides an easy-to-use Python interface to RTB House API. It allows you to read and manage you campaigns settings, browse offers, download statistics etc.


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


.. include LICENSE


License
-------

`MIT <http://opensource.org/licenses/MIT/>`_
