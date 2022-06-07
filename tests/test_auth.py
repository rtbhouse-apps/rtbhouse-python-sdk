"""Tests for auth methods."""
from typing import Union

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
def test_auth_backend_is_supported(auth_backend: Union[BasicAuth, BasicTokenAuth]) -> None:
    Client(auth=auth_backend)


def test_basic_token_auth_flow(base_url: str, mocked_response: respx.MockRouter) -> None:
    mocked_response.get(f"{base_url}/example-endpoint").respond(200, json={"data": {}})

    auth = BasicTokenAuth("abc")
    with Client(auth=auth) as cli:
        cli._get("/example-endpoint")  # pylint: disable=protected-access

    assert mocked_response.calls[0].request.headers["authorization"] == "Token abc"
