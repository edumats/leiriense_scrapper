"""Download a Leiriense page using Selenium and extract category links.

The site uses client-side rendering, so a simple ``requests`` fetch
will miss content that is added or modified by JavaScript.  Selenium
bootstraps a real browser, waits for the page to finish loading, and
then hands the fully rendered ``page_source`` off to BeautifulSoup for
parsing.

Dependencies:
  pip install selenium webdriver-manager beautifulsoup4

The example below uses Chrome via ``webdriver-manager`` to simplify
driver management, but any Selenium-supported browser will work.
"""

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, parse_qs
import time


def fetch_rendered_html(url: str, wait: float = 2.0) -> str:
    """Return fully rendered HTML for ``url`` using Selenium.

    ``wait`` is a simple sleep after navigation to give the page time to
    execute its initial JavaScript.  For more robust use cases you could
    replace this with an explicit ``WebDriverWait`` condition.
    """

    # create browser instance (headless by default);
    # webdriver-manager will download/update the driver if necessary
    options = webdriver.ChromeOptions()
    options.headless = True

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                              options=options)
    try:
        driver.get(url)
        # give JavaScript a moment to run
        time.sleep(wait)
        return driver.page_source
    finally:
        driver.quit()


def extract_categories(html: str) -> set[str]:
    """Parse the HTML and return a set of category values found in links."""

    soup = BeautifulSoup(html, "html.parser")
    categories: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]
        parsed = urlparse(href)
        params = parse_qs(parsed.query)
        if "categoria" in params:
            categories.add(params["categoria"][0])

    return categories


def main() -> None:
    url = "https://cicloleiriense.meuspedidos.com.br/"
    html = fetch_rendered_html(url)
    cats = extract_categories(html)
    print(f"found categories: {cats}")


if __name__ == "__main__":
    main()

