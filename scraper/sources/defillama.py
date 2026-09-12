"""DeFiLlama yields adapter.

Unlike the exchange scrapers, this is a real public, unauthenticated JSON
API — no browser automation needed. Docs: https://defillama.com/docs/api
"""

import requests

from .base import Offer

POOLS_URL = "https://yields.llama.fi/pools"
REQUEST_TIMEOUT_SECONDS = 20

# Tiny/new pools routinely report absurd APYs (thousands of percent) driven
# by short-lived emissions on near-zero liquidity — not a real, sustainable
# yield. Filter those out so alerts stay meaningful.
MIN_TVL_USD = 50_000
MAX_SANE_APR = 500


def fetch_defillama_offers(assets: list[str]) -> list[Offer]:
    if not assets:
        return []

    watched = {asset.upper() for asset in assets}

    response = requests.get(POOLS_URL, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    pools = response.json().get("data", [])

    offers = []
    for pool in pools:
        apy = pool.get("apy")
        symbol = pool.get("symbol")
        tvl_usd = pool.get("tvlUsd") or 0
        if apy is None or not symbol:
            continue
        if tvl_usd < MIN_TVL_USD or apy > MAX_SANE_APR:
            continue

        # symbol is often a pair like "USDC-ETH" — match if any leg is watched.
        legs = {leg.upper() for leg in symbol.split("-")}
        matched = legs & watched
        if not matched:
            continue

        pool_id = pool.get("pool")
        if not pool_id:
            continue

        for asset in matched:
            offers.append(
                Offer(
                    source="defillama",
                    external_id=pool_id,
                    asset=asset,
                    apr=round(float(apy), 2),
                    status="available",
                    product_type=f"defi:{pool.get('project', 'unknown')}",
                    duration_days=None,
                    extra={
                        "chain": pool.get("chain"),
                        "tvl_usd": pool.get("tvlUsd"),
                        "symbol": symbol,
                    },
                )
            )

    return offers
