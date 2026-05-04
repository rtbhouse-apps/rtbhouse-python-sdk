"""Tests for API token managers."""

import warnings
from collections.abc import Generator
from datetime import datetime, timedelta

import pytest
import respx
from freezegun import freeze_time

from rtbhouse_sdk._utils import utcnow
from rtbhouse_sdk.api_tokens.managers import (
    _ROTATION_WINDOW,
    ApiTokenExpiredException,
    ApiTokenManager,
    AsyncApiTokenManager,
)
from rtbhouse_sdk.api_tokens.models import ApiToken
from rtbhouse_sdk.api_tokens.storages.in_memory import AsyncInMemoryApiTokenStorage, InMemoryApiTokenStorage

_NOW = utcnow()

_EXPIRES_FAR_FUTURE = _NOW + timedelta(days=30)
_EXPIRES_IN_ROTATION_WINDOW = _NOW + timedelta(days=2)
_EXPIRES_SOON = _NOW + timedelta(seconds=30)

_TOKEN = "a" * 43
_ROTATED_TOKEN = "b" * 43

_ROTATED_EXPIRES_AT = _NOW + timedelta(days=60)


@pytest.fixture(autouse=True)
def _freeze_time() -> Generator[None]:
    with freeze_time(_NOW):
        yield


_API_TOKEN_DETAILS_RESPONSE = {
    "status": "ok",
    "data": {
        "expiresAt": _EXPIRES_FAR_FUTURE.isoformat(),
    },
}

_ROTATE_RESPONSE = {
    "status": "ok",
    "data": {
        "token": _ROTATED_TOKEN,
        "expiresAt": _ROTATED_EXPIRES_AT.isoformat(),
    },
}


def _create_api_token(
    token: str = _TOKEN,
    expires_at: datetime = _EXPIRES_FAR_FUTURE,
) -> ApiToken:
    return ApiToken(
        token=token,
        expires_at=expires_at,
    )


def test_configure_saves_token_to_storage(api_mock: respx.MockRouter) -> None:
    api_mock.get("/tokens/current").respond(
        200,
        json=_API_TOKEN_DETAILS_RESPONSE,
    )

    storage = InMemoryApiTokenStorage(None)
    manager = ApiTokenManager(storage)

    manager.configure(_TOKEN)

    saved = storage.load()

    assert saved.token == _TOKEN
    assert saved.expires_at == _EXPIRES_FAR_FUTURE


def test_configure_raises_on_invalid_token_length() -> None:
    storage = InMemoryApiTokenStorage(None)
    manager = ApiTokenManager(storage)

    with pytest.raises(ValueError):
        manager.configure("too_short")


def test_get_token_returns_token_when_not_in_rotation_window() -> None:
    api_token = _create_api_token()
    storage = InMemoryApiTokenStorage(api_token)
    manager = ApiTokenManager(storage)

    result = manager.get_token()

    assert result == _TOKEN


def test_get_token_rotates_when_in_rotation_window(api_mock: respx.MockRouter) -> None:
    api_mock.post("/tokens/current/rotate").respond(
        200,
        json=_ROTATE_RESPONSE,
    )

    api_token = _create_api_token(
        expires_at=_EXPIRES_IN_ROTATION_WINDOW,
    )
    storage = InMemoryApiTokenStorage(api_token)
    manager = ApiTokenManager(storage)

    result = manager.get_token()
    saved = storage.load()

    assert result == _ROTATED_TOKEN
    assert saved.token == _ROTATED_TOKEN
    assert saved.expires_at == _ROTATED_EXPIRES_AT


def test_get_token_returns_original_when_rotation_fails(api_mock: respx.MockRouter) -> None:
    api_mock.post("/tokens/current/rotate").respond(
        400,
        json={},
    )

    api_token = _create_api_token(
        expires_at=_EXPIRES_IN_ROTATION_WINDOW,
    )
    storage = InMemoryApiTokenStorage(api_token)
    manager = ApiTokenManager(storage)

    with warnings.catch_warnings(record=True) as caught_warnings:
        result = manager.get_token()

    assert result == _TOKEN
    assert len(caught_warnings) == 1
    assert "Attempted to rotate API token but failed" in str(caught_warnings[0].message)


def test_get_token_raises_when_expired() -> None:
    api_token = _create_api_token(
        expires_at=_EXPIRES_SOON,
    )
    storage = InMemoryApiTokenStorage(api_token)
    manager = ApiTokenManager(storage)

    with pytest.raises(ApiTokenExpiredException):
        manager.get_token()


def test_keep_alive_sends_request(api_mock: respx.MockRouter) -> None:
    api_mock.get("/tokens/current").respond(
        200,
        json=_API_TOKEN_DETAILS_RESPONSE,
    )

    api_token = _create_api_token()
    storage = InMemoryApiTokenStorage(api_token)
    manager = ApiTokenManager(storage)

    manager.keep_alive()

    assert api_mock.calls.call_count == 1


def test_keep_alive_rotates_when_in_rotation_window(api_mock: respx.MockRouter) -> None:
    api_mock.get("/tokens/current").respond(
        200,
        json=_API_TOKEN_DETAILS_RESPONSE,
    )
    api_mock.post("/tokens/current/rotate").respond(
        200,
        json=_ROTATE_RESPONSE,
    )

    api_token = _create_api_token(
        expires_at=_EXPIRES_IN_ROTATION_WINDOW,
    )
    storage = InMemoryApiTokenStorage(api_token)
    manager = ApiTokenManager(storage)

    manager.keep_alive(
        auto_rotate=True,
    )
    saved = storage.load()

    assert saved.token == _ROTATED_TOKEN


