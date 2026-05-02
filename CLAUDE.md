# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

Install in editable mode:
```bash
pip install -e .
```

Run locally without installing:
```bash
python3 -m amazon_sp_cli.main <command>
# or
python3 -m amazon_sp_cli <command>
```

Run the full test suite:
```bash
pytest
```

Run a single test file or test:
```bash
pytest tests/test_auth.py
pytest tests/test_sale_price.py::TestSalePrice::test_sale_price_percentage
```

Linting (must pass in CI):
```bash
black --check amazon_sp_cli/
isort --check-only --profile black amazon_sp_cli/
flake8 --max-line-length=120 amazon_sp_cli/
```

Auto-format:
```bash
black amazon_sp_cli/
isort --profile black amazon_sp_cli/
```

Run pre-commit hooks:
```bash
pre-commit run --all-files
```

Build package:
```bash
python -m build
twine check dist/*
```

## Architecture

This is a Python CLI for Amazon Selling Partner API (SP-API). It uses Click for the CLI, requests for HTTP, botocore for AWS SigV4 signing, and PyYAML for credentials.

### Entry Point

`amazon_sp_cli/main.py` defines a Click command group `cli`. The group callback instantiates `SPAPIAuth` and `SPAPIClient`, storing them in `ctx.obj` so every subcommand shares the same authenticated client. Two runnable modules exist: `__main__.py` (for `python -m amazon_sp_cli`) and `main.py`.

### Authentication (`amazon_sp_cli/auth.py`)

`SPAPIAuth` loads credentials from a YAML file (default `~/.config/amazon-sp-cli/credentials.yml`) and exchanges a refresh token for an access token via `https://api.amazon.com/auth/o2/token`. Tokens are cached in `~/.config/amazon-sp-cli/token-cache.json` with a 60-second expiry buffer. Call `invalidate()` to force a refresh.

### API Client (`amazon_sp_cli/client.py`)

`SPAPIClient` signs requests with AWS SigV4 using botocore's `SigV4Auth`. It targets `sellingpartnerapi-na.amazon.com` in `us-east-1`. Every request includes the `x-amz-access-token` header from `SPAPIAuth.get_access_token()`. Key methods:
- `get_listing(sku)` – GET `/listings/2021-08-01/items/{seller_id}/{sku}`
- `update_price(sku, price, mode)` – PUT to the same path with `LISTING_OFFER_ONLY` requirements
- `get_catalog_item(asin)` – GET `/catalog/2022-04-01/items/{asin}`

The client hardcodes `productType="PET_TOY"` and `currency="USD"` in listing payloads.

### CLI Commands

Design constraint: **one API call per command**. Do not chain multiple SP-API calls in a single command. Chaining multiple CLI commands together into a combo workflow is fine.

Actual Click command names (invoke with `amz-sp <command>`):
- `get-price <sku>` – fetch current price and ASIN
- `set-price <sku> <price> [--dry-run]` – update listing price; dry-run uses `VALIDATION_PREVIEW` mode
- `sale-price <sku> <discount> [--type percentage|fixed] [--start-date] [--end-date] [-o FILE]` – generate sale-price feed JSON (SP-API has no direct discount endpoint, so this outputs feed data)
- `create-discount <sku> <percent> [--all-variations]` – legacy command, also outputs feed JSON
- `check-competitors <asin>` – fetch catalog item attributes and sales rank
- `invalidate` – clear cached access token

### Credentials File Format

`~/.config/amazon-sp-cli/credentials.yml`:
```yaml
default:
  refresh_token: "..."
  client_id: "..."
  client_secret: "..."
  aws_access_key_id: "..."
  aws_secret_access_key: "..."
  seller_id: "..."
  marketplace_id: "ATVPDKIKX0DER"
```

### Testing

Tests use `unittest.mock` for auth/client and `click.testing.CliRunner` for CLI tests. There is no integration testing against live SP-API; all external calls are mocked.

### CI / Publishing

GitHub Actions run tests across Python 3.8–3.12, plus pre-commit and build checks. Publishing to PyPI happens only on tags starting with `v` after all jobs pass. The package name is `amazon-sp-cli` and the console script is `amz-sp`.
