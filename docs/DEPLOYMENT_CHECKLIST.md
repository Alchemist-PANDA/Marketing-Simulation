# Deployment Checklist

## Pre-Deploy Checklist

### Code Quality
- [ ] Run full test suite: `python -m pytest`
- [ ] All tests passing (currently 64 passed, 5 skipped)
- [ ] No syntax errors: `python -m compileall .`
- [ ] No hardcoded secrets in code
- [ ] `.gitignore` excludes `.env` and sensitive files

### Local Testing
- [ ] Test local mode (no Supabase credentials):
  - Remove `SUPABASE_URL` and `SUPABASE_ANON_KEY` from environment
  - Run `streamlit run app.py`
  - Verify sidebar shows "🟢 Local Developer Mode"
  - Verify simulation works
  - Verify save/history are disabled with clear messages

- [ ] Test Supabase mode (with credentials):
  - Set `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`
  - Run `streamlit run app.py`
  - Verify sidebar shows "🔴 Not Authenticated"
  - Verify login form appears
  - Log in with test account
  - Verify sidebar shows "🟢 Logged in as: user@example.com"
  - Run simulation and save results
  - Navigate to History tab and verify saved campaign appears
  - Load campaign details and verify export buttons work
  - Test logout

### Supabase Setup
- [ ] Supabase project created
- [ ] Migration script executed: `supabase/migrations/20260505_initial_schema.sql`
- [ ] Tables created: `campaigns`, `ad_variants`, `simulation_runs`
- [ ] Row Level Security (RLS) enabled on all tables
- [ ] RLS policies verified (users can only access their own data)
- [ ] Test user account created and confirmed
- [ ] Project URL and anon key copied

### Dependencies
- [ ] `requirements.txt` includes all dependencies
- [ ] No unnecessary dependencies added
- [ ] All dependencies are compatible with Streamlit Cloud

### Documentation
- [ ] `README.md` updated with deployment section
- [ ] `docs/DEPLOYMENT.md` complete
- [ ] No secrets exposed in documentation
- [ ] No instructions to use `SUPABASE_SERVICE_ROLE_KEY` in Streamlit

## Deployment Steps

- [ ] Push code to GitHub
- [ ] Sign up at https://share.streamlit.io
- [ ] Connect GitHub account
- [ ] Create new app
- [ ] Select repository and set main file to `app.py`
- [ ] Configure secrets in Streamlit Cloud:
  ```toml
  SUPABASE_URL = "https://your-project.supabase.co"
  SUPABASE_ANON_KEY = "your-anon-key-here"
  ```
- [ ] Deploy app
- [ ] Wait for deployment to complete

## Post-Deploy Smoke Tests

### Basic Functionality
- [ ] App loads without errors
- [ ] No console errors in browser
- [ ] Sidebar renders correctly
- [ ] Main tabs render: "🚀 New Simulation" and "📂 History"

### Authentication
- [ ] Sidebar shows "🔴 Not Authenticated"
- [ ] Login form appears
- [ ] Can log in with test account
- [ ] Sidebar shows "🟢 Logged in as: user@example.com"
- [ ] Logout button appears
- [ ] Logout works and returns to "🔴 Not Authenticated"

### Simulation
- [ ] Can enter ad copy in both text areas
- [ ] Can adjust number of agents (100-2000)
- [ ] Can select marketing channel
- [ ] "Run Simulation" button works
- [ ] Simulation completes successfully
- [ ] Results display: winner, lift, metrics
- [ ] Visualization renders correctly
- [ ] Forensic feedback appears

### Save Results
- [ ] "Save Results" button appears after simulation
- [ ] Button is disabled when not logged in
- [ ] Button is enabled when logged in
- [ ] Clicking button saves campaign
- [ ] Success message appears
- [ ] No errors in console

### History
- [ ] History tab loads
- [ ] Shows "Log in via the sidebar" when not authenticated
- [ ] Shows saved campaigns when authenticated
- [ ] Campaign list displays name, channel, date
- [ ] "Load Details" button works
- [ ] Campaign details show Ad A and Ad B comparison
- [ ] Metrics display correctly

### Export
- [ ] Current result export buttons appear after simulation
- [ ] "Download JSON" works (file downloads)
- [ ] "Download CSV" works (file downloads)
- [ ] JSON file contains full result structure
- [ ] CSV file contains Ad A and Ad B rows
- [ ] Campaign export buttons appear after loading campaign details
- [ ] Campaign JSON includes campaign, variants, runs
- [ ] Campaign CSV has one row per variant
- [ ] Filenames are distinct (simulation_result vs campaign_{id})

### Performance
- [ ] Simulation with 500 agents completes in reasonable time
- [ ] No memory errors
- [ ] No timeout errors
- [ ] App remains responsive after multiple simulations

### Error Handling
- [ ] Invalid login shows error message
- [ ] Failed save shows error message
- [ ] Failed history load shows error message
- [ ] No silent failures

## Rollback Plan

If deployment fails or critical issues are found:

1. **Immediate Rollback:**
   ```bash
   git revert HEAD
   git push origin main
   ```
   Streamlit Cloud will auto-deploy the reverted commit.

2. **Investigate Issues:**
   - Check Streamlit Cloud logs
   - Check Supabase logs
   - Verify secrets configuration
   - Test locally with same configuration

3. **Fix and Redeploy:**
   - Fix issues in a new commit
   - Test locally
   - Push to GitHub
   - Verify deployment

## Monitoring

After deployment:

- [ ] Monitor Streamlit Cloud resource usage
- [ ] Monitor Supabase database size
- [ ] Monitor Supabase bandwidth usage
- [ ] Check for errors in Streamlit Cloud logs
- [ ] Check for errors in Supabase logs
- [ ] Verify user feedback

## Notes

- Streamlit Community Cloud free tier limits: Check https://streamlit.io/cloud for current limits
- Supabase free tier limits: Check https://supabase.com/pricing for current limits
- Cold start latency is normal after inactivity
- First simulation may be slower due to model initialization
