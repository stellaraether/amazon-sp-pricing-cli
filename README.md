# Amazon SP-API CLI

Command line interface for Amazon Selling Partner API (SP-API) operations.

## Features

- **Pricing Management** — Get/set prices, create discounts
- **Listing Operations** — View and update listings
- **Catalog Lookup** — Check competitor ASINs
- **Inventory Checks** — View FBA inventory levels
- **Feed Submissions** — Bulk updates via feeds API

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
amz-sp pricing get PAW2603190101-BLU

# Set new price
amz-sp pricing set PAW2603190101-BLU 11.99

# Create discount feed
amz-sp pricing discount PAW2603190101-BLU 23
```

### Listings

```bash
# Get listing details
amz-sp listings get PAW2603190101-BLU

# Update listing
amz-sp listings update PAW2603190101-BLU --data '{...}'
```

### Catalog

```bash
# Check competitor
amz-sp catalog get B0GW72JGWK
```

### Inventory

```bash
# Get FBA inventory
amz-sp inventory list

# Get specific SKU
amz-sp inventory get PAW2603190101-BLU
```

## Development

```bash
# Clone repo
git clone https://github.com/stellaraether/amazon-sp-cli.git
cd amazon-sp-cli

# Install in editable mode
pip install -e .

# Run locally
python3 -m amazon_sp_cli.main pricing get PAW2603190101-BLU
```

## Requirements

- Python 3.8+
- Amazon SP-API credentials
- AWS IAM user with SP-API access

## License

MIT
