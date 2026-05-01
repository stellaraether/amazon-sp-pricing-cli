"""Main CLI entry point for Amazon SP-API CLI."""

import json
import os
from datetime import datetime, timezone

import click
import yaml

from .auth import SPAPIAuth
from .client import SPAPIClient

DEFAULT_CREDENTIALS_PATH = os.path.expanduser("~/.config/amazon-sp-cli/credentials.yml")


def _check_path():
    """Check if the CLI is accessible in PATH and warn once per day."""
    import shutil
    import sys
    from pathlib import Path

    if shutil.which("amz-sp"):
        return

    # Only warn once per day
    flag_file = Path.home() / ".config" / "amazon-sp-cli" / ".path-warned"
    flag_file.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    if flag_file.exists():
        last_warned = flag_file.read_text().strip()
        if last_warned == today:
            return

    flag_file.write_text(today)

    print(
        "\n⚠️  Note: 'amz-sp' is not in your PATH.",
        file=sys.stderr,
    )
    print(
        "   You can still use: python3 -m amazon_sp_cli",
        file=sys.stderr,
    )
    print(
        "   To add to PATH, add this to your shell config:",
        file=sys.stderr,
    )
    print(
        f'   export PATH="{sys.prefix}/bin:$PATH"',
        file=sys.stderr,
    )
    print("", file=sys.stderr)


@click.group()
@click.option("--credentials", "-c", help="Path to credentials YAML file")
@click.pass_context
def cli(ctx, credentials):
    """Amazon SP-API CLI - Manage listings, pricing, inventory, and more."""
    _check_path()
    ctx.ensure_object(dict)
    ctx.obj["auth"] = SPAPIAuth(credentials)
    ctx.obj["client"] = SPAPIClient(ctx.obj["auth"])


@cli.group()
def auth():
    """Authentication commands."""
    pass


@auth.command("setup")
@click.option("--path", default=DEFAULT_CREDENTIALS_PATH, help="Path to save credentials")
@click.option("--profile", default="default", help="Credential profile name")
@click.option("--refresh-token", help="Refresh token")
@click.option("--client-id", help="Client ID")
@click.option("--client-secret", help="Client secret")
@click.option("--aws-access-key-id", help="AWS Access Key ID")
@click.option("--aws-secret-access-key", help="AWS Secret Access Key")
@click.option("--seller-id", default="A2GKV2AN9F8YG3", help="Seller ID")
@click.option("--marketplace-id", default="ATVPDKIKX0DER", help="Marketplace ID")
@click.pass_context
def auth_setup(
    ctx,
    path,
    profile,
    refresh_token,
    client_id,
    client_secret,
    aws_access_key_id,
    aws_secret_access_key,
    seller_id,
    marketplace_id,
):
    """Set up Amazon SP-API credentials.

    When flags are omitted, falls back to interactive prompts.
    """
    click.echo("🔐 Amazon SP-API Credential Setup")
    click.echo("=" * 50)
    click.echo()

    interactive = not all([refresh_token, client_id, client_secret, aws_access_key_id, aws_secret_access_key])
    if interactive:
        click.echo("You'll need the following from your Amazon Developer account:")
        click.echo("  1. Refresh Token (from LWA authorization)")
        click.echo("  2. Client ID (from your app registration)")
        click.echo("  3. Client Secret (from your app registration)")
        click.echo("  4. AWS Access Key ID")
        click.echo("  5. AWS Secret Access Key")
        click.echo()

    profile = profile or click.prompt("Profile name", default="default")
    refresh_token = refresh_token or click.prompt("Refresh token", hide_input=True)
    client_id = client_id or click.prompt("Client ID")
    client_secret = client_secret or click.prompt("Client secret", hide_input=True)
    aws_access_key_id = aws_access_key_id or click.prompt("AWS Access Key ID")
    aws_secret_access_key = aws_secret_access_key or click.prompt("AWS Secret Access Key", hide_input=True)

    credentials = {
        "version": "1.0",
        profile: {
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "seller_id": seller_id,
            "marketplace_id": marketplace_id,
        },
    }

    # Merge with existing if present
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                existing = yaml.safe_load(f) or {}
            existing[profile] = credentials[profile]
            credentials = existing
            click.echo(f"\n📝 Merged with existing credentials at {path}")
        except Exception as e:
            click.echo(f"⚠️  Could not read existing file: {e}")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(credentials, f, default_flow_style=False, sort_keys=False)

    click.echo(f"✅ Credentials saved to {path}")
    click.echo(f"   Profile: {profile}")
    click.echo(f"   Seller ID: {seller_id}")
    click.echo(f"   Marketplace ID: {marketplace_id}")
    click.echo()
    click.echo("You can now use: python -m amazon_sp_cli.main --profile {profile} get-price <sku>")


