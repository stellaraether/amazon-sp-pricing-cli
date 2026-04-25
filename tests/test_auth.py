"""Tests for SP-API authentication."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from amazon_sp_cli.auth import SPAPIAuth


class TestSPAPIAuth:
    """Test SPAPIAuth class."""

    @pytest.fixture
    def temp_credentials(self):
        """Create temporary credentials file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(
                """
default:
  refresh_token: "test-refresh-token"
  client_id: "test-client-id"
  client_secret: "test-client-secret"
"""
            )
            path = f.name
        yield path
        os.unlink(path)

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = Path(tmpdir) / "token-cache.json"
            with patch.object(SPAPIAuth, "CACHE_FILE", cache_file):
                yield cache_file

    def test_load_credentials(self, temp_credentials):
        """Test credentials loading."""
        auth = SPAPIAuth(temp_credentials)
        assert auth.credentials["refresh_token"] == "test-refresh-token"
        assert auth.credentials["client_id"] == "test-client-id"
        assert auth.credentials["client_secret"] == "test-client-secret"

    def test_token_valid(self, temp_credentials, temp_cache_dir):
        """Test token validation."""
        auth = SPAPIAuth(temp_credentials)

        # Valid token
        valid_cache = {
            "access_token": "valid-token",
            "expires_at": 9999999999,
        }
        assert auth._is_token_valid(valid_cache) is True

        # Expired token
        expired_cache = {
            "access_token": "expired-token",
            "expires_at": 0,
        }
        assert auth._is_token_valid(expired_cache) is False

        # No token
        empty_cache = {"access_token": None}
        assert auth._is_token_valid(empty_cache) is False

    @patch("amazon_sp_cli.auth.requests.post")
    def test_exchange_token(self, mock_post, temp_credentials, temp_cache_dir):
        """Test token exchange."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new-access-token",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        auth = SPAPIAuth(temp_credentials)
        cache = auth._exchange_token()

        assert cache["access_token"] == "new-access-token"
        assert cache["expires_at"] > 0

    @patch("amazon_sp_cli.auth.requests.post")
    def test_get_access_token_cached(self, mock_post, temp_credentials, temp_cache_dir):
        """Test getting cached access token."""
        auth = SPAPIAuth(temp_credentials)

        # Pre-populate cache with valid token
        cache = {
            "access_token": "cached-token",
            "expires_at": 9999999999,
        }
        auth._save_cache(cache)

        token = auth.get_access_token()
        assert token == "cached-token"
        mock_post.assert_not_called()

    def test_invalidate(self, temp_credentials, temp_cache_dir):
        """Test token invalidation."""
        auth = SPAPIAuth(temp_credentials)

        # Pre-populate cache
        cache = {
            "access_token": "token",
            "expires_at": 9999999999,
        }
        auth._save_cache(cache)

        auth.invalidate()

        new_cache = auth._load_cache()
        assert new_cache["access_token"] is None
        assert new_cache["expires_at"] == 0
