"""Contains classes for managing API tokens."""

import warnings
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta

from .._utils import utcnow
from ..client import ApiTokenAuth, AsyncClient, AsyncDynamicApiTokenAuth, Client, DynamicApiTokenAuth
from ..exceptions import ApiRequestException
from .models import ApiToken
from .storages._base import ApiTokenStorage, AsyncApiTokenStorage

_TOKEN_LENGTH = 43
_ROTATION_WINDOW = timedelta(days=4)
_EXPIRATION_MARGIN = timedelta(minutes=1)


class ApiTokenExpiredException(Exception):
    """Exception raised when the API token has expired."""


class ApiTokenManager(DynamicApiTokenAuth):
    """
    Manages the lifecycle of an API token, including token initialization, retrieval, rotation and expiration handling.
    """

    _storage: ApiTokenStorage

    def __init__(self, storage: ApiTokenStorage) -> None:
        super().__init__()

        self._storage = storage

    @contextmanager
    def _with_client(self, token: str) -> Iterator[Client]:
        auth = ApiTokenAuth(token)
        client = Client(auth)

        try:
            yield client
        finally:
            client.close()

    def configure(self, token: str) -> None:
        if len(token) != _TOKEN_LENGTH:
            raise ValueError("Invalid token format.")

        with self._storage.lock():
            with self._with_client(token) as client:
                api_token_details = client.get_current_api_token()

            api_token = ApiToken(
                token=token,
                expires_at=api_token_details.expires_at,
            )
            self._storage.save(api_token)

    def get_token(self) -> str:
        token, in_rotation_window = self._get_validated_token()

        if not in_rotation_window:
            return token

        with self._storage.lock():
            # reload inside lock
            token, in_rotation_window = self._get_validated_token()

            if not in_rotation_window:
                return token

            with self._with_client(token) as client:
                rotated_api_token = self._rotate_and_save(
                    client,
                    raise_on_failure=False,
                )

            if rotated_api_token is not None:
                token = rotated_api_token

            return token

    def keep_alive(
        self,
        *,
        auto_rotate: bool = True,
    ) -> None:
        with self._storage.lock():
            token, in_rotation_window = self._get_validated_token()

            with self._with_client(token) as client:
                # bump last activity timestamp to keep the token alive
                client.get_current_api_token()

                if not auto_rotate or not in_rotation_window:
                    return

                self._rotate_and_save(client)

    def _get_validated_token(self) -> tuple[str, bool]:  # (token, in_rotation_window)
        now = utcnow()

        api_token = self._storage.load()
        _raise_if_expired(now, api_token.expires_at)

        in_rotation_window = _in_rotation_window(now, api_token.expires_at)

        return api_token.token, in_rotation_window

    def _rotate_and_save(
        self,
        client: Client,
        *,
        raise_on_failure: bool = True,
    ) -> str | None:
        try:
            rotated = client.rotate_current_api_token()
        except ApiRequestException as e:
            if raise_on_failure:
                raise

            warnings.warn(
                "Attempted to rotate API token but failed. "
                "Please check whether the token has already been rotated. "
                f"Original error: {e}"
            )

            return None

        api_token = ApiToken(
            token=rotated.token,
            expires_at=rotated.expires_at,
        )
        self._storage.save(api_token)

        return api_token.token


class AsyncApiTokenManager(AsyncDynamicApiTokenAuth):
    """Asynchronous version of ApiTokenManager."""

    _storage: AsyncApiTokenStorage

    def __init__(self, storage: AsyncApiTokenStorage) -> None:
        super().__init__()

        self._storage = storage

    @asynccontextmanager
    async def _with_client(self, token: str) -> AsyncIterator[AsyncClient]:
        auth = ApiTokenAuth(token)
        client = AsyncClient(auth)

        try:
            yield client
        finally:
            await client.close()

    async def configure(self, token: str) -> None:
        if len(token) != _TOKEN_LENGTH:
            raise ValueError("Invalid token format.")

        async with self._storage.lock():
            async with self._with_client(token) as client:
                api_token_details = await client.get_current_api_token()

            api_token = ApiToken(
                token=token,
                expires_at=api_token_details.expires_at,
            )
            await self._storage.save(api_token)

    async def get_token(self) -> str:
        token, in_rotation_window = await self._get_validated_token()

        if not in_rotation_window:
            return token

        async with self._storage.lock():
            # reload inside lock
            token, in_rotation_window = await self._get_validated_token()

            if not in_rotation_window:
                return token

            async with self._with_client(token) as client:
                rotated_api_token = await self._rotate_and_save(
                    client,
                    raise_on_failure=False,
                )

            if rotated_api_token is not None:
                token = rotated_api_token

            return token

    async def keep_alive(
        self,
        *,
        auto_rotate: bool = True,
    ) -> None:
        async with self._storage.lock():
            token, in_rotation_window = await self._get_validated_token()

            async with self._with_client(token) as client:
                # bump last activity timestamp to keep the token alive
                await client.get_current_api_token()

                if not auto_rotate or not in_rotation_window:
                    return

                await self._rotate_and_save(client)

    async def _get_validated_token(self) -> tuple[str, bool]:  # (token, in_rotation_window)
        now = utcnow()

        api_token = await self._storage.load()
        _raise_if_expired(now, api_token.expires_at)

        in_rotation_window = _in_rotation_window(now, api_token.expires_at)

        return api_token.token, in_rotation_window

    async def _rotate_and_save(
        self,
        client: AsyncClient,
        *,
        raise_on_failure: bool = True,
    ) -> str | None:
        try:
            rotated = await client.rotate_current_api_token()
        except ApiRequestException as e:
            if raise_on_failure:
                raise

            warnings.warn(
                "Attempted to rotate API token but failed. "
                "Please check whether the token has already been rotated. "
                f"Original error: {e}"
            )

            return None

        api_token = ApiToken(
            token=rotated.token,
            expires_at=rotated.expires_at,
        )
        await self._storage.save(api_token)

        return api_token.token


def _raise_if_expired(now: datetime, expires_at: datetime) -> None:
    if now >= expires_at - _EXPIRATION_MARGIN:
        raise ApiTokenExpiredException(
            "API token expired. Please manually create a new one and configure it in storage."
        )


def _in_rotation_window(now: datetime, expires_at: datetime) -> bool:
    return now >= (expires_at - _ROTATION_WINDOW)
