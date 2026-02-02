"""Contains classes for interacting with the API tokens endpoints."""

from datetime import datetime

import httpx

from rtbhouse_sdk.client import DEFAULT_TIMEOUT, _build_headers, _validate_response, build_base_url
from rtbhouse_sdk.exceptions import ApiException
from rtbhouse_sdk.schema import CamelizedBaseModel


class RotatedApiToken(CamelizedBaseModel):
    token: str
    expires_at: datetime


class ApiTokenStatus(CamelizedBaseModel):
    expires_at: datetime
    is_expired: bool
    can_rotate: bool


class ApiTokensAPI:
    def __init__(self) -> None:
        self._base_url = build_base_url()
        self._headers = _build_headers()
        self._timeout = DEFAULT_TIMEOUT.total_seconds()

    @property
    def _httpx_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self._base_url,
            headers=self._headers,
            timeout=self._timeout,
        )

    def heartbeat(self, token: str) -> ApiTokenStatus:
        with self._httpx_client as client:
            response = client.get(
                "/tokens/current/heartbeat",
                headers={"Authorization": f"Bearer {token}"},
            )
            _validate_response(response)
            try:
                resp_json = response.json()
                data = resp_json["data"]
            except (ValueError, KeyError) as exc:
                raise ApiException("Invalid response format") from exc

            return ApiTokenStatus(**data)

    def rotate(self, token: str) -> RotatedApiToken:
        with self._httpx_client as client:
            response = client.post(
                "/tokens/current/rotate",
                headers={"Authorization": f"Bearer {token}"},
            )
            _validate_response(response)
            try:
                resp_json = response.json()
                data = resp_json["data"]
            except (ValueError, KeyError) as exc:
                raise ApiException("Invalid response format") from exc

            return RotatedApiToken(**data)


class AsyncApiTokensAPI:
    def __init__(self) -> None:
        self._base_url = build_base_url()
        self._headers = _build_headers()
        self._timeout = DEFAULT_TIMEOUT.total_seconds()

    @property
    def _httpx_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            headers=self._headers,
            timeout=self._timeout,
        )

    async def heartbeat(self, token: str) -> ApiTokenStatus:
        async with self._httpx_client as client:
            response = await client.get(
                "/tokens/current/heartbeat",
                headers={"Authorization": f"Bearer {token}"},
            )
            _validate_response(response)
            try:
                resp_json = response.json()
                data = resp_json["data"]
            except (ValueError, KeyError) as exc:
                raise ApiException("Invalid response format") from exc

            return ApiTokenStatus(**data)

    async def rotate(self, token: str) -> RotatedApiToken:
        async with self._httpx_client as client:
            response = await client.post(
                "/tokens/current/rotate",
                headers={"Authorization": f"Bearer {token}"},
            )
            _validate_response(response)
            try:
                resp_json = response.json()
                data = resp_json["data"]
            except (ValueError, KeyError) as exc:
                raise ApiException("Invalid response format") from exc

            return RotatedApiToken(**data)
