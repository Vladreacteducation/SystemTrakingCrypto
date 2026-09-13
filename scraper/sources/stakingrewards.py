"""StakingRewards.com adapter.

Public GraphQL API for native PoS staking yields (the same rate a
non-custodial wallet like Trust Wallet shows when you delegate to a
validator directly) — a different category from exchange/DeFi earn
products, but a real public API needing only a free research API key
(no exchange account, no financial risk if it ever leaked).

Docs: https://api-docs.stakingrewards.com/
"""

import os

import requests

from .base import Offer

API_URL = "https://api.stakingrewards.com/public/query"
REQUEST_TIMEOUT_SECONDS = 15

QUERY = """
query AssetRewardRate($symbol: String!) {
  assets(where: { symbols: [$symbol] }, limit: 1) {
    symbol
    metrics(where: { metricKeys: ["reward_rate"] }, limit: 1) {
      metricKey
      defaultValue
    }
  }
}
"""


def fetch_stakingrewards_offers(assets: list[str]) -> list[Offer]:
    if not assets:
        return []

    api_key = os.environ["STAKINGREWARDS_API_KEY"]
    headers = {"Content-Type": "application/json", "X-API-KEY": api_key}

    offers = []
    for asset in assets:
        try:
            response = requests.post(
                API_URL,
                json={"query": QUERY, "variables": {"symbol": asset}},
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            print(f"[stakingrewards] {asset}: request failed: {exc}")
            continue

        if "errors" in payload:
            print(f"[stakingrewards] {asset}: API error: {payload['errors']}")
            continue

        for record in payload.get("data", {}).get("assets", []):
            for metric in record.get("metrics", []):
                value = metric.get("defaultValue")
                if value is None:
                    continue

                offers.append(
                    Offer(
                        source="stakingrewards",
                        external_id=f"{asset}:reward_rate",
                        asset=asset,
                        apr=round(float(value), 2),
                        status="available",
                        product_type="native_staking",
                        duration_days=None,
                        extra={},
                    )
                )

    return offers
