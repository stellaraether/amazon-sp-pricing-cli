"""A+ Content CLI commands."""

import base64
import hashlib
import json
import os
import urllib.parse

import click
import requests

from ..cli import handle_errors
from ..models.a_plus import build_content_from_json


def register_a_plus_commands(cli_group, ensure_auth_client):
    """Register A+ Content CLI commands."""

    @cli_group.group("a-plus")
    def a_plus():
        """A+ Content management (requires Brand Registry)."""
        pass

    @a_plus.command("create")
    @click.argument("content-name")
    @click.option("--data", "-d", type=click.Path(exists=True), required=True, help="JSON file with content data")
    @click.option("--dry-run", is_flag=True, help="Validate without creating")
    @click.pass_context
    @handle_errors
    def create_content(ctx, content_name, data, dry_run):
        """Create A+ Content document from JSON file."""
        _, client = ensure_auth_client(ctx)

        with open(data, "r") as f:
            content_data = json.load(f)

        content = build_content_from_json(content_name, content_data)

        issues = content.validate()
        if issues:
            click.echo("Validation issues:", err=True)
            for issue in issues:
                click.echo(f"  - {issue}", err=True)
            raise click.Abort()

        if dry_run:
            click.echo("Content is valid (dry run)")
            click.echo(json.dumps(content.to_dict(), indent=2))
            return

        response = client.create_a_plus_content(content.to_dict())
        click.echo(f"A+ Content created: {content_name}")
        click.echo(f"Modules: {len(content.content_module_list)}")
        if response:
            click.echo(json.dumps(response, indent=2))

    @a_plus.command("validate")
    @click.argument("content-name")
    @click.option("--data", "-d", type=click.Path(exists=True), required=True, help="JSON file with content data")
    @click.pass_context
    @handle_errors
    def validate_content(ctx, content_name, data):
        """Validate A+ Content without creating."""
        _, client = ensure_auth_client(ctx)

        with open(data, "r") as f:
            content_data = json.load(f)

        content = build_content_from_json(content_name, content_data)

        issues = content.validate()
        if issues:
            click.echo("Validation issues:", err=True)
            for issue in issues:
                click.echo(f"  - {issue}", err=True)
            raise click.Abort()

        response = client.validate_a_plus_content(content.to_dict())
        click.echo("API validation passed")
        if response:
            click.echo(json.dumps(response, indent=2))

    @a_plus.command("get")
    @click.argument("content-name")
    @click.pass_context
    @handle_errors
    def get_content(ctx, content_name):
        """Get A+ Content document."""
        _, client = ensure_auth_client(ctx)
        response = client.get_a_plus_content(content_name)
        click.echo(json.dumps(response, indent=2))

    @a_plus.command("list")
    @click.pass_context
    @handle_errors
    def list_content(ctx):
        """List A+ Content documents."""
        _, client = ensure_auth_client(ctx)
        response = client.list_a_plus_content(marketplaceId=client.marketplace_id)
        documents = response.get("contentDocumentList", [])
        click.echo(f"\nA+ Content Documents ({len(documents)} found):\n")
        for doc in documents:
            click.echo(f"  Name: {doc.get('name')}")
            click.echo(f"  Status: {doc.get('status', 'N/A')}")
            click.echo(f"  Locale: {doc.get('locale', 'N/A')}")
            asins = doc.get("asinSet", [])
            if asins:
                click.echo(f"  ASINs: {', '.join(asins)}")
            click.echo()

    @a_plus.command("update")
    @click.argument("content-name")
    @click.option("--data", "-d", type=click.Path(exists=True), required=True, help="JSON file with updated content")
    @click.pass_context
    @handle_errors
    def update_content(ctx, content_name, data):
        """Update existing A+ Content document."""
        _, client = ensure_auth_client(ctx)

        with open(data, "r") as f:
            content_data = json.load(f)

        content = build_content_from_json(content_name, content_data)

        issues = content.validate()
        if issues:
            click.echo("Validation issues:", err=True)
            for issue in issues:
                click.echo(f"  - {issue}", err=True)
            raise click.Abort()

        response = client.update_a_plus_content(content_name, content.to_dict())
        click.echo(f"A+ Content updated: {content_name}")
        if response:
            click.echo(json.dumps(response, indent=2))

    @a_plus.command("delete")
    @click.argument("content-name")
    @click.confirmation_option(prompt="Delete this A+ Content?")
    @click.pass_context
    @handle_errors
    def delete_content(ctx, content_name):
        """Delete A+ Content document."""
        _, client = ensure_auth_client(ctx)
        client.delete_a_plus_content(content_name)
        click.echo(f"A+ Content deleted: {content_name}")

    @a_plus.command("upload-image")
    @click.argument("file-path", type=click.Path(exists=True))
    @click.option("--content-type", default="image/jpeg", help="MIME type of the image")
    @click.option(
        "--resource", default="aplus/2020-11-01/contentDocuments", help="Resource type for upload destination"
    )
    @click.pass_context
    @handle_errors
    def upload_image(ctx, file_path, content_type, resource):
        """Upload an image and return an uploadDestinationId for A+ Content."""
        _, client = ensure_auth_client(ctx)

        with open(file_path, "rb") as f:
            file_data = f.read()

        md5_hash = hashlib.md5(file_data).digest()
        content_md5 = base64.b64encode(md5_hash).decode("ascii")
        file_name = os.path.basename(file_path)

        response = client.create_upload_destination(
            marketplace_id=client.marketplace_id,
            content_md5=content_md5,
            content_type=content_type,
            file_name=file_name,
            resource=resource,
        )

        payload = response.get("payload", response)
        upload_destination_id = payload.get("uploadDestinationId")
        upload_url = payload.get("url")

        if not upload_url:
            click.echo("Error: No upload URL returned", err=True)
            raise click.Abort()

        parsed = urllib.parse.urlparse(upload_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        form_fields = {k: v[0] for k, v in urllib.parse.parse_qs(parsed.query).items()}

        post_response = requests.post(
            base_url,
            data=form_fields,
            files={"File": (file_name, file_data, content_type)},
        )
        post_response.raise_for_status()

        click.echo(f"Upload successful: {file_name}")
        click.echo(f"uploadDestinationId: {upload_destination_id}")

    @a_plus.group("asin")
    def asin():
        """ASIN association commands."""
        pass

    @asin.command("add")
    @click.argument("content-name")
    @click.argument("asins", nargs=-1, required=True)
    @click.pass_context
    @handle_errors
    def add_asins(ctx, content_name, asins):
        """Associate ASINs with A+ Content."""
        _, client = ensure_auth_client(ctx)
        response = client.post_a_plus_content_asin_relations(content_name, list(asins))
        click.echo(f"Associated {len(asins)} ASIN(s) with {content_name}")
        if response:
            click.echo(json.dumps(response, indent=2))

    @asin.command("remove")
    @click.argument("content-name")
    @click.argument("asins", nargs=-1, required=True)
    @click.pass_context
    @handle_errors
    def remove_asins(ctx, content_name, asins):
        """Remove ASIN associations from A+ Content."""
        _, client = ensure_auth_client(ctx)
        response = client.delete_a_plus_content_asin_relations(content_name, list(asins))
        click.echo(f"Removed {len(asins)} ASIN(s) from {content_name}")
        if response:
            click.echo(json.dumps(response, indent=2))

    @asin.command("list")
    @click.argument("content-name")
    @click.pass_context
    @handle_errors
    def list_asins(ctx, content_name):
        """List ASINs associated with A+ Content."""
        _, client = ensure_auth_client(ctx)
        response = client.get_a_plus_content_asin_relations(content_name)
        asins = response.get("asinSet", [])
        click.echo(f"\nASINs for '{content_name}' ({len(asins)} found):\n")
        for asin in asins:
            click.echo(f"  {asin}")
