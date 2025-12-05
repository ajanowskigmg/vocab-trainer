# REST API Plan - Vocab Trainer MVP

## 1. Overview

This API plan outlines the REST endpoints for the Vocab Trainer application, built with Astro API routes and Supabase backend. The API follows RESTful principles and leverages Supabase Row Level Security (RLS) for data isolation.

**Base URL:** `/api`  
**Authentication:** Supabase Auth with JWT tokens in HTTP-only cookies  
**Content-Type:** `application/json`

## 2. Resources

### Primary Resources

| Resource | Database Table | Description |
|----------|---------------|-------------|
| **Cards** | `public.cards` | Flashcards (manual and AI-generated) with SM-2 metadata |
| **Reviews** | `public.review_history` | Learning session review history |
| **User** | `auth.users` | User authentication and profile (managed by Supabase Auth) |

### Virtual Resources

| Resource | Description |
|----------|-------------|
| **Learning Sessions** | Orchestrates learning flow with SM-2 algorithm |
| **AI Generation** | Handles AI card generation with staging workflow |

## 3. Authentication Endpoints

### 3.1. Register User

**Endpoint:** `POST /api/auth/register`

**Description:** Creates a new user account with email verification.

**Request Payload:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "gdprConsent": true
}
```

**Validation:**
- `email`: Valid email format, required
- `password`: Minimum 8 characters, required
- `gdprConsent`: Must be `true`, required

**Success Response (201 Created):**
```json
{
  "success": true,
  "message": "Registration successful. Please check your email to verify your account.",
  "data": {
    "userId": "uuid-here",
    "email": "user@example.com",
    "emailConfirmed": false
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input, missing GDPR consent
```json
{
  "success": false,
  "error": "VALIDATION_ERROR",
  "message": "Password must be at least 8 characters",
  "details": {
    "field": "password"
  }
}
```
- `409 Conflict`: Email already registered
```json
{
  "success": false,
  "error": "EMAIL_EXISTS",
  "message": "This email is already registered"
}
```

---

### 3.2. Login

**Endpoint:** `POST /api/auth/login`

**Description:** Authenticates user and creates session.

**Request Payload:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "rememberMe": false
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "userId": "uuid-here",
    "email": "user@example.com",
    "createdAt": "2023-12-05T10:30:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
```json
{
  "success": false,
  "error": "INVALID_CREDENTIALS",
  "message": "Invalid email or password"
}
```
- `403 Forbidden`: Email not verified
```json
{
  "success": false,
  "error": "EMAIL_NOT_VERIFIED",
  "message": "Please verify your email before logging in"
}
```

---

### 3.3. Logout

**Endpoint:** `POST /api/auth/logout`

**Description:** Terminates user session.

**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

### 3.4. Request Password Reset

**Endpoint:** `POST /api/auth/reset-password`

**Description:** Sends password reset email.

**Request Payload:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "If an account exists with this email, you will receive a password reset link"
}
```

**Note:** Response is identical whether email exists or not (security best practice).

---

### 3.5. Change Password

**Endpoint:** `POST /api/auth/change-password`

**Description:** Changes password for authenticated user.

**Authentication:** Required

**Request Payload:**
```json
{
  "currentPassword": "oldPassword123",
  "newPassword": "newPassword456",
  "confirmPassword": "newPassword456"
}
```

**Validation:**
- `newPassword`: Minimum 8 characters, different from current
- `newPassword` must match `confirmPassword`

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid current password
- `400 Bad Request`: Validation error

---

### 3.6. Get User Profile

**Endpoint:** `GET /api/auth/profile`

**Description:** Retrieves authenticated user's profile and statistics.

**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "userId": "uuid-here",
    "email": "user@example.com",
    "createdAt": "2023-12-05T10:30:00Z",
    "stats": {
      "totalCards": 150,
      "aiGeneratedCards": 120,
      "manualCards": 30,
      "rejectedCards": 15,
      "activeCards": 135,
      "stagingCards": 0
    }
  }
}
```

---

## 4. Card Management Endpoints

### 4.1. Create Manual Card

**Endpoint:** `POST /api/cards`

**Description:** Creates a single manual flashcard.

**Authentication:** Required

**Request Payload:**
```json
{
  "front": "What is the capital of France?",
  "back": "Paris"
}
```

**Validation:**
- Both `front` and `back` are required (non-empty strings)
- User must not exceed 500 active cards limit
- Maximum length: 5000 characters per field (optional)

**Success Response (201 Created):**
```json
{
  "success": true,
  "message": "Card created successfully",
  "data": {
    "id": "uuid-here",
    "front": "What is the capital of France?",
    "back": "Paris",
    "status": "active",
    "isAiGenerated": false,
    "interval": 0,
    "easeFactor": 2.5,
    "repetitions": 0,
    "nextReview": "2023-12-05T10:30:00Z",
    "createdAt": "2023-12-05T10:30:00Z",
    "updatedAt": "2023-12-05T10:30:00Z"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Validation error
- `403 Forbidden`: Card limit reached (500 cards)
```json
{
  "success": false,
  "error": "CARD_LIMIT_REACHED",
  "message": "You have reached the maximum limit of 500 cards. Please delete some cards to add new ones.",
  "details": {
    "currentCount": 500,
    "maxLimit": 500
  }
}
```

---

### 4.2. Get All Cards

**Endpoint:** `GET /api/cards`

**Description:** Retrieves user's cards with filtering, sorting, and pagination.

**Authentication:** Required

**Query Parameters:**
- `status` (optional): Filter by status - `staging`, `active`, `rejected`, or `all` (default: `all`)
- `isAiGenerated` (optional): Filter by source - `true`, `false`, or omit for all
- `search` (optional): Full-text search in front/back fields
- `sortBy` (optional): `createdAt`, `nextReview`, `alphabetical` (default: `createdAt`)
- `sortOrder` (optional): `asc`, `desc` (default: `desc`)
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 50, max: 100)

**Example Request:**
```
GET /api/cards?status=active&isAiGenerated=true&sortBy=nextReview&sortOrder=asc&page=1&limit=20
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "cards": [
      {
        "id": "uuid-1",
        "front": "Question text",
        "back": "Answer text",
        "status": "active",
        "isAiGenerated": true,
        "generationBatchId": "batch-uuid",
        "interval": 3,
        "easeFactor": 2.5,
        "repetitions": 2,
        "nextReview": "2023-12-08T10:30:00Z",
        "createdAt": "2023-12-05T10:30:00Z",
        "updatedAt": "2023-12-07T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "totalItems": 150,
      "totalPages": 8,
      "hasMore": true
    }
  }
}
```

---

### 4.3. Get Single Card

**Endpoint:** `GET /api/cards/{cardId}`

**Description:** Retrieves a single card by ID.

**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "uuid-here",
    "front": "Question text",
    "back": "Answer text",
    "status": "active",
    "isAiGenerated": true,
    "generationBatchId": "batch-uuid",
    "interval": 3,
    "easeFactor": 2.5,
    "repetitions": 2,
    "nextReview": "2023-12-08T10:30:00Z",
    "createdAt": "2023-12-05T10:30:00Z",
    "updatedAt": "2023-12-07T10:30:00Z"
  }
}
```

