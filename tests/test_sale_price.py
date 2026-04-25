"""Tests for sale-price command."""

import json
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from amazon_sp_cli.main import cli


class TestSalePrice:
    """Test sale-price command."""

    @pytest.fixture
    def mock_listing_response(self):
        """Mock listing response with price."""
        return {
            "summaries": [{"asin": "B09BBL8T4Z", "status": ["ACTIVE"]}],
            "attributes": {"list_price": [{"currency": "USD", "value": 29.99}]},
        }

    @pytest.fixture
    def runner(self):
        """Create Click test runner."""
        return CliRunner()

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
    def test_sale_price_percentage(self, mock_client_class, mock_auth_class, runner, mock_listing_response):
        """Test generating percentage sale price."""
        mock_client = Mock()
        mock_client.get_listing.return_value = mock_listing_response
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["sale-price", "TEST-SKU", "20"])

        assert result.exit_code == 0
        assert "20.0%" in result.output
        assert "$29.99" in result.output
        assert "$23.99" in result.output
        assert "feed_data" in result.output

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
    def test_sale_price_fixed(self, mock_client_class, mock_auth_class, runner, mock_listing_response):
        """Test generating fixed amount sale price."""
        mock_client = Mock()
        mock_client.get_listing.return_value = mock_listing_response
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["sale-price", "TEST-SKU", "5", "--type", "fixed"])

        assert result.exit_code == 0
        assert "$5" in result.output
        assert "$24.99" in result.output

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
    def test_sale_price_with_dates(self, mock_client_class, mock_auth_class, runner, mock_listing_response):
        """Test generating sale price with custom dates."""
        mock_client = Mock()
        mock_client.get_listing.return_value = mock_listing_response
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli,
            [
                "sale-price",
                "TEST-SKU",
                "15",
                "--start-date",
                "2026-05-01",
                "--end-date",
                "2026-06-01",
            ],
        )

        assert result.exit_code == 0
        assert "2026-05-01" in result.output
        assert "2026-06-01" in result.output

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
    def test_sale_price_output_file(self, mock_client_class, mock_auth_class, runner, mock_listing_response):
        """Test saving sale price data to file."""
        mock_client = Mock()
        mock_client.get_listing.return_value = mock_listing_response
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["sale-price", "TEST-SKU", "10", "-o", "sale-price.json"])

            assert result.exit_code == 0
            assert "saved to" in result.output

            # Verify file was created
            with open("sale-price.json") as f:
                data = json.load(f)
                assert data["sku"] == "TEST-SKU"
                assert data["pricing"]["discount_display"] == "10.0%"

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
    def test_sale_price_no_price(self, mock_client_class, mock_auth_class, runner):
        """Test error when listing has no price."""
        mock_client = Mock()
        mock_client.get_listing.return_value = {
            "summaries": [{"asin": "B09BBL8T4Z"}],
            "attributes": {},
        }
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["sale-price", "TEST-SKU", "20"])

        assert result.exit_code != 0
        assert "Error" in result.output
