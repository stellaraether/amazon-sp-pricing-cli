"""Amazon SP-API client with AWS SigV4 signing."""

import json
from urllib.parse import urlencode

import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials


class SPAPIError(Exception):
    """Raised when SP-API returns an error response."""

    def __init__(self, message, response_body=None):
        super().__init__(message)
        self.response_body = response_body


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
        body = json.dumps(data) if data is not None else ""

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
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            try:
                error_body = response.json()
            except ValueError:
                error_body = None
            raise SPAPIError(
                _format_spapi_error(response.status_code, error_body or response.text),
                response_body=error_body,
            ) from exc

        return response.json() if response.text else {}

    def get_listing(self, sku: str) -> dict:
        """Get listing information for a SKU."""
        path = f"/listings/2021-08-01/items/{self.seller_id}/{sku}"
        params = {
            "marketplaceIds": self.marketplace_id,
            "includedData": "summaries,attributes,issues,offers,fulfillmentAvailability",
        }
        path += "?" + urlencode(params)
        return self.request("GET", path)

    def put_listing(
        self, sku: str, product_type: str, attributes: dict, requirements: str = None, mode: str = None
    ) -> dict:
        """Create or fully replace a listing for a SKU."""
        path = f"/listings/2021-08-01/items/{self.seller_id}/{sku}"
        params = {
            "marketplaceIds": self.marketplace_id,
        }
        if mode:
            params["mode"] = mode
        path += "?" + urlencode(params)

        data = {
            "productType": product_type,
            "attributes": attributes,
        }
        if requirements:
            data["requirements"] = requirements

        return self.request("PUT", path, data)

    def delete_listing(self, sku: str) -> dict:
        """Delete a listing for a SKU."""
        path = f"/listings/2021-08-01/items/{self.seller_id}/{sku}"
        params = {
            "marketplaceIds": self.marketplace_id,
        }
        path += "?" + urlencode(params)
        return self.request("DELETE", path)

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

    # --- A+ Content API ---

    def _add_marketplace_param(self, path: str) -> str:
        """Append marketplaceId query param to A+ Content paths."""
        separator = "&" if "?" in path else "?"
        return f"{path}{separator}marketplaceId={self.marketplace_id}"

    def create_a_plus_content(self, content_data: dict) -> dict:
        """Create A+ Content document."""
        path = self._add_marketplace_param("/aplus/2020-11-01/contentDocuments")
        data = {"contentDocument": content_data}
        return self.request("POST", path, data)

    def validate_a_plus_content(self, content_data: dict) -> dict:
        """Validate A+ Content without creating."""
        path = "/aplus/2020-11-01/contentDocuments"
        params = {"mode": "VALIDATION_PREVIEW", "marketplaceId": self.marketplace_id}
        path += "?" + urlencode(params)
        data = {"contentDocument": content_data}
        return self.request("POST", path, data)

    def update_a_plus_content(self, content_name: str, content_data: dict) -> dict:
        """Update existing A+ Content document."""
        path = self._add_marketplace_param(f"/aplus/2020-11-01/contentDocuments/{content_name}")
        data = {"contentDocument": content_data}
        return self.request("POST", path, data)

    def get_a_plus_content(self, content_name: str) -> dict:
        """Get A+ Content document by name."""
        path = f"/aplus/2020-11-01/contentDocuments/{content_name}"
        params = {"marketplaceId": self.marketplace_id, "includedDataSet": "CONTENTS"}
        path += "?" + urlencode(params)
        return self.request("GET", path)

    def list_a_plus_content(self, **filters) -> dict:
        """List A+ Content documents."""
        path = "/aplus/2020-11-01/contentDocuments"
        params = {"marketplaceId": self.marketplace_id}
        params.update(filters)
        path += "?" + urlencode(params)
        return self.request("GET", path)

    def suspend_a_plus_content(self, content_reference_key: str) -> dict:
        """Suspend A+ Content document (API does not support delete)."""
        path = f"/aplus/2020-11-01/contentDocuments/{content_reference_key}/suspendSubmissions"
        params = {"marketplaceId": self.marketplace_id}
        path += "?" + urlencode(params)
        return self.request("POST", path)

    def get_a_plus_content_asin_relations(self, content_name: str) -> dict:
        """Get ASIN relations for a content document."""
        path = self._add_marketplace_param(f"/aplus/2020-11-01/contentDocuments/{content_name}/asins")
        return self.request("GET", path)

    def post_a_plus_content_asin_relations(self, content_name: str, asin_set: list) -> dict:
        """Associate ASINs with A+ Content document."""
        path = self._add_marketplace_param("/aplus/2020-11-01/contentAsinRelations")
        data = {"contentDocumentName": content_name, "asinSet": asin_set}
        return self.request("POST", path, data)

    def delete_a_plus_content_asin_relations(self, content_name: str, asin_set: list) -> dict:
        """Remove ASIN associations from A+ Content document."""
        path = "/aplus/2020-11-01/contentAsinRelations"
        params = {"contentDocumentName": content_name, "marketplaceId": self.marketplace_id}
        path += "?" + urlencode(params)
        data = {"asinSet": asin_set}
        return self.request("DELETE", path, data)

    def create_upload_destination(
        self,
        marketplace_id: str,
        content_md5: str,
        content_type: str,
        file_name: str = None,
        resource: str = None,
    ) -> dict:
        """Create an upload destination for a file."""
        path = f"/uploads/2020-11-01/uploadDestinations/{resource}"
        params = {
            "marketplaceIds": marketplace_id,
            "contentMD5": content_md5,
            "contentType": content_type,
        }
        if file_name:
            params["fileName"] = file_name
        path += "?" + urlencode(params)
        return self.request("POST", path)


def _format_spapi_error(status_code, body):
    """Format an SP-API error into a human-readable string."""
    if isinstance(body, dict):
        parts = [f"SP-API returned {status_code}"]
        for error in body.get("errors", []):
            code = error.get("code", "Unknown")
            message = error.get("message", "")
            parts.append(f"  [{code}] {message}")
        for issue in body.get("issues", []):
            code = issue.get("code", "Unknown")
            message = issue.get("message", "")
            severity = issue.get("severity", "")
            parts.append(f"  [{code}] ({severity}) {message}")
        if len(parts) == 1:
            parts.append(f"  {json.dumps(body)}")
        return "\n".join(parts)
    return f"SP-API returned {status_code}: {body}"
