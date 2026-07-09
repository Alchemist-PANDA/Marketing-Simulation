-- Migration: Add simulation_reports table for flat report history
-- Each simulation run is stored as a single row with full result JSON

create table if not exists public.simulation_reports (
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

create unique index if not exists simulation_reports_user_report
  on public.simulation_reports(user_id, report_number);

alter table public.simulation_reports enable row level security;

create policy "own simulation_reports"
  on public.simulation_reports for all
  using (auth.uid() = user_id);
