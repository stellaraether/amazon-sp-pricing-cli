"""Main CLI entry point for Amazon SP-API CLI."""

import json
from datetime import datetime, timezone

import click

from .auth import SPAPIAuth
from .client import SPAPIClient


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
    "coupon_type",
    type=click.Choice(["percentage", "fixed"]),
    default="percentage",
    help="Coupon type: percentage or fixed amount off",
)
@click.option("--min-purchase", type=float, default=0, help="Minimum purchase amount required")
@click.option("--start-date", help="Start date (YYYY-MM-DD). Defaults to today")
@click.option("--end-date", help="End date (YYYY-MM-DD). Defaults to 30 days from start")
@click.option("--budget", type=float, default=500, help="Total coupon budget in USD (default: 500)")
@click.option("--customer-budget", type=float, help="Maximum discount per customer (defaults to full discount)")
@click.option("--prime-only", is_flag=True, help="Prime members only")
@click.option("--clip-coupon", is_flag=True, default=True, help="Require customers to clip coupon (default: True)")
@click.option("--output", "-o", type=click.File("w"), help="Save coupon data to file")
@click.pass_context
def create_coupon(
    ctx,
    sku,
    discount,
    coupon_type,
    min_purchase,
    start_date,
    end_date,
    budget,
    customer_budget,
    prime_only,
    clip_coupon,
    output,
):
    """Create a coupon for a SKU.

    Since SP-API doesn't support direct coupon creation, this generates
    the coupon specification for use in Seller Central.

    Examples:
        amz-sp create-coupon PAW2603190101 20
        amz-sp create-coupon PAW2603190101 5 --type fixed --budget 1000
        amz-sp create-coupon PAW2603190101 15 --prime-only --start-date 2026-05-01
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
        if coupon_type == "percentage":
            discount_amount = round(current_price * discount / 100, 2)
            discount_display = f"{discount}%"
        else:
            discount_amount = discount
            discount_display = f"${discount}"

        sale_price = max(0, current_price - discount_amount)

        # Customer budget defaults to discount amount if not specified
        per_customer = customer_budget or discount_amount

        # Build coupon specification
        coupon = {
            "coupon_specification": {
                "sku": sku,
                "asin": response.get("summaries", [{}])[0].get("asin"),
                "coupon_type": coupon_type,
                "discount": {
                    "percentage" if coupon_type == "percentage" else "fixed_amount": discount,
                    "display": discount_display,
                },
                "pricing": {
                    "original_price": current_price,
                    "discounted_price": sale_price,
                    "savings": discount_amount,
                },
                "requirements": {
                    "minimum_purchase": min_purchase if min_purchase > 0 else None,
                    "prime_only": prime_only,
                    "clip_required": clip_coupon,
                },
                "schedule": {
                    "start_date": start_str,
                    "end_date": end_str,
                    "duration_days": (end - start).days,
                },
                "budget": {
                    "total_budget": budget,
                    "per_customer_max": per_customer,
                    "estimated_redemptions": int(budget / discount_amount) if discount_amount > 0 else 0,
                },
                "status": "DRAFT",
            },
            "seller_central_steps": [
                "1. Go to Seller Central → Advertising → Coupons",
                "2. Click 'Create a new coupon'",
                "3. Search for the ASIN or SKU above",
                "4. Select discount type: " + ("Percentage Off" if coupon_type == "percentage" else "Money Off"),
                "5. Enter discount value: " + str(discount),
                "6. Set budget: $" + str(budget),
                "7. Set schedule: " + start_str + " to " + end_str,
                f"8. {'Enable Prime-only targeting' if prime_only else 'Target all customers'}",
                "9. Review and submit",
            ],
            "notes": [
                "Coupons typically take 4-8 hours to activate after submission",
                "Amazon charges $0.60 per redemption (US marketplace)",
                "Coupon will display on product detail page and search results",
                f"Estimated cost per redemption: ${discount_amount + 0.60:.2f} (discount + Amazon fee)",
            ],
        }

        # Remove None values
        if coupon["coupon_specification"]["requirements"]["minimum_purchase"] is None:
            del coupon["coupon_specification"]["requirements"]["minimum_purchase"]

        # Output
        output_json = json.dumps(coupon, indent=2)

        if output:
            output.write(output_json)
            click.echo(f"✓ Coupon specification saved to {output.name}")

        click.echo(output_json)

        # Summary
        click.echo("\n" + "=" * 50)
        click.echo("SUMMARY")
        click.echo("=" * 50)
        click.echo(f"SKU: {sku}")
        click.echo(f"Discount: {discount_display}")
        click.echo(f"Price: ${current_price} → ${sale_price}")
        click.echo(f"Budget: ${budget}")
        click.echo(f"Duration: {start_str} to {end_str}")
        click.echo(f"Prime Only: {'Yes' if prime_only else 'No'}")
        click.echo("\n⚠️  SP-API does not support direct coupon creation.")
        click.echo("   Use the Seller Central steps above to create the coupon.")

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
