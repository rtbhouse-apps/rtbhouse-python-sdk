"""Tests for auth methods."""

import respx

from rtbhouse_sdk.client import BasicAuth, BasicTokenAuth, Client

from . import BASE_URL


def test_basic_auth(mocked_response: respx.MockRouter) -> None:
    mocked_response.get(f"{BASE_URL}/example-endpoint").respond(200, json={"data": {}})

    auth = BasicAuth("user", "pwd")
    with Client(auth=auth) as cli:
        cli._get("/example-endpoint")  # pylint: disable=protected-access

    auth_header = mocked_response.calls[0].request.headers["authorization"]
    assert auth_header.startswith("Basic ")


def test_basic_token_auth(mocked_response: respx.MockRouter) -> None:
    mocked_response.get(f"{BASE_URL}/example-endpoint").respond(200, json={"data": {}})

    auth = BasicTokenAuth("abc")
    with Client(auth=auth) as cli:
        cli._get("/example-endpoint")  # pylint: disable=protected-access

    assert mocked_response.calls[0].request.headers["authorization"] == "Token abc"
