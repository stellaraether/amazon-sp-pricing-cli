# Amazon SP-API Pricing CLI

Command line interface for Amazon Selling Partner API pricing and discount management.

## Installation

```bash
pip install amazon-sp-pricing-cli
```

## Setup

Create credentials file at `~/.config/amazon-sp-pricing/credentials.yml`:

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

### Get Current Price

```bash
# Get price for a SKU
amz-pricing get-price PAW2603190101-BLU
```

### Set Price

```bash
# Update price for a SKU
amz-pricing set-price PAW2603190101-BLU 11.99
```

### Create Discount

```bash
# Generate discount feed (23% off)
amz-pricing create-discount PAW2603190101-BLU 23

# Apply discount to all variations
amz-pricing create-discount --all-variations PAW2603190101 23
```

### Check Competitors

```bash
# Check competitor pricing for an ASIN
amz-pricing check-competitors B0GW72JGWK
```

### Bulk Operations

```bash
# Apply discount to multiple SKUs
amz-pricing bulk-discount --file skus.txt --percent 20

# Export pricing report
amz-pricing export --format csv > pricing-report.csv
```

## Development

```bash
# Clone repo
git clone https://github.com/stellaraether/amazon-sp-pricing-cli.git
cd amazon-sp-pricing-cli

# Install in editable mode
pip install -e .

# Run locally
python3 -m amazon_sp_pricing_cli.main get-price PAW2603190101-BLU
```

## Requirements

- Python 3.8+
- Amazon SP-API credentials
- AWS IAM user with SP-API access

## License

MIT
