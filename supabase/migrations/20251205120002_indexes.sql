-- ============================================================================
-- Migration: Performance Indexes
-- ============================================================================
-- Purpose: Create indexes for optimizing frequent queries
-- Strategy: Composite indexes for multi-column WHERE clauses
-- Performance target: < 100ms query execution time for 500 cards per user
-- Expected index hit rate: > 95%
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Indexes for table: cards
-- ----------------------------------------------------------------------------

-- Index: idx_cards_user_next_review (PRIORITY: HIGH)
-- Purpose: Optimize main use case - selecting cards due for review
-- Query: SELECT * FROM cards 
--        WHERE user_id = ? AND status = 'active' AND next_review <= NOW()
-- Performance: O(log n) lookup for composite key
-- Usage frequency: Every learning session (multiple times per day per user)
create index idx_cards_user_next_review on cards(user_id, next_review);

-- Index: idx_cards_user_status
-- Purpose: Fast filtering of cards by lifecycle status
-- Query: SELECT * FROM cards WHERE user_id = ? AND status = ?
-- Use cases:
--   - Dashboard: display staging/active/rejected cards separately
--   - Card management: bulk operations on cards in specific status
--   - Analytics: count cards by status
create index idx_cards_user_status on cards(user_id, status);

-- Index: idx_cards_user_ai_generated
-- Purpose: Calculate MVP success metrics (AI Usage Rate)
-- Query: SELECT COUNT(*) FROM cards 
--        WHERE user_id = ? AND is_ai_generated = true
-- Use cases:
--   - Analytics: AI-generated vs manually created cards ratio
--   - Success metric: AI Usage Rate = (ai_cards / total_cards) * 100%
--   - User profile: display AI usage statistics
create index idx_cards_user_ai_generated on cards(user_id, is_ai_generated);

-- Index: idx_cards_generation_batch
-- Purpose: Group operations on AI-generated card batches
-- Query: SELECT * FROM cards WHERE generation_batch_id = ?
-- Use cases:
--   - Bulk accept: move all cards from batch to active status
--   - Bulk reject: move all cards from batch to rejected status
--   - Display: show cards grouped by generation batch in staging area
create index idx_cards_generation_batch on cards(generation_batch_id) 
  where generation_batch_id is not null;

-- Index: idx_cards_search (GIN index for full-text search)
-- Purpose: Full-text search across card front and back content
-- Query: SELECT * FROM cards 
--        WHERE user_id = ? 
--          AND to_tsvector('english', front || ' ' || back) 
--              @@ plainto_tsquery('english', ?)
-- Use cases:
--   - Search functionality: find cards by keywords
--   - Content discovery: locate specific topics in card collection
-- Note: GIN index is optimized for text search operations
create index idx_cards_search on cards 
  using gin (to_tsvector('english', coalesce(front, '') || ' ' || coalesce(back, '')));

-- ----------------------------------------------------------------------------
-- Indexes for table: review_history
-- ----------------------------------------------------------------------------

-- Index: idx_review_history_card
-- Purpose: Retrieve review history for specific card
-- Query: SELECT * FROM review_history WHERE card_id = ?
-- Use cases:
--   - Card details view: show learning progress for individual card
--   - Analytics: analyze difficulty trends for specific card
--   - Debugging: verify SM-2 algorithm calculations
create index idx_review_history_card on review_history(card_id);

-- Index: idx_review_history_user_time
-- Purpose: Analyze user activity and learning patterns over time
-- Query: SELECT * FROM review_history 
--        WHERE user_id = ? AND reviewed_at >= ? 
--        ORDER BY reviewed_at DESC
-- Use cases:
--   - Dashboard: display recent review activity
--   - Statistics: calculate daily/weekly/monthly review counts
--   - Success metrics: calculate retention rate over time periods
--   - Progress tracking: show learning streaks and consistency
-- Note: Composite index supports both filtering and sorting
create index idx_review_history_user_time on review_history(user_id, reviewed_at desc);

-- ============================================================================
-- Index Performance Notes
-- ============================================================================
-- 
-- Expected storage overhead:
--   - Composite indexes: ~20% of table size
--   - GIN full-text index: ~50% of text column size
--   - Total: ~100KB per user with 500 cards
--
-- Index maintenance:
--   - Auto-updated on INSERT/UPDATE/DELETE
--   - VACUUM ANALYZE recommended weekly for optimal performance
--   - Monitor with pg_stat_user_indexes view
--
-- Query planner:
--   - PostgreSQL automatically selects best index
--   - Use EXPLAIN ANALYZE to verify index usage
--   - Indexes are most effective for selective queries (< 10% of rows)
--
-- ============================================================================
-- End of migration
-- ============================================================================

