"""Base classes for API token storage implementations."""

from abc import ABC, abstractmethod

from rtbhouse_sdk.api_tokens.models import ApiToken


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


class AsyncApiTokenStorage(ABC):
    """Abstract base class for asynchronous API token storage implementations."""

    @abstractmethod
    async def load(self) -> ApiToken:
        pass

    @abstractmethod
    async def save(self, api_token: ApiToken) -> None:
        pass
