"""In-memory storage for API tokens."""

import asyncio
import threading
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager

from ..models import ApiToken
from ._base import ApiTokenStorage, AsyncApiTokenStorage


class InMemoryApiTokenStorage(ApiTokenStorage):
    """In-memory storage for API tokens."""

    _api_token: ApiToken
    _lock: threading.Lock

    def __init__(self, api_token: ApiToken) -> None:
        super().__init__()

        self._api_token = api_token
        self._lock = threading.Lock()

    @contextmanager
    def lock(self) -> Iterator[None]:
        with self._lock:
            yield

    def load(self) -> ApiToken:
        return self._api_token

    def save(self, api_token: ApiToken) -> None:
        self._api_token = api_token


class AsyncInMemoryApiTokenStorage(AsyncApiTokenStorage):
    """Asynchronous in-memory storage for API tokens."""

    _api_token: ApiToken
    _lock: asyncio.Lock

    def __init__(self, api_token: ApiToken) -> None:
        super().__init__()

        self._api_token = api_token
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def lock(self) -> AsyncIterator[None]:
        async with self._lock:
            yield

    async def load(self) -> ApiToken:
        return self._api_token

    async def save(self, api_token: ApiToken) -> None:
        self._api_token = api_token
