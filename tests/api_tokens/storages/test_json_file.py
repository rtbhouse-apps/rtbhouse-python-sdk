"""Tests for JSON file API token storage."""

from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from rtbhouse_sdk._utils import utcnow
from rtbhouse_sdk.api_tokens.models import ApiToken
from rtbhouse_sdk.api_tokens.storages._base import ApiTokenStorageException
from rtbhouse_sdk.api_tokens.storages.json_file import AsyncJsonFileApiTokenStorage, JsonFileApiTokenStorage

_EXPIRES_AT = utcnow() + timedelta(days=30)

_API_TOKEN = ApiToken(
    token="original_token",
    expires_at=_EXPIRES_AT,
)

_UPDATED_API_TOKEN = ApiToken(
    token="updated_token",
    expires_at=_EXPIRES_AT,
)


@pytest.fixture(name="token_path")  # to avoid linters errors
def token_path_fixture(tmp_path: Path) -> Path:
    return tmp_path / "api_token.json"


def test_load_returns_initial_token(token_path: Path) -> None:
    storage = JsonFileApiTokenStorage(token_path)

    with storage.lock():
        storage.save(_API_TOKEN)

    result = storage.load()

    assert result.token == _API_TOKEN.token
    assert result.expires_at == _EXPIRES_AT


def test_save_updates_token(token_path: Path) -> None:
    storage = JsonFileApiTokenStorage(token_path)

    with storage.lock():
        storage.save(_API_TOKEN)
        storage.save(_UPDATED_API_TOKEN)

    result = storage.load()

    assert result.token == _UPDATED_API_TOKEN.token
    assert result.expires_at == _EXPIRES_AT


def test_load_raises_when_file_not_found(token_path: Path) -> None:
    storage = JsonFileApiTokenStorage(token_path)

    with pytest.raises(ApiTokenStorageException):
        storage.load()


def test_load_raises_on_invalid_json(token_path: Path) -> None:
    token_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    token_path.write_text(
        "not valid json",
        encoding="utf-8",
    )
    storage = JsonFileApiTokenStorage(token_path)

    with pytest.raises(ApiTokenStorageException):
        storage.load()


def test_load_uses_cache_on_second_call(token_path: Path) -> None:
    storage = JsonFileApiTokenStorage(token_path)
    with storage.lock():
        storage.save(_API_TOKEN)

    first_load = storage.load()
    # Overwrite file directly, cache should return old value
    token_path.write_text(
        _UPDATED_API_TOKEN.model_dump_json(),
        encoding="utf-8",
    )
    second_load = storage.load()

    assert first_load.token == _API_TOKEN.token
    assert second_load.token == _API_TOKEN.token


def test_load_bypasses_cache_after_expiry(token_path: Path) -> None:
    storage = JsonFileApiTokenStorage(token_path)
    with storage.lock():
        storage.save(_API_TOKEN)

    storage.load()  # populate cache

    # Overwrite file directly
    token_path.write_text(
        _UPDATED_API_TOKEN.model_dump_json(),
        encoding="utf-8",
    )

    # Update time so cache expires (>5 minutes)
    future_time = utcnow() + timedelta(minutes=6)
    with patch(
        "rtbhouse_sdk.api_tokens.storages.json_file.utcnow",
        return_value=future_time,
    ):
        result = storage.load()

    assert result.token == _UPDATED_API_TOKEN.token


def test_lock_invalidates_cache(token_path: Path) -> None:
    storage = JsonFileApiTokenStorage(token_path)
    with storage.lock():
        storage.save(_API_TOKEN)

    storage.load()  # populate cache

    # Overwrite file directly
    token_path.write_text(
        _UPDATED_API_TOKEN.model_dump_json(),
        encoding="utf-8",
    )

    with storage.lock():
        result = storage.load()

    assert result.token == _UPDATED_API_TOKEN.token


# async


async def test_async_load_returns_initial_token(token_path: Path) -> None:
    storage = AsyncJsonFileApiTokenStorage(token_path)

    async with storage.lock():
        await storage.save(_API_TOKEN)

    result = await storage.load()

    assert result.token == _API_TOKEN.token
    assert result.expires_at == _EXPIRES_AT


async def test_async_save_updates_token(token_path: Path) -> None:
    storage = AsyncJsonFileApiTokenStorage(token_path)

    async with storage.lock():
        await storage.save(_API_TOKEN)
        await storage.save(_UPDATED_API_TOKEN)

    result = await storage.load()

    assert result.token == _UPDATED_API_TOKEN.token
    assert result.expires_at == _EXPIRES_AT
