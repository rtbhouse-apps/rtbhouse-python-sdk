"""Contains models related to API tokens."""

from datetime import datetime

from pydantic import BaseModel


class ApiToken(BaseModel):
    """Basic model representing an API token."""

    token: str
    expires_at: datetime
