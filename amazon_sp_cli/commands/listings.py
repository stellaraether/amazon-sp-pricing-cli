"""Listing content management commands."""

import json

import click

from ..cli import handle_errors


def _build_attributes(
    title=None,
    description=None,
    bullet_points=None,
    price=None,
    currency="USD",
    condition=None,
    images=None,
    inventory=None,
    shipping_template=None,
    language_tag="en_US",
    attributes_json=None,
):
    """Build SP-API attributes dict from CLI options."""
    attributes = {}

    if title is not None:
        attributes["item_name"] = [{"value": title, "language_tag": language_tag}]

    if description is not None:
        attributes["product_description"] = [{"value": description, "language_tag": language_tag}]

    if bullet_points:
        attributes["bullet_point"] = [{"value": bp} for bp in bullet_points]

    if price is not None:
        attributes["list_price"] = [{"currency": currency, "value": price}]
        attributes["purchasable_price"] = [{"currency": currency, "value": price}]

    if condition is not None:
        attributes["condition_type"] = [{"value": condition}]

    if images:
        attributes["main_product_image_locator"] = [{"media_location": images[0]}]
        for idx, img in enumerate(images[1:], start=1):
            if idx > 8:
                break
            attributes[f"other_product_image_locator_{idx}"] = [{"media_location": img}]

    if inventory is not None:
        attributes["fulfillment_availability"] = [{"quantity": inventory, "fulfillment_channel_code": "DEFAULT"}]

    if shipping_template is not None:
        attributes["merchant_shipping_group"] = [{"value": shipping_template}]

    if attributes_json:
        try:
            extra = json.loads(attributes_json)
        except json.JSONDecodeError as exc:
            raise click.BadParameter(f"Invalid JSON in --attributes-json: {exc}")
        if not isinstance(extra, dict):
            raise click.BadParameter("--attributes-json must be a JSON object")
        attributes.update(extra)

    return attributes


def _check_issues(response):
    """Check response for issues and exit with error if any ERROR severity items exist."""
    issues = response.get("issues", [])
    errors = [i for i in issues if i.get("severity") == "ERROR"]
    if errors:
        click.echo("Validation issues found:", err=True)
        for issue in issues:
            code = issue.get("code", "Unknown")
            message = issue.get("message", "")
            severity = issue.get("severity", "")
            click.echo(f"  [{code}] ({severity}) {message}", err=True)
        raise click.Abort()
    return issues


def register_listings_commands(cli_group, ensure_auth_client):
    """Register listing management CLI commands."""

    @cli_group.command()
    @click.argument("sku")
    @click.pass_context
    @handle_errors
    def get_listing(ctx, sku):
        """Get full listing data for a SKU."""
        _, client = ensure_auth_client(ctx)
        response = client.get_listing(sku)
        click.echo(json.dumps(response, indent=2))

    @cli_group.command()
    @click.argument("sku")
    @click.option("--product-type", "-p", required=True, help="SP-API product type (e.g., PET_TOY)")
    @click.option(
        "--requirements",
        type=click.Choice(["LISTING", "LISTING_PRODUCT_ONLY", "LISTING_OFFER_ONLY"]),
        default="LISTING",
        help="Requirements level for the update",
    )
    @click.option("--title", help="Item title")
    @click.option("--description", help="Product description")
    @click.option("--bullet-point", multiple=True, help="Bullet point (can be used multiple times)")
    @click.option("--price", type=float, help="List price")
    @click.option("--currency", default="USD", help="Currency code (default USD)")
    @click.option("--condition", help="Condition type (e.g., new_new)")
    @click.option("--image", multiple=True, help="Image URL (first becomes main, rest become other)")
    @click.option("--inventory", type=int, help="Available quantity")
    @click.option("--shipping-template", help="Merchant shipping group name")
    @click.option("--language-tag", default="en_US", help="Language tag for text attributes")
    @click.option(
        "--attributes-json",
        help="Raw JSON string of additional attributes (merged on top of other flags)",
    )
    @click.option("--dry-run", is_flag=True, help="Validate without applying")
    @click.pass_context
    @handle_errors
    def update_listing(
        ctx,
        sku,
        product_type,
        requirements,
        title,
        description,
        bullet_point,
        price,
        currency,
        condition,
        image,
        inventory,
        shipping_template,
        language_tag,
        attributes_json,
        dry_run,
    ):
        """Update listing attributes for a SKU."""
        _, client = ensure_auth_client(ctx)

        attributes = _build_attributes(
            title=title,
            description=description,
            bullet_points=bullet_point or None,
            price=price,
            currency=currency,
            condition=condition,
            images=image or None,
            inventory=inventory,
            shipping_template=shipping_template,
            language_tag=language_tag,
            attributes_json=attributes_json,
        )

        if not attributes:
            click.echo("Error: No attributes provided. Use flags or --attributes-json.", err=True)
            raise click.Abort()

        mode = "VALIDATION_PREVIEW" if dry_run else None
        response = client.put_listing(
            sku,
            product_type=product_type,
            attributes=attributes,
            requirements=requirements,
            mode=mode,
        )

        issues = _check_issues(response)
        if dry_run and issues:
            click.echo("Validation warnings:")
            for issue in issues:
                code = issue.get("code", "Unknown")
                message = issue.get("message", "")
                severity = issue.get("severity", "")
                click.echo(f"  [{code}] ({severity}) {message}")
            click.echo("Validation passed with warnings")
        elif dry_run:
            click.echo("Validation passed")
        else:
            click.echo(json.dumps(response, indent=2))

    @cli_group.command()
    @click.argument("sku")
    @click.pass_context
    @handle_errors
    def delete_listing(ctx, sku):
        """Delete a listing for a SKU."""
        _, client = ensure_auth_client(ctx)
        response = client.delete_listing(sku)
        click.echo(json.dumps(response, indent=2))
