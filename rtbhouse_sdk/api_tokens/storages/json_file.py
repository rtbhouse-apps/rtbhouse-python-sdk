"""JSON file storage for API tokens."""

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from filelock import AsyncFileLock, FileLock

from ..._utils import utcnow
from ..models import ApiToken
from ._base import ApiTokenStorage, ApiTokenStorageException, AsyncApiTokenStorage

DEFAULT_JSON_FILE_PATH = "~/.rtbhouse/api_token.json"


class JsonFileApiTokenStorage(ApiTokenStorage):
    """JSON file storage for API tokens."""

    _path: Path
    _api_token_cache: tuple[ApiToken, datetime] | None
    _file_lock: FileLock

    def __init__(self, path: str | Path = DEFAULT_JSON_FILE_PATH) -> None:
        super().__init__()

        self._path = Path(path).expanduser()
        self._api_token_cache = None
        self._file_lock = FileLock(
            str(self._path) + ".lock",
            timeout=60,
        )

    @contextmanager
    def lock(self) -> Iterator[None]:
        with self._file_lock:
            self._api_token_cache = None
            yield

    def load(self) -> ApiToken:
        api_token = _get_cached_api_token(self._api_token_cache)
        if api_token is not None:
            return api_token

        api_token = _load_api_token_from_file(self._path)

        self._api_token_cache = _api_token_to_cache(api_token)

        return api_token

    def save(self, api_token: ApiToken) -> None:
        _save_api_token_to_file(self._path, api_token)

        self._api_token_cache = _api_token_to_cache(api_token)


class AsyncJsonFileApiTokenStorage(AsyncApiTokenStorage):
    """Asynchronous JSON file storage for API tokens."""

    _path: Path
    _api_token_cache: tuple[ApiToken, datetime] | None
    _file_lock: AsyncFileLock

    def __init__(self, path: str | Path = DEFAULT_JSON_FILE_PATH) -> None:
        super().__init__()

        self._path = Path(path).expanduser()
        self._api_token_cache = None
        self._file_lock = AsyncFileLock(
            str(self._path) + ".lock",
            timeout=60,
        )

    @asynccontextmanager
    async def lock(self) -> AsyncIterator[None]:
        async with self._file_lock:
            self._api_token_cache = None
            yield

    async def load(self) -> ApiToken:
        api_token = _get_cached_api_token(self._api_token_cache)
        if api_token is not None:
            return api_token

        api_token = _load_api_token_from_file(self._path)

        self._api_token_cache = _api_token_to_cache(api_token)

        return api_token

    async def save(self, api_token: ApiToken) -> None:
        _save_api_token_to_file(self._path, api_token)

        self._api_token_cache = _api_token_to_cache(api_token)


def _load_api_token_from_file(path: Path) -> ApiToken:
    try:
        api_token_json = path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise ApiTokenStorageException("JSON file does not exist. Please configure token first.") from e
    except OSError as e:
        raise ApiTokenStorageException("Failed to read API token JSON file.") from e

    try:
        api_token = ApiToken.model_validate_json(api_token_json)
    except ValueError as e:
        raise ApiTokenStorageException("Invalid API token JSON file format.") from e

    return api_token


def _save_api_token_to_file(path: Path, api_token: ApiToken) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    text = api_token.model_dump_json()
    path.write_text(
        text,
        encoding="utf-8",
    )


def _get_cached_api_token(cache: tuple[ApiToken, datetime] | None) -> ApiToken | None:
    if cache is not None:
        api_token, load_time = cache
        if utcnow() - load_time < timedelta(minutes=5):
            return api_token

    return None


def _api_token_to_cache(api_token: ApiToken) -> tuple[ApiToken, datetime]:
    return (api_token, utcnow())
