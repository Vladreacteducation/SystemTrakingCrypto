import { supabase, type EarnOffer } from "@/lib/supabase";
import Dashboard from "@/components/Dashboard";

export const revalidate = 60;

export default async function Home() {
  const { data, error } = await supabase
    .from("earn_offers")
    .select("*")
    .order("apr", { ascending: false });

  const offers: EarnOffer[] = error ? [] : data ?? [];

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-4 py-10">
      <header>
        <h1 className="text-2xl font-semibold">Crypto Earn Tracker</h1>
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          Staking/earn APR rates scraped on a schedule and stored in Supabase.
        </p>
      </header>

      {error ? (
        <p className="text-sm" style={{ color: "var(--status-critical)" }}>
          Failed to load offers: {error.message}
        </p>
      ) : (
        <Dashboard initialOffers={offers} />
      )}
    </main>
  );
}
