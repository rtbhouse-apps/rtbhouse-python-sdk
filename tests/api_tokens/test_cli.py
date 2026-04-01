"""Tests for API tokens CLI."""

from datetime import timedelta
from pathlib import Path

import pytest
import respx
from click.testing import CliRunner

from rtbhouse_sdk._utils import utcnow
from rtbhouse_sdk.api_tokens.__main__ import cli
from rtbhouse_sdk.api_tokens.managers import ApiTokenManager
from rtbhouse_sdk.api_tokens.storages.json_file import JsonFileApiTokenStorage

_VALID_TOKEN = "a" * 43
_INVALID_TOKEN = "short"

_EXPIRES_AT = utcnow() + timedelta(days=30)

_API_TOKEN_DETAILS_RESPONSE = {
    "status": "ok",
    "data": {
        "expiresAt": _EXPIRES_AT.isoformat(),
    },
}


@pytest.fixture(name="token_path")  # name to avoid linters errors
def token_path_fixture(tmp_path: Path) -> Path:
    return tmp_path / "api_token.json"


@pytest.fixture(name="runner")
def runner_fixture() -> CliRunner:
    return CliRunner()


def test_init_json_success(token_path: Path, runner: CliRunner, api_mock: respx.MockRouter) -> None:
    api_mock.get("/tokens/current").respond(
        200,
        json=_API_TOKEN_DETAILS_RESPONSE,
    )

    result = runner.invoke(
        cli,
        ["init-json", "--path", str(token_path)],
        input=_VALID_TOKEN,
    )

    assert result.exit_code == 0
    assert "Token successfully initialized" in result.output
    assert token_path.exists()


def test_init_json_rejects_invalid_token_length(runner: CliRunner) -> None:
    result = runner.invoke(
        cli,
        ["init-json"],
        input=_INVALID_TOKEN,
    )

    assert result.exit_code != 0
    assert "Invalid token format" in result.output


def test_keep_alive_json_success(token_path: Path, runner: CliRunner, api_mock: respx.MockRouter) -> None:
    api_mock.get("/tokens/current").respond(
        200,
        json=_API_TOKEN_DETAILS_RESPONSE,
    )

    # initialize token first
    storage = JsonFileApiTokenStorage(token_path)
    manager = ApiTokenManager(storage)
    manager.configure(_VALID_TOKEN)

    result = runner.invoke(
        cli,
        ["keep-alive-json", "--path", str(token_path)],
    )

    assert result.exit_code == 0
    assert "Token valid" in result.output


def test_keep_alive_json_fails_when_file_missing(tmp_path: Path, runner: CliRunner) -> None:
    token_path = tmp_path / "nonexistent.json"

    result = runner.invoke(
        cli,
        ["keep-alive-json", "--path", str(token_path)],
    )

    assert result.exit_code != 0
    assert "Keep-alive failed" in result.output
