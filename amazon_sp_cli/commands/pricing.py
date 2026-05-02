"""Pricing and catalog commands."""

import json
from datetime import datetime, timedelta, timezone

import click

from ..cli import handle_errors


def register_pricing_commands(cli_group, ensure_auth_client):
    """Register pricing and catalog CLI commands."""

    @cli_group.command()
    @click.argument("sku")
    @click.pass_context
    @handle_errors
    def get_price(ctx, sku):
        """Get current price for a SKU."""
        _, client = ensure_auth_client(ctx)
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

    @cli_group.command()
    @click.argument("sku")
    @click.argument("price", type=float)
    @click.option("--dry-run", is_flag=True, help="Validate without applying")
    @click.pass_context
    @handle_errors
    def set_price(ctx, sku, price, dry_run):
        """Set price for a SKU."""
        _, client = ensure_auth_client(ctx)
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

    @cli_group.command()
    @click.argument("sku")
    @click.argument("percent", type=float)
    @click.option("--all-variations", is_flag=True, help="Apply to all variations")
    @click.pass_context
    @handle_errors
    def create_discount(ctx, sku, percent, all_variations):
        """Create discount for a SKU."""
        _, client = ensure_auth_client(ctx)

        if all_variations:
            parent_sku = sku.split("-")[0] if "-" in sku else sku
            click.echo(f"Creating {percent}% discount for all variations of {parent_sku}")
            return

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

    @cli_group.command()
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
    @handle_errors
    def sale_price(ctx, sku, discount, discount_type, start_date, end_date, output):
        """Generate sale price data for a SKU."""
        _, client = ensure_auth_client(ctx)

        response = client.get_listing(sku)
        attributes = response.get("attributes", {})
        list_price = attributes.get("list_price", [{}])[0]
        current_price = list_price.get("value", 0)

        if not current_price:
            click.echo("Error: Could not get current price for SKU", err=True)
            raise click.Abort()

        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.now(timezone.utc)
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else start + timedelta(days=30)

        start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")

        if discount_type == "percentage":
            discount_amount = round(current_price * discount / 100, 2)
            discount_display = f"{discount}%"
        else:
            discount_amount = discount
            discount_display = f"${discount}"

        new_sale_price = max(0, current_price - discount_amount)

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

        output_json = json.dumps(feed, indent=2)

        if output:
            output.write(output_json)
            click.echo(f"✓ Sale price data saved to {output.name}")

        click.echo(output_json)

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

    @cli_group.command()
    @click.argument("asin")
    @click.pass_context
    @handle_errors
    def check_competitors(ctx, asin):
        """Check competitor pricing for an ASIN."""
        _, client = ensure_auth_client(ctx)
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
