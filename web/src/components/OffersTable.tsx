"use client";

import type { EarnOffer } from "@/lib/supabase";
import { formatApr, formatDuration, formatRelativeTime, seriesColorVar } from "@/lib/format";

export default function OffersTable({ offers }: { offers: EarnOffer[] }) {
  const sorted = [...offers].sort((a, b) => b.apr - a.apr);

  if (sorted.length === 0) {
    return (
      <p className="text-sm" style={{ color: "var(--muted)" }}>
        No offers match this filter yet.
      </p>
    );
  }

  return (
    <div
      className="overflow-x-auto rounded-lg border"
      style={{ borderColor: "var(--border)", background: "var(--surface)" }}
    >
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left" style={{ color: "var(--subtle)" }}>
            <th className="px-4 py-3 font-medium">Source</th>
            <th className="px-4 py-3 font-medium">Asset</th>
            <th className="px-4 py-3 font-medium">Product</th>
            <th className="px-4 py-3 font-medium">Duration</th>
            <th className="px-4 py-3 font-medium text-right">APR</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium text-right">Updated</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((offer) => (
            <tr
              key={`${offer.source}:${offer.external_id}`}
              className="border-t"
              style={{ borderColor: "var(--gridline)" }}
            >
              <td className="px-4 py-3">
                <span className="inline-flex items-center gap-2">
                  <span
                    aria-hidden
                    className="inline-block h-2.5 w-2.5 rounded-full"
                    style={{ background: seriesColorVar(offer.source) }}
                  />
                  {offer.source}
                </span>
              </td>
              <td className="px-4 py-3 font-medium">{offer.asset}</td>
              <td className="px-4 py-3" style={{ color: "var(--muted)" }}>
                {offer.product_type}
              </td>
              <td className="px-4 py-3" style={{ color: "var(--muted)" }}>
                {formatDuration(offer.duration_days)}
              </td>
              <td
                className="px-4 py-3 text-right font-semibold"
                style={{ fontVariantNumeric: "tabular-nums" }}
              >
                {formatApr(offer.apr)}
              </td>
              <td className="px-4 py-3">
                {offer.status === "available" ? (
                  <span style={{ color: "var(--status-good)" }}>Available</span>
                ) : (
                  <span style={{ color: "var(--subtle)" }}>{offer.status}</span>
                )}
              </td>
              <td
                className="px-4 py-3 text-right"
                style={{ color: "var(--subtle)", fontVariantNumeric: "tabular-nums" }}
              >
                {formatRelativeTime(offer.last_seen_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
