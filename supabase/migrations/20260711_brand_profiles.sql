-- Migration: persistent brand profile for the expert marketing copilot
-- (plan Section 3.1 / 4). One row per user; the copilot grounds every
-- recommendation in these fields. change_log stores timestamped corrections
-- (Section 3.6) so advice regressions can be traced to a bad assumption.

create table if not exists public.brand_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  business_name text default '',
  business_model text default '',
  business_stage text default '',
  monthly_budget text default '',
  brand_voice text default '',
  icp text default '',
  competitors text default '',
  active_channels text default '',
  seasonality text default '',
  change_log jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create unique index if not exists brand_profiles_user
  on public.brand_profiles(user_id);

alter table public.brand_profiles enable row level security;

drop policy if exists "own brand_profile" on public.brand_profiles;
create policy "own brand_profile"
  on public.brand_profiles for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
