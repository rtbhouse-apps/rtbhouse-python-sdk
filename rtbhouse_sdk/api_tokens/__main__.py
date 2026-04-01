"""CLI for managing RTB House API tokens.

Usage:
    python -m rtbhouse_sdk.api_tokens <command> [options]

Commands:
    init-json         Initialize API token in JSON file storage.
    keep-alive-json   Refresh token's last activity timestamp from JSON file storage,
                      optionally rotating it if in the rotation window.

Examples:
    # Initialize token interactively (prompts for token):
    $ python -m rtbhouse_sdk.api_tokens init-json

    # Initialize token via environment variable:
    $ python -m rtbhouse_sdk.api_tokens init-json <<< "$API_TOKEN"

    # Initialize token with custom path:
    $ python -m rtbhouse_sdk.api_tokens init-json < token.txt

    # Keep alive:
    $ python -m rtbhouse_sdk.api_tokens keep-alive-json

    # Keep alive without auto-rotation:
    $ python -m rtbhouse_sdk.api_tokens keep-alive-json --skip-auto-rotate

"""

from pathlib import Path

import click

from ..exceptions import ApiRequestException
from .managers import ApiTokenExpiredException, ApiTokenManager
from .storages._base import ApiTokenStorageException
from .storages.json_file import DEFAULT_JSON_FILE_PATH, JsonFileApiTokenStorage


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
    token = _read_token_from_stdin_or_prompt()

    storage = JsonFileApiTokenStorage(path)
    manager = ApiTokenManager(storage)

    try:
        manager.configure(token)
    except (ValueError, ApiRequestException, ApiTokenStorageException) as e:
        raise click.ClickException(f"Token initialization failed. Original error: {e}.") from e

    click.echo(f"Token successfully initialized in {path}.")


@cli.command(
    help=(
        "Refresh the last activity timestamp of the API token stored in the JSON file. "
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
    storage = JsonFileApiTokenStorage(path)
    manager = ApiTokenManager(storage)

    try:
        manager.keep_alive(
            auto_rotate=not skip_auto_rotate,
        )
    except (ApiTokenStorageException, ApiRequestException, ApiTokenExpiredException) as e:
        raise click.ClickException(f"Keep-alive failed. Original error: {e}.") from e

    click.echo("Token valid.")


def _read_token_from_stdin_or_prompt() -> str:
    stdin = click.get_text_stream("stdin")

    if stdin.isatty():
        token: str = click.prompt(
            "Paste your token",
            hide_input=True,
            type=str,
        )
    else:
        token = stdin.read()

    token = token.strip()

    return token


if __name__ == "__main__":
    cli()
