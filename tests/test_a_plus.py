"""Tests for A+ Content module."""

import json
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from amazon_sp_cli.main import cli
from amazon_sp_cli.models.a_plus import (
    APlusContentDocument,
    ContentModule,
    StandardCompanyLogoModule,
    StandardTextModule,
    TextComponent,
    build_content_from_json,
    build_module_from_json,
)


class TestDataModels:
    def test_text_component_to_dict(self):
        tc = TextComponent("Hello", [{"type": "BOLD"}])
        assert tc.to_dict() == {"value": "Hello", "decoratorSet": [{"type": "BOLD"}]}

    def test_standard_text_module_to_dict(self):
        from amazon_sp_cli.models.a_plus import ParagraphComponent

        mod = StandardTextModule(
            headline=TextComponent("Headline"),
            body=ParagraphComponent(text_list=[TextComponent("Body text")]),
        )
        result = mod.to_dict()
        assert result["headline"]["value"] == "Headline"
        assert result["body"]["textList"][0]["value"] == "Body text"

    def test_content_module_wrapper(self):
        mod = ContentModule(
            module_type="STANDARD_TEXT",
            standard_text=StandardTextModule(
                headline=TextComponent("H"),
            ),
        )
        result = mod.to_dict()
        assert result["contentModuleType"] == "STANDARD_TEXT"
        assert result["standardText"]["headline"]["value"] == "H"

    def test_document_validation_passes(self):
        doc = APlusContentDocument(name="test-doc")
        doc.content_module_list = [ContentModule("STANDARD_TEXT", standard_text=StandardTextModule())]
        assert doc.validate() == []

    def test_document_validation_no_name(self):
        doc = APlusContentDocument(name="")
        doc.content_module_list = [ContentModule("STANDARD_TEXT", standard_text=StandardTextModule())]
        assert "Content name is required" in doc.validate()

    def test_document_validation_no_modules(self):
        doc = APlusContentDocument(name="test")
        assert "At least 1 module is required" in doc.validate()

    def test_document_validation_too_many_modules(self):
        doc = APlusContentDocument(name="test")
        doc.content_module_list = [ContentModule("STANDARD_TEXT", standard_text=StandardTextModule()) for _ in range(8)]
        assert "Maximum 7 modules allowed" in doc.validate()

    def test_document_validation_invalid_type(self):
        doc = APlusContentDocument(name="test")
        doc.content_module_list = [ContentModule("INVALID_TYPE")]
        assert "invalid contentModuleType" in doc.validate()[0]

    def test_document_validation_empty_module(self):
        doc = APlusContentDocument(name="test")
        doc.content_module_list = [ContentModule("STANDARD_TEXT")]
        assert "has no content" in doc.validate()[0]

    def test_module_validate_empty_content(self):
        mod = ContentModule("STANDARD_IMAGE_TEXT")
        issues = mod.validate(0)
        assert len(issues) == 1
        assert "has no content" in issues[0]

    def test_module_validate_valid(self):
        mod = ContentModule(
            "STANDARD_TEXT",
            standard_text=StandardTextModule(headline=TextComponent("H")),
        )
        assert mod.validate(0) == []


