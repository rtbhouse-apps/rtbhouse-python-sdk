"""Base classes for API token storage implementations."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager

from ..models import ApiToken


class ApiTokenStorageException(Exception):
    """Exception raised for errors in the API token storage operations."""


class ApiTokenStorage(ABC):
    """Abstract base class for API token storage implementations."""

    _is_exclusive_lock_held: bool

    def __init__(self) -> None:
        super().__init__()

        self._is_exclusive_lock_held = False

    @contextmanager
    @abstractmethod
    def acquire_exclusive_for_update(self) -> Generator[None]:
        yield

    @abstractmethod
    def load(self) -> ApiToken:
        pass

    @abstractmethod
    def save(self, api_token: ApiToken) -> None:
        pass

    def _ensure_exclusive_lock_held(self) -> None:
        assert self._is_exclusive_lock_held


class AsyncApiTokenStorage(ABC):
    """Abstract base class for asynchronous API token storage implementations."""

    _is_exclusive_lock_held: bool

    def __init__(self) -> None:
        super().__init__()

        self._is_exclusive_lock_held = False

    @asynccontextmanager
    @abstractmethod
    async def acquire_exclusive_for_update(self) -> AsyncGenerator[None]:
        yield

    @abstractmethod
    async def load(self) -> ApiToken:
        pass

    @abstractmethod
    async def save(self, api_token: ApiToken) -> None:
        pass

    def _ensure_exclusive_lock_held(self) -> None:
        assert self._is_exclusive_lock_held
