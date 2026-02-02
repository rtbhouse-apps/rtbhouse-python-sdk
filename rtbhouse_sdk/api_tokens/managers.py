"""Contains classes for managing API tokens"""

import asyncio
import os
import threading
import warnings
from datetime import datetime, timedelta

from rtbhouse_sdk._utils import utcnow
from rtbhouse_sdk.api_tokens.api import ApiTokensAPI, AsyncApiTokensAPI
from rtbhouse_sdk.api_tokens.models import ApiToken
from rtbhouse_sdk.api_tokens.storages import ApiTokenStorage, ApiTokenStorageException, AsyncApiTokenStorage
from rtbhouse_sdk.client import ApiTokenProvider, AsyncApiTokenProvider

ROTATION_WINDOW = timedelta(days=4)

DEFAULT_TOKEN_CONFIGURE_ENV_VAR = "RTBH_API_TOKEN"

EXPIRED_MSG = "API token expired. Please manually create a new one and configure it by calling the configure() method."


class TokenExpiredException(Exception):
    """Exception raised when the API token has expired."""


class ApiTokenManager(ApiTokenProvider):
    """
    Manages the lifecycle of an API token, including configuration, rotation and expiration handling.

    Initial token configuration example:
    ```
    manager = ApiTokenManager(storage)
    manager.configure(token="your_initial_token")
    ```

    You can also configure it from environment variable:
    ```
    manager.configure_from_env(env_var="RTBH_API_TOKEN")
    ```
    """

    def __init__(self, storage: ApiTokenStorage) -> None:
        self._storage = storage
        self._api = ApiTokensAPI()
        self._lock = threading.Lock()
        self._expiration_margin = timedelta(minutes=1)

    def configure(self, token: str) -> None:
        status = self._api.heartbeat(token)

        if status.is_expired:
            raise TokenExpiredException(EXPIRED_MSG)

        api_token = ApiToken(
            token=token,
            expires_at=status.expires_at,
        )
        self._storage.save(api_token)

    def configure_from_env(
        self,
        env_var: str = DEFAULT_TOKEN_CONFIGURE_ENV_VAR,
        overwrite: bool = False,
    ) -> None:
        token = os.getenv(env_var)
        if token is None:
            raise ValueError(f"Environment variable '{env_var}' is not set")

        if not overwrite and self.is_configured():
            return

        self.configure(token)

    def is_configured(self) -> bool:
        try:
            self._storage.load()
            return True
        except ApiTokenStorageException:
            return False

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

            status = self._api.heartbeat(api_token.token)

            if status.is_expired:
                raise TokenExpiredException(EXPIRED_MSG)

            if not status.can_rotate:
                if _in_rotation_window(api_token, now):
                    warnings.warn(
                        "Couldn't rotate API token and it may expire soon. "
                        "Please check whether it has already been rotated."
                    )
                return api_token.token

            rotated = self._api.rotate(api_token.token)

            new_api_token = ApiToken(
                token=rotated.token,
                expires_at=rotated.expires_at,
            )
            self._storage.save(new_api_token)

            return new_api_token.token

    def keep_alive(self) -> None:
        with self._lock:
            api_token = self._storage.load()
            now = utcnow()

            _raise_if_expired(api_token, now, self._expiration_margin)

            status = self._api.heartbeat(api_token.token)

            if status.is_expired:
                raise TokenExpiredException(EXPIRED_MSG)

            if not status.can_rotate:
                if _in_rotation_window(api_token, now):
                    warnings.warn(
                        "Couldn't rotate API token and it may expire soon. "
                        "Please check whether it has already been rotated."
                    )
                return

            rotated = self._api.rotate(api_token.token)
            new_api_token = ApiToken(
                token=rotated.token,
                expires_at=rotated.expires_at,
            )
            self._storage.save(new_api_token)


class AsyncApiTokenManager(AsyncApiTokenProvider):
    """Asynchronous version of ApiTokenManager."""

    def __init__(self, storage: AsyncApiTokenStorage) -> None:
        self._storage = storage
        self._api = AsyncApiTokensAPI()
        self._lock = asyncio.Lock()
        self._expiration_margin = timedelta(minutes=1)

    async def configure(self, token: str) -> None:
        status = await self._api.heartbeat(token)

        if status.is_expired:
            raise TokenExpiredException(EXPIRED_MSG)

        api_token = ApiToken(
            token=token,
            expires_at=status.expires_at,
        )
        await self._storage.save(api_token)

    async def configure_from_env(
        self,
        env_var: str = DEFAULT_TOKEN_CONFIGURE_ENV_VAR,
        overwrite: bool = False,
    ) -> None:
        token = os.getenv(env_var)
        if token is None:
            raise ValueError(f"Environment variable '{env_var}' is not set")

        if not overwrite and await self.is_configured():
            return

        await self.configure(token)

    async def is_configured(self) -> bool:
        try:
            await self._storage.load()
            return True
        except ApiTokenStorageException:
            return False

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

            status = await self._api.heartbeat(api_token.token)

            if status.is_expired:
                raise TokenExpiredException(EXPIRED_MSG)

            if not status.can_rotate:
                if _in_rotation_window(api_token, now):
                    warnings.warn(
                        "Couldn't rotate API token and it may expire soon. "
                        "Please check whether it has already been rotated."
                    )
                return api_token.token

            rotated = await self._api.rotate(api_token.token)

            new_api_token = ApiToken(
                token=rotated.token,
                expires_at=rotated.expires_at,
            )
            await self._storage.save(new_api_token)

            return new_api_token.token

    async def keep_alive(self) -> None:
        async with self._lock:
            api_token = await self._storage.load()
            now = utcnow()

            _raise_if_expired(api_token, now, self._expiration_margin)

            status = await self._api.heartbeat(api_token.token)

            if status.is_expired:
                raise TokenExpiredException(EXPIRED_MSG)

            if not status.can_rotate:
                if _in_rotation_window(api_token, now):
                    warnings.warn(
                        "Couldn't rotate API token and it may expire soon. "
                        "Please check whether it has already been rotated."
                    )
                return

            rotated = await self._api.rotate(api_token.token)
            new_api_token = ApiToken(
                token=rotated.token,
                expires_at=rotated.expires_at,
            )
            await self._storage.save(new_api_token)


def _raise_if_expired(api_token: ApiToken, now: datetime, expiration_margin: timedelta) -> None:
    if now >= api_token.expires_at - expiration_margin:
        raise TokenExpiredException(EXPIRED_MSG)


def _in_rotation_window(api_token: ApiToken, now: datetime) -> bool:
    return now >= (api_token.expires_at - ROTATION_WINDOW)
