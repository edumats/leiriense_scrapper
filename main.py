import requests
import json
import csv
from typing import Any, Dict, List

"""Entry point for the leiriense_scrapper project."""

CATEGORIES = {
    '1010389', '1022022', '3183741', '3548766', '3994388', '2210069',
    '1289996', '1022010', '3183655', '1023550', '3184101', '2294700',
    '1023635', '1011389', '3183777', '2294705', '1009940', '1021203',
    '1023661', '1010513', '1022035', '1021908', '1023697', '3184048',
    '998307', '999606', '1219452', '2294699', '1587788', '1022066',
    '1010884', '1011116', '2280037', '3437394', '3183666', '1023632',
    '3183664', '1023700', '3457632', '998308', '2280038'
}


def main():
    url = "https://app.mercos.com/api_b2b/v1/produtos"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://cicloleiriense.meuspedidos.com.br/",
        "Origin": "https://cicloleiriense.meuspedidos.com.br"
    }

    all_rows: List[Dict[str, Any]] = []

    for categoria in sorted(CATEGORIES):
        page = 1
        while True:
            params = {
                "representada": "413939",
                "categoria": categoria,
                "comprados_recentemente": "false",
                "ordenar_por": "1",
                "token": "24cf50cc-5992-4250-8fc6-b01f759318f1",
                "pagina": str(page),
            }

            resp = requests.get(url, params=params, headers=headers)
            if resp.status_code != 200:
                print(
                    f"warning: status {resp.status_code} for cat {categoria} page {page}"
                )
                break

            data = resp.json()
            if not data:  # empty list indicates no more pages
                break

            # assume each element in data is a dict representing a product
            all_rows.extend(data)
            page += 1

    if all_rows:
        # determine fieldnames from the first row and any additional keys seen
        fieldnames = set().union(*(row.keys() for row in all_rows))
        fieldnames = sorted(fieldnames)

        with open("output.csv", "w", newline="", encoding="utf-8") as csvf:
            writer = csv.DictWriter(csvf, fieldnames=fieldnames)
            writer.writeheader()
            for row in all_rows:
                writer.writerow(row)

        print(f"wrote {len(all_rows)} rows to output.csv")
    else:
        print("no data collected")


if __name__ == "__main__":
    main()
