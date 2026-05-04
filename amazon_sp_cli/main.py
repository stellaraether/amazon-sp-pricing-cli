"""Main CLI entry point for Amazon SP-API CLI."""

from .cli import _ensure_auth_client, cli
from .commands.a_plus import register_a_plus_commands
from .commands.auth import register_auth_commands
from .commands.listings import register_listings_commands
from .commands.pricing import register_pricing_commands

register_auth_commands(cli)
register_listings_commands(cli, _ensure_auth_client)
register_pricing_commands(cli, _ensure_auth_client)
register_a_plus_commands(cli, _ensure_auth_client)
