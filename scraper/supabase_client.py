import os
from datetime import datetime, timezone

from supabase import Client, create_client

from sources.base import Offer


def get_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def upsert_offers(client: Client, offers: list[Offer]) -> None:
    if not offers:
        return

    now = datetime.now(timezone.utc).isoformat()

    snapshot_rows = [
        {
            "source": o.source,
            "external_id": o.external_id,
            "asset": o.asset,
            "product_type": o.product_type,
            "duration_days": o.duration_days,
            "apr": o.apr,
            "status": o.status,
            "extra": o.extra,
            "last_seen_at": now,
        }
        for o in offers
    ]
    client.table("earn_offers").upsert(snapshot_rows, on_conflict="source,external_id").execute()

    history_rows = [
        {
            "source": o.source,
            "external_id": o.external_id,
            "asset": o.asset,
            "product_type": o.product_type,
            "duration_days": o.duration_days,
            "apr": o.apr,
            "status": o.status,
        }
        for o in offers
    ]
    client.table("earn_offers_history").insert(history_rows).execute()


def prune_stale_offers(client: Client, source: str, current_external_ids: set[str]) -> None:
    existing = client.table("earn_offers").select("external_id").eq("source", source).execute()
    stale_ids = [row["external_id"] for row in existing.data if row["external_id"] not in current_external_ids]
    if not stale_ids:
        return
    client.table("earn_offers").delete().eq("source", source).in_("external_id", stale_ids).execute()
    print(f"[supabase] pruned {len(stale_ids)} stale {source} offer(s)")


def get_watchlist(client: Client) -> dict[str, float]:
    result = client.table("watchlist").select("asset,min_apr").eq("enabled", True).execute()
    return {row["asset"].upper(): float(row["min_apr"]) for row in result.data}
