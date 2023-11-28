"""Compatibility utils for Pydantic v1"""
from pydantic.version import VERSION as PYDANTIC_VERSION

PYDANTIC_V1 = PYDANTIC_VERSION[0] == "1"
