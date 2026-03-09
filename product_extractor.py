"""Extract detailed product information from Mercos API.

Reads produto_id values from leiriense_data.csv, makes individual API
requests for each product, and saves the results to a new CSV file.
"""

import csv
import requests
import json
from typing import Any, Dict, List, Set


def read_produto_ids(csv_file: str) -> Set[str]:
    """Read all unique produto_id values from the CSV file."""
    produto_ids: Set[str] = set()

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            if row and "produto_id" in row:
                pid = row["produto_id"].strip()
                if pid:
                    produto_ids.add(pid)

    return produto_ids


def fetch_product_details(produto_id: str, token: str) -> Dict[str, Any] | None:
    """Fetch detailed product info from API for a single produto_id."""
    url = f"https://app.mercos.com/api_b2b/v1/produtos/{produto_id}"
    params = {"token": token}

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://cicloleiriense.meuspedidos.com.br/",
        "Origin": "https://cicloleiriense.meuspedidos.com.br"
    }

    try:
        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"warning: status {resp.status_code} for produto_id {produto_id}")
            return None
    except Exception as e:
        print(f"error fetching produto_id {produto_id}: {e}")
        return None


def main() -> None:
    token = "24cf50cc-5992-4250-8fc6-b01f759318f1"
    input_csv = "leiriense_data.csv"
    output_csv = "produtos_detalhados.csv"

    # read all unique produto IDs from the input CSV
    produto_ids = read_produto_ids(input_csv)
    print(f"found {len(produto_ids)} unique produto IDs")

    all_products: List[Dict[str, Any]] = []

    # fetch details for each produto_id
    for idx, pid in enumerate(sorted(produto_ids), 1):
        product_data = fetch_product_details(pid, token)
        if product_data:
            # ensure produto_id is included in the output
            if isinstance(product_data, dict):
                product_data["produto_id"] = pid
            all_products.append(product_data)

        if idx % 100 == 0:
            print(f"processed {idx}/{len(produto_ids)}")

    # write results to CSV
    if all_products:
        # collect all fieldnames from all products
        fieldnames = set()
        for product in all_products:
            if isinstance(product, dict):
                fieldnames.update(product.keys())
        fieldnames = sorted(fieldnames)

        with open(output_csv, "w", newline="", encoding="utf-8") as csvf:
            writer = csv.DictWriter(csvf, fieldnames=fieldnames)
            writer.writeheader()
            for product in all_products:
                if isinstance(product, dict):
                    writer.writerow(product)

        print(f"wrote {len(all_products)} products to {output_csv}")
    else:
        print("no product data collected")


if __name__ == "__main__":
    main()
