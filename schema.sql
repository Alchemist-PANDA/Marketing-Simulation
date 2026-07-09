-- profiles: one row per auth.users, holds plan/billing state (NEW — nothing references this yet)
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  plan text not null default 'free' check (plan in ('free','pro','enterprise')),
  stripe_customer_id text,
  stripe_subscription_id text,
  simulations_today int not null default 0,
  simulations_reset_at date not null default current_date,
  role text not null default 'free' check (role in ('free', 'pro', 'enterprise', 'admin')),
  created_at timestamptz not null default now()
);

-- campaigns: matches save_campaign()'s payload exactly (name, channel, budget)
create table public.campaigns (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  channel text,
  budget numeric,
  created_at timestamptz not null default now()
);

-- ad_variants: matches save_ad_variant()'s payload exactly
create table public.ad_variants (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  campaign_id uuid references public.campaigns(id) on delete cascade,
  text text not null,
  price numeric,
  category text,
  scores_json jsonb,
  created_at timestamptz not null default now()
);

-- simulation_runs: matches save_simulation_run()'s payload exactly
create table public.simulation_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  variant_id uuid references public.ad_variants(id) on delete cascade,
  results_json jsonb,
  created_at timestamptz not null default now()
);

-- simulation_reports: flat table storing full A/B test results per user
create table public.simulation_reports (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  report_number int not null,
  created_at timestamptz not null default now(),
  ad_a_text text,
  ad_b_text text,
  winner text,
  lift_percentage double precision,
  objective text,
  channel text,
  num_agents int,
  campaign_name text,
  result_json jsonb not null,
  ad_a_image text,
  ad_b_image text
);

create unique index simulation_reports_user_report on public.simulation_reports(user_id, report_number);

-- api_keys: stores API keys for programmatic access
create table public.api_keys (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  key_hash text not null unique,
  name text not null,
  permissions jsonb default '{"read": true, "write": true}'::jsonb,
  rate_limit int default 10,
  last_used timestamptz,
  created_at timestamptz not null default now(),
  expires_at timestamptz
);

alter table public.profiles enable row level security;
alter table public.campaigns enable row level security;
alter table public.ad_variants enable row level security;
alter table public.simulation_runs enable row level security;
alter table public.simulation_reports enable row level security;
alter table public.api_keys enable row level security;

create policy "own profile" on public.profiles for all using (auth.uid() = id);
create policy "own campaigns" on public.campaigns for all using (auth.uid() = user_id);
create policy "own ad_variants" on public.ad_variants for all using (auth.uid() = user_id);
create policy "own simulation_runs" on public.simulation_runs for all using (auth.uid() = user_id);
create policy "own simulation_reports" on public.simulation_reports for all using (auth.uid() = user_id);
create policy "own api_keys" on public.api_keys for all using (auth.uid() = user_id);
