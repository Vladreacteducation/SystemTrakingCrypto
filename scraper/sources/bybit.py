"""Bybit Earn scraper.

Like MEXC, Bybit's Earn product list has no clean public API. Unlike MEXC
though, the page has a coin-name search box, so instead of fighting
pagination/virtualization we just type the asset symbol in and read
whatever rows render for it. Each product row is a
`div.collapsible_item__<hash>` with clean, separately-classed children:

    div.collapsible_productType__*  -> "Easy Earn" / "On-Chain Earn" / ...
    div.collapsible_itemDuration__* -> "Flexible" / "90 Days" / ...
    div.collapsible_itemApy__*      -> "1.00%" (or "1.00% ~ 2.55%" for the
                                        collapsed summary row, which we skip)

The hash suffix in each class name is a CSS-module build artifact and may
change between Bybit deployments; matching on the stable prefix via
`contains(@class, ...)` avoids depending on it.
"""

import re
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from .base import Offer

EARN_URL = "https://www.bybit.com/en/earn/home/"
SEARCH_INPUT_XPATH = "//input[@placeholder='Search coin name']"
SEARCH_WAIT_SECONDS = 20
RESULTS_SETTLE_SECONDS = 2


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


def _parse_rows(driver, asset: str) -> list[Offer]:
    offers = []
    rows = driver.find_elements(By.XPATH, "//div[contains(@class,'collapsible_item__')]")

    for row in rows:
        try:
            product_type = row.find_element(
                By.XPATH, ".//div[contains(@class,'collapsible_productType__')]"
            ).text.strip()
            duration_text = row.find_element(
                By.XPATH, ".//div[contains(@class,'collapsible_itemDuration__')]"
            ).text.strip()
            apr_text = row.find_element(
                By.XPATH, ".//div[contains(@class,'collapsible_itemApy__')]"
            ).text.strip()
        except Exception:
            continue

        if not product_type or "~" in apr_text:
            continue  # collapsed summary row showing a range, not a single product

        apr_match = re.search(r"(\d+(?:\.\d+)?)\s*%", apr_text)
        if not apr_match:
            continue
        apr = float(apr_match.group(1))

        duration_match = re.search(r"(\d+)\s*Days?", duration_text, re.IGNORECASE)
        duration_days = int(duration_match.group(1)) if duration_match else None

        try:
            button_text = row.find_element(By.TAG_NAME, "button").text.strip().lower()
        except Exception:
            button_text = ""
        status = "available" if "invest" in button_text else "sold_out"

        offers.append(
            Offer(
                source="bybit",
                external_id=f"{asset}:{product_type}:{duration_text}",
                asset=asset,
                apr=apr,
                status=status,
                product_type=product_type,
                duration_days=duration_days,
                extra={"duration_text": duration_text},
            )
        )

    return offers


def fetch_bybit_offers(assets: list[str]) -> list[Offer]:
    if not assets:
        return []

    offers: list[Offer] = []
    driver = _build_driver()

    try:
        driver.get(EARN_URL)
        WebDriverWait(driver, SEARCH_WAIT_SECONDS).until(
            EC.presence_of_element_located((By.XPATH, SEARCH_INPUT_XPATH))
        )

        for asset in assets:
            try:
                search_box = driver.find_element(By.XPATH, SEARCH_INPUT_XPATH)
                search_box.clear()
                search_box.send_keys(asset)
                time.sleep(RESULTS_SETTLE_SECONDS)

                found = _parse_rows(driver, asset)
                print(f"[bybit] '{asset}': parsed {len(found)} offer(s)")
                offers.extend(found)
            except Exception as exc:
                print(f"[bybit] {asset}: {exc}")
    finally:
        driver.quit()

    return offers
