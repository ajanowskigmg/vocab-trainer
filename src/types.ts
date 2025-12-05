import type { Database } from './db/database.types';

// ============================================================================
// DATABASE ENTITY TYPES
// ============================================================================

// Base entity types derived directly from database schema
export type CardEntity = Database['public']['Tables']['cards']['Row'];
export type CardInsert = Database['public']['Tables']['cards']['Insert'];
export type CardUpdate = Database['public']['Tables']['cards']['Update'];

export type ReviewHistoryEntity = Database['public']['Tables']['review_history']['Row'];
export type ReviewHistoryInsert = Database['public']['Tables']['review_history']['Insert'];
export type ReviewHistoryUpdate = Database['public']['Tables']['review_history']['Update'];

// ============================================================================
// ENUMS AND CONSTANTS
// ============================================================================

/**
 * Card status in the application workflow
 * - staging: AI-generated cards awaiting user review
 * - active: Cards available for learning
 * - rejected: Cards explicitly rejected by user
 */
export type CardStatus = 'staging' | 'active' | 'rejected';

/**
 * SM-2 algorithm quality ratings
 * - 0: Again (complete blackout)
 * - 3: Hard (correct response with serious difficulty)
 * - 4: Good (correct response after hesitation)
 * - 5: Easy (perfect response)
 */
export type QualityRating = 0 | 3 | 4 | 5;

/**
 * Sort options for cards listing
 */
export type CardSortBy = 'createdAt' | 'nextReview' | 'alphabetical';

/**
 * Sort order
 */
export type SortOrder = 'asc' | 'desc';

/**
 * Statistics period filter
 */
export type StatsPeriod = 'today' | 'week' | 'month' | 'all';

// ============================================================================
// SHARED DTOs
// ============================================================================

/**
 * Standard API response wrapper for successful operations
 */
export interface ApiSuccessResponse<T> {
  success: true;
  message?: string;
  data: T;
}

/**
 * Standard API response wrapper for errors
 */
