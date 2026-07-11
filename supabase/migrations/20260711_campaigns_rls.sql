-- Migration: explicit Row-Level-Security policies for campaigns
-- --------------------------------------------------------------
-- The initial schema already ships a single `FOR ALL USING (auth.uid() = user_id)`
-- policy on public.campaigns, which is functionally sufficient. This migration
-- makes the intent explicit with one policy per operation (and an explicit
-- WITH CHECK on INSERT/UPDATE), which is easier to audit and matches the naming
-- used elsewhere.
--
-- IMPORTANT: RLS only works if the request carries the *user's* JWT so that
-- Postgres can resolve auth.uid(). The app now attaches the logged-in user's
-- access token to every PostgREST call (see SupabaseManager._apply_user_auth).
-- Without that step auth.uid() is NULL and every insert fails with
-- "new row violates row-level security policy for table \"campaigns\"".

alter table public.campaigns enable row level security;

-- Replace the broad catch-all with explicit per-operation policies.
drop policy if exists "Users can manage own campaigns" on public.campaigns;
drop policy if exists "Users can insert their own campaigns" on public.campaigns;
drop policy if exists "Users can view their own campaigns"  on public.campaigns;
drop policy if exists "Users can update their own campaigns" on public.campaigns;
drop policy if exists "Users can delete their own campaigns" on public.campaigns;

create policy "Users can insert their own campaigns"
  on public.campaigns for insert
  with check (auth.uid() = user_id);

create policy "Users can view their own campaigns"
  on public.campaigns for select
  using (auth.uid() = user_id);

create policy "Users can update their own campaigns"
  on public.campaigns for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "Users can delete their own campaigns"
  on public.campaigns for delete
  using (auth.uid() = user_id);
