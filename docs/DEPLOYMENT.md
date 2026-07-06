# Deployment Guide

This guide covers deploying the Marketing Simulation app to Streamlit Community Cloud with Supabase backend.

## Prerequisites

- GitHub account
- Supabase account (free tier available)
- Streamlit Community Cloud account (free tier available)

## Architecture

- **Frontend**: Streamlit (hosted on Streamlit Community Cloud)
- **Backend**: Supabase (PostgreSQL + Auth)
- **Authentication**: Supabase Auth with JWT tokens
- **Persistence**: PostgreSQL with Row Level Security (RLS)

## Deployment Steps

### 1. Set Up Supabase

1. Create a Supabase project at https://supabase.com
2. Navigate to the SQL Editor in your Supabase dashboard
3. Run the migration script from `supabase/migrations/20260505_initial_schema.sql`
4. Verify tables are created: `campaigns`, `ad_variants`, `simulation_runs`
5. Verify Row Level Security (RLS) is enabled on all tables
6. Copy your project credentials:
   - Project URL (e.g., `https://abcdefgh.supabase.co`)
   - Anon/Public Key (starts with `eyJ...`)

**IMPORTANT**: Never use or expose the `service_role` key in Streamlit. Only use the `anon` key.

### 2. Deploy to Streamlit Community Cloud

1. Push your code to GitHub (if not already done)
2. Sign up at https://share.streamlit.io
3. Click "New app"
4. Connect your GitHub account
5. Select repository: `your-username/Marketing-Simulation`
6. Set main file path: `app.py`
7. Click "Advanced settings"
8. Add secrets in TOML format:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key-here"
```

9. Click "Deploy"

### 3. Create a Test User

After deployment:

1. Visit your deployed app URL
2. The app will show "🔴 Not Authenticated" in the sidebar
3. Use the Supabase dashboard to create a test user:
   - Go to Authentication → Users
   - Click "Add user"
   - Enter email and password
   - Confirm the user
4. Return to your app and log in with the test credentials

### 4. Verify Deployment

Run through the post-deploy checklist in `docs/DEPLOYMENT_CHECKLIST.md`.

## Local Development Setup

### Option 1: Local Mode (No Supabase)

Run the app without Supabase credentials:

```bash
# Do not set SUPABASE_URL or SUPABASE_ANON_KEY
streamlit run app.py
```

**Behavior:**
- Sidebar shows "🟢 Local Developer Mode"
- No authentication required
- Simulation works normally
- Save and History features are disabled

### Option 2: Local Mode with Supabase

Create a `.env` file in the project root (never commit this file):

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
```

Then run:

```bash
streamlit run app.py
```

**Behavior:**
- Sidebar shows "🔴 Not Authenticated" with login form
- Authentication required for save/history features
- All features work as in production

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | No | Supabase project URL. If missing, app runs in local mode. |
| `SUPABASE_ANON_KEY` | No | Supabase anon/public key. If missing, app runs in local mode. |

**Security Notes:**
- Never commit `.env` files to version control
- Never use `SUPABASE_SERVICE_ROLE_KEY` in Streamlit (server-side only)
- The `anon` key is safe to use in client-side code (it's public)
- Row Level Security (RLS) protects user data even with the anon key

## Modes of Operation

### Local Mode
**When:** `SUPABASE_URL` or `SUPABASE_ANON_KEY` environment variables are missing

**Behavior:**
- Streamlit sidebar shows: "🟢 Local Developer Mode"
- No login form displayed
- Simulation works normally
- Save and History features are disabled with clear messaging
- No database queries attempted

### Supabase Mode
**When:** Both `SUPABASE_URL` and `SUPABASE_ANON_KEY` are configured

**Before Login:**
- Streamlit sidebar shows: "🔴 Not Authenticated"
- Login form with email/password fields
- Simulation works normally
- Save and History features are disabled until login

**After Login:**
- Streamlit sidebar shows: "🟢 Logged in as: user@example.com"
- Logout button available
- All features enabled: simulation, save, history, export

**Invalid Credentials:**
- If Supabase credentials are present but invalid, the app will show an error
- The app will NOT fall back to local mode when credentials are invalid
- Fix the credentials in Streamlit secrets or Supabase dashboard

## Troubleshooting

### "Failed to connect to Supabase"
- Verify `SUPABASE_URL` is correct (should start with `https://`)
- Verify `SUPABASE_ANON_KEY` is the anon key, not the service role key
- Check Supabase project status (not paused)

### "Authentication failed"
- Verify user exists in Supabase dashboard (Authentication → Users)
- Verify user is confirmed (not pending email verification)
- Check password is correct

### "Failed to save campaign"
- Verify user is logged in
- Verify RLS policies are enabled on tables
- Check Supabase logs for errors

### "History unavailable"
- Verify user is logged in
- Verify campaigns exist for this user
- Check Supabase table browser for data

### App is slow
- Check Streamlit Cloud resource usage
- Reduce number of agents (default is 500, max is 2000)
- Check Supabase free tier limits (verify current limits at https://supabase.com/pricing)

### Cold start latency
- First load after inactivity may be slow (Streamlit Cloud behavior)
- Subsequent loads should be faster

## Rollback Plan

If deployment fails:

1. Check Streamlit Cloud logs for errors
2. Verify secrets are configured correctly
3. Revert to previous working commit:
   ```bash
   git revert HEAD
   git push origin main
   ```
4. Streamlit Cloud will auto-deploy the reverted commit

## Provider Limits

**Streamlit Community Cloud:**
- Check current limits at https://streamlit.io/cloud

**Supabase Free Tier:**
- Check current limits at https://supabase.com/pricing
- Row Level Security (RLS) prevents data leaks between users

## Security Best Practices

1. Never commit `.env` files
2. Never expose `SUPABASE_SERVICE_ROLE_KEY`
3. Only use `SUPABASE_ANON_KEY` in Streamlit
4. Enable Row Level Security (RLS) on all tables
5. Use strong passwords for user accounts
6. Regularly review Supabase logs for suspicious activity

## Next Steps

After successful deployment:

1. Create user accounts for your team
2. Run test simulations
3. Verify save/history/export features
4. Monitor Streamlit Cloud and Supabase usage
5. Set up monitoring/alerts if needed
