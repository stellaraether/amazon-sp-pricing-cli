"""Amazon SP-API client with AWS SigV4 signing."""

import json
from urllib.parse import urlencode

import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
from botocore.session import Session


class SPAPIClient:
    """Client for making signed requests to Amazon SP-API."""

    HOST = "sellingpartnerapi-na.amazon.com"
    REGION = "us-east-1"
    SERVICE = "execute-api"

    def __init__(self, auth, aws_access_key: str = None, aws_secret_key: str = None):
        self.auth = auth
        self.credentials = auth.credentials
        self.aws_access_key = aws_access_key or self.credentials.get("aws_access_key_id")
        self.aws_secret_key = aws_secret_key or self.credentials.get("aws_secret_access_key")
        self.marketplace_id = self.credentials.get("marketplace_id", "ATVPDKIKX0DER")
        self.seller_id = self.credentials.get("seller_id")

    def _sign_request(self, method: str, path: str, data: dict = None) -> dict:
        """Create signed request headers."""
        access_token = self.auth.get_access_token()

        headers = {
            "x-amz-access-token": access_token,
            "accept": "application/json",
        }

        if data is not None:
            headers["content-type"] = "application/json"

        # Create the request
        url = f"https://{self.HOST}{path}"
        body = json.dumps(data) if data else ""

        # Create AWS request for signing
        request = AWSRequest(method=method, url=url, headers=headers, data=body)

        # Sign with SigV4
        credentials = Credentials(self.aws_access_key, self.aws_secret_key)
        signer = SigV4Auth(credentials, self.SERVICE, self.REGION)
        signer.add_auth(request)

        return dict(request.headers), request.url, body

    def request(self, method: str, path: str, data: dict = None) -> dict:
        """Make a signed request to SP-API."""
        headers, url, body = self._sign_request(method, path, data)

        response = requests.request(method, url, headers=headers, data=body)
        response.raise_for_status()

        return response.json() if response.text else {}

    def get_listing(self, sku: str) -> dict:
        """Get listing information for a SKU."""
        path = f"/listings/2021-08-01/items/{self.seller_id}/{sku}"
        params = {
            "marketplaceIds": self.marketplace_id,
            "includedData": "summaries,attributes",
        }
        path += "?" + urlencode(params)
        return self.request("GET", path)

    def update_price(self, sku: str, price: float, mode: str = "VALIDATION_PREVIEW") -> dict:
        """Update listing price."""
        path = f"/listings/2021-08-01/items/{self.seller_id}/{sku}"
        params = {
            "marketplaceIds": self.marketplace_id,
        }
        if mode:
            params["mode"] = mode
        path += "?" + urlencode(params)

        data = {
            "productType": "PET_TOY",
            "requirements": "LISTING_OFFER_ONLY",
            "attributes": {
                "condition_type": [{"value": "new_new"}],
                "item_name": [{"value": "Placeholder"}],
                "list_price": [{"currency": "USD", "value": price}],
                "purchasable_price": [{"currency": "USD", "value": price}],
            },
        }

        return self.request("PUT", path, data)

    def get_catalog_item(self, asin: str) -> dict:
        """Get catalog item details."""
        path = f"/catalog/2022-04-01/items/{asin}"
        params = {
            "marketplaceIds": self.marketplace_id,
            "includedData": "attributes,salesRanks",
        }
        path += "?" + urlencode(params)
        return self.request("GET", path)
