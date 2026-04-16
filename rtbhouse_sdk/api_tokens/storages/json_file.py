"""JSON file storage for API tokens."""

import os
import tempfile
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import ClassVar

from filelock import AsyncFileLock, FileLock

from ..._utils import utcnow
from ..models import ApiToken
from ._base import ApiTokenStorage, ApiTokenStorageException, AsyncApiTokenStorage


class JsonFileApiTokenStorageMixin:  # pylint: disable=too-few-public-methods

    PATH_DEFAULT: ClassVar[str] = "~/.rtbhouse/api_token.json"
    _API_TOKEN_CACHE_TTL: ClassVar[timedelta] = timedelta(minutes=5)

    _path: Path
    _api_token_cache: tuple[ApiToken, datetime] | None

    def __init__(self, path: str | Path | None = None) -> None:
        super().__init__()

        if path is None:
            path = self.PATH_DEFAULT
        self._path = Path(path).expanduser()

        self._api_token_cache = None

    def _load_api_token_from_file(self) -> ApiToken:
        try:
            api_token_json = self._path.read_text(encoding="utf-8")
        except FileNotFoundError as e:
            raise ApiTokenStorageException("JSON file does not exist. Please configure token first.") from e
        except OSError as e:
            raise ApiTokenStorageException("Failed to read API token JSON file.") from e

        try:
            api_token = ApiToken.model_validate_json(api_token_json)
        except ValueError as e:
            raise ApiTokenStorageException("Invalid API token JSON file format.") from e

        return api_token

    def _save_api_token_to_file(self, api_token: ApiToken) -> None:
        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        api_token_json = api_token.model_dump_json()
        self._atomic_write_api_token_json(api_token_json)

    def _atomic_write_api_token_json(self, api_token_json: str) -> None:
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
                file.write(api_token_json)
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
            except OSError:
                pass

    def _get_api_token_cache(self) -> ApiToken | None:
        if self._api_token_cache is not None:
            api_token, load_time = self._api_token_cache
            if utcnow() - load_time < self._API_TOKEN_CACHE_TTL:
                return api_token

        return None

    def _set_api_token_cache(self, api_token: ApiToken | None) -> None:
        self._api_token_cache = (api_token, utcnow()) if api_token is not None else None


class JsonFileApiTokenStorage(JsonFileApiTokenStorageMixin, ApiTokenStorage):
    """JSON file storage for API tokens."""

    _file_lock: FileLock

    def __init__(self, path: str | Path | None = None) -> None:
        super().__init__(path)

        self._file_lock = FileLock(
            self._path.with_name(self._path.name + ".lock"),
            timeout=60,
        )

    @contextmanager
    def lock(self) -> Generator[None]:
        with self._file_lock:
            self._set_api_token_cache(None)

            yield

    def load(self) -> ApiToken:
        api_token = self._get_api_token_cache()
        if api_token is not None:
            return api_token

        api_token = self._load_api_token_from_file()

        self._set_api_token_cache(api_token)

        return api_token

    def save(self, api_token: ApiToken) -> None:
        assert self._file_lock.lock_counter > 0  # ensure that lock is held

        self._save_api_token_to_file(api_token)

        self._set_api_token_cache(api_token)


class AsyncJsonFileApiTokenStorage(JsonFileApiTokenStorageMixin, AsyncApiTokenStorage):
    """Asynchronous JSON file storage for API tokens."""

    _file_lock: AsyncFileLock

    def __init__(self, path: str | Path | None = None) -> None:
        super().__init__(path)

        self._file_lock = AsyncFileLock(
            self._path.with_name(self._path.name + ".lock"),
            timeout=60,
        )

    @asynccontextmanager
    async def lock(self) -> AsyncGenerator[None]:
        async with self._file_lock:
            self._set_api_token_cache(None)

            yield

    async def load(self) -> ApiToken:
        api_token = self._get_api_token_cache()
        if api_token is not None:
            return api_token

        api_token = self._load_api_token_from_file()

        self._set_api_token_cache(api_token)

        return api_token

    async def save(self, api_token: ApiToken) -> None:
        assert self._file_lock.lock_counter > 0  # ensure that lock is held

        self._save_api_token_to_file(api_token)

        self._set_api_token_cache(api_token)
