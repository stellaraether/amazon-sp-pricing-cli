"""A+ Content API module for Amazon SP-API."""

import base64
import hashlib
import json
import os

import click
import requests

# --- Data Models ---


class TextComponent:
    """Text component for A+ Content modules."""

    def __init__(self, value: str, decoration: str = "NONE"):
        self.value = value
        self.decoration = decoration

    def to_dict(self) -> dict:
        return {"value": self.value, "decoration": self.decoration}


class ImageComponent:
    """Image component for A+ Content modules."""

    def __init__(self, upload_destination_id: str, image_crop: dict = None):
        self.upload_destination_id = upload_destination_id
        self.image_crop = image_crop

    def to_dict(self) -> dict:
        result = {"uploadDestinationId": self.upload_destination_id}
        if self.image_crop:
            result["imageCrop"] = self.image_crop
        return result


class StandardImageTextModule:
    """Standard Image & Text module."""

    def __init__(self, headline=None, image=None, body=None):
        self.headline = headline
        self.image = image
        self.body = body

    def to_dict(self) -> dict:
        result = {}
        if self.headline:
            result["headline"] = self.headline.to_dict()
        if self.image:
            result["image"] = self.image.to_dict()
        if self.body:
            result["body"] = self.body.to_dict()
        return result


class StandardSingleImageModule:
    """Standard Single Image module."""

    def __init__(self, image=None, image_caption=None):
        self.image = image
        self.image_caption = image_caption

    def to_dict(self) -> dict:
        result = {}
        if self.image:
            result["image"] = self.image.to_dict()
        if self.image_caption:
            result["imageCaption"] = self.image_caption.to_dict()
        return result


class StandardMultipleImageTextModule:
    """Standard Multiple Image & Text module."""

    def __init__(self, headline=None, image_text_boxes=None):
        self.headline = headline
        self.image_text_boxes = image_text_boxes or []

    def to_dict(self) -> dict:
        result = {}
        if self.headline:
            result["headline"] = self.headline.to_dict()
        if self.image_text_boxes:
            result["imageTextBoxes"] = self.image_text_boxes
        return result


class StandardFourImageTextModule:
    """Standard Four Image & Text module."""

    def __init__(self, headline=None, image_text_boxes=None):
        self.headline = headline
        self.image_text_boxes = image_text_boxes or []

    def to_dict(self) -> dict:
        result = {}
        if self.headline:
            result["headline"] = self.headline.to_dict()
        if self.image_text_boxes:
            result["imageTextBoxes"] = self.image_text_boxes
        return result


class StandardComparisonTableModule:
    """Standard Comparison Table module."""

    def __init__(self, headline=None, comparison_table_rows=None):
        self.headline = headline
        self.comparison_table_rows = comparison_table_rows or []

    def to_dict(self) -> dict:
        result = {}
        if self.headline:
            result["headline"] = self.headline.to_dict()
        if self.comparison_table_rows:
            result["comparisonTableRows"] = self.comparison_table_rows
        return result


class StandardTextModule:
    """Standard Text-only module."""

    def __init__(self, headline=None, body=None):
        self.headline = headline
        self.body = body

    def to_dict(self) -> dict:
        result = {}
        if self.headline:
            result["headline"] = self.headline.to_dict()
        if self.body:
            result["body"] = self.body.to_dict()
        return result


class StandardImageTextOverlayModule:
    """Standard Image with Text Overlay module."""

    def __init__(self, headline=None, image=None, body=None):
        self.headline = headline
        self.image = image
        self.body = body

    def to_dict(self) -> dict:
        result = {}
        if self.headline:
            result["headline"] = self.headline.to_dict()
        if self.image:
            result["image"] = self.image.to_dict()
        if self.body:
            result["body"] = self.body.to_dict()
        return result


