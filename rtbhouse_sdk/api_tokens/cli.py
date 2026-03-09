"""CLI for API token management."""

import argparse
import getpass
import os
import sys
from pathlib import Path
from typing import Any

from ..client import ApiTokenAuth, Client
from ..exceptions import ApiRequestException
from ..schema import ApiToken as ApiTokenResponse
from .managers import ApiTokenExpiredException, ApiTokenManager
from .models import ApiToken
from .storages.base import ApiTokenStorageException
from .storages.json_file import DEFAULT_JSON_FILE_PATH, JsonFileApiTokenStorage


def _read_token_from_stdin() -> str:
    if sys.stdin.isatty():
        token = getpass.getpass("Paste API token: ").strip()
        return token

    token = sys.stdin.read().strip()

    return token


def _resolve_token(
    *,
    token_arg: str | None = None,
    env_var: str | None = None,
) -> str:
    print(token_arg, env_var)
    if token_arg:
        return token_arg.strip()

    if env_var:
        env_val = os.getenv(env_var)
        return env_val.strip() if env_val else ""

    return _read_token_from_stdin()


def _get_token(token: str) -> ApiTokenResponse:
    with Client(auth=ApiTokenAuth(token=token)) as client:
        return client.get_current_api_token()


def cmd_init_json(args: argparse.Namespace) -> int:
    path = Path(args.path).expanduser()

    token = _resolve_token(token_arg=args.token, env_var=args.env_var)
    if not token:
        print("ERROR: Empty token. Aborting.", file=sys.stderr)
        return 1

    try:
        api_token_response = _get_token(token)
    except ApiRequestException as e:
        print(f"ERROR: Could not verify token via API or token is invalid. Original error: {e}.", file=sys.stderr)
        return 1

    storage = JsonFileApiTokenStorage(path)
    api_token = ApiToken(
        token=token,
        expires_at=api_token_response.expires_at,
    )
    storage.save(api_token)

    print(f"OK: Token successfully initialized in {path}", file=sys.stdout)
    return 0


def cmd_keep_alive_json(args: argparse.Namespace) -> int:
    path = Path(args.path).expanduser()
    storage = JsonFileApiTokenStorage(path)
    manager = ApiTokenManager(storage=storage)

    try:
        manager.keep_alive(args.auto_rotate)
    except (ApiTokenStorageException, ApiRequestException, ApiTokenExpiredException) as e:
        print(f"ERROR: Keep-alive failed. Original error: {e}", file=sys.stderr)
        return 1

    print("OK: Token keep-alive successful", file=sys.stdout)
    return 0


def cmd_keep_alive(args: argparse.Namespace) -> int:
    token = _resolve_token(token_arg=args.token, env_var=args.env_var)
    if not token:
        print("ERROR: Empty token. Aborting.", file=sys.stderr)
        return 1

    try:
        api_token_response = _get_token(token)
    except ApiRequestException as e:
        print(f"ERROR: Could not verify token via API or token is invalid. Original error: {e}.", file=sys.stderr)
        return 1

    if api_token_response.can_rotate:
        print("WARNING: token can be rotated. Consider rotating it before it expires.", file=sys.stderr)

    print("OK: Token keep-alive successful", file=sys.stdout)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rtbhouse_sdk",
        description="RTB House Python SDK CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    api_token = sub.add_parser(
        "api-token",
        help="API token utilities",
    )
    api_token_sub = api_token.add_subparsers(
        dest="api_token_cmd",
        required=True,
    )
    build_cmd_init_json(api_token_sub)
    build_cmd_keep_alive_json(api_token_sub)
    build_cmd_keep_alive(api_token_sub)

    return parser


def build_cmd_init_json(parser: Any) -> None:
    init_json = parser.add_parser(
        "init-json",
        help="Initialize API token JSON file storage",
    )
    init_json.add_argument(
        "--token",
        default=None,
        help="Token value (discouraged). Prefer stdin/env/pipe.",
    )
    init_json.add_argument(
        "--path",
        default=DEFAULT_JSON_FILE_PATH,
        help=f"Path to token JSON file (default: {DEFAULT_JSON_FILE_PATH})",
    )
    init_json.add_argument(
        "--env-var",
        help="Environment variable to read token from.",
    )
    init_json.set_defaults(func=cmd_init_json)


def build_cmd_keep_alive_json(parser: Any) -> None:
    keep_alive_json = parser.add_parser(
        "keep-alive-json",
        help="Keep alive API token stored in JSON file storage by bumping its usage. Allows automatic rotation.",
    )
    keep_alive_json.add_argument(
        "--path",
        default=DEFAULT_JSON_FILE_PATH,
        help=f"Path to token JSON file (default: {DEFAULT_JSON_FILE_PATH})",
    )
    keep_alive_json.add_argument(
        "--auto-rotate",
        action="store_true",
        help="Enable automatic rotation if token is in rotation window",
    )
    keep_alive_json.set_defaults(func=cmd_keep_alive_json)


def build_cmd_keep_alive(parser: Any) -> None:
    keep_alive = parser.add_parser(
        "keep-alive",
        help="Keep alive API token by bumping its usage.",
    )
    keep_alive.add_argument(
        "--token",
        default=None,
        help="Token value (discouraged). Prefer stdin/env/pipe.",
    )
    keep_alive.add_argument(
        "--env-var",
        default=None,
        help="Environment variable to read token from.",
    )
    keep_alive.set_defaults(func=cmd_keep_alive)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
