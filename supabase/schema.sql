-- Crypto Earn/Staking Tracker — Supabase schema
-- Run this once in the Supabase SQL editor (or via `supabase db push`).

-- external_id is the natural dedup key *within* a source, e.g. for MEXC
-- "APT:30" (asset:duration_days), for DeFiLlama the pool's own id (already
-- globally unique). Combined with `source` it uniquely identifies an offer
-- even when duration_days is null (DeFiLlama pools have no fixed term).
create table if not exists earn_offers (
    id bigserial primary key,
    source text not null,
    external_id text not null,
    asset text not null,
    product_type text not null default 'staking',
    duration_days int,
    apr numeric not null,
    status text not null,
    extra jsonb not null default '{}'::jsonb,
    first_seen_at timestamptz not null default now(),
    last_seen_at timestamptz not null default now(),
    unique (source, external_id)
);

create table if not exists earn_offers_history (
    id bigserial primary key,
    source text not null,
    external_id text not null,
    asset text not null,
    product_type text not null default 'staking',
    duration_days int,
    apr numeric not null,
    status text not null,
    recorded_at timestamptz not null default now()
);

create index if not exists earn_offers_history_lookup
    on earn_offers_history (source, asset, recorded_at desc);

create table if not exists watchlist (
    id bigserial primary key,
    asset text not null unique,
    min_apr numeric not null,
    enabled boolean not null default true
);

insert into watchlist (asset, min_apr)
values ('APT', 20)
on conflict (asset) do nothing;

create table if not exists notifications_log (
    id bigserial primary key,
    source text not null,
    external_id text not null,
    asset text not null,
    apr numeric not null,
    status text not null,
    notified_at timestamptz not null default now(),
    unique (source, external_id, apr, status)
);

-- Row Level Security: the GitHub Action writes with the service role key,
-- which bypasses RLS entirely. These policies only govern the anon key
-- used later by the public dashboard — read-only access.
alter table earn_offers enable row level security;
alter table earn_offers_history enable row level security;

drop policy if exists "public read earn_offers" on earn_offers;
create policy "public read earn_offers"
    on earn_offers for select
    to anon
    using (true);

drop policy if exists "public read earn_offers_history" on earn_offers_history;
create policy "public read earn_offers_history"
    on earn_offers_history for select
    to anon
    using (true);

-- watchlist and notifications_log stay locked down (no anon policies ->
-- RLS enabled with zero policies means anon has no access at all).
alter table watchlist enable row level security;
alter table notifications_log enable row level security;
