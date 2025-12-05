-- ============================================================================
-- Migration: Row Level Security (RLS) Policies
-- ============================================================================
-- Purpose: Define granular access control policies for cards and review_history
-- Security Model: Users can only access their own data
-- Roles: 
--   - anon: unauthenticated users (no access to data)
--   - authenticated: logged-in users (access to own data only)
-- Notes:
--   - Policies are granular: separate policy per operation (select, insert, update, delete)
--   - Policies are role-specific: separate policy per Supabase role
--   - auth.uid() returns the currently authenticated user's UUID
-- ============================================================================

-- ----------------------------------------------------------------------------
-- RLS Policies for table: cards
-- ----------------------------------------------------------------------------
-- Access pattern: Users can fully manage (CRUD) their own flashcards
-- Security: auth.uid() = user_id ensures data isolation between users
-- ----------------------------------------------------------------------------

-- Policy: Anonymous users cannot select any cards
create policy "anon_cannot_select_cards" on cards
  as permissive
  for select
  to anon
  using (false);

-- Policy: Authenticated users can select only their own cards
create policy "authenticated_select_own_cards" on cards
  as permissive
  for select
  to authenticated
  using (auth.uid() = user_id);

-- Policy: Anonymous users cannot insert any cards
create policy "anon_cannot_insert_cards" on cards
  as permissive
  for insert
  to anon
  with check (false);

-- Policy: Authenticated users can insert cards only for themselves
-- WITH CHECK ensures user_id in inserted row matches authenticated user
create policy "authenticated_insert_own_cards" on cards
  as permissive
  for insert
  to authenticated
  with check (auth.uid() = user_id);

-- Policy: Anonymous users cannot update any cards
create policy "anon_cannot_update_cards" on cards
  as permissive
  for update
  to anon
  using (false);

-- Policy: Authenticated users can update only their own cards
-- USING clause: which rows can be selected for update
-- WITH CHECK clause: ensures updated row still belongs to user
create policy "authenticated_update_own_cards" on cards
  as permissive
  for update
  to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- Policy: Anonymous users cannot delete any cards
create policy "anon_cannot_delete_cards" on cards
  as permissive
  for delete
  to anon
  using (false);

-- Policy: Authenticated users can delete only their own cards
create policy "authenticated_delete_own_cards" on cards
  as permissive
  for delete
  to authenticated
  using (auth.uid() = user_id);

-- ----------------------------------------------------------------------------
-- RLS Policies for table: review_history
-- ----------------------------------------------------------------------------
-- Access pattern: Users can view and create their own review history
-- Immutability: No UPDATE or DELETE policies (history is append-only)
-- Security: auth.uid() = user_id ensures data isolation between users
-- ----------------------------------------------------------------------------

-- Policy: Anonymous users cannot select any review history
create policy "anon_cannot_select_reviews" on review_history
  as permissive
  for select
  to anon
  using (false);

-- Policy: Authenticated users can select only their own review history
create policy "authenticated_select_own_reviews" on review_history
  as permissive
  for select
  to authenticated
  using (auth.uid() = user_id);

-- Policy: Anonymous users cannot insert any review history
create policy "anon_cannot_insert_reviews" on review_history
  as permissive
  for insert
  to anon
  with check (false);

-- Policy: Authenticated users can insert review history only for themselves
-- WITH CHECK ensures user_id in inserted row matches authenticated user
-- Note: Application must validate card_id belongs to same user
create policy "authenticated_insert_own_reviews" on review_history
  as permissive
  for insert
  to authenticated
  with check (auth.uid() = user_id);

-- ----------------------------------------------------------------------------
-- No UPDATE or DELETE policies for review_history
-- ----------------------------------------------------------------------------
-- Rationale: Review history is immutable audit log
-- Operations: Only INSERT (create new entries) and SELECT (read history)
-- Data retention: History is deleted only via CASCADE when user/card is deleted
-- ----------------------------------------------------------------------------

-- ============================================================================
-- End of migration
-- ============================================================================

