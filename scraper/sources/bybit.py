"""Bybit Earn adapter.

Bybit exposes a real REST endpoint for its Earn product catalog:
GET /v5/earn/product?category=<...>&coin=<...>. Bybit's own SDK
(tiagosiebler/bybit-api) calls this unsigned, but anonymous requests from
GitHub Actions' IP ranges get a 403 from Bybit's edge/WAF — so we sign the
request the same way as any other V5 call (HMAC-SHA256 over
timestamp+api_key+recv_window+queryString), which gets through.

Categories map to the two product types shown on the Earn page:
  - FlexibleSaving -> "Easy Earn"
  - OnChain        -> "On-Chain Earn"
"""

import hashlib
import hmac
import os
import re
import time
from urllib.parse import urlencode

import requests

from .base import Offer

BASE_URL = "https://api.bybit.com"
PRODUCT_PATH = "/v5/earn/product"
CATEGORIES = ["FlexibleSaving", "OnChain"]
RECV_WINDOW = "5000"
REQUEST_TIMEOUT_SECONDS = 15


def _signed_get(path: str, params: dict) -> dict:
    api_key = os.environ["BYBIT_API_KEY"]
    api_secret = os.environ["BYBIT_API_SECRET"]

    query_string = urlencode(params)
    timestamp = str(int(time.time() * 1000))
    sign_payload = f"{timestamp}{api_key}{RECV_WINDOW}{query_string}"
    signature = hmac.new(api_secret.encode(), sign_payload.encode(), hashlib.sha256).hexdigest()

    headers = {
        "X-BAPI-API-KEY": api_key,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-SIGN": signature,
        "X-BAPI-RECV-WINDOW": RECV_WINDOW,
    }

    response = requests.get(
        f"{BASE_URL}{path}?{query_string}", headers=headers, timeout=REQUEST_TIMEOUT_SECONDS
    )
    response.raise_for_status()
    return response.json()


def fetch_bybit_offers(assets: list[str]) -> list[Offer]:
    if not assets:
        return []

    offers = []

    for asset in assets:
        for category in CATEGORIES:
            try:
                payload = _signed_get(PRODUCT_PATH, {"category": category, "coin": asset})
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