**Error Responses:**
- `404 Not Found`: Card doesn't exist or doesn't belong to user

---

### 4.4. Update Card

**Endpoint:** `PUT /api/cards/{cardId}`

**Description:** Updates card content. Does not modify SM-2 metadata.

**Authentication:** Required

**Request Payload:**
```json
{
  "front": "Updated question text",
  "back": "Updated answer text"
}
```

**Validation:**
- At least one field (`front` or `back`) must be provided
- Fields cannot be empty strings

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Card updated successfully",
  "data": {
    "id": "uuid-here",
    "front": "Updated question text",
    "back": "Updated answer text",
    "status": "active",
    "isAiGenerated": true,
    "interval": 3,
    "easeFactor": 2.5,
    "repetitions": 2,
    "nextReview": "2023-12-08T10:30:00Z",
    "createdAt": "2023-12-05T10:30:00Z",
    "updatedAt": "2023-12-07T14:20:00Z"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Validation error
- `404 Not Found`: Card doesn't exist or doesn't belong to user

---

### 4.5. Update Card Status

**Endpoint:** `PATCH /api/cards/{cardId}/status`

**Description:** Changes card status (accept, reject, restore).

**Authentication:** Required

**Request Payload:**
```json
{
  "status": "active"
}
```

**Validation:**
- `status` must be one of: `staging`, `active`, `rejected`

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Card status updated successfully",
  "data": {
    "id": "uuid-here",
    "status": "active"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid status value
- `404 Not Found`: Card doesn't exist or doesn't belong to user

---

### 4.6. Delete Card

**Endpoint:** `DELETE /api/cards/{cardId}`

**Description:** Permanently deletes a card and its review history.

**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Card deleted successfully"
}
```

**Error Responses:**
- `404 Not Found`: Card doesn't exist or doesn't belong to user

---

### 4.7. Batch Update Card Status

**Endpoint:** `PATCH /api/cards/batch/status`

**Description:** Updates status for multiple cards (e.g., "Accept all" from staging).

**Authentication:** Required

**Request Payload:**
```json
{
  "cardIds": ["uuid-1", "uuid-2", "uuid-3"],
  "status": "active"
}
```

**Alternative for generation batch:**
```json
{
  "generationBatchId": "batch-uuid",
  "status": "active"
}
```

**Validation:**
- Either `cardIds` array or `generationBatchId` must be provided
- `status` must be valid

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Updated 8 cards successfully",
  "data": {
    "updatedCount": 8,
    "cardIds": ["uuid-1", "uuid-2", "uuid-3", "..."]
  }
}
```

---

### 4.8. Get Cards Due for Review

**Endpoint:** `GET /api/cards/due`

**Description:** Retrieves cards scheduled for review (next_review <= now, status = active).

**Authentication:** Required

**Query Parameters:**
- `limit` (optional): Maximum number of cards (default: no limit)

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "cards": [
      {
        "id": "uuid-1",
        "front": "Question text",
        "back": "Answer text",
        "status": "active",
        "isAiGenerated": true,
        "interval": 3,
        "easeFactor": 2.5,
        "repetitions": 2,
        "nextReview": "2023-12-05T10:30:00Z"
      }
    ],
    "totalDue": 25
  }
}
```

---

## 5. AI Generation Endpoints

### 5.1. Generate Cards from Text

**Endpoint:** `POST /api/ai/generate-cards`

**Description:** Generates flashcards from user-provided text using AI.

**Authentication:** Required

**Request Payload:**
```json
{
  "text": "The French Revolution was a period of radical political and societal change in France...",
  "model": "openai/gpt-4o-mini"
}
```

**Validation:**
- `text`: Required, 10-2000 characters
- `model`: Optional, defaults to `openai/gpt-4o-mini`
- User must not exceed 500 total cards limit (including staging)

**Success Response (201 Created):**
```json
{
  "success": true,
  "message": "Generated 6 cards successfully",
  "data": {
    "generationBatchId": "batch-uuid",
    "cards": [
      {
        "id": "uuid-1",
        "front": "When did the French Revolution begin?",
        "back": "1789",
        "status": "staging",
        "isAiGenerated": true,
        "generationBatchId": "batch-uuid",
        "interval": 0,
        "easeFactor": 2.5,
        "repetitions": 0,
        "nextReview": "2023-12-05T10:30:00Z",
        "createdAt": "2023-12-05T10:30:00Z",
        "updatedAt": "2023-12-05T10:30:00Z"
      }
    ],
    "metadata": {
      "model": "openai/gpt-4o-mini",
      "tokensUsed": 450,
      "estimatedCost": 0.002
    }
  }
}
```

**Error Responses:**
- `400 Bad Request`: Text length validation error
```json
{
  "success": false,
  "error": "VALIDATION_ERROR",
  "message": "Text must be between 10 and 2000 characters",
  "details": {
    "field": "text",
    "actualLength": 5
  }
}
```
- `403 Forbidden`: Card limit reached
- `429 Too Many Requests`: Rate limit exceeded
```json
{
  "success": false,
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Please wait before generating more cards",
  "details": {
    "retryAfter": 60
  }
}
```
- `500 Internal Server Error`: AI service error
```json
{
  "success": false,
  "error": "AI_SERVICE_ERROR",
  "message": "Failed to generate cards. Please try again.",
  "details": {
    "reason": "API timeout"
  }
}
```
- `503 Service Unavailable`: Monthly AI budget exceeded
```json
{
  "success": false,
  "error": "BUDGET_EXCEEDED",
  "message": "Monthly AI generation limit reached. Please try again next month.",
  "details": {
    "resetDate": "2024-01-01T00:00:00Z"
  }
}
```

---

## 6. Learning Session Endpoints

### 6.1. Start Learning Session

**Endpoint:** `GET /api/learning/session/start`

**Description:** Retrieves cards due for review and initializes a learning session.

**Authentication:** Required

**Query Parameters:**
- `limit` (optional): Maximum cards per session (default: unlimited)

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "sessionId": "session-uuid",
    "cards": [
      {
        "id": "uuid-1",
        "front": "Question text",
        "back": "Answer text",
        "interval": 3,
        "easeFactor": 2.5,
        "repetitions": 2
      }
    ],
    "totalCards": 25,
    "startedAt": "2023-12-05T10:30:00Z"
  }
}
```

