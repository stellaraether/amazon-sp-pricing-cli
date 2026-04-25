"""Tests for SP-API client."""

from unittest.mock import Mock, patch

import pytest

from amazon_sp_cli.auth import SPAPIAuth
from amazon_sp_cli.client import SPAPIClient


class TestSPAPIClient:
    """Test SPAPIClient class."""

    @pytest.fixture
    def mock_auth(self):
        """Create mock auth object."""
        auth = Mock(spec=SPAPIAuth)
        auth.credentials = {
            "aws_access_key_id": "test-aws-key",
            "aws_secret_access_key": "test-aws-secret",
            "seller_id": "TESTSELLER",
            "marketplace_id": "ATVPDKIKX0DER",
        }
        auth.get_access_token.return_value = "test-access-token"
        return auth

    @pytest.fixture
    def client(self, mock_auth):
        """Create SPAPIClient instance."""
        return SPAPIClient(mock_auth)

    def test_init(self, client, mock_auth):
        """Test client initialization."""
        assert client.auth == mock_auth
        assert client.seller_id == "TESTSELLER"
        assert client.marketplace_id == "ATVPDKIKX0DER"

    def test_get_listing_path(self, client):
        """Test listing path construction."""
        path = f"/listings/2021-08-01/items/{client.seller_id}/TEST-SKU"
        assert "TESTSELLER" in path
        assert "TEST-SKU" in path

    @patch("amazon_sp_cli.client.requests.request")
    @patch("amazon_sp_cli.client.SigV4Auth")
    def test_request(self, mock_signer_class, mock_request, client):
        """Test API request."""
        mock_response = Mock()
        mock_response.json.return_value = {"test": "data"}
        mock_response.text = '{"test": "data"}'
        mock_request.return_value = mock_response

        mock_signer = Mock()
        mock_signer_class.return_value = mock_signer

        result = client.request("GET", "/test/path")

        assert result == {"test": "data"}
        mock_request.assert_called_once()
