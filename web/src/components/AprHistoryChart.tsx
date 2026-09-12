"use client";

import { useMemo, useRef, useState } from "react";
import type { EarnOfferHistoryPoint } from "@/lib/supabase";
import { formatApr, seriesColorVar } from "@/lib/format";

const WIDTH = 800;
const HEIGHT = 320;
const PAD_LEFT = 48;
const PAD_RIGHT = 16;
const PAD_TOP = 16;
const PAD_BOTTOM = 32;

function niceMax(value: number): number {
  if (value <= 0) return 1;
  const magnitude = Math.pow(10, Math.floor(Math.log10(value)));
  const normalized = value / magnitude;
  const step = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  return step * magnitude;
}

type Series = {
  source: string;
  points: { t: number; apr: number }[];
};

export default function AprHistoryChart({ data, asset }: { data: EarnOfferHistoryPoint[]; asset: string }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoverX, setHoverX] = useState<number | null>(null);

  const series: Series[] = useMemo(() => {
    // A single scrape run can log many distinct products for the same
    // source+asset (e.g. several DeFiLlama pools). Plotting every row as one
    // connected line stitches unrelated products together into fake spikes,
    // so each source's line tracks its single best (max) APR per timestamp.
    const bySourceAndTime = new Map<string, Map<number, number>>();
    for (const row of data) {
      const t = new Date(row.recorded_at).getTime();
      if (!bySourceAndTime.has(row.source)) bySourceAndTime.set(row.source, new Map());
      const byTime = bySourceAndTime.get(row.source)!;
      byTime.set(t, Math.max(byTime.get(t) ?? -Infinity, row.apr));
    }
    return [...bySourceAndTime.entries()]
      .map(([source, byTime]) => ({
        source,
        points: [...byTime.entries()]
          .map(([t, apr]) => ({ t, apr }))
          .sort((a, b) => a.t - b.t),
      }))
      .sort((a, b) => a.source.localeCompare(b.source));
  }, [data]);

  const allPoints = series.flatMap((s) => s.points);
  const hasData = allPoints.length > 0;

  const minT = hasData ? Math.min(...allPoints.map((p) => p.t)) : 0;
  const maxT = hasData ? Math.max(...allPoints.map((p) => p.t)) : 1;
  const maxApr = hasData ? niceMax(Math.max(...allPoints.map((p) => p.apr)) * 1.1) : 1;

  const xScale = (t: number) =>
    PAD_LEFT + (maxT === minT ? 0 : ((t - minT) / (maxT - minT)) * (WIDTH - PAD_LEFT - PAD_RIGHT));
  const yScale = (v: number) =>
    HEIGHT - PAD_BOTTOM - (v / maxApr) * (HEIGHT - PAD_TOP - PAD_BOTTOM);

  const yTicks = [0, maxApr * 0.25, maxApr * 0.5, maxApr * 0.75, maxApr];

  function handleMove(e: React.MouseEvent<SVGSVGElement>) {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * WIDTH;
    setHoverX(Math.max(PAD_LEFT, Math.min(WIDTH - PAD_RIGHT, x)));
  }

  const hoveredT = hoverX === null ? null : minT + ((hoverX - PAD_LEFT) / (WIDTH - PAD_LEFT - PAD_RIGHT)) * (maxT - minT);

  const tooltipRows =
    hoveredT === null
      ? []
      : series
          .map((s) => {
            const nearest = s.points.reduce((best, p) =>
              Math.abs(p.t - hoveredT) < Math.abs(best.t - hoveredT) ? p : best
            , s.points[0]);
            return nearest ? { source: s.source, apr: nearest.apr, t: nearest.t } : null;
          })
          .filter((r): r is { source: string; apr: number; t: number } => r !== null);

  if (!hasData) {
    return (
      <p className="text-sm" style={{ color: "var(--muted)" }}>
        No history yet for {asset} — check back after a few scrape runs.
      </p>
    );
  }

  return (
    <div>
      <div className="mb-2 flex flex-wrap items-center gap-4 text-xs" style={{ color: "var(--muted)" }}>
        {series.map((s) => (
          <span key={s.source} className="inline-flex items-center gap-1.5">
            <span
              aria-hidden
              className="inline-block h-0.5 w-4 rounded-full"
              style={{ background: seriesColorVar(s.source) }}
            />
            {s.source}
          </span>
        ))}
      </div>

      <div className="relative">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          className="w-full"
          onMouseMove={handleMove}
          onMouseLeave={() => setHoverX(null)}
          role="img"
          aria-label={`APR history for ${asset}`}
        >
          {yTicks.map((tick) => (
            <g key={tick}>
              <line
                x1={PAD_LEFT}
                x2={WIDTH - PAD_RIGHT}
                y1={yScale(tick)}
                y2={yScale(tick)}
                stroke="var(--gridline)"
                strokeWidth={1}
              />
              <text x={PAD_LEFT - 8} y={yScale(tick)} textAnchor="end" dominantBaseline="middle" fontSize={11} fill="var(--subtle)">
                {tick.toFixed(tick < 1 ? 2 : 0)}%
              </text>
            </g>
          ))}
          <line
            x1={PAD_LEFT}
            x2={PAD_LEFT}
            y1={PAD_TOP}
            y2={HEIGHT - PAD_BOTTOM}
            stroke="var(--baseline)"
            strokeWidth={1}
          />

          {series.map((s) => {
            const d = s.points.map((p, i) => `${i === 0 ? "M" : "L"} ${xScale(p.t)} ${yScale(p.apr)}`).join(" ");
            const last = s.points[s.points.length - 1];
            return (
              <g key={s.source}>
                <path d={d} fill="none" stroke={seriesColorVar(s.source)} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                <circle cx={xScale(last.t)} cy={yScale(last.apr)} r={4} fill={seriesColorVar(s.source)} stroke="var(--surface)" strokeWidth={2} />
              </g>
            );
          })}

          {hoverX !== null && (
            <line x1={hoverX} x2={hoverX} y1={PAD_TOP} y2={HEIGHT - PAD_BOTTOM} stroke="var(--baseline)" strokeWidth={1} />
          )}
        </svg>

        {hoverX !== null && tooltipRows.length > 0 && (
          <div
            className="pointer-events-none absolute top-2 rounded-md border px-3 py-2 text-xs shadow-sm"
            style={{
              left: `${Math.min(85, (hoverX / WIDTH) * 100)}%`,
              background: "var(--surface)",
              borderColor: "var(--border)",
              color: "var(--foreground)",
            }}
          >
            {tooltipRows.map((row) => (
              <div key={row.source} className="flex items-center gap-2 whitespace-nowrap">
                <span
                  aria-hidden
                  className="inline-block h-0.5 w-3 rounded-full"
                  style={{ background: seriesColorVar(row.source) }}
                />
                <span className="font-semibold" style={{ fontVariantNumeric: "tabular-nums" }}>
                  {formatApr(row.apr)}
                </span>
                <span style={{ color: "var(--subtle)" }}>{row.source}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
