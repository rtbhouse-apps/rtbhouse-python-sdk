"""Contains classes for managing API tokens"""

import asyncio
import threading
import warnings
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta

from .._utils import utcnow
from ..client import ApiTokenAuth, AsyncClient, AsyncDynamicApiTokenAuth, Client, DynamicApiTokenAuth
from ..exceptions import ApiRequestException
from .models import ApiToken
from .storages.base import ApiTokenStorage, AsyncApiTokenStorage

ROTATION_WINDOW = timedelta(days=4)


EXPIRED_MSG = "API token expired. Please manually create a new one and configure it in storage."


class ApiTokenExpiredException(Exception):
    """Exception raised when the API token has expired."""


class ApiTokenManager(DynamicApiTokenAuth):
    """
    Manages the lifecycle of an API token, including token retrieval, rotation and expiration handling.
    """

    _storage: ApiTokenStorage
    _lock: threading.Lock
    _expiration_margin: timedelta

    def __init__(self, storage: ApiTokenStorage) -> None:
        super().__init__()
        self._storage = storage
        self._lock = threading.Lock()
        self._expiration_margin = timedelta(minutes=1)

    @contextmanager
    def with_client(self, token: str) -> Iterator[Client]:
        client = Client(auth=ApiTokenAuth(token=token))
        try:
            yield client
        finally:
            client.close()

    def get_token(self) -> str:
        api_token = self._storage.load()
        now = utcnow()

        _raise_if_expired(api_token, now, self._expiration_margin)

        if not _in_rotation_window(api_token, now):
            # fast path
            return api_token.token

        with self._lock:
            # reload inside lock
            api_token = self._storage.load()
            now = utcnow()

            _raise_if_expired(api_token, now, self._expiration_margin)

            if not _in_rotation_window(api_token, now):
                return api_token.token

            with self.with_client(api_token.token) as client:
                try:
                    rotated = client.rotate_current_api_token()

                    api_token = ApiToken(
                        token=rotated.token,
                        expires_at=rotated.expires_at,
                    )
                    self._storage.save(api_token)
                except ApiRequestException as e:
                    warnings.warn(
                        f"Attempted to rotate API token but failed. "
                        "Please check whether the token has already been rotated. "
                        f"Original error: {e}"
                    )

            return api_token.token

    def keep_alive(self, auto_rotate: bool = False) -> None:
        with self._lock:
            api_token = self._storage.load()
            now = utcnow()

            _raise_if_expired(api_token, now, self._expiration_margin)

            with self.with_client(api_token.token) as client:
                # bump used at to now to keep the token alive
                client.get_current_api_token()

                if not auto_rotate:
                    return

                if not _in_rotation_window(api_token, now):
                    return

                rotated = client.rotate_current_api_token()

            api_token = ApiToken(
                token=rotated.token,
                expires_at=rotated.expires_at,
            )
            self._storage.save(api_token)


class AsyncApiTokenManager(AsyncDynamicApiTokenAuth):
    """Asynchronous version of ApiTokenManager."""

    _storage: AsyncApiTokenStorage
    _lock: asyncio.Lock
    _expiration_margin: timedelta

    def __init__(self, storage: AsyncApiTokenStorage) -> None:
        super().__init__()
        self._storage = storage
        self._lock = asyncio.Lock()
        self._expiration_margin = timedelta(minutes=1)

    @asynccontextmanager
    async def with_client(self, token: str) -> AsyncIterator[AsyncClient]:
        client = AsyncClient(auth=ApiTokenAuth(token=token))
        try:
            yield client
        finally:
            await client.close()

    async def get_token(self) -> str:
        api_token = await self._storage.load()
        now = utcnow()

        _raise_if_expired(api_token, now, self._expiration_margin)

        if not _in_rotation_window(api_token, now):
            # fast path
            return api_token.token

        async with self._lock:
            # reload inside lock
            api_token = await self._storage.load()
            now = utcnow()

            _raise_if_expired(api_token, now, self._expiration_margin)

            if not _in_rotation_window(api_token, now):
                return api_token.token

            async with self.with_client(api_token.token) as client:
                try:
                    rotated = await client.rotate_current_api_token()

                    api_token = ApiToken(
                        token=rotated.token,
                        expires_at=rotated.expires_at,
                    )
                    await self._storage.save(api_token)
                except ApiRequestException as e:
                    warnings.warn(
                        f"Attempted to rotate API token but failed. "
                        "Please check whether the token has already been rotated. "
                        f"Original error: {e}"
                    )

            return api_token.token

    async def keep_alive(self, auto_rotate: bool) -> None:
        async with self._lock:
            api_token = await self._storage.load()
            now = utcnow()

            _raise_if_expired(api_token, now, self._expiration_margin)

            async with self.with_client(api_token.token) as client:
                # bump used at to now to keep the token alive
                await client.get_current_api_token()

                if not auto_rotate:
                    return

                if not _in_rotation_window(api_token, now):
                    return

                rotated = await client.rotate_current_api_token()

            api_token = ApiToken(
                token=rotated.token,
                expires_at=rotated.expires_at,
            )
            await self._storage.save(api_token)


def _raise_if_expired(api_token: ApiToken, now: datetime, expiration_margin: timedelta) -> None:
    if now >= api_token.expires_at - expiration_margin:
        raise ApiTokenExpiredException(EXPIRED_MSG)


def _in_rotation_window(api_token: ApiToken, now: datetime) -> bool:
    return now >= (api_token.expires_at - ROTATION_WINDOW)
