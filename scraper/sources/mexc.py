"""MEXC Earn scraper.

MEXC doesn't expose a public API for its Earn/staking page, so this drives a
headless Chrome browser the same way the original script did: open each Earn
page, find the row for a given asset, click it open, and parse the "N
Day(s) ... X.XX%" lines out of the rendered page text.

Unlike the original script, this returns every APR tier found for every
watched asset (no hardcoded 20%/25% filter) — filtering against the
watchlist happens centrally in main.py.
"""

import re
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from .base import Offer

PAGES_TO_SCAN = 4
PAGE_LOAD_WAIT_SECONDS = 6
ROW_EXPAND_WAIT_SECONDS = 4


def _build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--mute-audio")
    options.add_argument("user-agent=Mozilla/5.0")
    options.page_load_strategy = "eager"

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(25)
    return driver


def _parse_asset_offers(body_text: str, asset: str, page: int) -> list[Offer]:
    offers = []
    lines = body_text.split("\n")

    for i, line in enumerate(lines):
        if "Day(s)" not in line:
            continue

        context = " ".join(lines[max(0, i - 2):min(len(lines), i + 3)])
        days_match = re.search(r"(\d+)\s*Day\(s\)", context)
        percent_match = re.search(r"(\d+\.\d+)\s*%", context)
        if not (days_match and percent_match):
            continue

        duration_days = int(days_match.group(1))
        apr = float(percent_match.group(1))
        status = "fully_staked" if "Fully Staked" in context else "available"

        offers.append(
            Offer(
                source="mexc",
                external_id=f"{asset}:{duration_days}",
                asset=asset,
                apr=apr,
                status=status,
                duration_days=duration_days,
                extra={"page": page},
            )
        )

    return offers


def fetch_mexc_offers(assets: list[str]) -> list[Offer]:
    if not assets:
        return []

    offers: list[Offer] = []
    driver = _build_driver()

    try:
        for page in range(1, PAGES_TO_SCAN + 1):
            url = f"https://www.mexc.com/earn?page={page}"
            try:
                driver.get(url)
            except Exception as exc:
                print(f"[mexc] page {page} load error: {exc}")
            time.sleep(PAGE_LOAD_WAIT_SECONDS)

            page_body = driver.find_element(By.TAG_NAME, "body").text
            print(f"[mexc] page {page}: title={driver.title!r} body_len={len(page_body)}")
            if len(page_body) < 500:
                # Likely a bot-check/error page rather than the real Earn table.
                print(f"[mexc] page {page}: suspiciously short body, snippet={page_body[:300]!r}")

            for asset in assets:
                if asset not in page_body:
                    print(f"[mexc] page {page}: '{asset}' not present in rendered page text")
                    continue

                try:
                    row = driver.find_element(By.XPATH, f"//tr[contains(., '{asset}')]")
                except Exception as exc:
                    print(f"[mexc] page {page}: '{asset}' found in text but no matching <tr>: {exc}")
                    continue

                try:
                    driver.execute_script("arguments[0].click();", row)
                    time.sleep(ROW_EXPAND_WAIT_SECONDS)
                    body_text = driver.find_element(By.TAG_NAME, "body").text
                    found = _parse_asset_offers(body_text, asset, page)
                    print(f"[mexc] page {page}: '{asset}' row expanded, parsed {len(found)} offer(s)")
                    offers.extend(found)
                except Exception as exc:
                    print(f"[mexc] {asset} page {page}: {exc}")
    finally:
        driver.quit()

    return offers
