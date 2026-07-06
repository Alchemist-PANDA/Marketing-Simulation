# Supabase Setup Guide

This guide explains how to set up a free-tier Supabase project for persistence and authentication in the Marketing Simulation project.

## 1. Create Supabase Project
1. Go to [Supabase](https://supabase.com/) and create a new project.
2. Note your **Project URL** and **Anon Key** from the project settings.

## 2. Initialize Database
Go to the **SQL Editor** in your Supabase dashboard and run the contents of the following file:
- `supabase/migrations/20260505_initial_schema.sql`

This will create the necessary tables (`profiles`, `campaigns`, `ad_variants`, `simulation_runs`) and set up Row Level Security (RLS) policies.

## 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```bash
SUPABASE_URL=your-project-url
SUPABASE_ANON_KEY=your-anon-key
APP_ENV=local
```

### Streamlit Secrets (for Deployment)
When deploying to Streamlit Community Cloud, add these to your app's "Secrets":
```toml
SUPABASE_URL = "your-project-url"
SUPABASE_ANON_KEY = "your-anon-key"
APP_ENV = "production"
```

## 4. Local Development (No-Persistence Mode)
If you do not provide Supabase environment variables, the application will automatically enter **Local Mode**.
- Persistence will be disabled.
- Authentication will be bypassed with a default "Local Developer" profile.
- All simulation results will be ephemeral.

## ⚠️ Security Note
**NEVER** expose the `SUPABASE_SERVICE_ROLE_KEY` in Streamlit secrets or client-side code. This key bypasses all RLS policies and should only be used in secure, server-side environments.
