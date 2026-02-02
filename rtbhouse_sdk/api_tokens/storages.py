"""Contains classes for API token storage implementations."""

import asyncio
import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

from rtbhouse_sdk.api_tokens.models import ApiToken

DEFAULT_JSON_FILE_PATH = "~/.rtbhouse/api_token.json"


class ApiTokenStorageException(Exception):
    """Exception raised for errors in the API token storage operations."""


class ApiTokenStorage(ABC):
    """Abstract base class for API token storage implementations."""

    @abstractmethod
    def load(self) -> ApiToken:
        pass

    @abstractmethod
    def save(self, api_token: ApiToken) -> None:
        pass

    @abstractmethod
    def delete(self) -> None:
        pass


class InMemoryApiTokenStorage(ApiTokenStorage):
    """In-memory storage for API tokens."""

    def __init__(self, api_token: ApiToken | None = None) -> None:
        super().__init__()
        self._api_token = api_token

    def load(self) -> ApiToken:
        if self._api_token is None:
            raise ApiTokenStorageException("No API token stored in memory")
        return self._api_token

    def save(self, api_token: ApiToken) -> None:
        self._api_token = api_token

    def delete(self) -> None:
        self._api_token = None


class JsonFileApiTokenStorage(ApiTokenStorage):
    """JSON file storage for API tokens."""

    def __init__(self, path: str | Path = DEFAULT_JSON_FILE_PATH) -> None:
        super().__init__()
        self._path = Path(path).expanduser()

    def load(self) -> ApiToken:
        try:
            text = self._path.read_text(encoding="utf-8")
        except FileNotFoundError as e:
            raise ApiTokenStorageException("JSON file does not exist. Please configure token first.") from e
        except OSError as e:
            raise ApiTokenStorageException("Failed to read API token JSON file") from e

        try:
            return ApiToken.model_validate_json(text)
        except ValueError as e:
            raise ApiTokenStorageException("Invalid API token JSON file format") from e

    def save(self, api_token: ApiToken) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        text = api_token.model_dump_json()
        self._atomic_write_text(text)

    def delete(self) -> None:
        try:
            self._path.unlink()
        except FileNotFoundError:
            pass

    def _atomic_write_text(self, text: str) -> None:
        descriptor, temp_path = tempfile.mkstemp(
            prefix=self._path.name + ".",
            dir=self._path.parent,
        )
        try:
            with os.fdopen(
                descriptor,
                "w",
                encoding="utf-8",
            ) as file:
                file.write(text)
                file.flush()
                os.fsync(file.fileno())

            try:
                os.chmod(temp_path, 0o600)
            except OSError:
                pass

            os.replace(temp_path, self._path)

        finally:
            try:
                os.remove(temp_path)
            except FileNotFoundError:
                pass
            except OSError:
                pass


class AsyncApiTokenStorage(ABC):
    """Abstract base class for asynchronous API token storage implementations."""

    @abstractmethod
    async def load(self) -> ApiToken:
        pass

    @abstractmethod
    async def save(self, api_token: ApiToken) -> None:
        pass

    @abstractmethod
    async def delete(self) -> None:
        pass


class AsyncInMemoryApiTokenStorage(AsyncApiTokenStorage):
    """Asynchronous in-memory storage for API tokens."""

    def __init__(self, api_token: ApiToken | None = None) -> None:
        super().__init__()
        self._api_token = api_token

    async def load(self) -> ApiToken:
        if self._api_token is None:
            raise ApiTokenStorageException("No API token stored in memory")
        return self._api_token

    async def save(self, api_token: ApiToken) -> None:
        self._api_token = api_token

    async def delete(self) -> None:
        self._api_token = None


class AsyncJsonFileApiTokenStorage(AsyncApiTokenStorage):
    """Asynchronous JSON file storage for API tokens."""

    def __init__(self, path: str | Path = DEFAULT_JSON_FILE_PATH) -> None:
        self._sync = JsonFileApiTokenStorage(path)

    async def load(self) -> ApiToken:
        return self._sync.load()

    async def save(self, api_token: ApiToken) -> None:
        return await asyncio.to_thread(self._sync.save, api_token)

    async def delete(self) -> None:
        return await asyncio.to_thread(self._sync.delete)
