"""Tests for A+ Content module."""

import json
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from amazon_sp_cli.a_plus import (
    APlusContentDocument,
    ContentModule,
    StandardTextModule,
    TextComponent,
    build_content_from_json,
    build_module_from_json,
)
from amazon_sp_cli.main import cli


class TestDataModels:
    def test_text_component_to_dict(self):
        tc = TextComponent("Hello", "BOLD")
        assert tc.to_dict() == {"value": "Hello", "decoration": "BOLD"}

    def test_standard_text_module_to_dict(self):
        mod = StandardTextModule(
            headline=TextComponent("Headline"),
            body=TextComponent("Body text"),
        )
        result = mod.to_dict()
        assert result["headline"]["value"] == "Headline"
        assert result["body"]["value"] == "Body text"

    def test_content_module_wrapper(self):
        mod = ContentModule(
            module_type="STANDARD_TEXT",
            standard_text=StandardTextModule(
                headline=TextComponent("H"),
            ),
        )
        result = mod.to_dict()
        assert result["moduleType"] == "STANDARD_TEXT"
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
        assert "invalid moduleType" in doc.validate()[0]

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
            "locale": "en_US",
            "modules": [{"moduleType": "STANDARD_TEXT", "headline": "Hello", "body": "World"}],
        }
        doc = build_content_from_json("my-doc", data)
        assert doc.name == "my-doc"
        assert doc.locale == "en_US"
        assert len(doc.content_module_list) == 1
        assert doc.content_module_list[0].module_type == "STANDARD_TEXT"

    def test_build_module_from_json_unknown_type(self):
        with pytest.raises(ValueError, match="Unsupported moduleType"):
            build_module_from_json({"moduleType": "UNKNOWN"})

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


class TestAPlusCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
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

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
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

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
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

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
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

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
    def test_get(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.get_a_plus_content.return_value = {"name": "test-doc"}
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["a-plus", "get", "test-doc"])

        assert result.exit_code == 0
        assert "test-doc" in result.output
        mock_client.get_a_plus_content.assert_called_once_with("test-doc")

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
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

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
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

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
    def test_delete(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["a-plus", "delete", "test-doc"], input="y\n")

        assert result.exit_code == 0
        mock_client.delete_a_plus_content.assert_called_once_with("test-doc")

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
    def test_asin_add(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.post_a_plus_content_asin_relations.return_value = {}
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["a-plus", "asin", "add", "test-doc", "B123", "B456"])

        assert result.exit_code == 0
        mock_client.post_a_plus_content_asin_relations.assert_called_once_with("test-doc", ["B123", "B456"])

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
    def test_asin_remove(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.delete_a_plus_content_asin_relations.return_value = {}
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["a-plus", "asin", "remove", "test-doc", "B123"])

        assert result.exit_code == 0
        mock_client.delete_a_plus_content_asin_relations.assert_called_once_with("test-doc", ["B123"])

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
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

    @patch("amazon_sp_cli.a_plus.requests.put")
    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
    def test_upload_image(self, mock_client_class, mock_auth_class, mock_put, runner):
        mock_client = Mock()
        mock_client.marketplace_id = "ATVPDKIKX0DER"
        mock_client.create_upload_destination.return_value = {
            "uploadDestinationId": "upload-123",
            "url": "https://s3.amazonaws.com/presigned-url",
            "headers": [{"name": "Content-Type", "value": "image/jpeg"}],
        }
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        mock_put.return_value = Mock()
        mock_put.return_value.raise_for_status = Mock()

        with runner.isolated_filesystem():
            with open("test-image.jpg", "wb") as f:
                f.write(b"fake-image-data")

            result = runner.invoke(cli, ["a-plus", "upload-image", "test-image.jpg"])

        assert result.exit_code == 0
        assert "upload-123" in result.output
        mock_client.create_upload_destination.assert_called_once()
        mock_put.assert_called_once()