class ContentModule:
    """A+ Content module wrapper."""

    MODULE_TYPES = {
        "STANDARD_IMAGE_TEXT": "standardImageText",
        "STANDARD_SINGLE_IMAGE": "standardSingleImage",
        "STANDARD_MULTIPLE_IMAGE_TEXT": "standardMultipleImageText",
        "STANDARD_FOUR_IMAGE_TEXT": "standardFourImageText",
        "STANDARD_COMPARISON_TABLE": "standardComparisonTable",
        "STANDARD_TEXT": "standardText",
        "STANDARD_IMAGE_TEXT_OVERLAY": "standardImageTextOverlay",
    }

    def __init__(
        self,
        module_type: str,
        standard_image_text: StandardImageTextModule = None,
        standard_single_image: StandardSingleImageModule = None,
        standard_multiple_image_text: StandardMultipleImageTextModule = None,
        standard_four_image_text: StandardFourImageTextModule = None,
        standard_comparison_table: StandardComparisonTableModule = None,
        standard_text: StandardTextModule = None,
        standard_image_text_overlay: StandardImageTextOverlayModule = None,
    ):
        self.module_type = module_type
        self.standard_image_text = standard_image_text
        self.standard_single_image = standard_single_image
        self.standard_multiple_image_text = standard_multiple_image_text
        self.standard_four_image_text = standard_four_image_text
        self.standard_comparison_table = standard_comparison_table
        self.standard_text = standard_text
        self.standard_image_text_overlay = standard_image_text_overlay

    def to_dict(self) -> dict:
        result = {"moduleType": self.module_type}
        field_name = self.MODULE_TYPES.get(self.module_type)

        if field_name == "standardImageText" and self.standard_image_text:
            result["standardImageText"] = self.standard_image_text.to_dict()
        elif field_name == "standardSingleImage" and self.standard_single_image:
            result["standardSingleImage"] = self.standard_single_image.to_dict()
        elif field_name == "standardMultipleImageText" and self.standard_multiple_image_text:
            result["standardMultipleImageText"] = self.standard_multiple_image_text.to_dict()
        elif field_name == "standardFourImageText" and self.standard_four_image_text:
            result["standardFourImageText"] = self.standard_four_image_text.to_dict()
        elif field_name == "standardComparisonTable" and self.standard_comparison_table:
            result["standardComparisonTable"] = self.standard_comparison_table.to_dict()
        elif field_name == "standardText" and self.standard_text:
            result["standardText"] = self.standard_text.to_dict()
        elif field_name == "standardImageTextOverlay" and self.standard_image_text_overlay:
            result["standardImageTextOverlay"] = self.standard_image_text_overlay.to_dict()

        return result

    def validate(self, index: int) -> list:
        """Validate module structure. Returns list of issues."""
        issues = []

        if not self.module_type:
            issues.append(f"Module {index + 1}: moduleType is required")
            return issues

        if self.module_type not in self.MODULE_TYPES:
            issues.append(f"Module {index + 1}: invalid moduleType '{self.module_type}'")
            return issues

        data = self.to_dict()
        if len(data) == 1:
            issues.append(f"Module {index + 1}: {self.module_type} has no content")

        return issues


class APlusContentDocument:
    """A+ Content document."""

    def __init__(
        self,
        name: str,
        content_type: str = "EBC",
        locale: str = "en_US",
        content_module_list: list = None,
    ):
        self.name = name
        self.content_type = content_type
        self.locale = locale
        self.content_module_list = content_module_list or []

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "contentType": self.content_type,
            "locale": self.locale,
            "contentModuleList": [m.to_dict() for m in self.content_module_list],
        }

    def validate(self) -> list:
        """Validate content structure. Returns list of issues."""
        issues = []

        if not self.name:
            issues.append("Content name is required")

        if not self.content_module_list:
            issues.append("At least 1 module is required")
        elif len(self.content_module_list) > 7:
            issues.append("Maximum 7 modules allowed")

        for i, module in enumerate(self.content_module_list):
            issues.extend(module.validate(i))

        return issues


# --- Helper Functions ---


