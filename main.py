import argparse
import json
import requests
import time
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pandas as pd
from dotenv import dotenv_values
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from category_extractor import extract_categories

"""Entry point for the leiriense_scrapper project."""

SITE_URL = "https://cicloleiriense.meuspedidos.com.br/"
LOGIN_URL = f"{SITE_URL}entrar"
DEFAULT_REQUEST_DELAY_SECONDS = 1.5
SAVED_CATEGORIES_PATH = Path("category_ids.csv")
DEFAULT_OUTPUT_PATH = Path("output.xlsx")
PRODUCTS_URL = f"{SITE_URL}api_b2b/v1/produtos"

# Original URL
# https://app.mercos.com/api_b2b/v1/produtos?representada=413939&categoria=3180345&comprados_recentemente=false&ordenar_por=1


def load_credentials(env_path: Path = Path(".env")) -> Tuple[str, str]:
    env = dotenv_values(env_path)
    username = env.get("USERNAME")
    password = env.get("PASSWORD")

    if not username or not password:
        raise RuntimeError("missing USERNAME or PASSWORD in .env")

    return username, password


def load_request_delay(env_path: Path = Path(".env")) -> float:
    env = dotenv_values(env_path)
    raw_delay = env.get("REQUEST_DELAY_SECONDS")

    if raw_delay is None:
        return DEFAULT_REQUEST_DELAY_SECONDS

    try:
        delay = float(raw_delay)
    except ValueError as error:
        raise RuntimeError("REQUEST_DELAY_SECONDS must be a number") from error

    if delay < 0:
        raise RuntimeError("REQUEST_DELAY_SECONDS must be zero or greater")

    return delay


def load_saved_categories(path: Path = SAVED_CATEGORIES_PATH) -> Set[str]:
    if not path.exists():
        return set()

    df = pd.read_csv(path)
    if "categoria_id" not in df.columns:
        raise RuntimeError(f"{path} must contain a categoria_id column")

    categories = df["categoria_id"].dropna().astype(int).astype(str)
    return set(categories)


def create_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1000")
    return webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options,
    )


def wait_for_first_selector(
    driver: webdriver.Chrome,
    selectors: List[str],
    timeout: int = 20,
):
    def find_first(loaded_driver):
        for selector in selectors:
            elements = loaded_driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    return element
        return False

    wait = WebDriverWait(driver, timeout)
    try:
        return wait.until(find_first)
    except Exception as error:
        raise RuntimeError(f"could not find any selector: {', '.join(selectors)}") from error


def wait_for_auth_token(driver: webdriver.Chrome, timeout: int = 30) -> str:
    deadline = time.time() + timeout

    while time.time() < deadline:
        cookie = driver.get_cookie("auth_token")
        if cookie and cookie.get("value"):
            return cookie["value"]
        time.sleep(0.5)

    raise RuntimeError("auth_token cookie was not found after login")


def wait_for_categories(driver: webdriver.Chrome, timeout: int = 20) -> Set[str]:
    deadline = time.time() + timeout

    while time.time() < deadline:
        categories = extract_categories(driver.page_source)
        if categories:
            return categories
        time.sleep(0.5)

    return set()


def login_and_load_categories(
    load_categories: bool = True,
    verbose: bool = True,
) -> Tuple[str, Set[str]]:
    username, password = load_credentials()

    if verbose:
        print("logging in...")
    driver = create_driver()
    try:
        driver.get(LOGIN_URL)

        username_input = wait_for_first_selector(
            driver,
            [
                "input[name='email']",
                "input[type='email']",
                "input[name='username']",
                "input[name='login']",
                "input[name='usuario']",
                "input[type='text']",
            ],
        )
        password_input = wait_for_first_selector(
            driver,
            [
                "input[name='password']",
                "input[type='password']",
            ],
        )

        username_input.clear()
        username_input.send_keys(username)
        password_input.clear()
        password_input.send_keys(password)

        try:
            submit = wait_for_first_selector(
                driver,
                [
                    "button[type='submit']",
                    "input[type='submit']",
                    "button",
                ],
                timeout=5,
            )
            submit.click()
        except RuntimeError:
            password_input.send_keys(Keys.ENTER)

        token = wait_for_auth_token(driver)
        if verbose:
            print("login succeeded")

        if not load_categories:
            return token, set()

        if verbose:
            print("loading categories...")
        driver.get(SITE_URL)
        WebDriverWait(driver, 20).until(
            lambda loaded_driver: loaded_driver.execute_script("return document.readyState")
            == "complete"
        )
        categories = wait_for_categories(driver)
        if verbose:
            print(f"found {len(categories)} categories")

        return token, categories
    finally:
        driver.quit()