def test_keep_alive_raises_when_expired() -> None:
    api_token = _create_api_token(
        expires_at=_EXPIRES_SOON,
    )
    storage = InMemoryApiTokenStorage(api_token)
    manager = ApiTokenManager(storage)

    with pytest.raises(ApiTokenExpiredException):
        manager.keep_alive()


@pytest.mark.parametrize(
    ("time_until_expiry", "expected_in_rotation_window"),
    [
        (timedelta(days=5), False),
        (_ROTATION_WINDOW, True),
        (timedelta(days=3), True),
        (timedelta(hours=1), True),
    ],
)
def test_rotation_window_boundary(
    time_until_expiry: timedelta,
    expected_in_rotation_window: bool,
    api_mock: respx.MockRouter,
) -> None:
    if expected_in_rotation_window:
        api_mock.post("/tokens/current/rotate").respond(
            200,
            json=_ROTATE_RESPONSE,
        )

    expires_at = _NOW + time_until_expiry
    api_token = _create_api_token(
        expires_at=expires_at,
    )
    storage = InMemoryApiTokenStorage(api_token)
    manager = ApiTokenManager(storage)

    result = manager.get_token()

    if expected_in_rotation_window:
        assert result == _ROTATED_TOKEN
    else:
        assert result == _TOKEN


# async


async def test_async_configure_saves_token_to_storage(api_mock: respx.MockRouter) -> None:
    api_mock.get("/tokens/current").respond(
        200,
        json=_API_TOKEN_DETAILS_RESPONSE,
    )

    storage = AsyncInMemoryApiTokenStorage(None)
    manager = AsyncApiTokenManager(storage)

    await manager.configure(_TOKEN)

    saved = await storage.load()

    assert saved.token == _TOKEN
    assert saved.expires_at == _EXPIRES_FAR_FUTURE


async def test_async_configure_raises_on_invalid_token_length() -> None:
    storage = AsyncInMemoryApiTokenStorage(None)
    manager = AsyncApiTokenManager(storage)

    with pytest.raises(ValueError):
        await manager.configure("too_short")


async def test_async_get_token_returns_token_when_not_in_rotation_window() -> None:
    api_token = _create_api_token()
    storage = AsyncInMemoryApiTokenStorage(api_token)
    manager = AsyncApiTokenManager(storage)

    result = await manager.get_token()

    assert result == _TOKEN


async def test_async_get_token_rotates_when_in_rotation_window(
    api_mock: respx.MockRouter,
) -> None:
    api_mock.post("/tokens/current/rotate").respond(
        200,
        json=_ROTATE_RESPONSE,
    )

    api_token = _create_api_token(
        expires_at=_EXPIRES_IN_ROTATION_WINDOW,
    )
    storage = AsyncInMemoryApiTokenStorage(api_token)
    manager = AsyncApiTokenManager(storage)

    result = await manager.get_token()
    saved = await storage.load()

    assert result == _ROTATED_TOKEN
    assert saved.token == _ROTATED_TOKEN


async def test_async_get_token_returns_original_when_rotation_fails(api_mock: respx.MockRouter) -> None:
    api_mock.post("/tokens/current/rotate").respond(
        400,
        json={},
    )

    api_token = _create_api_token(
        expires_at=_EXPIRES_IN_ROTATION_WINDOW,
    )
    storage = AsyncInMemoryApiTokenStorage(api_token)
    manager = AsyncApiTokenManager(storage)

    with warnings.catch_warnings(record=True) as caught_warnings:
        result = await manager.get_token()

    assert result == _TOKEN
    assert len(caught_warnings) == 1
    assert "Attempted to rotate API token but failed" in str(caught_warnings[0].message)


async def test_async_get_token_raises_when_expired() -> None:
    api_token = _create_api_token(
        expires_at=_EXPIRES_SOON,
    )
    storage = AsyncInMemoryApiTokenStorage(api_token)
    manager = AsyncApiTokenManager(storage)

    with pytest.raises(ApiTokenExpiredException):
        await manager.get_token()


async def test_async_keep_alive_sends_request(api_mock: respx.MockRouter) -> None:
    api_mock.get("/tokens/current").respond(
        200,
        json=_API_TOKEN_DETAILS_RESPONSE,
    )

    api_token = _create_api_token()
    storage = AsyncInMemoryApiTokenStorage(api_token)
    manager = AsyncApiTokenManager(storage)

    await manager.keep_alive()

    assert api_mock.calls.call_count == 1


async def test_async_keep_alive_rotates_when_in_rotation_window(
    api_mock: respx.MockRouter,
) -> None:
    api_mock.get("/tokens/current").respond(
        200,
        json=_API_TOKEN_DETAILS_RESPONSE,
    )
    api_mock.post("/tokens/current/rotate").respond(
        200,
        json=_ROTATE_RESPONSE,
    )

    api_token = _create_api_token(
        expires_at=_EXPIRES_IN_ROTATION_WINDOW,
    )
    storage = AsyncInMemoryApiTokenStorage(api_token)
    manager = AsyncApiTokenManager(storage)

    await manager.keep_alive(
        auto_rotate=True,
    )
    saved = await storage.load()

    assert saved.token == _ROTATED_TOKEN
