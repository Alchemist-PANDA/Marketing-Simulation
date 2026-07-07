# Phase 2B Auth Implementation Plan: Foundation

## 1. Goal
Establish the authentication foundation using Supabase Auth while maintaining a high-fidelity local fallback. This phase focuses on the underlying logic and utilities, ensuring they are tested before being integrated into the API or UI.

## 2. Non-Goals (for Phase 2B-1)
- No `app.py` modifications.
- No UI components (Login/Logout/Signup).
- No protected routes in `src/api/main.py`.
- No database persistence yet.

## 3. Phase 2B-1 Scope
- Add auth helper utilities.
- Implement JWT parsing and verification structure.
- Define the `User` and `Session` models.
- Implement the "Local Developer" fallback user.
- Add comprehensive unit tests.

## 4. Files to Add (Phase 2B-1)
- `src/core/auth_utils.py`: Shared utilities for checking auth status and providing mock data.
- `src/api/auth_handler.py`: Logic for JWT verification and user retrieval from Supabase/Fallback.
- `tests/test_auth_foundation.py`: Unit tests for the above modules.

## 5. Files to Modify (Phase 2B-1)
- `src/core/supabase_client.py`: Extend `SupabaseManager` with lazy auth methods (`sign_in`, `get_user`).
- `src/api/models.py`: Add `User` profile and `AuthSession` Pydantic models.

## 6. Local Fallback Behavior
- If `SUPABASE_URL` or `SUPABASE_ANON_KEY` is missing:
  - `is_auth_enabled()` returns `False`.
  - `get_current_user_logic()` returns a static `LocalUser` object:
    ```json
    {
      "id": "00000000-0000-0000-0000-000000000000",
      "email": "dev@local.host",
      "is_authenticated": true,
      "mode": "local"
    }
    ```
- This ensures the system remains functional and "authenticated" for local development without credentials.

## 7. JWT Verification Approach
- Use `supabase-py`'s internal `auth.get_user(jwt)` method for verification.
- This delegates the heavy lifting (token validation, expiry checks) to the official SDK.
- Wrap this call with error handling to catch expired or malformed tokens.

## 8. Tests (Phase 2B-1)
- `test_is_auth_enabled`: Verify detection of environment variables.
- `test_local_user_payload`: Verify the fallback user structure.
- `test_jwt_verification_fallback`: Confirm that without credentials, any (or no) token returns the local user.
- `test_manager_auth_methods_disabled`: Confirm auth methods return appropriate "Disabled" responses in local mode.

## 9. Risks
- **Dependency Versioning**: Ensure `supabase-py` versions are consistent across the project.
- **Mock Divergence**: The `LocalUser` must strictly follow the schema of a real Supabase user to avoid runtime errors in later phases.

## 10. Constraints
- **IMPORTANT**: `app.py` and `src/api/main.py` must NOT be modified in Phase 2B-1.