def build_content_from_json(name: str, data: dict) -> APlusContentDocument:
    """Build APlusContentDocument from JSON dict."""
    content = APlusContentDocument(
        name=name,
        locale=data.get("locale", "en_US"),
    )

    for mod_data in data.get("modules", []):
        module = build_module_from_json(mod_data)
        content.content_module_list.append(module)

    return content


def build_module_from_json(data: dict) -> ContentModule:
    """Build ContentModule from JSON dict."""
    module_type = data.get("moduleType", "STANDARD_TEXT")

    if module_type == "STANDARD_IMAGE_TEXT":
        return ContentModule(
            module_type=module_type,
            standard_image_text=StandardImageTextModule(
                headline=TextComponent(data["headline"]) if data.get("headline") else None,
                body=TextComponent(data["body"]) if data.get("body") else None,
                image=ImageComponent(data["imageId"]) if data.get("imageId") else None,
            ),
        )
    elif module_type == "STANDARD_SINGLE_IMAGE":
        return ContentModule(
            module_type=module_type,
            standard_single_image=StandardSingleImageModule(
                image=ImageComponent(data["imageId"]) if data.get("imageId") else None,
                image_caption=TextComponent(data["caption"]) if data.get("caption") else None,
            ),
        )
    elif module_type == "STANDARD_MULTIPLE_IMAGE_TEXT":
        return ContentModule(
            module_type=module_type,
            standard_multiple_image_text=StandardMultipleImageTextModule(
                headline=TextComponent(data["headline"]) if data.get("headline") else None,
                image_text_boxes=data.get("boxes", []),
            ),
        )
    elif module_type == "STANDARD_FOUR_IMAGE_TEXT":
        return ContentModule(
            module_type=module_type,
            standard_four_image_text=StandardFourImageTextModule(
                headline=TextComponent(data["headline"]) if data.get("headline") else None,
                image_text_boxes=data.get("boxes", []),
            ),
        )
    elif module_type == "STANDARD_COMPARISON_TABLE":
        return ContentModule(
            module_type=module_type,
            standard_comparison_table=StandardComparisonTableModule(
                headline=TextComponent(data["headline"]) if data.get("headline") else None,
                comparison_table_rows=data.get("rows", []),
            ),
        )
    elif module_type == "STANDARD_TEXT":
        return ContentModule(
            module_type=module_type,
            standard_text=StandardTextModule(
                headline=TextComponent(data["headline"]) if data.get("headline") else None,
                body=TextComponent(data["body"]) if data.get("body") else None,
            ),
        )
    elif module_type == "STANDARD_IMAGE_TEXT_OVERLAY":
        return ContentModule(
            module_type=module_type,
            standard_image_text_overlay=StandardImageTextOverlayModule(
                headline=TextComponent(data["headline"]) if data.get("headline") else None,
                body=TextComponent(data["body"]) if data.get("body") else None,
                image=ImageComponent(data["imageId"]) if data.get("imageId") else None,
            ),
        )
    else:
        raise ValueError(f"Unsupported moduleType: {module_type}")