class TestBuildFromJson:
    def test_build_content_from_json(self):
        data = {
            "locale": "en-US",
            "modules": [{"moduleType": "STANDARD_TEXT", "headline": "Hello", "body": "World"}],
        }
        doc = build_content_from_json("my-doc", data)
        assert doc.name == "my-doc"
        assert doc.locale == "en-US"
        assert len(doc.content_module_list) == 1
        assert doc.content_module_list[0].module_type == "STANDARD_TEXT"

    def test_build_module_from_json_unknown_type(self):
        with pytest.raises(ValueError, match="Unsupported moduleType"):
            build_module_from_json({"moduleType": "UNKNOWN"})

    def test_build_module_from_json_uses_content_module_type(self):
        data = {"contentModuleType": "STANDARD_TEXT", "headline": "Hello"}
        mod = build_module_from_json(data)
        assert mod.module_type == "STANDARD_TEXT"

    def test_build_module_company_logo(self):
        data = {
            "contentModuleType": "STANDARD_COMPANY_LOGO",
            "imageId": "logo-123",
            "altText": "Company Logo",
            "imageCropSpecification": {
                "size": {
                    "width": {"value": 600, "units": "pixels"},
                    "height": {"value": 180, "units": "pixels"},
                },
                "offset": {
                    "x": {"value": 0, "units": "pixels"},
                    "y": {"value": 0, "units": "pixels"},
                },
            },
        }
        mod = build_module_from_json(data)
        assert mod.module_type == "STANDARD_COMPANY_LOGO"
        result = mod.to_dict()
        assert result["standardCompanyLogo"]["companyLogo"]["uploadDestinationId"] == "logo-123"
        assert result["standardCompanyLogo"]["companyLogo"]["altText"] == "Company Logo"
        assert result["standardCompanyLogo"]["companyLogo"]["imageCropSpecification"]["size"]["width"]["value"] == 600

    def test_standard_company_logo_module_to_dict_empty(self):
        mod = StandardCompanyLogoModule()
        assert mod.to_dict() == {}

    def test_build_module_image_text(self):
        data = {
            "moduleType": "STANDARD_IMAGE_TEXT",
            "headline": "H",
            "body": "B",
            "imageId": "img-1",
        }
        mod = build_module_from_json(data)
        assert mod.module_type == "STANDARD_IMAGE_TEXT"
        result = mod.to_dict()
        assert result["standardImageText"]["headline"]["value"] == "H"
        assert result["standardImageText"]["image"]["uploadDestinationId"] == "img-1"

    def test_build_module_comparison_table(self):
        data = {
            "moduleType": "STANDARD_COMPARISON_TABLE",
            "headline": "Compare",
            "rows": [{"name": "Feature", "values": ["a", "b", "c"]}],
        }
        mod = build_module_from_json(data)
        assert mod.module_type == "STANDARD_COMPARISON_TABLE"
        result = mod.to_dict()
        assert result["standardComparisonTable"]["headline"]["value"] == "Compare"
        assert result["standardComparisonTable"]["comparisonTableRows"][0]["name"] == "Feature"

    def test_integration_full_document_from_json(self):
        data = {
            "modules": [
                {
                    "moduleType": "STANDARD_COMPANY_LOGO",
                    "imageId": "aplus-media/sc/76a7fb65-607b-4e96-a3fa-a145d1397725.jpg",
                    "altText": "Pawified Logo",
                    "imageCropSpecification": {
                        "size": {
                            "width": {"value": 600, "units": "pixels"},
                            "height": {"value": 180, "units": "pixels"},
                        },
                        "offset": {
                            "x": {"value": 0, "units": "pixels"},
                            "y": {"value": 0, "units": "pixels"},
                        },
                    },
                },
                {
                    "moduleType": "STANDARD_IMAGE_TEXT",
                    "headline": "Pure Joy in Every Bite",
                    "body": "Treat your feline friend to the finest premium catnip...",
                    "imageId": "aplus-media/sc/77967e76-a03c-4514-85e1-371e7f2395d1.jpg",
                },
                {
                    "moduleType": "STANDARD_IMAGE_TEXT",
                    "headline": "100% Natural & Safe",
                    "body": "Made in the USA with all-natural...",
                    "imageId": "aplus-media/sc/215948ec-b306-4a0b-8491-f1342dc83f91.jpg",
                },
                {
                    "moduleType": "STANDARD_IMAGE_TEXT",
                    "headline": "Perfect for Playtime",
                    "body": "Each 2-pack includes convenient 5g sachets...",
                    "imageId": "aplus-media/sc/2e6493d5-e7a4-4c3a-8e47-a78e5f5b4802.jpg",
                },
                {
                    "moduleType": "STANDARD_IMAGE_TEXT",
                    "headline": "Premium Quality You Can Trust",
                    "body": "Pawified is committed to delivering premium pet products...",
                    "imageId": "aplus-media/sc/ef864286-0fec-4472-ad20-8b7dfee4922e.jpg",
                },
            ]
        }
        doc = build_content_from_json("pawified-catnip", data)
        assert doc.name == "pawified-catnip"
        assert len(doc.content_module_list) == 5
        assert doc.content_module_list[0].module_type == "STANDARD_COMPANY_LOGO"
        assert doc.content_module_list[1].module_type == "STANDARD_IMAGE_TEXT"

        result = doc.to_dict()
        modules = result["contentModuleList"]
        assert len(modules) == 5

        logo_module = modules[0]["standardCompanyLogo"]
        assert "image" not in logo_module["companyLogo"]
        assert (
            logo_module["companyLogo"]["uploadDestinationId"]
            == "aplus-media/sc/76a7fb65-607b-4e96-a3fa-a145d1397725.jpg"
        )
        assert logo_module["companyLogo"]["altText"] == "Pawified Logo"
        assert logo_module["companyLogo"]["imageCropSpecification"]["size"]["width"]["value"] == 600

        for i in range(1, 5):
            mod = modules[i]["standardImageText"]
            assert "headline" in mod
            assert "body" in mod
            assert "image" in mod
            assert mod["image"]["uploadDestinationId"].startswith("aplus-media/sc/")


class TestAPlusCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_create_dry_run(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        with runner.isolated_filesystem():
            with open("content.json", "w") as f:
                json.dump(
                    {
                        "locale": "en_US",
                        "modules": [{"moduleType": "STANDARD_TEXT", "headline": "H"}],
                    },
                    f,
                )

            result = runner.invoke(cli, ["a-plus", "create", "test-doc", "--data", "content.json", "--dry-run"])

        assert result.exit_code == 0
        assert "Content is valid" in result.output
        mock_client.create_a_plus_content.assert_not_called()

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_create(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.create_a_plus_content.return_value = {}
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        with runner.isolated_filesystem():
            with open("content.json", "w") as f:
                json.dump(
                    {
                        "locale": "en_US",
                        "modules": [{"moduleType": "STANDARD_TEXT", "headline": "H"}],
                    },
                    f,
                )

            result = runner.invoke(cli, ["a-plus", "create", "test-doc", "--data", "content.json"])

        assert result.exit_code == 0
        assert "A+ Content created" in result.output
        mock_client.create_a_plus_content.assert_called_once()

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_validate(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.validate_a_plus_content.return_value = {}
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        with runner.isolated_filesystem():
            with open("content.json", "w") as f:
                json.dump(
                    {
                        "locale": "en_US",
                        "modules": [{"moduleType": "STANDARD_TEXT", "headline": "H"}],
                    },
                    f,
                )

            result = runner.invoke(cli, ["a-plus", "validate", "test-doc", "--data", "content.json"])

        assert result.exit_code == 0
        assert "API validation passed" in result.output
        mock_client.validate_a_plus_content.assert_called_once()

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_validate_fails_local(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        with runner.isolated_filesystem():
            with open("content.json", "w") as f:
                json.dump({"locale": "en_US", "modules": []}, f)

            result = runner.invoke(cli, ["a-plus", "validate", "test-doc", "--data", "content.json"])

        assert result.exit_code != 0
        mock_client.validate_a_plus_content.assert_not_called()

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_get(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.get_a_plus_content.return_value = {"contentRecord": {"contentDocument": {"name": "test-doc"}}}
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["a-plus", "get", "abc123"])

        assert result.exit_code == 0
        assert "test-doc" in result.output
        mock_client.get_a_plus_content.assert_called_once_with("abc123")

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_list(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.marketplace_id = "ATVPDKIKX0DER"
        mock_client.list_a_plus_content.return_value = {
            "contentDocumentList": [{"name": "doc1", "status": "APPROVED", "locale": "en_US"}]
        }
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["a-plus", "list"])

        assert result.exit_code == 0
        assert "doc1" in result.output
        mock_client.list_a_plus_content.assert_called_once_with(marketplaceId="ATVPDKIKX0DER")

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_update(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.update_a_plus_content.return_value = {}
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        with runner.isolated_filesystem():
            with open("content.json", "w") as f:
                json.dump(
                    {
                        "locale": "en_US",
                        "modules": [{"moduleType": "STANDARD_TEXT", "headline": "H"}],
                    },
                    f,
                )

            result = runner.invoke(cli, ["a-plus", "update", "test-doc", "--data", "content.json"])

        assert result.exit_code == 0
        assert "A+ Content updated" in result.output
        mock_client.update_a_plus_content.assert_called_once()

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_suspend(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["a-plus", "suspend", "test-doc"], input="y\n")

        assert result.exit_code == 0
        mock_client.suspend_a_plus_content.assert_called_once_with("test-doc")

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_asin_add(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.post_a_plus_content_asin_relations.return_value = {}
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["a-plus", "asin", "add", "test-doc", "B123", "B456"])

        assert result.exit_code == 0
        mock_client.post_a_plus_content_asin_relations.assert_called_once_with("test-doc", ["B123", "B456"])

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_asin_remove(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.delete_a_plus_content_asin_relations.return_value = {}
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["a-plus", "asin", "remove", "test-doc", "B123"])

        assert result.exit_code == 0
        mock_client.delete_a_plus_content_asin_relations.assert_called_once_with("test-doc", ["B123"])

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_asin_list(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.get_a_plus_content_asin_relations.return_value = {"asinSet": ["B123", "B456"]}
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["a-plus", "asin", "list", "test-doc"])

        assert result.exit_code == 0
        assert "B123" in result.output
        mock_client.get_a_plus_content_asin_relations.assert_called_once_with("test-doc")

    @patch("amazon_sp_cli.commands.a_plus.requests.post")
    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_upload_image(self, mock_client_class, mock_auth_class, mock_post, runner):
        mock_client = Mock()
        mock_client.marketplace_id = "ATVPDKIKX0DER"
        mock_client.create_upload_destination.return_value = {
            "payload": {
                "uploadDestinationId": "upload-123",
                "url": (
                    "https://aplus-media.s3.amazonaws.com/"
                    "?x-amz-date=20251003T113949Z"
                    "&x-amz-signature=sig"
                    "&acl=private"
                    "&key=sc/image.jpg"
                    "&x-amz-algorithm=AWS4-HMAC-SHA256"
                    "&policy=pol"
                    "&x-amz-credential=cred"
                ),
            }
        }
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        mock_post.return_value = Mock()
        mock_post.return_value.raise_for_status = Mock()

        with runner.isolated_filesystem():
            with open("test-image.jpg", "wb") as f:
                f.write(b"fake-image-data")

            result = runner.invoke(cli, ["a-plus", "upload-image", "test-image.jpg"])

        assert result.exit_code == 0
        assert "upload-123" in result.output
        mock_client.create_upload_destination.assert_called_once()
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://aplus-media.s3.amazonaws.com/"
        assert call_args[1]["data"]["key"] == "sc/image.jpg"
        assert call_args[1]["data"]["acl"] == "private"
        assert "File" in call_args[1]["files"]
