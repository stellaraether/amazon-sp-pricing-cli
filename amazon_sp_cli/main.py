"""Main CLI entry point for Amazon SP-API CLI."""

import json
from datetime import datetime, timezone

import click

from .auth import SPAPIAuth
from .client import SPAPIClient


@click.group()
@click.option("--credentials", "-c", help="Path to credentials YAML file")
@click.pass_context
def cli(ctx, credentials):
    """Amazon SP-API CLI - Manage listings, pricing, inventory, and more."""
    ctx.ensure_object(dict)
    ctx.obj["auth"] = SPAPIAuth(credentials)
    ctx.obj["client"] = SPAPIClient(ctx.obj["auth"])


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
