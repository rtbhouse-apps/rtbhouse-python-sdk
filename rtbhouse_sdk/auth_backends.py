"""Defines auth backends used by SDK."""
import typing

from httpx import Auth
from httpx import BasicAuth as HttpxBasicAuth
from httpx import Request, Response


class BasicAuth(HttpxBasicAuth):
    """A basic auth backend redefinition."""


class BasicTokenAuth(Auth):
    """Basic token auth backend."""

    def __init__(self, token: str):
        self._token = token

    def auth_flow(self, request: Request) -> typing.Generator[Request, Response, None]:
        request.headers["Authorization"] = f"Token {self._token}"
        yield request
