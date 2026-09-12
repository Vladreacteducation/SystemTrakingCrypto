# Crypto Earn/Staking Tracker

Scrapes crypto earn/staking APR offers (currently MEXC + DeFiLlama), stores
them in Supabase with full history, and pushes a Telegram alert whenever an
offer clears a per-asset APR threshold you control from a Supabase table.
Runs on a schedule via GitHub Actions — no server to maintain.

## How it works

- `.github/workflows/scrape.yml` runs `scraper/main.py` every 30 minutes.
- `scraper/main.py` reads the `watchlist` table from Supabase (which assets
  you care about, and the minimum APR worth alerting on), scrapes each
  source in `scraper/sources/`, upserts results into `earn_offers` /
  `earn_offers_history`, and sends a Telegram message for anything new that
  clears its threshold (deduped via `notifications_log` so you don't get
  repeat pings for an unchanged offer).

## One-time setup

1. **Create a Supabase project** at [supabase.com](https://supabase.com),
   then open the SQL editor and run `supabase/schema.sql`. This creates the
   tables and seeds the `watchlist` with one row (`APT`, min APR 20) to
   match the old script's behavior — edit that table any time to add coins
   or change thresholds, no redeploy needed.
2. **Rotate the Telegram bot token.** The token in the original script was
   pasted into chat and must be treated as leaked — regenerate it via
   [@BotFather](https://t.me/BotFather).
3. **Add GitHub Actions secrets** (repo Settings → Secrets and variables →
   Actions):
   - `SUPABASE_URL` — Project Settings → API → Project URL
   - `SUPABASE_SERVICE_ROLE_KEY` — Project Settings → API → `service_role`
     key (never expose this one publicly — it bypasses RLS)
   - `TELEGRAM_BOT_TOKEN` — the new token from step 2
   - `TELEGRAM_CHAT_ID` — your chat id
4. Push this repo to GitHub. The workflow runs automatically on schedule,
   or trigger it manually from the Actions tab (`workflow_dispatch`).

## Running locally

```bash
cd scraper
pip install -r requirements.txt
cp .env.example .env   # fill in the four values, then export them
python main.py
```

## Adding a new source

Add a `fetch_<name>_offers(assets: list[str]) -> list[Offer]` function under
`scraper/sources/`, returning `Offer` objects (see `sources/base.py`), and
wire it into the loop in `scraper/main.py`. `defillama.py` is the simplest
example (plain REST API); `mexc.py` shows the Selenium fallback pattern for
exchanges with no public Earn API.

## Roadmap

- Bybit / OKX / Binance adapters — these need their internal Earn endpoint
  identified via browser devtools first (no clean public API found yet).
- Next.js dashboard on Vercel reading Supabase directly (table + APR
  history chart) for a non-Telegram view.