@auth.command("show")
@click.option("--path", default=DEFAULT_CREDENTIALS_PATH, help="Path to credentials file")
@click.pass_context
def auth_show(ctx, path):
    """Show configured profiles (without secrets)."""
    if not os.path.exists(path):
        click.echo(f"❌ No credentials file found at {path}")
        click.echo("Run: python -m amazon_sp_cli.main auth setup")
        return

    with open(path, "r") as f:
        creds = yaml.safe_load(f) or {}

    click.echo(f"\n📄 Credentials file: {path}")
    click.echo("-" * 40)

    for profile, data in creds.items():
        if profile == "version":
            continue
        click.echo(f"Profile: {profile}")
        click.echo(f"  Client ID: {data.get('client_id', 'N/A')[:20]}...")
        click.echo(f"  Seller ID: {data.get('seller_id', 'N/A')}")
        click.echo(f"  Marketplace ID: {data.get('marketplace_id', 'N/A')}")
        click.echo()


@cli.command()
@click.argument("sku")
@click.pass_context
def get_price(ctx, sku):
    """Get current price for a SKU."""
    client = ctx.obj["client"]
    try:
        response = client.get_listing(sku)
        attributes = response.get("attributes", {})
        list_price = attributes.get("list_price", [{}])[0]

        result = {
            "sku": sku,
            "asin": response.get("summaries", [{}])[0].get("asin"),
            "status": response.get("summaries", [{}])[0].get("status", []),
            "price": list_price.get("value"),
            "currency": list_price.get("currency"),
        }
        click.echo(json.dumps(result, indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument("sku")
@click.argument("price", type=float)
@click.option("--dry-run", is_flag=True, help="Validate without applying")
@click.pass_context
def set_price(ctx, sku, price, dry_run):
    """Set price for a SKU."""
    client = ctx.obj["client"]
    try:
        mode = "VALIDATION_PREVIEW" if dry_run else None
        response = client.update_price(sku, price, mode)

        if dry_run:
            if response.get("issues"):
                click.echo("Validation issues found:")
                click.echo(json.dumps(response["issues"], indent=2))
            else:
                click.echo("✓ Validation passed")
        else:
            click.echo(json.dumps(response, indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument("sku")
@click.argument("percent", type=float)
@click.option("--all-variations", is_flag=True, help="Apply to all variations")
@click.pass_context
def create_discount(ctx, sku, percent, all_variations):
    """Create discount for a SKU."""
    client = ctx.obj["client"]

    try:
        if all_variations:
            # Get parent SKU and find all variations
            parent_sku = sku.split("-")[0] if "-" in sku else sku
            click.echo(f"Creating {percent}% discount for all variations of {parent_sku}")
            # TODO: Implement variation discovery
            return

        # Get current price
        response = client.get_listing(sku)
        attributes = response.get("attributes", {})
        list_price = attributes.get("list_price", [{}])[0]
        current_price = list_price.get("value", 0)

        if not current_price:
            click.echo("Error: Could not get current price", err=True)
            raise click.Abort()

        sale_price = round(current_price * (100 - percent) / 100, 2)
        effective_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        click.echo(f"Current price: ${current_price}")
        click.echo(f"Sale price: ${sale_price} ({percent}% off)")
        click.echo("")
        click.echo("Note: SP-API doesn't support direct discount creation.")
        click.echo("Options:")
        click.echo("1. Seller Central → Advertising → Prime Exclusive Discounts")
        click.echo("2. Seller Central → Advertising → Coupons")
        click.echo("3. Submit feed via SP-API Feeds API")
        click.echo("")
        click.echo("Feed data for option 3:")

        feed = {
            "header": {
                "sellerId": client.seller_id,
                "version": "2.0",
                "issueLocale": "en_US",
            },
            "messages": [
                {
                    "messageId": 1,
                    "sku": sku,
                    "operationType": "PARTIAL_UPDATE",
                    "productType": "PET_TOY",
                    "attributes": {
                        "list_price": [{"currency": "USD", "value": current_price}],
                        "sale_price": [
                            {
                                "currency": "USD",
                                "value": sale_price,
                                "effective_date": effective_date,
                            }
                        ],
                    },
                }
            ],
        }
        click.echo(json.dumps(feed, indent=2))

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument("sku")
@click.argument("discount", type=float)
@click.option(
    "--type",
    "discount_type",
    type=click.Choice(["percentage", "fixed"]),
    default="percentage",
    help="Discount type: percentage or fixed amount off",
)
@click.option("--start-date", help="Start date (YYYY-MM-DD). Defaults to today")
@click.option("--end-date", help="End date (YYYY-MM-DD). Defaults to 30 days from start")
@click.option("--output", "-o", type=click.File("w"), help="Save price adjustment data to file")
@click.pass_context
def sale_price(
    ctx,
    sku,
    discount,
    discount_type,
    start_date,
    end_date,
    output,
):
    """Generate sale price data for a SKU.

    SP-API does not support direct sale price creation. This generates
    the feed data you can submit via the Feeds API or use in Seller Central.

    Examples:
        amz-sp sale-price PAW2603190101 20
        amz-sp sale-price PAW2603190101 5 --type fixed
        amz-sp sale-price PAW2603190101 15 --start-date 2026-05-01 --end-date 2026-05-31
    """
    client = ctx.obj["client"]

    try:
        # Get current listing info
        response = client.get_listing(sku)
        attributes = response.get("attributes", {})
        list_price = attributes.get("list_price", [{}])[0]
        current_price = list_price.get("value", 0)

        if not current_price:
            click.echo("Error: Could not get current price for SKU", err=True)
            raise click.Abort()

        # Calculate dates
        from datetime import timedelta

        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.now(timezone.utc)
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else start + timedelta(days=30)

        # Format for Amazon (ISO 8601)
        start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Calculate discount values
        if discount_type == "percentage":
            discount_amount = round(current_price * discount / 100, 2)
            discount_display = f"{discount}%"
        else:
            discount_amount = discount
            discount_display = f"${discount}"

        new_sale_price = max(0, current_price - discount_amount)

        # Build sale price feed data
        feed = {
            "sku": sku,
            "asin": response.get("summaries", [{}])[0].get("asin"),
            "pricing": {
                "original_price": current_price,
                "sale_price": new_sale_price,
                "discount_amount": discount_amount,
                "discount_display": discount_display,
            },
            "schedule": {
                "start_date": start_str,
                "end_date": end_str,
                "duration_days": (end - start).days,
            },
            "feed_data": {
                "messageId": 1,
                "sku": sku,
                "operationType": "PARTIAL_UPDATE",
                "productType": "PET_TOY",
                "attributes": {
                    "list_price": [{"currency": "USD", "value": current_price}],
                    "sale_price": [
                        {
                            "currency": "USD",
                            "value": new_sale_price,
                            "effective_date": start_str,
                            "end_date": end_str,
                        }
                    ],
                },
            },
        }

        # Output
        output_json = json.dumps(feed, indent=2)

        if output:
            output.write(output_json)
            click.echo(f"✓ Sale price data saved to {output.name}")

        click.echo(output_json)

        # Summary
        click.echo("\n" + "=" * 50)
        click.echo("SALE PRICE SUMMARY")
        click.echo("=" * 50)
        click.echo(f"SKU: {sku}")
        click.echo(f"Discount: {discount_display}")
        click.echo(f"Price: ${current_price} → ${new_sale_price}")
        click.echo(f"Duration: {start_str} to {end_str}")
        click.echo("\n⚠️  SP-API does not support direct sale price creation.")
        click.echo("   Submit the feed_data above via the Feeds API")
        click.echo("   or update manually in Seller Central.")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument("asin")
@click.pass_context
def check_competitors(ctx, asin):
    """Check competitor pricing for an ASIN."""
    client = ctx.obj["client"]
    try:
        response = client.get_catalog_item(asin)
        attributes = response.get("attributes", {})

        result = {
            "asin": response.get("asin"),
            "title": attributes.get("item_name", [{}])[0].get("value"),
            "brand": attributes.get("brand", [{}])[0].get("value"),
            "list_price": attributes.get("list_price", [{}])[0].get("value"),
            "sales_rank": response.get("salesRanks", [{}])[0].get("displayRank"),
        }
        click.echo(json.dumps(result, indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.pass_context
def invalidate(ctx):
    """Invalidate cached access token."""
    ctx.obj["auth"].invalidate()


if __name__ == "__main__":
    cli()