def normalize_output_path(output_path: Path) -> Path:
    if output_path.suffix:
        return output_path
    return output_path.with_suffix(".xlsx")


def build_headers(token: str) -> Dict[str, str]:
    return {
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,pt-BR;q=0.9,ja;q=0.8,en;q=0.7",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:148.0) Gecko/20100101 Firefox/148.0",
        "Referer": SITE_URL,
        "Origin": SITE_URL.rstrip("/"),
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {token}",
        "Cookie": f"auth_token={token}",
    }


def fetch_auth_token() -> str:
    token, _ = login_and_load_categories(load_categories=False, verbose=False)
    return token


def fetch_single_product(product_id: int) -> Dict[str, Any]:
    token, _ = login_and_load_categories(load_categories=False)
    url = f"{PRODUCTS_URL}/{product_id}"
    print(f"fetching product {product_id}...")
    response = requests.get(url, headers=build_headers(token), timeout=30)

    if response.status_code != 200:
        raise RuntimeError(
            f"product request failed with HTTP {response.status_code}: {response.text}"
        )

    return response.json()


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape Leiriense products")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"output XLSX file path (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--product-id",
        type=int,
        help="fetch one product by ID and print its JSON response",
    )
    parser.add_argument(
        "--token",
        action="store_true",
        help="log in and print only the auth token without making API requests",
    )
    return parser.parse_args(argv)


def main(output_path: Path = DEFAULT_OUTPUT_PATH):
    output_path = normalize_output_path(output_path)

    all_rows: List[Dict[str, Any]] = []
    request_delay = load_request_delay()
    token, discovered_categories = login_and_load_categories()
    saved_categories = load_saved_categories()
    categories = discovered_categories | saved_categories
    headers = build_headers(token)

    if not categories:
        print("no categories found")
        return

    sorted_categories = sorted(categories)
    print(
        f"using {len(sorted_categories)} categories "
        f"({len(discovered_categories)} discovered, {len(saved_categories)} saved)"
    )
    print(f"starting scrape for {len(sorted_categories)} categories")
    print(f"waiting {request_delay:.2f}s between product API requests")
    requests_made = 0

    for category_idx, categoria in enumerate(sorted_categories, start=1):
        category_rows = 0
        page = 1
        print(f"[{category_idx}/{len(sorted_categories)}] category {categoria}: starting")

        while True:
            params = {
                "representada": "413939",
                "categoria": categoria,
                "comprados_recentemente": "false",
                "ordenar_por": "1",
                
                "pagina": str(page),
            }

            if requests_made:
                time.sleep(request_delay)

            print(f"[{category_idx}/{len(sorted_categories)}] category {categoria}: fetching page {page}")
            resp = requests.get(PRODUCTS_URL, params=params, headers=headers)
            requests_made += 1
            if resp.status_code != 200:
                print(
                    f"warning: status {resp.status_code} for cat {categoria} page {page}"
                )
                break

            data = resp.json()
            if not data:  # empty list indicates no more pages
                print(
                    f"[{category_idx}/{len(sorted_categories)}] category {categoria}: "
                    f"finished after {page - 1} pages, {category_rows} rows"
                )
                break

            # assume each element in data is a dict representing a product
            all_rows.extend(data)
            category_rows += len(data)
            print(
                f"[{category_idx}/{len(sorted_categories)}] category {categoria}: "
                f"page {page} returned {len(data)} rows "
                f"({category_rows} category rows, {len(all_rows)} total)"
            )
            page += 1

    if all_rows:
        # determine fieldnames from the first row and any additional keys seen
        fieldnames = set().union(*(row.keys() for row in all_rows))
        fieldnames = sorted(fieldnames)

        output_df = pd.DataFrame(all_rows, columns=fieldnames)
        row_count_before_dedup = len(output_df)
        if "produto_id" in output_df.columns:
            output_df = output_df.drop_duplicates(subset=["produto_id"])
        else:
            output_df = output_df.drop_duplicates()
        duplicates_removed = row_count_before_dedup - len(output_df)
        if duplicates_removed:
            print(f"removed {duplicates_removed} duplicate rows before writing")

        output_df.to_excel(output_path, index=False)

        print(f"wrote {len(output_df)} rows to {output_path}")
    else:
        print("no data collected")


if __name__ == "__main__":
    args = parse_args()
    if args.token:
        print(fetch_auth_token())
    elif args.product_id is not None:
        product = fetch_single_product(args.product_id)
        print(json.dumps(product, ensure_ascii=False, indent=2))
    else:
        main(args.output)
