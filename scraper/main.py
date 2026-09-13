from sources.bybit import fetch_bybit_offers
from sources.defillama import fetch_defillama_offers
from sources.mexc import fetch_mexc_offers
from supabase_client import (
    get_client,
    get_notified_keys,
    get_watchlist,
    log_notifications,
    prune_stale_offers,
    upsert_offers,
)
from telegram import send_telegram


def format_offer(offer) -> str:
    parts = [f"[{offer.source}] {offer.asset} — {offer.apr}%"]
    if offer.duration_days:
        parts.append(f"{offer.duration_days}d")
    parts.append(offer.product_type)
    tvl = offer.extra.get("tvl_usd")
    if tvl:
        parts.append(f"TVL ${tvl:,.0f}")
    return " | ".join(parts)


def run() -> None:
    client = get_client()
    watchlist = get_watchlist(client)
    assets = list(watchlist.keys())

    if not assets:
        print("[main] watchlist is empty, nothing to scrape")
        return

    offers = []
    for label, fetch in (
        ("mexc", fetch_mexc_offers),
        ("bybit", fetch_bybit_offers),
        ("defillama", fetch_defillama_offers),
    ):
        try:
            found = fetch(assets)
            print(f"[main] {label}: {len(found)} offers")
            offers.extend(found)
            upsert_offers(client, found)
            prune_stale_offers(client, label, {o.external_id for o in found})
        except Exception as exc:
            print(f"[main] {label} failed: {exc}")
            send_telegram(f"[WARN] {label} scrape failed:\n{exc}")

    if not offers:
        print("[main] no offers found this run")
        return

    notified_keys = get_notified_keys(client)
    to_notify = [
        offer
        for offer in offers
        if offer.status == "available"
        and offer.apr >= watchlist.get(offer.asset.upper(), float("inf"))
        and (offer.source, offer.external_id, offer.apr, offer.status) not in notified_keys
    ]

    if to_notify:
        message = "\n".join(format_offer(o) for o in to_notify)
        print(f"[main] notifying about {len(to_notify)} offer(s):\n{message}")
        send_telegram(message)
        log_notifications(client, to_notify)
    else:
        print("[main] nothing new to notify")


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        send_telegram(f"[ERROR] Crypto tracker run failed:\n{exc}")
        raise