export interface ApiErrorResponse {
  success: false;
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

/**
 * Combined API response type
 */
export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse;

/**
 * Pagination metadata
 */
export interface PaginationMeta {
  page: number;
  limit: number;
  totalItems: number;
  totalPages: number;
  hasMore: boolean;
}

/**
 * Paginated response wrapper
 */
export interface PaginatedData<T> {
  items: T[];
  pagination: PaginationMeta;
}

// ============================================================================
// CARD DTOs
// ============================================================================

/**
 * Card DTO - Public representation of a card
 * Transforms database entity field names from snake_case to camelCase
 */
export interface CardDto {
  id: string;
  front: string;
  back: string;
  status: CardStatus;
  isAiGenerated: boolean;
  generationBatchId: string | null;
  interval: number;
  easeFactor: number;
  repetitions: number;
  nextReview: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Minimal card DTO for learning sessions
 * Omits user_id and timestamps for privacy and reduced payload
 */
export type LearningCardDto = Pick<
  CardDto,
  'id' | 'front' | 'back' | 'interval' | 'easeFactor' | 'repetitions'
>;

/**
 * Card DTO with status for session views
 */
export type SessionCardDto = Pick<
  CardDto,
  'id' | 'front' | 'back' | 'status' | 'isAiGenerated' | 'interval' | 'easeFactor' | 'repetitions' | 'nextReview'
>;

/**
 * Minimal card reference for nested responses
 */
export type CardReference = Pick<CardDto, 'front' | 'back'>;

/**
 * SM-2 algorithm metadata
 */
export type SM2Metadata = Pick<CardDto, 'interval' | 'easeFactor' | 'repetitions' | 'nextReview'>;

// ============================================================================
// REVIEW HISTORY DTOs
// ============================================================================

/**
 * Review history DTO - Public representation of a review record
 */
export interface ReviewHistoryDto {
  id: string;
  cardId: string;
  quality: QualityRating;
  reviewedAt: string;
}

/**
 * Review with nested card information
 */
export interface ReviewWithCardDto extends ReviewHistoryDto {
  card: CardReference;
}

// ============================================================================
// USER DTOs
// ============================================================================

/**
 * User statistics DTO
 */
export interface UserStatsDto {
  totalCards: number;
  aiGeneratedCards: number;
  manualCards: number;
  rejectedCards: number;
  activeCards: number;
  stagingCards: number;
}

/**
 * User profile DTO
 */
export interface UserProfileDto {
  userId: string;
  email: string;
  createdAt: string;
  stats: UserStatsDto;
}

/**
 * Minimal user data DTO
 */
export type UserDataDto = Pick<UserProfileDto, 'userId' | 'email' | 'createdAt'>;

// ============================================================================
// AUTHENTICATION COMMAND MODELS
// ============================================================================

/**
 * Command: Register new user
 */
export interface RegisterCommand {
  email: string;
  password: string;
  gdprConsent: boolean;
}

/**
 * Response: User registration
 */
export interface RegisterResponseDto {
  userId: string;
  email: string;
  emailConfirmed: boolean;
}

/**
 * Command: User login
 */
export interface LoginCommand {
  email: string;
  password: string;
  rememberMe?: boolean;
}

/**
 * Response: User login (reuses UserDataDto)
 */
export type LoginResponseDto = UserDataDto;

/**
 * Command: Request password reset
 */
export interface ResetPasswordCommand {
  email: string;
}

/**
 * Command: Change password
 */
export interface ChangePasswordCommand {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

// ============================================================================
// CARD MANAGEMENT COMMAND MODELS
// ============================================================================

/**
 * Command: Create manual card
 */
export interface CreateCardCommand {
  front: string;
  back: string;
}

/**
 * Command: Update card content
 */
export interface UpdateCardCommand {
  front?: string;
  back?: string;
}

/**
 * Command: Update card status
 */
export interface UpdateCardStatusCommand {
  status: CardStatus;
}

/**
 * Command: Batch update card status
 */
export interface BatchUpdateCardStatusCommand {
  cardIds?: string[];
  generationBatchId?: string;
  status: CardStatus;
}

/**
 * Response: Batch update result
 */
export interface BatchUpdateResponseDto {
  updatedCount: number;
  cardIds: string[];
}

/**
 * Query parameters: Get cards with filters
 */
export interface GetCardsQuery {
  status?: CardStatus | 'all';
  isAiGenerated?: boolean;
  search?: string;
  sortBy?: CardSortBy;
  sortOrder?: SortOrder;
  page?: number;
  limit?: number;
}

/**
 * Response: Cards list with pagination
 */
export interface GetCardsResponseDto {
  cards: CardDto[];
  pagination: PaginationMeta;
}

/**
 * Response: Due cards
 */
export interface GetDueCardsResponseDto {
  cards: SessionCardDto[];
  totalDue: number;
}

// ============================================================================
// AI GENERATION COMMAND MODELS
// ============================================================================

/**
 * Command: Generate cards from text using AI
 */
export interface GenerateCardsCommand {
  text: string;
  model?: string;
}

/**
 * AI generation metadata
 */
export interface GenerationMetadataDto {
  model: string;
  tokensUsed: number;
  estimatedCost: number;
}

/**
 * Response: AI card generation result
 */
export interface GenerateCardsResponseDto {
  generationBatchId: string;
  cards: CardDto[];
  metadata: GenerationMetadataDto;
}

// ============================================================================
// LEARNING SESSION COMMAND MODELS
// ============================================================================

/**
 * Query parameters: Start learning session
 */
export interface StartLearningSessionQuery {
  limit?: number;
}

/**
 * Response: Learning session initialized
 */
export interface StartLearningSessionResponseDto {
  sessionId: string;
  cards: LearningCardDto[];
  totalCards: number;
  startedAt: string;
}

/**
 * Command: Submit card review
 */
export interface SubmitReviewCommand {
  cardId: string;
  quality: QualityRating;
}

/**
 * Response: Review submission result
 */
export interface SubmitReviewResponseDto {
  cardId: string;
  quality: QualityRating;
  updatedCard: SM2Metadata;
  reviewHistoryId: string;
}

/**
 * Quality breakdown for statistics
 */
export interface QualityBreakdownDto {
  again: number;
  hard: number;
  good: number;
  easy: number;
}

/**
 * Review count by date
 */
export interface ReviewByDateDto {
  date: string;
  count: number;
}

/**
 * Query parameters: Get learning statistics
 */
export interface GetLearningStatsQuery {
  period?: StatsPeriod;
}

/**
 * Response: Learning statistics
 */
export interface GetLearningStatsResponseDto {
  period: StatsPeriod;
  totalReviews: number;
  breakdown: QualityBreakdownDto;
  averageQuality: number;
  dueToday: number;
  nextReviewDate: string | null;
  streakDays: number;
  reviewsByDate: ReviewByDateDto[];
}

// ============================================================================
// REVIEW HISTORY COMMAND MODELS
// ============================================================================

/**
 * Query parameters: Get review history
 */
export interface GetReviewsQuery {
  cardId?: string;
  startDate?: string;
  endDate?: string;
  page?: number;
  limit?: number;
}

/**
 * Response: Review history list with pagination
 */
export interface GetReviewsResponseDto {
  reviews: ReviewWithCardDto[];
  pagination: PaginationMeta;
}

/**
 * Response: Card-specific review history
 */
export interface GetCardReviewsResponseDto {
  cardId: string;
  reviews: ReviewHistoryDto[];
  totalReviews: number;
  averageQuality: number;
}

// ============================================================================
// HEALTH CHECK DTO
// ============================================================================

/**
 * Response: API health check
 */
export interface HealthCheckResponseDto {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
}

// ============================================================================
// ERROR DETAILS DTOs
// ============================================================================

/**
 * Validation error details
 */
export interface ValidationErrorDetails {
  field: string;
  [key: string]: unknown;
}

/**
 * Card limit error details
 */
export interface CardLimitErrorDetails {
  currentCount: number;
  maxLimit: number;
}

/**
 * Rate limit error details
 */
export interface RateLimitErrorDetails {
  retryAfter: number;
}

/**
 * AI service error details
 */
export interface AiServiceErrorDetails {
  reason: string;
}

/**
 * Budget exceeded error details
 */
export interface BudgetExceededErrorDetails {
  resetDate: string;
}

// ============================================================================
// UTILITY TYPES
// ============================================================================

/**
 * Transform database entity to DTO
 * Converts snake_case field names to camelCase
 */
export function transformCardEntityToDto(entity: CardEntity): CardDto {
  return {
    id: entity.id,
    front: entity.front,
    back: entity.back,
    status: entity.status as CardStatus,
    isAiGenerated: entity.is_ai_generated,
    generationBatchId: entity.generation_batch_id,
    interval: entity.interval,
    easeFactor: entity.ease_factor,
    repetitions: entity.repetitions,
    nextReview: entity.next_review,
    createdAt: entity.created_at,
    updatedAt: entity.updated_at,
  };
}

/**
 * Transform review entity to DTO
 */
export function transformReviewEntityToDto(entity: ReviewHistoryEntity): ReviewHistoryDto {
  return {
    id: entity.id,
    cardId: entity.card_id,
    quality: entity.quality as QualityRating,
    reviewedAt: entity.reviewed_at,
  };
}

/**
 * Create API success response
 */
export function createSuccessResponse<T>(data: T, message?: string): ApiSuccessResponse<T> {
  return {
    success: true,
    ...(message && { message }),
    data,
  };
}

/**
 * Create API error response
 */
export function createErrorResponse(
  error: string,
  message: string,
  details?: Record<string, unknown>
): ApiErrorResponse {
  return {
    success: false,
    error,
    message,
    ...(details && { details }),
  };
}

