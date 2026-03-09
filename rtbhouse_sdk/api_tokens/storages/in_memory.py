"""In-memory storage for API tokens."""

from ..models import ApiToken
from .base import ApiTokenStorage, ApiTokenStorageException, AsyncApiTokenStorage


class InMemoryApiTokenStorage(ApiTokenStorage):
    """In-memory storage for API tokens."""

    _api_token: ApiToken

    def __init__(self, api_token: ApiToken) -> None:
        super().__init__()
        self._api_token = api_token

    def load(self) -> ApiToken:
        if self._api_token is None:
            raise ApiTokenStorageException("No API token stored in memory")
        return self._api_token

    def save(self, api_token: ApiToken) -> None:
        self._api_token = api_token


class AsyncInMemoryApiTokenStorage(AsyncApiTokenStorage):
    """Asynchronous in-memory storage for API tokens."""

    _api_token: ApiToken

    def __init__(self, api_token: ApiToken) -> None:
        super().__init__()
        self._api_token = api_token

    async def load(self) -> ApiToken:
        if self._api_token is None:
            raise ApiTokenStorageException("No API token stored in memory")
        return self._api_token

    async def save(self, api_token: ApiToken) -> None:
        self._api_token = api_token