# --- CLI Commands ---


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

        try:
            response = client.create_a_plus_content(content.to_dict())
            click.echo(f"A+ Content created: {content_name}")
            click.echo(f"Modules: {len(content.content_module_list)}")
            if response:
                click.echo(json.dumps(response, indent=2))
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()

    @a_plus.command("validate")
    @click.argument("content-name")
    @click.option("--data", "-d", type=click.Path(exists=True), required=True, help="JSON file with content data")
    @click.pass_context
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

        try:
            response = client.validate_a_plus_content(content.to_dict())
            click.echo("API validation passed")
            if response:
                click.echo(json.dumps(response, indent=2))
        except Exception as e:
            click.echo(f"API validation failed: {e}", err=True)
            raise click.Abort()

    @a_plus.command("get")
    @click.argument("content-name")
    @click.pass_context
    def get_content(ctx, content_name):
        """Get A+ Content document."""
        _, client = ensure_auth_client(ctx)

        try:
            response = client.get_a_plus_content(content_name)
            click.echo(json.dumps(response, indent=2))
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()

    @a_plus.command("list")
    @click.pass_context
    def list_content(ctx):
        """List A+ Content documents."""
        _, client = ensure_auth_client(ctx)

        try:
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
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()

    @a_plus.command("update")
    @click.argument("content-name")
    @click.option("--data", "-d", type=click.Path(exists=True), required=True, help="JSON file with updated content")
    @click.pass_context
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

        try:
            response = client.update_a_plus_content(content_name, content.to_dict())
            click.echo(f"A+ Content updated: {content_name}")
            if response:
                click.echo(json.dumps(response, indent=2))
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()

    @a_plus.command("delete")
    @click.argument("content-name")
    @click.confirmation_option(prompt="Delete this A+ Content?")
    @click.pass_context
    def delete_content(ctx, content_name):
        """Delete A+ Content document."""
        _, client = ensure_auth_client(ctx)

        try:
            client.delete_a_plus_content(content_name)
            click.echo(f"A+ Content deleted: {content_name}")
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()

    @a_plus.command("upload-image")
    @click.argument("file-path", type=click.Path(exists=True))
    @click.option("--content-type", default="image/jpeg", help="MIME type of the image")
    @click.option("--resource", default="aplus", help="Resource type for upload destination")
    @click.pass_context
    def upload_image(ctx, file_path, content_type, resource):
        """Upload an image and return an uploadDestinationId for A+ Content."""
        _, client = ensure_auth_client(ctx)

        with open(file_path, "rb") as f:
            file_data = f.read()

        md5_hash = hashlib.md5(file_data).digest()
        content_md5 = base64.b64encode(md5_hash).decode("ascii")
        file_name = os.path.basename(file_path)

        try:
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
            headers = payload.get("headers", [])

            if not upload_url:
                click.echo("Error: No upload URL returned", err=True)
                raise click.Abort()

            upload_headers = {h["name"]: h["value"] for h in headers}
            upload_headers.setdefault("Content-Type", content_type)
            upload_headers.setdefault("Content-MD5", content_md5)

            put_response = requests.put(upload_url, data=file_data, headers=upload_headers)
            put_response.raise_for_status()

            click.echo(f"Upload successful: {file_name}")
            click.echo(f"uploadDestinationId: {upload_destination_id}")
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()

    @a_plus.group("asin")
    def asin():
        """ASIN association commands."""
        pass

    @asin.command("add")
    @click.argument("content-name")
    @click.argument("asins", nargs=-1, required=True)
    @click.pass_context
    def add_asins(ctx, content_name, asins):
        """Associate ASINs with A+ Content."""
        _, client = ensure_auth_client(ctx)

        try:
            response = client.post_a_plus_content_asin_relations(content_name, list(asins))
            click.echo(f"Associated {len(asins)} ASIN(s) with {content_name}")
            if response:
                click.echo(json.dumps(response, indent=2))
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()

    @asin.command("remove")
    @click.argument("content-name")
    @click.argument("asins", nargs=-1, required=True)
    @click.pass_context
    def remove_asins(ctx, content_name, asins):
        """Remove ASIN associations from A+ Content."""
        _, client = ensure_auth_client(ctx)

        try:
            response = client.delete_a_plus_content_asin_relations(content_name, list(asins))
            click.echo(f"Removed {len(asins)} ASIN(s) from {content_name}")
            if response:
                click.echo(json.dumps(response, indent=2))
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()

    @asin.command("list")
    @click.argument("content-name")
    @click.pass_context
    def list_asins(ctx, content_name):
        """List ASINs associated with A+ Content."""
        _, client = ensure_auth_client(ctx)

        try:
            response = client.get_a_plus_content_asin_relations(content_name)
            asins = response.get("asinSet", [])
            click.echo(f"\nASINs for '{content_name}' ({len(asins)} found):\n")
            for asin in asins:
                click.echo(f"  {asin}")
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()
