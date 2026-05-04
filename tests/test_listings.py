"""Tests for listing commands."""

import json
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from amazon_sp_cli.main import cli


class TestGetListing:
    """Test get-listing command."""

    @pytest.fixture
    def mock_listing_response(self):
        """Mock full listing response."""
        return {
            "summaries": [{"asin": "B09BBL8T4Z", "status": ["ACTIVE"]}],
            "attributes": {
                "item_name": [{"value": "Test Product", "language_tag": "en_US"}],
                "list_price": [{"currency": "USD", "value": 29.99}],
            },
            "issues": [],
        }

    @pytest.fixture
    def runner(self):
        """Create Click test runner."""
        return CliRunner()

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_get_listing(self, mock_client_class, mock_auth_class, runner, mock_listing_response):
        """Test fetching a listing."""
        mock_client = Mock()
        mock_client.get_listing.return_value = mock_listing_response
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["get-listing", "TEST-SKU"])

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["summaries"][0]["asin"] == "B09BBL8T4Z"
        assert output["attributes"]["item_name"][0]["value"] == "Test Product"


class TestUpdateListing:
    """Test update-listing command."""

    @pytest.fixture
    def runner(self):
        """Create Click test runner."""
        return CliRunner()

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_update_listing_with_title(self, mock_client_class, mock_auth_class, runner):
        """Test updating a listing title."""
        mock_client = Mock()
        mock_client.put_listing.return_value = {"sku": "TEST-SKU", "status": "ACCEPTED"}
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli,
            [
                "update-listing",
                "TEST-SKU",
                "--product-type",
                "PET_TOY",
                "--title",
                "New Title",
            ],
        )

        assert result.exit_code == 0
        mock_client.put_listing.assert_called_once()
        call_args = mock_client.put_listing.call_args
        assert call_args.kwargs["product_type"] == "PET_TOY"
        assert call_args.kwargs["attributes"]["item_name"] == [{"value": "New Title", "language_tag": "en_US"}]

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_update_listing_with_multiple_flags(self, mock_client_class, mock_auth_class, runner):
        """Test updating multiple attributes at once."""
        mock_client = Mock()
        mock_client.put_listing.return_value = {"sku": "TEST-SKU", "status": "ACCEPTED"}
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli,
            [
                "update-listing",
                "TEST-SKU",
                "--product-type",
                "PET_TOY",
                "--title",
                "New Title",
                "--description",
                "New Description",
                "--bullet-point",
                "Point 1",
                "--bullet-point",
                "Point 2",
                "--price",
                "19.99",
                "--condition",
                "new_new",
                "--inventory",
                "100",
                "--shipping-template",
                "Std Template",
            ],
        )

        assert result.exit_code == 0
        attrs = mock_client.put_listing.call_args.kwargs["attributes"]
        assert attrs["item_name"] == [{"value": "New Title", "language_tag": "en_US"}]
        assert attrs["product_description"] == [{"value": "New Description", "language_tag": "en_US"}]
        assert attrs["bullet_point"] == [{"value": "Point 1"}, {"value": "Point 2"}]
        assert attrs["list_price"] == [{"currency": "USD", "value": 19.99}]
        assert attrs["purchasable_price"] == [{"currency": "USD", "value": 19.99}]
        assert attrs["condition_type"] == [{"value": "new_new"}]
        assert attrs["fulfillment_availability"] == [{"quantity": 100, "fulfillment_channel_code": "DEFAULT"}]
        assert attrs["merchant_shipping_group"] == [{"value": "Std Template"}]

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_update_listing_with_images(self, mock_client_class, mock_auth_class, runner):
        """Test updating images."""
        mock_client = Mock()
        mock_client.put_listing.return_value = {"sku": "TEST-SKU", "status": "ACCEPTED"}
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli,
            [
                "update-listing",
                "TEST-SKU",
                "--product-type",
                "PET_TOY",
                "--image",
                "https://example.com/main.jpg",
                "--image",
                "https://example.com/other1.jpg",
                "--image",
                "https://example.com/other2.jpg",
            ],
        )

        assert result.exit_code == 0
        attrs = mock_client.put_listing.call_args.kwargs["attributes"]
        assert attrs["main_product_image_locator"] == [{"media_location": "https://example.com/main.jpg"}]
        assert attrs["other_product_image_locator_1"] == [{"media_location": "https://example.com/other1.jpg"}]
        assert attrs["other_product_image_locator_2"] == [{"media_location": "https://example.com/other2.jpg"}]

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_update_listing_with_attributes_json(self, mock_client_class, mock_auth_class, runner):
        """Test updating with raw attributes JSON."""
        mock_client = Mock()
        mock_client.put_listing.return_value = {"sku": "TEST-SKU", "status": "ACCEPTED"}
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli,
            [
                "update-listing",
                "TEST-SKU",
                "--product-type",
                "PET_TOY",
                "--attributes-json",
                '{"item_name": [{"value": "JSON Title", "language_tag": "en_US"}]}',
            ],
        )

        assert result.exit_code == 0
        attrs = mock_client.put_listing.call_args.kwargs["attributes"]
        assert attrs["item_name"] == [{"value": "JSON Title", "language_tag": "en_US"}]

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_update_listing_flags_override_json(self, mock_client_class, mock_auth_class, runner):
        """Test that CLI flags override --attributes-json for same keys."""
        mock_client = Mock()
        mock_client.put_listing.return_value = {"sku": "TEST-SKU", "status": "ACCEPTED"}
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli,
            [
                "update-listing",
                "TEST-SKU",
                "--product-type",
                "PET_TOY",
                "--title",
                "Flag Title",
                "--attributes-json",
                '{"item_name": [{"value": "JSON Title", "language_tag": "en_US"}]}',
            ],
        )

        assert result.exit_code == 0
        attrs = mock_client.put_listing.call_args.kwargs["attributes"]
        # flags are built first, then attributes_json is merged on top
        assert attrs["item_name"] == [{"value": "JSON Title", "language_tag": "en_US"}]

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_update_listing_dry_run(self, mock_client_class, mock_auth_class, runner):
        """Test dry-run mode."""
        mock_client = Mock()
        mock_client.put_listing.return_value = {"sku": "TEST-SKU", "issues": []}
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli,
            [
                "update-listing",
                "TEST-SKU",
                "--product-type",
                "PET_TOY",
                "--title",
                "New Title",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert "Validation passed" in result.output
        assert mock_client.put_listing.call_args.kwargs["mode"] == "VALIDATION_PREVIEW"

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_update_listing_with_issues(self, mock_client_class, mock_auth_class, runner):
        """Test that ERROR issues cause failure."""
        mock_client = Mock()
        mock_client.put_listing.return_value = {
            "sku": "TEST-SKU",
            "issues": [
                {
                    "code": "99022",
                    "message": "Invalid attribute",
                    "severity": "ERROR",
                }
            ],
        }
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli,
            [
                "update-listing",
                "TEST-SKU",
                "--product-type",
                "PET_TOY",
                "--title",
                "New Title",
            ],
        )

        assert result.exit_code != 0
        assert "Validation issues found" in result.output

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_update_listing_no_attributes(self, mock_client_class, mock_auth_class, runner):
        """Test error when no attributes are provided."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli,
            [
                "update-listing",
                "TEST-SKU",
                "--product-type",
                "PET_TOY",
            ],
        )

        assert result.exit_code != 0
        assert "No attributes provided" in result.output

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_update_listing_invalid_json(self, mock_client_class, mock_auth_class, runner):
        """Test error with invalid attributes JSON."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli,
            [
                "update-listing",
                "TEST-SKU",
                "--product-type",
                "PET_TOY",
                "--attributes-json",
                "not json",
            ],
        )

        assert result.exit_code != 0
        assert "Invalid JSON" in result.output

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_update_listing_requirements_option(self, mock_client_class, mock_auth_class, runner):
        """Test requirements option is passed through."""
        mock_client = Mock()
        mock_client.put_listing.return_value = {"sku": "TEST-SKU", "status": "ACCEPTED"}
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli,
            [
                "update-listing",
                "TEST-SKU",
                "--product-type",
                "PET_TOY",
                "--requirements",
                "LISTING_OFFER_ONLY",
                "--price",
                "9.99",
            ],
        )

        assert result.exit_code == 0
        call_args = mock_client.put_listing.call_args
        assert call_args.kwargs["requirements"] == "LISTING_OFFER_ONLY"


class TestDeleteListing:
    """Test delete-listing command."""

    @pytest.fixture
    def runner(self):
        """Create Click test runner."""
        return CliRunner()

    @patch("amazon_sp_cli.cli.SPAPIAuth")
    @patch("amazon_sp_cli.cli.SPAPIClient")
    def test_delete_listing(self, mock_client_class, mock_auth_class, runner):
        """Test deleting a listing."""
        mock_client = Mock()
        mock_client.delete_listing.return_value = {"sku": "TEST-SKU", "status": "ACCEPTED"}
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["delete-listing", "TEST-SKU"])

        assert result.exit_code == 0
        mock_client.delete_listing.assert_called_once_with("TEST-SKU")
        output = json.loads(result.output)
        assert output["status"] == "ACCEPTED"
