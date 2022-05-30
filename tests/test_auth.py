import httpx
import pytest

from rtbhouse_sdk.auth_backends import BasicAuth, BasicTokenAuth
from rtbhouse_sdk.client import Client


@pytest.mark.parametrize(
    "auth_backend",
    (
        BasicAuth("user", "pwd"),
        BasicTokenAuth("token"),
    ),
)
def test_auth_backend_is_supported(auth_backend):
    Client(auth=auth_backend)


def test_basic_token_auth_flow(mocked_response):
    url = "http://example.com"
    mocked_response.get(url).respond(200)

    auth = BasicTokenAuth("abc")
    httpx.get(url, auth=auth)

    assert mocked_response.calls[0].request.headers["authorization"] == "Token abc"