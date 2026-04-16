"""CLI for managing RTB House API tokens.

Usage:
    python -m rtbhouse_sdk.api_tokens <command> [options]

Commands:
    init-json         Initialize API token in JSON file storage.
    keep-alive-json   Refresh token's last activity timestamp from JSON file storage,
                      optionally rotating it if in the rotation window.

Note:
    Your API tokens can be created in the Clients Panel (https://panel.rtbhouse.com/#/user/api-tokens).

Examples:
    # Initialize token interactively (prompts for token):
    $ python -m rtbhouse_sdk.api_tokens init-json

    # Initialize token via environment variable:
    $ python -m rtbhouse_sdk.api_tokens init-json <<< "$API_TOKEN"

    # Initialize token with custom path:
    $ python -m rtbhouse_sdk.api_tokens init-json < token.txt

    # Initialize token in custom path:
    $ python -m rtbhouse_sdk.api_tokens init-json --path /custom/path/token.json

    # Keep alive:
    $ python -m rtbhouse_sdk.api_tokens keep-alive-json

    # Keep alive without auto-rotation:
    $ python -m rtbhouse_sdk.api_tokens keep-alive-json --skip-auto-rotate

    # Keep alive token stored in custom path:
    $ python -m rtbhouse_sdk.api_tokens keep-alive-json --path /custom/path/token.json

"""

from pathlib import Path

import click

from .managers import ApiTokenManager
from .storages.json_file import JsonFileApiTokenStorage, JsonFileApiTokenStorageMixin


@click.group(help="API token utilities.")
def cli() -> None:
    pass


@cli.command(
    help=(
        "Initialize API token in JSON file storage. "
        "Reads the token from stdin if input is piped, otherwise prompts interactively. "
        "NOTE: First API token can be created in the Clients Panel under Account > API Tokens section."
    )
)
@click.option(
    "--path",
    default=JsonFileApiTokenStorageMixin.PATH_DEFAULT,
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
    except Exception as e:
        raise click.ClickException(f"Token initialization failed. Original error: {e}.") from e

    click.echo(f"Token successfully initialized in {path}.")


@cli.command(
    help=(
        "Refresh the last activity timestamp of the API token stored in the JSON file. "
        "If the token is in the rotation window, it will be rotated and saved "
        "unless --skip-auto-rotate is set. "
        "Can also be used to verify that the token is valid. "
    )
)
@click.option(
    "--path",
    default=JsonFileApiTokenStorageMixin.PATH_DEFAULT,
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
    except Exception as e:
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
