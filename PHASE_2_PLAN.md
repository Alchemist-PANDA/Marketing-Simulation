# Phase 2 Implementation Plan: Auth & Persistence

## 1. Goal
Transition the Marketing-Simulation engine from a stateless local prototype to a multi-user persistent application using Supabase for authentication and data storage.

## 2. Scope
- Supabase project integration.
- User authentication (Sign up / Log in / Log out).
- Persistent storage for Campaigns, Ad Variants, and Simulation Runs.
- Dashboard enhancements for history and data export.
- Reliable "Local Mode" fallback when Supabase is disconnected.

## 3. Non-Goals
- Multi-tenancy/Teams (Phase 3).
- Advanced analytics or cohort analysis.
- Third-party social auth (keeping it to Email/Password or Magic Link for simplicity).
- Database migrations for local SQLite/Postgres (Local mode uses in-memory/JSON).

## 4. Proposed Architecture
```text
[ Streamlit UI ] <---(JWT)---> [ FastAPI Backend ]
       |                              |
       | (Auth/Direct DB)             | (Auth Validation/DB)
       v                              v
[ Supabase Auth ]              [ Supabase Postgres ]
       |                              |
       +------( Local Fallback )------+
                     |
              [ In-Memory/JSON ]
```

## 5. Supabase Schema
### `profiles`
- `id`: uuid (references auth.users)
- `email`: text
- `created_at`: timestamptz

### `campaigns`
- `id`: uuid (primary key)
- `user_id`: uuid (references profiles.id)
- `name`: text
- `channel`: text
- `budget`: float
- `created_at`: timestamptz

### `ad_variants`
- `id`: uuid (primary key)
- `campaign_id`: uuid (references campaigns.id)
- `text`: text
- `price`: float
- `scores_json`: jsonb (price, trust, urgency scores)
- `created_at`: timestamptz

### `simulation_runs`
- `id`: uuid (primary key)
- `variant_id`: uuid (references ad_variants.id)
- `user_id`: uuid (references profiles.id)
- `results_json`: jsonb (likes, conversions, lift, analysis)
- `timestamp`: timestamptz

## 6. Environment Variables
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key # API side only
USE_SUPABASE=true # Set to false for Local Mode
```

## 7. Auth Flow
1. **Streamlit**: User enters credentials in the sidebar.
2. **Supabase**: `auth.signInWithPassword` returns a JWT.
3. **Session**: JWT stored in `st.session_state`.
4. **API Requests**: JWT sent in `Authorization: Bearer <token>` header.
5. **FastAPI**: `src/api/auth.py` validates JWT using Supabase public key or client.

## 8. Persistence Flow
- **Simulation**:
  - User runs `/simulate`.
  - API processes simulation.
  - If `USE_SUPABASE=true`, API saves Variant and Run to DB.
  - Returns results + `database_id`.
- **History**:
  - Streamlit calls `GET /history`.
  - API queries `simulation_runs` filtered by `user_id`.

## 9. Streamlit UX Changes
- **Sidebar**: Login/Signup/Logout forms.
- **Header**: User profile indicator + "Mode: Cloud/Local".
- **Tabs**: 
  - `New Test`: Current UI.
  - `History`: Searchable table of past runs.
- **Export**: "Download CSV" button on result blocks.

## 10. API Changes
- **New Endpoints**:
  - `GET /history`: List user's past simulations.
  - `GET /campaigns`: List user's campaigns.
- **Modified Endpoints**:
  - `POST /simulate`: Add `campaign_id` (optional) and save results to DB.
- **Auth**: Add `get_current_user` dependency to all POST/GET (except `/health`).

## 11. Test Plan
- **Unit**: Mock Supabase client to test fallback logic.
- **Integration**: Test FastAPI Auth dependency with valid/invalid tokens.
- **E2E**: Manual walk-through of Login -> Simulate -> History -> Logout.
- **Determinism**: Verify that persisted results match the re-run of a seeded simulation.

## 12. Deployment Notes ($0 Tier)
- Use Supabase Free Tier (500MB DB).
- Use Streamlit Community Cloud for hosting.
- Set secrets in Streamlit Cloud Dashboard.

## 13. Risks and Rollback Plan
- **Risk**: Supabase connection timeout or rate limit.
- **Mitigation**: Robust `is_active` check and immediate fallback to Local Mode.
- **Rollback**: Git revert Phase 2 commits; the system remains functional in Local Mode.

## 14. Implementation Sequence
1. **2A**: Create `supabase_client.py` wrapper + `.env.example`.
2. **2B**: Implement `auth.py` (FastAPI) and Sidebar Login (Streamlit).
3. **2C**: Create DB tables and implement saving in `/simulate`.
4. **2D**: Implement `GET /history` and the History tab in UI.
5. **2E**: Add export functionality and final documentation.