**Note:** Session management can be client-side only in MVP. Server doesn't need to track session state.

---

### 6.2. Submit Card Review

**Endpoint:** `POST /api/learning/review`

**Description:** Records user's review of a card and updates SM-2 parameters.

**Authentication:** Required

**Request Payload:**
```json
{
  "cardId": "uuid-here",
  "quality": 4
}
```

**Validation:**
- `cardId`: Required, must exist and belong to user
- `quality`: Required, must be one of: `0` (Again), `3` (Hard), `4` (Good), `5` (Easy)

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Review recorded successfully",
  "data": {
    "cardId": "uuid-here",
    "quality": 4,
    "updatedCard": {
      "interval": 5,
      "easeFactor": 2.5,
      "repetitions": 3,
      "nextReview": "2023-12-10T10:30:00Z"
    },
    "reviewHistoryId": "review-uuid"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid quality value
- `404 Not Found`: Card doesn't exist or doesn't belong to user

---

### 6.3. Get Learning Statistics

**Endpoint:** `GET /api/learning/stats`

**Description:** Retrieves user's learning statistics and progress.

**Authentication:** Required

**Query Parameters:**
- `period` (optional): `today`, `week`, `month`, `all` (default: `all`)

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "period": "week",
    "totalReviews": 120,
    "breakdown": {
      "again": 15,
      "hard": 25,
      "good": 65,
      "easy": 15
    },
    "averageQuality": 3.8,
    "dueToday": 25,
    "nextReviewDate": "2023-12-06T08:00:00Z",
    "streakDays": 7,
    "reviewsByDate": [
      {
        "date": "2023-12-05",
        "count": 20
      }
    ]
  }
}
```

---

## 7. Review History Endpoints

### 7.1. Get Review History

**Endpoint:** `GET /api/reviews`

**Description:** Retrieves user's review history with filtering and pagination.

**Authentication:** Required

**Query Parameters:**
- `cardId` (optional): Filter by specific card
- `startDate` (optional): ISO 8601 date string
- `endDate` (optional): ISO 8601 date string
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 50, max: 100)

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "reviews": [
      {
        "id": "review-uuid",
        "cardId": "card-uuid",
        "quality": 4,
        "reviewedAt": "2023-12-05T10:30:00Z",
        "card": {
          "front": "Question text",
          "back": "Answer text"
        }
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "totalItems": 320,
      "totalPages": 7,
      "hasMore": true
    }
  }
}
```

