# leiriense_scrapper

Scraper and converter utilities for Leiriense supplier product data.

The main scraper logs in to the Leiriense website, captures the authenticated
`auth_token`, scrapes product pages from the supplier API, removes duplicated
products, and writes the result to an Excel file.

## Setup

Create a `.env` file in the project root:

```env
USERNAME=your-login
PASSWORD=your-password
REQUEST_DELAY_SECONDS=1.5
```

`REQUEST_DELAY_SECONDS` is optional. If omitted, the scraper waits `1.5`
seconds between product API requests.

Install dependencies:

```bash
pip install requests pandas openpyxl python-dotenv selenium webdriver-manager beautifulsoup4
```

The project currently includes a local `venv`, so commands can also be run with
`venv/bin/python`.

## Usage

Run the authenticated product scraper:

```bash
python main.py
```

By default, the scraper writes:

```text
output.xlsx
```

Choose a different output file:

```bash
python main.py --output output_full.xlsx
```

Short form:

```bash
python main.py -o output_full
```

If the output path has no extension, `.xlsx` is added automatically.

Fetch one authenticated product by its ID and print the API response as JSON:

```bash
python main.py --product-id 123456
```

Single-product mode calls
`https://cicloleiriense.meuspedidos.com.br/api_b2b/v1/produtos/<product_id>`.
It logs in using `.env` as usual, but skips category discovery and does not
create an Excel file.

Print only the authenticated token:

```bash
python main.py --token
```

Token mode logs in using `.env`, prints only the raw `auth_token` value, skips
category discovery, and does not make product API requests.

The scraper prints progress while it runs:

- login status
- discovered category count
- saved category count
- current category and page
- rows returned per page
- duplicate rows removed before writing
- final output row count

## Authentication

`main.py` logs in at:

```text
https://cicloleiriense.meuspedidos.com.br/entrar
```

It uses Selenium to submit the credentials from `.env`, waits for the
`auth_token` cookie, then sends product API requests with both:

```text
Authorization: Bearer <token>
Cookie: auth_token=<token>
```

## Categories

The scraper uses two category sources:

1. Categories discovered from the logged-in website HTML.
2. Saved historical categories from `category_ids.csv`.

Those two sets are merged before scraping. This avoids missing categories that
do not appear in the headless Selenium-rendered page.

`category_ids.csv` must contain a `categoria_id` column.

## Duplicate Products

Some category requests can return the same product more than once, especially
when parent and child categories overlap. Before writing the Excel output,
`main.py` removes duplicates using `produto_id` when that column is present.

## Convert to Tiny Format

Use `convert_tiny.py` to convert a Leiriense export into the Tiny import
layout:

```bash
python convert_tiny.py output_full_no_duplicates.xlsx leiriense_full.xlsx
```

If the output path is omitted, it writes:

```text
converted.xlsx
```

The converter:

- maps supplier fields into Tiny's expected columns
- prefixes SKUs with `LEIRI`
- keeps `Código (SKU)` and `Cód do Fornecedor` as Excel text fields
- formats numeric-looking codes like `15.0` as `15`
- fills image URL columns from the `imagens` list
- extracts `Marca` from the `categorias` field

## Category Extraction Helper

`category_extractor.py` can be run by itself to render the Leiriense homepage
and print category IDs found in links:

```bash
python category_extractor.py
```

This helper is also used by `main.py`.

## Product Detail Helper

`product_extractor.py` reads `produto_id` values from `leiriense_data.csv`,
fetches each product detail endpoint, and writes:

```text
produtos_detalhados.csv
```

This script is separate from the main authenticated scraper.

## Tests

Run converter tests:

```bash
python -m unittest tests/test_convert_tiny.py
```

Using the local virtualenv:

```bash
venv/bin/python -m unittest tests/test_convert_tiny.py
```
