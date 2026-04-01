"""Tests for in-memory API token storage."""

from datetime import timedelta

from rtbhouse_sdk._utils import utcnow
from rtbhouse_sdk.api_tokens.models import ApiToken
from rtbhouse_sdk.api_tokens.storages.in_memory import AsyncInMemoryApiTokenStorage, InMemoryApiTokenStorage

_EXPIRES_AT = utcnow() + timedelta(days=30)

_API_TOKEN = ApiToken(
    token="original_token",
    expires_at=_EXPIRES_AT,
)

_UPDATED_API_TOKEN = ApiToken(
    token="updated_token",
    expires_at=_EXPIRES_AT,
)


def test_load_returns_initial_token() -> None:
    storage = InMemoryApiTokenStorage(_API_TOKEN)

    result = storage.load()

    assert result.token == _API_TOKEN.token
    assert result.expires_at == _EXPIRES_AT


def test_save_updates_token() -> None:
    storage = InMemoryApiTokenStorage(_API_TOKEN)

    storage.save(_UPDATED_API_TOKEN)

    result = storage.load()

    assert result.token == _UPDATED_API_TOKEN.token
    assert result.expires_at == _EXPIRES_AT


# async


async def test_async_load_returns_initial_token() -> None:
    storage = AsyncInMemoryApiTokenStorage(_API_TOKEN)

    result = await storage.load()

    assert result.token == _API_TOKEN.token
    assert result.expires_at == _EXPIRES_AT


async def test_async_save_updates_token() -> None:
    storage = AsyncInMemoryApiTokenStorage(_API_TOKEN)

    await storage.save(_UPDATED_API_TOKEN)

    result = await storage.load()

    assert result.token == _UPDATED_API_TOKEN.token
    assert result.expires_at == _EXPIRES_AT