---

### 7.2. Get Card Review History

**Endpoint:** `GET /api/cards/{cardId}/reviews`

**Description:** Retrieves review history for a specific card.

**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "cardId": "uuid-here",
    "reviews": [
      {
        "id": "review-uuid-1",
        "quality": 4,
        "reviewedAt": "2023-12-05T10:30:00Z"
      },
      {
        "id": "review-uuid-2",
        "quality": 3,
        "reviewedAt": "2023-12-03T14:20:00Z"
      }
    ],
    "totalReviews": 8,
    "averageQuality": 3.75
  }
}
```

---

## 8. Health and Utility Endpoints

### 8.1. Health Check

**Endpoint:** `GET /api/health`

**Description:** Checks API and database connectivity.

**Authentication:** Not required

**Success Response (200 OK):**
```json
{
  "success": true,
  "status": "healthy",
  "timestamp": "2023-12-05T10:30:00Z",
  "version": "1.0.0"
}
```

---

## 9. Authentication and Authorization

### 9.1. Authentication Mechanism

**Provider:** Supabase Auth

**Method:** JWT tokens stored in HTTP-only cookies

**Implementation:**
- Client requests include authentication cookie automatically
- Astro API routes use `supabase.auth.getUser()` to verify session
- Invalid/expired tokens return 401 Unauthorized
- Missing authentication returns 401 with redirect to login

### 9.2. Authorization

**Row Level Security (RLS):**
- Supabase RLS policies enforce `user_id = auth.uid()` at database level
- All queries automatically filtered by authenticated user
- Impossible to access other users' data even with direct database queries

**Endpoint Authorization:**
- All endpoints except `/api/health` and `/api/auth/register|login|reset-password` require authentication
- Ownership validation happens automatically via RLS
- 403 Forbidden returned when attempting unauthorized operations (e.g., card limit exceeded)

### 9.3. Session Management

**Session Duration:**
- Default: 1 hour (access token)
- Refresh token: 30 days
- "Remember me" option extends refresh token to 90 days

**Session Storage:**
- Access token: HTTP-only cookie, secure flag in production
- Refresh token: HTTP-only cookie, secure flag in production
- Automatic refresh handled by Supabase SDK

---

## 10. Validation and Business Logic

### 10.1. Card Validation

**Creation/Update:**
- `front` and `back`: Required, non-empty strings
- Maximum length: 5000 characters per field (optional constraint)
- `status`: Must be `staging`, `active`, or `rejected`
- User card limit: Maximum 500 cards (active + staging, excluding rejected)

**SM-2 Parameters:**
- `interval`: Integer >= 0
- `easeFactor`: Decimal between 1.3 and 3.0
- `repetitions`: Integer >= 0
- Validated at database level via CHECK constraints

### 10.2. Review Validation

**Quality Score:**
- Must be one of: `0` (Again), `3` (Hard), `4` (Good), `5` (Easy)
- Enforced at database level via CHECK constraint

**Review Recording:**
- Card must exist and belong to user
- Creates entry in `review_history` table
- Updates card SM-2 parameters atomically

### 10.3. AI Generation Validation

**Input Text:**
- Minimum: 10 characters
- Maximum: 2000 characters
- Validated on both frontend and backend

**Rate Limiting:**
- Maximum 10 requests per minute per user
- Monthly budget cap: $10 total across all users
- Returns 429 Too Many Requests when exceeded

**Output Processing:**
- Generated cards saved with `status = 'staging'`
- Assigned unique `generation_batch_id`
- `is_ai_generated = true`
- User can review before accepting to active

### 10.4. Business Logic Implementation

#### Card Limit Enforcement (US-007)
```
BEFORE card creation:
  1. Count user's cards WHERE status IN ('active', 'staging')
  2. If count >= 500, return 403 Forbidden
  3. Else, proceed with creation
