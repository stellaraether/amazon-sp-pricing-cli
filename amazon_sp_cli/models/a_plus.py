"""A+ Content data models for Amazon SP-API."""


class TextComponent:
    """Text component for A+ Content modules."""

    def __init__(self, value: str, decorator_set: list = None):
        self.value = value
        self.decorator_set = decorator_set or []

    def to_dict(self) -> dict:
        result = {"value": self.value}
        if self.decorator_set:
            result["decoratorSet"] = self.decorator_set
        return result


class ImageComponent:
    """Image component for A+ Content modules."""

    def __init__(
        self,
        upload_destination_id: str,
        image_crop: dict = None,
        alt_text: str = None,
        image_crop_specification: dict = None,
    ):
        self.upload_destination_id = upload_destination_id
        self.image_crop = image_crop
        self.alt_text = alt_text
        self.image_crop_specification = image_crop_specification

    def to_dict(self) -> dict:
        result = {"uploadDestinationId": self.upload_destination_id}
        if self.image_crop:
            result["imageCrop"] = self.image_crop
        if self.alt_text:
            result["altText"] = self.alt_text
        if self.image_crop_specification:
            result["imageCropSpecification"] = self.image_crop_specification
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


class ParagraphComponent:
    """Paragraph component containing a list of text."""

    def __init__(self, text_list: list = None):
        self.text_list = text_list or []

    def to_dict(self) -> dict:
        return {"textList": [t.to_dict() for t in self.text_list]}


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

    def __init__(self, headline=None, image=None, body=None, overlay_color_type="DARK"):
        self.headline = headline
        self.image = image
        self.body = body
        self.overlay_color_type = overlay_color_type

    def to_dict(self) -> dict:
        result = {"overlayColorType": self.overlay_color_type}
        block = {}
        if self.headline:
            block["headline"] = self.headline.to_dict()
        if self.image:
            block["image"] = self.image.to_dict()
        if self.body:
            block["body"] = self.body.to_dict()
        if block:
            result["block"] = block
        return result


class StandardCompanyLogoModule:
    """Standard Company Logo module."""

    def __init__(self, company_logo=None):
        self.company_logo = company_logo

    def to_dict(self) -> dict:
        result = {}
        if self.company_logo:
            result["companyLogo"] = self.company_logo.to_dict()
        return result


class ContentModule:
    """A+ Content module wrapper."""

    MODULE_TYPES = {
        "STANDARD_IMAGE_TEXT": "standardImageTextOverlay",
        "STANDARD_SINGLE_IMAGE": "standardSingleImage",
        "STANDARD_MULTIPLE_IMAGE_TEXT": "standardMultipleImageText",
        "STANDARD_FOUR_IMAGE_TEXT": "standardFourImageText",
        "STANDARD_COMPARISON_TABLE": "standardComparisonTable",
        "STANDARD_TEXT": "standardText",
        "STANDARD_IMAGE_TEXT_OVERLAY": "standardImageTextOverlay",
        "STANDARD_COMPANY_LOGO": "standardCompanyLogo",
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
        standard_company_logo: StandardCompanyLogoModule = None,
    ):
        self.module_type = module_type
        self.standard_image_text = standard_image_text
        self.standard_single_image = standard_single_image
        self.standard_multiple_image_text = standard_multiple_image_text
        self.standard_four_image_text = standard_four_image_text
        self.standard_comparison_table = standard_comparison_table
        self.standard_text = standard_text
        self.standard_image_text_overlay = standard_image_text_overlay
        self.standard_company_logo = standard_company_logo

    def to_dict(self) -> dict:
        result = {"contentModuleType": self.module_type}
        field_name = self.MODULE_TYPES.get(self.module_type)

        if field_name == "standardImageTextOverlay" and self.standard_image_text_overlay:
            result["standardImageTextOverlay"] = self.standard_image_text_overlay.to_dict()
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
        elif field_name == "standardCompanyLogo" and self.standard_company_logo:
            result["standardCompanyLogo"] = self.standard_company_logo.to_dict()

        return result

    def validate(self, index: int) -> list:
        """Validate module structure. Returns list of issues."""
        issues = []

        if not self.module_type:
            issues.append(f"Module {index + 1}: contentModuleType is required")
            return issues

        if self.module_type not in self.MODULE_TYPES:
            issues.append(f"Module {index + 1}: invalid contentModuleType '{self.module_type}'")
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
        locale: str = "en-US",
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


def build_content_from_json(name: str, data: dict) -> APlusContentDocument:
    """Build APlusContentDocument from JSON dict."""
    content = APlusContentDocument(
        name=name,
        locale=data.get("locale", "en-US"),
    )

    for mod_data in data.get("modules", []):
        module = build_module_from_json(mod_data)
        content.content_module_list.append(module)

    return content


def build_module_from_json(data: dict) -> ContentModule:
    """Build ContentModule from JSON dict."""
    module_type = data.get("contentModuleType") or data.get("moduleType", "STANDARD_TEXT")

    if module_type == "STANDARD_IMAGE_TEXT":
        body = None
        if data.get("body"):
            body = ParagraphComponent(text_list=[TextComponent(data["body"])])
        return ContentModule(
            module_type=module_type,
            standard_image_text_overlay=StandardImageTextOverlayModule(
                headline=TextComponent(data["headline"]) if data.get("headline") else None,
                body=body,
                image=(
                    ImageComponent(
                        data["imageId"],
                        alt_text=data.get("altText"),
                        image_crop_specification=data.get("imageCropSpecification"),
                    )
                    if data.get("imageId")
                    else None
                ),
            ),
        )
    elif module_type == "STANDARD_SINGLE_IMAGE":
        return ContentModule(
            module_type=module_type,
            standard_single_image=StandardSingleImageModule(
                image=(
                    ImageComponent(
                        data["imageId"],
                        alt_text=data.get("altText"),
                        image_crop_specification=data.get("imageCropSpecification"),
                    )
                    if data.get("imageId")
                    else None
                ),
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
        body = None
        if data.get("body"):
            body = ParagraphComponent(text_list=[TextComponent(data["body"])])
        return ContentModule(
            module_type=module_type,
            standard_text=StandardTextModule(
                headline=TextComponent(data["headline"]) if data.get("headline") else None,
                body=body,
            ),
        )
    elif module_type == "STANDARD_IMAGE_TEXT_OVERLAY":
        body = None
        if data.get("body"):
            body = ParagraphComponent(text_list=[TextComponent(data["body"])])
        return ContentModule(
            module_type=module_type,
            standard_image_text_overlay=StandardImageTextOverlayModule(
                headline=TextComponent(data["headline"]) if data.get("headline") else None,
                body=body,
                image=(
                    ImageComponent(
                        data["imageId"],
                        alt_text=data.get("altText"),
                        image_crop_specification=data.get("imageCropSpecification"),
                    )
                    if data.get("imageId")
                    else None
                ),
                overlay_color_type=data.get("overlayColorType", "DARK"),
            ),
        )
    elif module_type == "STANDARD_COMPANY_LOGO":
        return ContentModule(
            module_type=module_type,
            standard_company_logo=StandardCompanyLogoModule(
                company_logo=(
                    ImageComponent(
                        data["imageId"],
                        alt_text=data.get("altText"),
                        image_crop_specification=data.get("imageCropSpecification"),
                    )
                    if data.get("imageId")
                    else None
                ),
            ),
        )
    else:
        raise ValueError(f"Unsupported moduleType: {module_type}")
