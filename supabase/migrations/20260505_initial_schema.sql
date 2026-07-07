-- Marketing Simulation Initial Schema

-- 1. Profiles (linked to auth.users)
create table if not exists public.profiles (
  id uuid not null references auth.users(id) on delete cascade,
  email text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  primary key (id)
);
-- Enable RLS
alter table public.profiles enable row level security;
drop policy if exists "Users can view own profile" on public.profiles;
create policy "Users can view own profile" on public.profiles for select using (auth.uid() = id);
drop policy if exists "Users can update own profile" on public.profiles;
create policy "Users can update own profile" on public.profiles for update using (auth.uid() = id);

-- 2. Campaigns
create table if not exists public.campaigns (
  id uuid not null default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  name text not null,
  channel text not null,
  budget numeric not null default 0,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  primary key (id)
);
-- Indexes
create index if not exists idx_campaigns_user_id on public.campaigns(user_id);
create index if not exists idx_campaigns_created_at on public.campaigns(created_at);
-- RLS
alter table public.campaigns enable row level security;
drop policy if exists "Users can manage own campaigns" on public.campaigns;
create policy "Users can manage own campaigns" on public.campaigns for all using (auth.uid() = user_id);

-- 3. Ad Variants
create table if not exists public.ad_variants (
  id uuid not null default gen_random_uuid(),
  campaign_id uuid references public.campaigns(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  text text not null,
  price numeric not null,
  category text,
  scores_json jsonb not null default '{}'::jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  primary key (id)
);
-- Indexes
create index if not exists idx_ad_variants_campaign_id on public.ad_variants(campaign_id);
create index if not exists idx_ad_variants_user_id on public.ad_variants(user_id);
-- RLS
alter table public.ad_variants enable row level security;
drop policy if exists "Users can manage own ad variants" on public.ad_variants;
create policy "Users can manage own ad variants" on public.ad_variants for all using (auth.uid() = user_id);

-- 4. Simulation Runs
create table if not exists public.simulation_runs (
  id uuid not null default gen_random_uuid(),
  variant_id uuid not null references public.ad_variants(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  results_json jsonb not null default '{}'::jsonb,
  timestamp timestamp with time zone default timezone('utc'::text, now()) not null,
  primary key (id)
);
-- Indexes
create index if not exists idx_simulation_runs_variant_id on public.simulation_runs(variant_id);
create index if not exists idx_simulation_runs_user_id on public.simulation_runs(user_id);
create index if not exists idx_simulation_runs_timestamp on public.simulation_runs(timestamp);
-- RLS
alter table public.simulation_runs enable row level security;
drop policy if exists "Users can manage own simulation runs" on public.simulation_runs;
create policy "Users can manage own simulation runs" on public.simulation_runs for all using (auth.uid() = user_id);

-- 5. Trigger for updated_at on campaigns
create or replace function public.handle_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists handle_updated_at_campaigns on public.campaigns;
create trigger handle_updated_at_campaigns
  before update on public.campaigns
  for each row
  execute procedure public.handle_updated_at();