```

#### SM-2 Algorithm Implementation (US-019-022)
```
ON review submission:
  1. Validate quality value (0, 3, 4, 5)
  2. Calculate new SM-2 parameters:
     - quality = 0: interval=0, repetitions=0, next_review=NOW()
     - quality = 3: decrease ease_factor, calculate shorter interval
     - quality = 4: maintain ease_factor, standard interval calculation
     - quality = 5: increase ease_factor, calculate longer interval
  3. Update card with new parameters
  4. Insert review into review_history
  5. Return updated card data
```

#### Staging Workflow (US-006-008)
```
AI Generation Flow:
  1. Validate text (10-2000 chars)
  2. Call OpenRouter.ai API
  3. Parse JSON response
  4. Create cards with status='staging', shared generation_batch_id
  5. Return cards for user review
  
Staging Actions:
  - Accept: Update status to 'active', set next_review to NOW()
  - Edit: Update front/back, auto-accept (status='active')
  - Reject: Update status to 'rejected' (excluded from learning)
  - Accept All: Batch update all cards in generation_batch_id to 'active'
```

#### Search Implementation (US-013)
```
Full-text search using PostgreSQL:
  - Use GIN index on tsvector(front || ' ' || back)
  - Query: to_tsvector('english', front || ' ' || back) @@ plainto_tsquery('english', search_term)
  - Case-insensitive
  - Works with filters and sorting
