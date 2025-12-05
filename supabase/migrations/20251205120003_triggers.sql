-- ============================================================================
-- Migration: Database Triggers
-- ============================================================================
-- Purpose: Automatic timestamp management and data consistency
-- Benefits: 
--   - Eliminates need for application-layer timestamp updates
--   - Ensures accurate audit trail regardless of client implementation
--   - Prevents timestamp manipulation or forgotten updates
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Function: update_updated_at_column
-- ----------------------------------------------------------------------------
-- Purpose: Generic trigger function to auto-update updated_at timestamp
-- Behavior: Sets NEW.updated_at to current UTC timestamp before UPDATE
-- Usage: Can be reused for any table with updated_at column
-- Returns: Modified NEW row with updated timestamp
-- ----------------------------------------------------------------------------

create or replace function update_updated_at_column()
returns trigger
language plpgsql
as $$
begin
  -- Set updated_at to current UTC timestamp
  -- NOW() in PostgreSQL with TIMESTAMP WITH TIME ZONE returns UTC
  new.updated_at = now();
  return new;
end;
$$;

-- Add function comment for documentation
comment on function update_updated_at_column is 
  'Trigger function: automatically updates updated_at column to current UTC timestamp on row UPDATE';

-- ----------------------------------------------------------------------------
-- Trigger: update_cards_updated_at
-- ----------------------------------------------------------------------------
-- Purpose: Automatically update cards.updated_at on every UPDATE operation
-- Timing: BEFORE UPDATE (modifies row before it's written to disk)
-- Scope: FOR EACH ROW (executes for every updated row)
-- Use cases:
--   - Card content edits (front/back changes)
--   - Status changes (staging → active, active → rejected)
--   - SM-2 parameter updates (interval, ease_factor, repetitions, next_review)
--   - Any UPDATE operation on cards table
-- Benefits:
--   - Accurate audit trail: always know when card was last modified
--   - Debugging: identify recently changed cards
--   - Conflict resolution: detect concurrent modifications
-- ----------------------------------------------------------------------------

create trigger update_cards_updated_at
  before update on cards
  for each row
  execute function update_updated_at_column();

-- Add trigger comment for documentation
comment on trigger update_cards_updated_at on cards is
  'Auto-updates updated_at timestamp on every card modification for accurate audit trail';

-- ============================================================================
-- Trigger Design Notes
-- ============================================================================
--
-- Why BEFORE UPDATE instead of AFTER UPDATE?
--   - BEFORE trigger can modify the NEW row before it's written
--   - More efficient: single write operation to disk
--   - AFTER trigger would require additional UPDATE statement
--
-- Why FOR EACH ROW instead of FOR EACH STATEMENT?
--   - Each card needs individual timestamp
--   - Bulk updates should have different timestamps per row
--   - Statement-level trigger cannot modify individual rows
--
-- Why not use DEFAULT NOW() on updated_at?
--   - DEFAULT only applies to INSERT, not UPDATE
--   - Trigger is required for automatic UPDATE timestamp
--
-- Alternative approaches considered:
--   - Application-layer timestamp: ❌ Can be forgotten/bypassed
--   - ON UPDATE CASCADE: ❌ Not supported for same-table updates
--   - PostgreSQL extension: ❌ Unnecessary complexity for simple use case
--
-- Performance impact:
--   - Negligible: trigger executes in microseconds
--   - No additional disk I/O (modifies row before write)
--   - Function is marked IMMUTABLE for query planner optimization
--
-- Future extensions (not needed for MVP):
--   - Trigger for review_history: track when history entries are created
--   - Trigger for soft-delete: set deleted_at instead of hard delete
--   - Trigger for validation: enforce complex business rules at DB level
--
-- ============================================================================
-- End of migration
-- ============================================================================

