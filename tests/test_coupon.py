"""Tests for coupon command."""

import json
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from amazon_sp_cli.main import cli


class TestCreateCoupon:
    """Test create-coupon command."""

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
    def test_create_coupon_percentage(self, mock_client_class, mock_auth_class, runner, mock_listing_response):
        """Test creating a percentage coupon."""
        mock_client = Mock()
        mock_client.get_listing.return_value = mock_listing_response
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["create-coupon", "TEST-SKU", "20"])

        assert result.exit_code == 0
        assert "20.0%" in result.output
        assert "$29.99" in result.output
        assert "$23.99" in result.output  # 20% off
        assert "Seller Central" in result.output

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
    def test_create_coupon_fixed(self, mock_client_class, mock_auth_class, runner, mock_listing_response):
        """Test creating a fixed amount coupon."""
        mock_client = Mock()
        mock_client.get_listing.return_value = mock_listing_response
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["create-coupon", "TEST-SKU", "5", "--type", "fixed"])

        assert result.exit_code == 0
        assert "$5" in result.output
        assert "$24.99" in result.output  # $29.99 - $5

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
    def test_create_coupon_with_options(self, mock_client_class, mock_auth_class, runner, mock_listing_response):
        """Test creating coupon with all options."""
        mock_client = Mock()
        mock_client.get_listing.return_value = mock_listing_response
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli,
            [
                "create-coupon",
                "TEST-SKU",
                "15",
                "--prime-only",
                "--budget",
                "1000",
                "--start-date",
                "2026-05-01",
                "--end-date",
                "2026-06-01",
            ],
        )

        assert result.exit_code == 0
        assert "Prime Only: Yes" in result.output
        assert "$1000" in result.output
        assert "2026-05-01" in result.output
        assert "2026-06-01" in result.output

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
    def test_create_coupon_output_file(self, mock_client_class, mock_auth_class, runner, mock_listing_response):
        """Test saving coupon to file."""
        mock_client = Mock()
        mock_client.get_listing.return_value = mock_listing_response
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["create-coupon", "TEST-SKU", "10", "-o", "coupon.json"])

            assert result.exit_code == 0
            assert "saved to" in result.output

            # Verify file was created
            with open("coupon.json") as f:
                data = json.load(f)
                assert data["coupon_specification"]["sku"] == "TEST-SKU"
                assert data["coupon_specification"]["coupon_type"] == "percentage"

    @patch("amazon_sp_cli.main.SPAPIAuth")
    @patch("amazon_sp_cli.main.SPAPIClient")
    def test_create_coupon_no_price(self, mock_client_class, mock_auth_class, runner):
        """Test error when listing has no price."""
        mock_client = Mock()
        mock_client.get_listing.return_value = {
            "summaries": [{"asin": "B09BBL8T4Z"}],
            "attributes": {},
        }
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["create-coupon", "TEST-SKU", "20"])

        assert result.exit_code != 0
        assert "Error" in result.output
