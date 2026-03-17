"""CLI for managing API tokens."""

from pathlib import Path
from typing import Any

import click

from ..client import ApiTokenAuth, Client
from ..exceptions import ApiRequestException
from ..schema import ApiTokenDetails
from .managers import ApiTokenExpiredException, ApiTokenManager
from .models import ApiToken
from .storages.base import ApiTokenStorageException
from .storages.json_file import DEFAULT_JSON_FILE_PATH, JsonFileApiTokenStorage

_TOKEN_LENGTH = 43


def _init_json(path: Path) -> None:
    path = path.expanduser()
    token = _read_token_from_stdin_or_prompt()
    _validate_token(token)

    api_token_details = _get_api_token_details(token)

    storage = JsonFileApiTokenStorage(path)
    api_token = ApiToken(
        token=token,
        expires_at=api_token_details.expires_at,
    )

    try:
        storage.save(api_token)
    except ApiTokenStorageException as e:
        raise click.ClickException(f"Could not save token. Original error: {e}.") from e

    click.echo(f"Token successfully initialized in {path}.")


def _keep_alive_json(path: Path, skip_auto_rotate: bool) -> None:
    path = path.expanduser()
    storage = JsonFileApiTokenStorage(path)
    manager = ApiTokenManager(storage)

    try:
        manager.keep_alive(
            skip_auto_rotate=skip_auto_rotate,
        )
    except (ApiTokenStorageException, ApiRequestException, ApiTokenExpiredException) as e:
        raise click.ClickException(f"Keep-alive failed. Original error: {e}.") from e

    click.echo("Token valid.")


def _keep_alive() -> None:
    token = _read_token_from_stdin_or_prompt()
    _validate_token(token)

    _get_api_token_details(token)

    click.echo("Token valid.")


def build_cli() -> Any:
    @click.group(help="API token utilities.")
    def cli() -> None:
        pass

    @cli.command(
        help=(
            "Initialize API token in JSON file storage. "
            "Reads the token from stdin if input is piped, otherwise prompts interactively."
        )
    )
    @click.option(
        "--path",
        default=DEFAULT_JSON_FILE_PATH,
        show_default=True,
        type=click.Path(path_type=Path),
        help="Path to token JSON file.",
    )
    def init_json(path: Path) -> None:
        _init_json(path)

    @cli.command(
        help=(
            "Refresh the used_at timestamp of the API token stored in the JSON file. "
            "If the token is in the rotation window, it will be rotated and preserved "
            "unless --skip-auto-rotate is set. "
            "Can also be used to verify that the token is valid. "
        )
    )
    @click.option(
        "--path",
        default=DEFAULT_JSON_FILE_PATH,
        show_default=True,
        type=click.Path(path_type=Path),
        help="Path to token JSON file",
    )
    @click.option(
        "--skip-auto-rotate",
        is_flag=True,
        default=False,
        help="Skip automatic rotation when the token is in the rotation window.",
    )
    def keep_alive_json(path: Path, skip_auto_rotate: bool) -> None:
        _keep_alive_json(path, skip_auto_rotate)

    @cli.command(
        help=(
            "Refresh the used_at timestamp of the provided API token. "
            "Reads the token from stdin if input is piped; otherwise prompts interactively. "
            "Use this command when not operating on JSON file storage. "
            "Can also be used to verify that the token is valid. "
        )
    )
    def keep_alive() -> None:
        _keep_alive()

    return cli()


def _read_token_from_stdin_or_prompt() -> str:
    stdin = click.get_text_stream("stdin")
    if not stdin.isatty():
        return stdin.read().strip()

    token: str = click.prompt(
        "Paste your token",
        hide_input=True,
        type=str,
    )
    return token.strip()


def _validate_token(token: str) -> None:
    if len(token) != _TOKEN_LENGTH:
        raise click.ClickException("Invalid token format.")


def _get_api_token_details(token: str) -> ApiTokenDetails:
    auth = ApiTokenAuth(token)

    with Client(auth) as client:
        try:
            return client.get_current_api_token()
        except ApiRequestException as e:
            raise click.ClickException(f"Could not verify token. Original error: {e}.") from e
