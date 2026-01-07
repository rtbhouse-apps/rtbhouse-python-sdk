"""Tests for auth methods."""

import pytest
import respx

from rtbhouse_sdk.client import BasicAuth, BasicTokenAuth, Client


@pytest.mark.parametrize(
    "auth_backend",
    (
        BasicAuth("user", "pwd"),
        BasicTokenAuth("token"),
    ),
)
def test_auth_backend_is_supported(auth_backend: BasicAuth | BasicTokenAuth) -> None:
    Client(auth=auth_backend)


def test_basic_token_auth_flow(api_mock: respx.MockRouter) -> None:
    api_mock.get("/example-endpoint").respond(200, json={"data": {}})

    auth = BasicTokenAuth("abc")
    with Client(auth=auth) as cli:
        cli._get("/example-endpoint")  # pylint: disable=protected-access

    (call,) = api_mock.calls
    assert call.request.headers["authorization"] == "Token abc"
