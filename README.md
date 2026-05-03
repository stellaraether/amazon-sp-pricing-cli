# Amazon SP-API CLI

Command line interface for Amazon Selling Partner API (SP-API) operations.

## Features

- **Pricing Management** — Get/set prices, create discounts
- **Listing Operations** — View and update listings
- **Catalog Lookup** — Check competitor ASINs
- **Inventory Checks** — View FBA inventory levels
- **Feed Submissions** — Bulk updates via feeds API
- **A+ Content** — Manage A+ Content documents and image uploads (requires Brand Registry)

## Installation

```bash
pip install amazon-sp-cli
```

## Setup

Create credentials file at `~/.config/amazon-sp-cli/credentials.yml`:

```yaml
version: '1.0'

default:
  refresh_token: "your-refresh-token"
  client_id: "your-client-id"
  client_secret: "your-client-secret"
  aws_access_key_id: "your-aws-access-key"
  aws_secret_access_key: "your-aws-secret-key"
  seller_id: "your-seller-id"
  marketplace_id: "ATVPDKIKX0DER"  # US marketplace
```

## Usage

### Pricing

```bash
# Get current price
amz-sp get-price PAW2603190101-BLU

# Set new price
amz-sp set-price PAW2603190101-BLU 11.99

# Create sale price feed JSON
amz-sp sale-price PAW2603190101-BLU 23

# Create discount feed JSON (legacy)
amz-sp create-discount PAW2603190101-BLU 23
```

### Catalog

```bash
# Check competitor
amz-sp check-competitors B0GW72JGWK
```

### A+ Content

Requires Brand Registry.

```bash
# Upload an image (returns uploadDestinationId)
amz-sp a-plus upload-image banner.jpg

# Create content from JSON
amz-sp a-plus create my-content --data content.json

# Validate without creating
amz-sp a-plus validate my-content --data content.json

# Get content details (includes approval status)
amz-sp a-plus get my-content

# List all content documents
amz-sp a-plus list

# Update content
amz-sp a-plus update my-content --data content.json

# Delete content
amz-sp a-plus delete my-content

# Associate ASINs
amz-sp a-plus asin add my-content B123456789 B987654321

# List associated ASINs
amz-sp a-plus asin list my-content

# Remove ASIN associations
amz-sp a-plus asin remove my-content B123456789
```

## Development

```bash
# Clone repo
git clone https://github.com/stellaraether/amazon-sp-cli.git
cd amazon-sp-cli

# One-shot setup (creates venv, installs deps, sets up pre-commit)
./setup.sh
source .venv/bin/activate

# Or manually
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install

# Run locally
python3 -m amazon_sp_cli get-price PAW2603190101-BLU
```

## Releasing

This repository uses automated releases. To publish a new version:

1. Open a **standalone PR** that only bumps `__version__` in `amazon_sp_cli/__init__.py`.
2. The PR must not include code, test, or documentation changes — a CI check enforces this.
3. Once the PR is merged to `main`, the `Auto Release` workflow runs the full test suite, creates a tag (e.g. `v0.2.1`), creates a GitHub release, and publishes to PyPI.

Do not create tags manually.

## Requirements

- Python 3.8+
- Amazon SP-API credentials
- AWS IAM user with SP-API access

## License

MIT
