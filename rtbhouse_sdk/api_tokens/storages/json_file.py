"""JSON file storage for API tokens."""

import asyncio
import os
import tempfile
from pathlib import Path

from cachetools import TTLCache, cachedmethod
from cachetools.keys import hashkey

from ..models import ApiToken
from .base import ApiTokenStorage, ApiTokenStorageException, AsyncApiTokenStorage

DEFAULT_JSON_FILE_PATH = "~/.rtbhouse/api_token.json"


class JsonFileApiTokenStorage(ApiTokenStorage):
    """JSON file storage for API tokens."""

    _path: Path
    _load_cache: TTLCache[str, ApiToken]

    def __init__(self, path: str | Path = DEFAULT_JSON_FILE_PATH) -> None:
        super().__init__()
        self._path = Path(path).expanduser()
        self._load_cache = TTLCache(maxsize=1, ttl=300)

    @cachedmethod(lambda self: self._load_cache, key=lambda self: hashkey())
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
        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        text = api_token.model_dump_json()
        self._atomic_write_text(text)

        self._load_cache.clear()

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


class AsyncJsonFileApiTokenStorage(AsyncApiTokenStorage):
    """Asynchronous JSON file storage for API tokens."""

    _sync: JsonFileApiTokenStorage

    def __init__(self, path: str | Path = DEFAULT_JSON_FILE_PATH) -> None:
        super().__init__()
        self._sync = JsonFileApiTokenStorage(path)

    async def load(self) -> ApiToken:
        return self._sync.load()

    async def save(self, api_token: ApiToken) -> None:
        return await asyncio.to_thread(self._sync.save, api_token)