```

---

## 11. Error Handling

### 11.1. Standard Error Response Format

```json
{
  "success": false,
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "field": "fieldName",
    "additionalInfo": "value"
  }
}
```

### 11.2. HTTP Status Codes

| Code | Usage |
|------|-------|
| `200 OK` | Successful GET, PUT, PATCH, DELETE |
| `201 Created` | Successful POST (resource created) |
| `400 Bad Request` | Validation error, malformed request |
| `401 Unauthorized` | Missing or invalid authentication |
| `403 Forbidden` | Valid auth but operation not allowed (e.g., card limit) |
| `404 Not Found` | Resource doesn't exist or doesn't belong to user |
| `409 Conflict` | Resource conflict (e.g., email already exists) |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Unexpected server error |
| `503 Service Unavailable` | External service unavailable (e.g., AI budget exceeded) |

### 11.3. Common Error Codes

| Error Code | Description |
|------------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `INVALID_CREDENTIALS` | Login failed |
| `EMAIL_EXISTS` | Email already registered |
| `EMAIL_NOT_VERIFIED` | Email verification required |
| `CARD_LIMIT_REACHED` | User exceeded 500 card limit |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `AI_SERVICE_ERROR` | AI generation failed |
| `BUDGET_EXCEEDED` | Monthly AI budget exceeded |
| `NOT_FOUND` | Resource not found |
| `UNAUTHORIZED` | Authentication required |

---

## 12. Rate Limiting

### 12.1. Rate Limits

| Endpoint Pattern | Limit | Window |
|------------------|-------|--------|
| `/api/auth/login` | 5 attempts | 15 minutes |
| `/api/auth/register` | 3 attempts | 1 hour |
| `/api/ai/generate-cards` | 10 requests | 1 minute |
| All other authenticated endpoints | 100 requests | 1 minute |

### 12.2. Rate Limit Headers

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1638720000
```

### 12.3. Rate Limit Response

```json
{
  "success": false,
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests. Please try again later.",
  "details": {
    "retryAfter": 45
  }
}
```

---

## 13. Performance Considerations

### 13.1. Database Optimization

**Indexes Used:**
- `idx_cards_user_next_review` - Primary learning query optimization
- `idx_cards_user_status` - Filtering by status
- `idx_cards_user_ai_generated` - AI metrics calculation
- `idx_cards_search` - Full-text search (GIN index)
- `idx_review_history_user` - User analytics

**Query Performance:**
- Target: < 100ms for CRUD operations
- Composite indexes optimize common filter combinations
- RLS policies use indexed `user_id` column

### 13.2. Pagination

**Default Limits:**
- Cards list: 50 items per page (max 100)
- Reviews list: 50 items per page (max 100)

**Implementation:**
- Offset-based pagination for simplicity in MVP
- Future: Consider cursor-based for better performance

### 13.3. Caching Strategy (Future Enhancement)

**Candidates for caching:**
- User statistics (due count, totals)
- Learning session card list
- User profile data

**MVP:** No caching implemented; direct database queries only

---

## 14. Security Considerations

### 14.1. Input Validation

**All Endpoints:**
- Sanitize user input to prevent XSS
- Validate data types and formats
- Enforce length limits
- Use parameterized queries (Supabase SDK handles this)

### 14.2. SQL Injection Prevention

- Supabase SDK uses parameterized queries
- No raw SQL in application code
- RLS policies use built-in `auth.uid()` function

### 14.3. CORS Policy

**Development:**
- Allow localhost origins

**Production:**
- Restrict to application domain only
- Credentials: true (for cookies)

### 14.4. Data Privacy (GDPR)

**User Data:**
- GDPR consent required during registration
- User can delete account (cascades to all cards and reviews)
- AI-generated content may be sent to OpenRouter.ai (disclosed to users)

**Data Deletion:**
- `DELETE /api/auth/account` endpoint (future enhancement)
- Cascading deletes via `ON DELETE CASCADE` foreign keys

---

## 15. Versioning

**MVP:** No versioning implemented

**Future:** Consider URL versioning (`/api/v1/...`) or header versioning when breaking changes are needed

---

## 16. Testing Strategy

### 16.1. Unit Tests

- Validation logic
- SM-2 algorithm calculations
- Error handling

### 16.2. Integration Tests

- API endpoint functionality
- Database operations
- RLS policy enforcement
- AI generation workflow

### 16.3. Manual Testing Checklist

- User registration and login flow
- Card CRUD operations
- AI generation and staging workflow
- Learning session with all quality ratings
- Search, filter, sort functionality
- Card limit enforcement
- Rate limiting
- Cross-user data isolation (security)

---

## 17. Monitoring and Logging

### 17.1. Metrics to Monitor

**Application:**
- Request rate and latency per endpoint
- Error rates by endpoint and error code
- Authentication success/failure rates
- AI generation success rate and latency

**Business:**
- Active users (daily/weekly)
- Cards created (AI vs manual)
- AI Acceptance Rate
- Reviews completed per user
- Card limit utilization

**Infrastructure:**
- Database connection pool usage
- API response times
- AI API costs (OpenRouter.ai dashboard)
- Supabase resource usage

### 17.2. Logging Strategy

