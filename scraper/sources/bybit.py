"""Bybit Earn adapter.

Unlike MEXC, Bybit exposes a real public REST endpoint for its Earn product
catalog: GET /v5/earn/product?category=<...>&coin=<...>. Confirmed against
Bybit's official SDK (tiagosiebler/bybit-api, rest-client-v5.ts) that this
call goes through the unsigned `get()` path — no API key needed at all.

Categories map to the two product types shown on the Earn page:
  - FlexibleSaving -> "Easy Earn"
  - OnChain        -> "On-Chain Earn"
"""

import re

import requests

from .base import Offer

PRODUCT_URL = "https://api.bybit.com/v5/earn/product"
CATEGORIES = ["FlexibleSaving", "OnChain"]
REQUEST_TIMEOUT_SECONDS = 15


def fetch_bybit_offers(assets: list[str]) -> list[Offer]:
    if not assets:
        return []

    offers = []

    for asset in assets:
        for category in CATEGORIES:
            try:
                response = requests.get(
                    PRODUCT_URL,
                    params={"category": category, "coin": asset},
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                response.raise_for_status()
                payload = response.json()
            except Exception as exc:
                print(f"[bybit] {asset}/{category}: request failed: {exc}")
                continue

            if payload.get("retCode") != 0:
                print(f"[bybit] {asset}/{category}: API error: {payload.get('retMsg')}")
                continue

            for product in payload.get("result", {}).get("list", []):
                apr_match = re.search(r"(\d+(?:\.\d+)?)", product.get("estimateApr", ""))
                if not apr_match:
                    continue
                apr = float(apr_match.group(1))

                term = product.get("term") or 0
                duration_days = int(term) if term else None
                status = "available" if product.get("status") == "Available" else "sold_out"
                product_id = product.get("productId")

                offers.append(
                    Offer(
                        source="bybit",
                        external_id=f"{category}:{asset}:{product_id}",
                        asset=asset,
                        apr=apr,
                        status=status,
                        product_type=category,
                        duration_days=duration_days,
                        extra={"product_id": product_id, "duration_text": product.get("duration")},
                    )
                )

    return offers
