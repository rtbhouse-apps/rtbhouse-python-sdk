"""Base classes for API token storage implementations."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager

from ..models import ApiToken


class ApiTokenStorageException(Exception):
    """Exception raised for errors in the API token storage operations."""


class ApiTokenStorage(ABC):
    """Abstract base class for API token storage implementations."""

    @contextmanager
    @abstractmethod
    def lock(self) -> Iterator[None]:
        yield

    @abstractmethod
    def load(self) -> ApiToken:
        pass

    @abstractmethod
    def save(self, api_token: ApiToken) -> None:
        pass


class AsyncApiTokenStorage(ABC):
    """Abstract base class for asynchronous API token storage implementations."""

    @asynccontextmanager
    @abstractmethod
    async def lock(self) -> AsyncIterator[None]:
        yield

    @abstractmethod
    async def load(self) -> ApiToken:
        pass

    @abstractmethod
    async def save(self, api_token: ApiToken) -> None:
        pass
