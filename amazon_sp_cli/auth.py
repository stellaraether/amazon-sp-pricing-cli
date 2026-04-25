"""Amazon SP-API authentication handler."""

import json
import os
import time
from pathlib import Path

import requests
import yaml


class SPAPIAuth:
    """Handles SP-API token refresh and caching."""

    TOKEN_ENDPOINT = "https://api.amazon.com/auth/o2/token"
    CACHE_FILE = Path.home() / ".config" / "amazon-sp-cli" / "token-cache.json"
    BUFFER_SECONDS = 60

    def __init__(self, credentials_path: str = None):
        self.credentials = self._load_credentials(credentials_path)
        self._ensure_cache_dir()

    def _load_credentials(self, path: str = None) -> dict:
        """Load credentials from YAML file."""
        if path is None:
            path = Path.home() / ".config" / "amazon-sp-cli" / "credentials.yml"

        with open(path, "r") as f:
            config = yaml.safe_load(f)

        return config.get("default", config)

    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    def _load_cache(self) -> dict:
        """Load token cache from disk."""
        if self.CACHE_FILE.exists():
            with open(self.CACHE_FILE, "r") as f:
                return json.load(f)
        return {
            "access_token": None,
            "expires_at": 0,
            "refreshed_at": None,
        }

    def _save_cache(self, cache: dict):
        """Save token cache to disk."""
        with open(self.CACHE_FILE, "w") as f:
            json.dump(cache, f)
        os.chmod(self.CACHE_FILE, 0o600)

    def _is_token_valid(self, cache: dict) -> bool:
        """Check if cached token is still valid."""
        if cache.get("access_token") is None:
            return False
        now = time.time()
        return now < cache.get("expires_at", 0) - self.BUFFER_SECONDS

    def _exchange_token(self) -> dict:
        """Exchange refresh token for access token."""
        response = requests.post(
            self.TOKEN_ENDPOINT,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.credentials["refresh_token"],
                "client_id": self.credentials["client_id"],
                "client_secret": self.credentials["client_secret"],
            },
        )
        response.raise_for_status()
        data = response.json()

        now = time.time()
        return {
            "access_token": data["access_token"],
            "expires_at": now + data["expires_in"],
            "refreshed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        cache = self._load_cache()

        # Fast path: valid cached token
        if self._is_token_valid(cache):
            return cache["access_token"]

        # Slow path: refresh token
        new_cache = self._exchange_token()
        self._save_cache(new_cache)
        return new_cache["access_token"]

    def invalidate(self):
        """Invalidate cached token."""
        self._save_cache(
            {
                "access_token": None,
                "expires_at": 0,
                "refreshed_at": None,
            }
        )
        print("Token cache invalidated.")
