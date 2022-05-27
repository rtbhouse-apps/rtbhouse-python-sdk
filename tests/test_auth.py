import httpx
import pytest

from rtbhouse_sdk.auth_backends import BasicAuth, BasicTokenAuth
from rtbhouse_sdk.client import Client


def test_no_auth_provided():
    with pytest.raises(ValueError) as cm:
        Client()

    assert str(cm.value) == "You need to provide either auth or username and password."


def test_auth_with_username_and_password():
    Client(username="name", password="pwd")


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
