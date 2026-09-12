"use client";

import { useEffect, useMemo, useState } from "react";
import { supabase, type EarnOffer, type EarnOfferHistoryPoint } from "@/lib/supabase";
import OffersTable from "@/components/OffersTable";
import AprHistoryChart from "@/components/AprHistoryChart";

export default function Dashboard({ initialOffers }: { initialOffers: EarnOffer[] }) {
  const assets = useMemo(
    () => [...new Set(initialOffers.map((o) => o.asset))].sort(),
    [initialOffers]
  );

  const [selectedAsset, setSelectedAsset] = useState<string>(assets[0] ?? "");
  const [history, setHistory] = useState<EarnOfferHistoryPoint[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    if (!selectedAsset) return;
    let cancelled = false;
    setLoadingHistory(true);

    supabase
      .from("earn_offers_history")
      .select("source,asset,apr,status,recorded_at")
      .eq("asset", selectedAsset)
      // Pre-filter-fix scrapes briefly recorded absurd DeFiLlama APYs (low-liquidity
      // pools with inflated emissions); keep the chart's scale meaningful.
      .lte("apr", 500)
      .order("recorded_at", { ascending: true })
      .limit(2000)
      .then(({ data, error }) => {
        if (cancelled) return;
        if (error) {
          console.error("Failed to load APR history", error);
          setHistory([]);
        } else {
          setHistory(data ?? []);
        }
        setLoadingHistory(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedAsset]);

  const filteredOffers = selectedAsset
    ? initialOffers.filter((o) => o.asset === selectedAsset)
    : initialOffers;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center gap-3">
        <label className="text-sm" style={{ color: "var(--muted)" }} htmlFor="asset-filter">
          Asset
        </label>
        <select
          id="asset-filter"
          value={selectedAsset}
          onChange={(e) => setSelectedAsset(e.target.value)}
          className="rounded-md border px-3 py-1.5 text-sm"
          style={{ borderColor: "var(--border)", background: "var(--surface)", color: "var(--foreground)" }}
        >
          <option value="">All assets</option>
          {assets.map((asset) => (
            <option key={asset} value={asset}>
              {asset}
            </option>
          ))}
        </select>
      </div>

      {selectedAsset && (
        <section
          className="rounded-lg border p-4"
          style={{ borderColor: "var(--border)", background: "var(--surface)" }}
        >
          <h2 className="mb-1 text-sm font-medium" style={{ color: "var(--muted)" }}>
            APR history — {selectedAsset}
          </h2>
          <p className="mb-3 text-xs" style={{ color: "var(--subtle)" }}>
            Best available rate per source at each scan
          </p>
          {loadingHistory ? (
            <p className="text-sm" style={{ color: "var(--subtle)" }}>
              Loading…
            </p>
          ) : (
            <AprHistoryChart data={history} asset={selectedAsset} />
          )}
        </section>
      )}

      <section>
        <h2 className="mb-3 text-sm font-medium" style={{ color: "var(--muted)" }}>
          Current offers
        </h2>
        <OffersTable offers={filteredOffers} />
      </section>
    </div>
  );
}
