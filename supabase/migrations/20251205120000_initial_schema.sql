-- ============================================================================
-- Migration: Initial Schema - Cards and Review History Tables
-- ============================================================================
-- Purpose: Create core tables for vocab trainer MVP
-- Tables: cards, review_history
-- Dependencies: auth.users (managed by Supabase Auth)
-- Notes: 
--   - auth.users table already exists (Supabase Auth managed)
--   - All tables created in public schema (default)
--   - Foreign keys reference auth.users with CASCADE delete for GDPR compliance
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: cards
-- ----------------------------------------------------------------------------
-- Purpose: Central table storing all user flashcards (staging, active, rejected)
-- Status flow: staging (AI generated) → active (accepted) or rejected
-- SM-2 Algorithm: interval, ease_factor, repetitions, next_review
-- Limits: 500 cards per user (validated in application layer)
-- ----------------------------------------------------------------------------

create table cards (
  -- Primary key
  id uuid primary key default gen_random_uuid(),
  
  -- Foreign key to auth.users (Supabase Auth managed table)
  -- ON DELETE CASCADE: automatic cleanup when user account is deleted (GDPR)
  user_id uuid not null references auth.users(id) on delete cascade,
  
  -- Card content
  front text not null,  -- Question/front side of flashcard
  back text not null,   -- Answer/back side of flashcard
  
  -- Card lifecycle status
  -- staging: AI generated, awaiting user approval
  -- active: accepted by user, included in learning sessions
  -- rejected: dismissed by user, excluded from learning
  status varchar(20) not null check (status in ('staging', 'active', 'rejected')),
  
  -- AI generation metadata
  is_ai_generated boolean not null,  -- false for manually created cards
  generation_batch_id uuid,          -- groups cards from same AI generation (nullable)
  
  -- SM-2 spaced repetition algorithm parameters
  -- interval: days until next review (0 = due now)
  interval integer not null default 0 check (interval >= 0),
  
  -- ease_factor: difficulty multiplier (1.3-3.0, default 2.5)
  -- lower = harder card, higher = easier card
  ease_factor decimal(3,2) not null default 2.50 
    check (ease_factor >= 1.3 and ease_factor <= 3.0),
  
  -- repetitions: count of successful reviews in current learning streak
  repetitions integer not null default 0 check (repetitions >= 0),
  
  -- next_review: UTC timestamp when card should be reviewed next
  -- cards with next_review <= NOW() are due for review
  next_review timestamp with time zone not null default now(),
  
  -- Audit timestamps
  created_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone not null default now()
);

-- Enable Row Level Security (RLS) for cards table
-- Policies will be defined in separate migration
alter table cards enable row level security;

-- Add table comment for documentation
comment on table cards is 'Flashcards for spaced repetition learning with SM-2 algorithm';
comment on column cards.status is 'Lifecycle: staging → active (accepted) or rejected';
comment on column cards.generation_batch_id is 'Groups cards from same AI generation batch';
comment on column cards.interval is 'SM-2: days until next review (0 = due now)';
comment on column cards.ease_factor is 'SM-2: difficulty multiplier (1.3-3.0, default 2.5)';
comment on column cards.repetitions is 'SM-2: count of successful reviews in current streak';

-- ----------------------------------------------------------------------------
-- Table: review_history
-- ----------------------------------------------------------------------------
-- Purpose: Immutable audit log of all flashcard reviews
-- Usage: Analytics, success metrics, learning progress tracking
-- Operations: INSERT and SELECT only (no UPDATE/DELETE - history is immutable)
-- Quality scale: 0=Again, 3=Hard, 4=Good, 5=Easy (SM-2 algorithm)
-- ----------------------------------------------------------------------------

create table review_history (
  -- Primary key
  id uuid primary key default gen_random_uuid(),
  
  -- Foreign key to cards table
  -- ON DELETE CASCADE: remove history when card is deleted
  card_id uuid not null references cards(id) on delete cascade,
  
  -- Foreign key to auth.users (denormalized for query performance)
  -- ON DELETE CASCADE: remove history when user account is deleted (GDPR)
  user_id uuid not null references auth.users(id) on delete cascade,
  
  -- Quality rating from user's self-assessment during review
  -- 0 = Again (complete fail, restart learning)
  -- 3 = Hard (passed with difficulty)
  -- 4 = Good (passed normally)
  -- 5 = Easy (passed easily, increase interval more)
  quality integer not null check (quality in (0, 3, 4, 5)),
  
  -- Timestamp of review (UTC)
  reviewed_at timestamp with time zone not null default now()
);

-- Enable Row Level Security (RLS) for review_history table
-- Policies will be defined in separate migration
alter table review_history enable row level security;

-- Add table comment for documentation
comment on table review_history is 'Immutable audit log of flashcard reviews for analytics and progress tracking';
comment on column review_history.quality is 'SM-2 quality rating: 0=Again, 3=Hard, 4=Good, 5=Easy';
comment on column review_history.user_id is 'Denormalized from cards for efficient queries';

-- ============================================================================
-- End of migration
-- ============================================================================