**Log Levels:**
- `ERROR`: Unhandled exceptions, critical failures
- `WARN`: Business rule violations (card limit, rate limit)
- `INFO`: Successful operations (registration, card creation)
- `DEBUG`: Detailed request/response data (development only)

**Sensitive Data:**
- Never log passwords or tokens
- Mask email addresses in production logs
- Sanitize card content in logs (user privacy)

---

## 18. Migration and Deployment

### 18.1. Database Migrations

**Tool:** Supabase Migrations CLI

**Migration Files:**
```
/supabase/migrations/
  20231205000001_initial_schema.sql
  20231205000002_rls_policies.sql
  20231205000003_indexes.sql
  20231205000004_triggers.sql
```

**Deployment:** GitHub Actions runs migrations automatically on deploy

### 18.2. API Deployment

**Environment:** DigitalOcean Droplet (Docker container)

**Deployment Process:**
1. GitHub Actions builds Docker image
2. Runs database migrations
3. Deploys new container
4. Health check verification
5. Rollback on failure

---

## 19. Future Enhancements (Post-MVP)

### 19.1. Potential New Endpoints

- `POST /api/cards/import` - Bulk import from CSV/JSON
- `GET /api/cards/export` - Export cards to various formats
- `POST /api/cards/{cardId}/duplicate` - Duplicate existing card
- `GET /api/analytics/retention` - Retention curve analytics
- `POST /api/feedback` - User feedback submission
- `DELETE /api/auth/account` - Account deletion (GDPR right to be forgotten)

### 19.2. Feature Improvements

- WebSocket support for real-time session sync across devices
- GraphQL alternative for more flexible queries
- Batch operations for card management
- Advanced search with boolean operators
- Custom AI prompts per user
- Spaced repetition algorithm selection (SM-2, FSRS, Anki)

---

## 20. API Client Examples

### 20.1. JavaScript/TypeScript Client

```typescript
// Login
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  }),
  credentials: 'include' // Important for cookies
});

const data = await response.json();

// Create card
const cardResponse = await fetch('/api/cards', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    front: 'Question?',
    back: 'Answer!'
  }),
  credentials: 'include'
});

// Generate AI cards
const aiResponse = await fetch('/api/ai/generate-cards', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: 'Your learning material here...'
  }),
  credentials: 'include'
});

// Submit review
const reviewResponse = await fetch('/api/learning/review', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    cardId: 'card-uuid',
    quality: 4
  }),
  credentials: 'include'
});
```

---

## 21. Appendix: Mapping PRD User Stories to Endpoints

| User Story | Endpoint(s) |
|------------|-------------|
| US-001: Register | `POST /api/auth/register` |
| US-002: Login | `POST /api/auth/login` |
| US-003: Reset Password | `POST /api/auth/reset-password` |
| US-004: Logout | `POST /api/auth/logout` |
| US-005: Manual Card Creation | `POST /api/cards` |
| US-006-007: AI Generation | `POST /api/ai/generate-cards` |
| US-008: Edit Staged Card | `PUT /api/cards/{id}`, `PATCH /api/cards/{id}/status` |
| US-009: Error Handling | All endpoints (standardized error responses) |
| US-010: View All Cards | `GET /api/cards` |
| US-011: Filter Cards | `GET /api/cards?status=...&isAiGenerated=...` |
| US-012: Sort Cards | `GET /api/cards?sortBy=...&sortOrder=...` |
| US-013: Search Cards | `GET /api/cards?search=...` |
| US-014: Edit Card | `PUT /api/cards/{id}` |
| US-015: Delete Card | `DELETE /api/cards/{id}` |
| US-016: Reject/Restore Card | `PATCH /api/cards/{id}/status` |
| US-017: Start Learning | `GET /api/cards/due` or `GET /api/learning/session/start` |
| US-018-022: Review Card | `POST /api/learning/review` |
| US-023-024: Session Summary | `GET /api/learning/stats` |
| US-025: View Profile | `GET /api/auth/profile` |
| US-026: Change Password | `POST /api/auth/change-password` |
| US-028: RLS Security | Enforced at database level (all endpoints) |
| US-029: Due Cards Counter | `GET /api/cards/due` (totalDue field) |
| US-030: Input Validation | All endpoints (validation middleware) |

---

## Document Version

**Version:** 1.0.0  
**Last Updated:** December 5, 2023  
**Status:** MVP Implementation Plan

