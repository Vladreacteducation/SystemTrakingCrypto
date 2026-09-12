import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export type EarnOffer = {
  id: number;
  source: string;
  external_id: string;
  asset: string;
  product_type: string;
  duration_days: number | null;
  apr: number;
  status: string;
  extra: Record<string, unknown>;
  first_seen_at: string;
  last_seen_at: string;
};

export type EarnOfferHistoryPoint = {
  source: string;
  asset: string;
  apr: number;
  status: string;
  recorded_at: string;
};
