# API Endpoint Implementation Plan: GET /api/cards

## 1. Przegląd punktu końcowego

**Endpoint:** `GET /api/cards`

**Cel:** Pobieranie listy wszystkich kart flashcard użytkownika z zaawansowanym filtrowaniem, sortowaniem i paginacją.

**Funkcjonalność:**
- Wyświetlanie kart w różnych statusach (staging, active, rejected, all)
- Filtrowanie kart według źródła (AI-generated vs manual)
- Wyszukiwanie pełnotekstowe w treści pytań i odpowiedzi
- Sortowanie według różnych kryteriów (data utworzenia, data następnej powtórki, alfabetycznie)
- Paginacja z konfigurowalnymi limitami dla optymalnej wydajności

**Wymagania biznesowe (User Stories):**
- US-010: View All Cards
- US-011: Filter Cards by status and source
- US-012: Sort Cards
- US-013: Search Cards

**Autentykacja:** Wymagana (Supabase Auth JWT w HTTP-only cookies)

**Autoryzacja:** Row Level Security (RLS) automatycznie filtruje karty użytkownika na poziomie bazy danych.

---

## 2. Szczegóły żądania

### HTTP Method
`GET`

### URL Structure
```
/api/cards
```

### Query Parameters

| Parameter | Type | Required | Default | Constraints | Description |
|-----------|------|----------|---------|-------------|-------------|
| `status` | string | No | `'all'` | Enum: 'staging', 'active', 'rejected', 'all' | Filtruje karty według statusu |
| `isAiGenerated` | boolean | No | - | true/false | Filtruje karty według źródła (AI vs manual) |
| `search` | string | No | - | Min length: 1 | Wyszukiwanie pełnotekstowe w front/back |
| `sortBy` | string | No | `'createdAt'` | Enum: 'createdAt', 'nextReview', 'alphabetical' | Kryterium sortowania |
| `sortOrder` | string | No | `'desc'` | Enum: 'asc', 'desc' | Kierunek sortowania |
| `page` | number | No | `1` | Min: 1 | Numer strony (1-indexed) |
| `limit` | number | No | `50` | Min: 1, Max: 100 | Liczba elementów na stronę |

### Request Headers
```
Cookie: sb-access-token=<jwt_token>; sb-refresh-token=<refresh_token>
```

### Przykładowe zapytania

**Podstawowe - wszystkie karty:**
```
GET /api/cards
```

**Zaawansowane - karty AI w staging, sortowane po dacie utworzenia:**
```
GET /api/cards?status=staging&isAiGenerated=true&sortBy=createdAt&sortOrder=asc&page=1&limit=20
```

**Wyszukiwanie:**
```
GET /api/cards?search=French%20Revolution&status=active
```

---

## 3. Wykorzystywane typy

### Typy z `src/types.ts`

**Query Interface:**
```typescript
GetCardsQuery {
  status?: CardStatus | 'all';
  isAiGenerated?: boolean;
  search?: string;
  sortBy?: CardSortBy;
  sortOrder?: SortOrder;
  page?: number;
  limit?: number;
}
```

**Response DTOs:**
```typescript
GetCardsResponseDto {
  cards: CardDto[];
  pagination: PaginationMeta;
}

CardDto {
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

PaginationMeta {
  page: number;
  limit: number;
  totalItems: number;
  totalPages: number;
  hasMore: boolean;
}
```

**Database Entities:**
```typescript
CardEntity // Raw database row
transformCardEntityToDto(entity: CardEntity): CardDto // Transformer function
```

**Response Helpers:**
```typescript
createSuccessResponse<T>(data: T, message?: string): ApiSuccessResponse<T>
createErrorResponse(error: string, message: string, details?: Record<string, unknown>): ApiErrorResponse
```

---

## 4. Szczegóły odpowiedzi

### Success Response (200 OK)

```json
{
  "success": true,
  "data": {
    "cards": [
      {
        "id": "uuid-1",
        "front": "What is the capital of France?",
        "back": "Paris",
        "status": "active",
        "isAiGenerated": false,
        "generationBatchId": null,
        "interval": 3,
        "easeFactor": 2.5,
        "repetitions": 2,
        "nextReview": "2023-12-08T10:30:00Z",
        "createdAt": "2023-12-05T10:30:00Z",
        "updatedAt": "2023-12-07T10:30:00Z"
      },
      {
        "id": "uuid-2",
        "front": "When did the French Revolution begin?",
        "back": "1789",
        "status": "active",
        "isAiGenerated": true,
        "generationBatchId": "batch-uuid",
        "interval": 1,
        "easeFactor": 2.5,
        "repetitions": 1,
        "nextReview": "2023-12-06T10:30:00Z",
        "createdAt": "2023-12-05T11:00:00Z",
        "updatedAt": "2023-12-05T11:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "totalItems": 150,
      "totalPages": 3,
      "hasMore": true
    }
  }
}
```

**Uwagi:**
- Pusta lista kart (`cards: []`) to poprawny response 200, nie 404
- `user_id` NIE jest zwracany w DTO (privacy)
- Timestamps w formacie ISO 8601 UTC

### Error Responses

**400 Bad Request - Validation Error:**
```json
{
  "success": false,
  "error": "VALIDATION_ERROR",
  "message": "Invalid request parameters",
  "details": {
    "field": "limit",
    "reason": "Must be between 1 and 100"
  }
}
```

**401 Unauthorized - Missing Authentication:**
```json
{
  "success": false,
  "error": "UNAUTHORIZED",
  "message": "Authentication required"
}
```

**500 Internal Server Error - Database Error:**
```json
{
  "success": false,
  "error": "INTERNAL_ERROR",
  "message": "An unexpected error occurred"
}
```

---

## 5. Przepływ danych

### High-Level Flow

```
1. HTTP Request → Astro API Route Handler
2. Middleware Authentication Check (context.locals.supabase)
3. Query Parameters Validation (Zod schema)
4. Call CardService.getCards(userId, queryParams)
5. CardService builds Supabase query with filters
6. Supabase executes query (RLS auto-filters by user_id)
7. CardService transforms CardEntity[] → CardDto[]
8. CardService returns {cards, pagination}
9. API Route wraps in ApiSuccessResponse
10. HTTP Response → Client
```

### Detailed Flow Diagram

```
┌─────────────┐
│   Client    │
└─────┬───────┘
      │ GET /api/cards?status=active&page=1
      ▼
┌─────────────────────────────────────┐
│  Astro Middleware                   │
│  - Extract Supabase client          │
│  - Verify JWT token                 │
│  - Set context.locals.supabase      │
└─────┬───────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  API Route: /api/cards/index.ts     │
│  - Parse query parameters           │
│  - Validate with Zod                │
│  - Get authenticated user           │
└─────┬───────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  CardService.getCards()             │
│  - Build Supabase query builder     │
│  - Apply filters (status, AI, etc)  │
│  - Apply search (full-text)         │
│  - Apply sorting                    │
│  - Apply pagination                 │
│  - Execute count query              │
│  - Execute data query               │
└─────┬───────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  Supabase PostgreSQL                │
│  - RLS: WHERE user_id = auth.uid()  │
│  - Use indexes for performance      │
│  - Return CardEntity[]              │
└─────┬───────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  CardService (continued)            │
│  - Transform entities to DTOs       │
│  - Calculate pagination metadata    │
│  - Return {cards, pagination}       │
└─────┬───────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  API Route (continued)              │
│  - Wrap in ApiSuccessResponse       │
│  - Set Content-Type: application/json│
│  - Return 200 OK                    │
└─────┬───────────────────────────────┘
      │
      ▼
┌─────────────┐
│   Client    │
└─────────────┘
```

### Database Query Construction

**Base Query:**
```typescript
let query = supabase
  .from('cards')
  .select('*', { count: 'exact' });
```

**Apply Filters:**
```typescript
// Status filter
if (status !== 'all') {
  query = query.eq('status', status);
}

// AI-generated filter
if (isAiGenerated !== undefined) {
  query = query.eq('is_ai_generated', isAiGenerated);
}

// Full-text search (uses GIN index)
if (search) {
  query = query.textSearch('front,back', search);
}
```

**Apply Sorting:**
```typescript
if (sortBy === 'createdAt') {
  query = query.order('created_at', { ascending: sortOrder === 'asc' });
} else if (sortBy === 'nextReview') {
  query = query.order('next_review', { ascending: sortOrder === 'asc' });
} else if (sortBy === 'alphabetical') {
  query = query.order('front', { ascending: sortOrder === 'asc' });
}
```

**Apply Pagination:**
```typescript
const offset = (page - 1) * limit;
query = query.range(offset, offset + limit - 1);
```

---

## 6. Względy bezpieczeństwa

### Autentykacja

**Mechanizm:**
- Supabase Auth z JWT tokens w HTTP-only cookies
- Middleware sprawdza `context.locals.supabase.auth.getUser()`
- Brak sesji → 401 Unauthorized

**Implementacja w API Route:**
```typescript
const { data: { user }, error: authError } = await supabase.auth.getUser();

if (authError || !user) {
  return new Response(
    JSON.stringify(createErrorResponse('UNAUTHORIZED', 'Authentication required')),
    { status: 401 }
  );
}
```

### Autoryzacja

**Row Level Security (RLS):**
- Policy: `select_own_cards` - `WHERE auth.uid() = user_id`
- Automatyczne filtrowanie na poziomie bazy danych
- Niemożliwy dostęp do kart innych użytkowników
- Nie wymagana dodatkowa walidacja w aplikacji

**Korzyści:**
- Defense in depth - security na poziomie DB
- Ochrona przed błędami aplikacyjnymi
- Uproszczony kod - nie trzeba ręcznie filtrować po user_id

### Walidacja i sanityzacja

**Zod Schema:**
```typescript
const GetCardsQuerySchema = z.object({
  status: z.enum(['staging', 'active', 'rejected', 'all']).optional().default('all'),
  isAiGenerated: z.coerce.boolean().optional(),
  search: z.string().min(1).trim().optional(),
  sortBy: z.enum(['createdAt', 'nextReview', 'alphabetical']).optional().default('createdAt'),
  sortOrder: z.enum(['asc', 'desc']).optional().default('desc'),
  page: z.coerce.number().int().min(1).optional().default(1),
  limit: z.coerce.number().int().min(1).max(100).optional().default(50),
});
```

**Sanityzacja:**
- `.trim()` na search query - usuwa whitespace
- `.coerce.number()` - bezpieczna konwersja string→number
- `.coerce.boolean()` - bezpieczna konwersja string→boolean
- Max limit 100 - zapobieganie DoS

### Zapobieganie atakom

**SQL Injection:**
- Supabase SDK używa parameterized queries - automatyczna ochrona
- Full-text search przez `textSearch()` - escapuje input
- Brak raw SQL w aplikacji

**DoS Prevention:**
- Limit max 100 items per page
- Rate limiting (100 req/min) na poziomie middleware
- Paginacja zapobiega dużym payloadom

**Privacy:**
- `user_id` nie jest zwracany w response DTO
- Search queries NIE są logowane (zawartość kart to sensitive data)
- RLS zapewnia data isolation między użytkownikami

**Enumeration Attacks:**
- Search nie ujawnia istnienia kart innych użytkowników (RLS)
- 401 dla unauthenticated nie ujawnia szczegółów
- Consistent timing dla valid/invalid queries

---

## 7. Obsługa błędów

### Error Scenarios & HTTP Status Codes

| Scenario | Status Code | Error Code | Message | Details |
|----------|-------------|------------|---------|---------|
| Brak autentykacji | 401 | UNAUTHORIZED | Authentication required | - |
| Wygasły token | 401 | UNAUTHORIZED | Authentication required | - |
| Invalid status value | 400 | VALIDATION_ERROR | Invalid request parameters | field: "status" |
| Limit > 100 | 400 | VALIDATION_ERROR | Invalid request parameters | field: "limit", reason: "Must be between 1 and 100" |
| Limit < 1 | 400 | VALIDATION_ERROR | Invalid request parameters | field: "limit" |
| Page < 1 | 400 | VALIDATION_ERROR | Invalid request parameters | field: "page" |
| Invalid sortBy | 400 | VALIDATION_ERROR | Invalid request parameters | field: "sortBy" |
| Invalid sortOrder | 400 | VALIDATION_ERROR | Invalid request parameters | field: "sortOrder" |
| Błąd Supabase | 500 | INTERNAL_ERROR | An unexpected error occurred | - |
| Błąd transformacji | 500 | INTERNAL_ERROR | An unexpected error occurred | - |

### Error Handling Implementation

**1. Authentication Errors:**
```typescript
const { data: { user }, error: authError } = await supabase.auth.getUser();

if (authError || !user) {
  return new Response(
    JSON.stringify(createErrorResponse('UNAUTHORIZED', 'Authentication required')),
    { 
      status: 401,
      headers: { 'Content-Type': 'application/json' }
    }
  );
}
```

**2. Validation Errors (Zod):**
```typescript
const validation = GetCardsQuerySchema.safeParse(queryParams);

if (!validation.success) {
  const firstError = validation.error.issues[0];
  return new Response(
    JSON.stringify(createErrorResponse(
      'VALIDATION_ERROR',
      'Invalid request parameters',
      {
        field: firstError.path.join('.'),
        reason: firstError.message
      }
    )),
    { 
      status: 400,
      headers: { 'Content-Type': 'application/json' }
    }
  );
}
```

**3. Database Errors:**
```typescript
const { data, error: dbError, count } = await query;

if (dbError) {
  console.error('[GET /api/cards] Database error:', dbError);
  return new Response(
    JSON.stringify(createErrorResponse(
      'INTERNAL_ERROR',
      'An unexpected error occurred'
    )),
    { 
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    }
  );
}
```

**4. Unexpected Errors (Catch-all):**
```typescript
try {
  // ... main logic
} catch (error) {
  console.error('[GET /api/cards] Unexpected error:', error);
  return new Response(
    JSON.stringify(createErrorResponse(
      'INTERNAL_ERROR',
      'An unexpected error occurred'
    )),
    { 
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    }
  );
}
```

### Logging Strategy

**Log Levels:**
- **ERROR:** Database errors, unexpected exceptions (500)
- **WARN:** Validation errors (400), frequent failed validations from same user
- **INFO:** Authentication failures (401) - for monitoring
- **DEBUG:** Successful requests (development only)

**What to Log:**
```typescript
// ERROR level
console.error('[GET /api/cards] Database error:', {
  userId: user.id,
  error: dbError.message,
  code: dbError.code,
  timestamp: new Date().toISOString()
});

// WARN level
console.warn('[GET /api/cards] Validation failed:', {
  userId: user.id,
  field: firstError.path.join('.'),
  timestamp: new Date().toISOString()
});
```

**What NOT to Log (Privacy):**
- Search query content (zawiera sensitive user data)
- Card content (front/back fields)
- Full query parameters (może zawierać PII)

---

## 8. Rozważania dotyczące wydajności

### Database Optimization

**Wykorzystywane indeksy:**
- `idx_cards_user_status` - dla filtrowania po statusie
- `idx_cards_user_ai_generated` - dla filtrowania po is_ai_generated
- `idx_cards_user_next_review` - dla sortowania po next_review
- `idx_cards_search` (GIN) - dla full-text search

**Query Performance Expectations:**
- Typowy query: < 100ms
- Full-text search: < 200ms
- Z paginacją (limit 50): < 50ms

**Optymalizacje:**
- Composite indexes (user_id + inne pole) - O(log n) lookup
- RLS używa indexed user_id column
- Paginacja zapobiega dużym payloadom
- Count query z `{ count: 'exact', head: false }` w jednym zapytaniu

### Response Size Management

**Typowe rozmiary:**
- 1 karta: ~500 bytes (średnia długość pytania/odpowiedzi)
- 50 kart (default): ~25 KB
- 100 kart (max): ~50 KB

**Paginacja:**
- Default limit: 50 (balance między UX a performance)
- Max limit: 100 (zapobiega przeciążeniu)
- Frontend powinien używać infinite scroll lub pagination

### Caching Considerations

**MVP: Brak cachingu**
- Direct database queries dla świeżości danych
- RLS policies nie współpracują dobrze z shared cache

**Future Enhancement:**
- Redis cache dla popular filters
- Cache invalidation przy UPDATE/DELETE kart
- User-specific cache keys

### N+1 Query Prevention

**Obecny endpoint:**
- Nie ma nested relations w response
- Single query z transformacją w memory
- Brak potrzeby joins

**Gdyby był nested data:**
- Używać `.select('*, relation(*)')` syntax Supabase
- Eager loading zamiast lazy loading

### Rate Limiting

**Limity (zgodnie z api-plan):**
- 100 requests/minute dla authenticated endpoints
- Implementacja w middleware (nie w route handler)

**Headers w response:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1701781200
```

### Monitoring Metrics

**Kluczowe metryki:**
- Response time (p50, p95, p99)
- Database query time
- Error rate
- Most used filters (analytics)
- Cache hit rate (future)

---

## 9. Etapy wdrożenia

### Krok 1: Struktura plików

Utworzyć następujące pliki:

```
src/
├── pages/
│   └── api/
│       └── cards/
│           └── index.ts          # GET /api/cards endpoint
├── lib/
│   └── services/
│       └── card.service.ts       # CardService z logiką biznesową
└── lib/
    └── validators/
        └── card.validator.ts     # Zod schemas dla walidacji
```

### Krok 2: Zod Schemas (card.validator.ts)

Utworzyć schema walidacyjne:

```typescript
import { z } from 'zod';

export const GetCardsQuerySchema = z.object({
  status: z.enum(['staging', 'active', 'rejected', 'all']).optional().default('all'),
  isAiGenerated: z.coerce.boolean().optional(),
  search: z.string().min(1).trim().optional(),
  sortBy: z.enum(['createdAt', 'nextReview', 'alphabetical']).optional().default('createdAt'),
  sortOrder: z.enum(['asc', 'desc']).optional().default('desc'),
  page: z.coerce.number().int().min(1).optional().default(1),
  limit: z.coerce.number().int().min(1).max(100).optional().default(50),
});

export type GetCardsQueryValidated = z.infer<typeof GetCardsQuerySchema>;
```

### Krok 3: Card Service (card.service.ts)

Implementować logikę biznesową:

```typescript
import type { SupabaseClient } from '@/db/supabase.client';
import type { CardEntity } from '@/types';
import { transformCardEntityToDto } from '@/types';
import type { GetCardsQueryValidated } from '@/lib/validators/card.validator';
import type { GetCardsResponseDto } from '@/types';

export class CardService {
  constructor(private supabase: SupabaseClient) {}

  async getCards(
    userId: string,
    query: GetCardsQueryValidated
  ): Promise<GetCardsResponseDto> {
    const { status, isAiGenerated, search, sortBy, sortOrder, page, limit } = query;

    // Build base query
    let queryBuilder = this.supabase
      .from('cards')
      .select('*', { count: 'exact' });

    // Apply status filter
    if (status !== 'all') {
      queryBuilder = queryBuilder.eq('status', status);
    }

    // Apply AI-generated filter
    if (isAiGenerated !== undefined) {
      queryBuilder = queryBuilder.eq('is_ai_generated', isAiGenerated);
    }

    // Apply full-text search
    if (search) {
      queryBuilder = queryBuilder.textSearch('front,back', search);
    }

    // Apply sorting
    const sortColumn = this.getSortColumn(sortBy);
    queryBuilder = queryBuilder.order(sortColumn, { ascending: sortOrder === 'asc' });

    // Apply pagination
    const offset = (page - 1) * limit;
    queryBuilder = queryBuilder.range(offset, offset + limit - 1);

    // Execute query
    const { data, error, count } = await queryBuilder;

    if (error) {
      throw error;
    }

    // Transform entities to DTOs
    const cards = (data || []).map(transformCardEntityToDto);

    // Calculate pagination metadata
    const totalItems = count || 0;
    const totalPages = Math.ceil(totalItems / limit);
    const hasMore = page < totalPages;

    return {
      cards,
      pagination: {
        page,
        limit,
        totalItems,
        totalPages,
        hasMore,
      },
    };
  }

  private getSortColumn(sortBy: string): string {
    switch (sortBy) {
      case 'createdAt':
        return 'created_at';
      case 'nextReview':
        return 'next_review';
      case 'alphabetical':
        return 'front';
      default:
        return 'created_at';
    }
  }
}
```

### Krok 4: API Route Handler (pages/api/cards/index.ts)

Implementować endpoint:

```typescript
import type { APIRoute } from 'astro';
import { GetCardsQuerySchema } from '@/lib/validators/card.validator';
import { CardService } from '@/lib/services/card.service';
import { createSuccessResponse, createErrorResponse } from '@/types';

export const prerender = false;

export const GET: APIRoute = async ({ request, locals }) => {
  try {
    // 1. Authentication check
    const supabase = locals.supabase;
    const { data: { user }, error: authError } = await supabase.auth.getUser();

    if (authError || !user) {
      return new Response(
        JSON.stringify(createErrorResponse('UNAUTHORIZED', 'Authentication required')),
        { 
          status: 401,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }

    // 2. Parse and validate query parameters
    const url = new URL(request.url);
    const queryParams = Object.fromEntries(url.searchParams);

    const validation = GetCardsQuerySchema.safeParse(queryParams);

    if (!validation.success) {
      const firstError = validation.error.issues[0];
      return new Response(
        JSON.stringify(createErrorResponse(
          'VALIDATION_ERROR',
          'Invalid request parameters',
          {
            field: firstError.path.join('.'),
            reason: firstError.message
          }
        )),
        { 
          status: 400,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }

    // 3. Call service
    const cardService = new CardService(supabase);
    const result = await cardService.getCards(user.id, validation.data);

    // 4. Return success response
    return new Response(
      JSON.stringify(createSuccessResponse(result)),
      { 
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      }
    );

  } catch (error) {
    // 5. Handle unexpected errors
    console.error('[GET /api/cards] Unexpected error:', error);
    
    return new Response(
      JSON.stringify(createErrorResponse(
        'INTERNAL_ERROR',
        'An unexpected error occurred'
      )),
      { 
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};
```

### Krok 5: Middleware Setup (jeśli nie istnieje)

Upewnić się, że middleware Astro konfiguruje Supabase client:

```typescript
// src/middleware/index.ts
import { defineMiddleware } from 'astro:middleware';
import { createSupabaseClient } from '@/db/supabase.client';

export const onRequest = defineMiddleware(async (context, next) => {
  // Create Supabase client with cookies
  context.locals.supabase = createSupabaseClient(context.cookies);
  
  return next();
});
```

### Krok 6: TypeScript Types Update

Upewnić się że `src/env.d.ts` zawiera definicję `locals`:

```typescript
/// <reference types="astro/client" />

declare namespace App {
  interface Locals {
    supabase: import('@/db/supabase.client').SupabaseClient;
  }
}
```

### Krok 7: Testing Checklist

**Unit Tests (card.service.ts):**
- [ ] getCards() zwraca puste cards dla nowego użytkownika
- [ ] Filtrowanie po status działa poprawnie
- [ ] Filtrowanie po isAiGenerated działa poprawnie
- [ ] Search zwraca matching cards
- [ ] Sortowanie po createdAt (asc/desc)
- [ ] Sortowanie po nextReview (asc/desc)
- [ ] Sortowanie po alphabetical (asc/desc)
- [ ] Paginacja - strona 1 zwraca pierwsze N items
- [ ] Paginacja - hasMore = true gdy są kolejne strony
- [ ] Paginacja - hasMore = false na ostatniej stronie
- [ ] Transformacja entity→DTO działa poprawnie

**Integration Tests (API endpoint):**
- [ ] 401 gdy brak authentication
- [ ] 400 przy invalid status value
- [ ] 400 przy limit > 100
- [ ] 400 przy page < 1
- [ ] 200 dla valid request
- [ ] RLS policy - użytkownik widzi tylko własne karty
- [ ] Response zawiera pagination metadata
- [ ] Pusta lista kart zwraca 200 (nie 404)
- [ ] Search ignoruje case
- [ ] Kombinacja wielu filtrów działa poprawnie

**Manual Testing:**
- [ ] Postman/Insomnia collection z przykładowymi requests
- [ ] Test z różnymi kombinacjami query params
- [ ] Test performance z 500 kartami
- [ ] Test cross-user isolation (security)

### Krok 8: Documentation

- [ ] Dodać JSDoc comments do funkcji w service
- [ ] Dodać przykłady użycia w komentarzach API route
- [ ] Zaktualizować API documentation (jeśli istnieje)
- [ ] Dodać przykłady request/response do README

### Krok 9: Deployment Checklist

- [ ] Sprawdzić environment variables (Supabase URL, Anon Key)
- [ ] Upewnić się że RLS policies są deployed
- [ ] Upewnić się że indexes są utworzone
- [ ] Sprawdzić rate limiting w production
- [ ] Monitoring i alerting dla error rate
- [ ] Verify CORS configuration

### Krok 10: Post-Deployment Verification

- [ ] Health check endpoint działa
- [ ] GET /api/cards zwraca 200 dla authenticated user
- [ ] GET /api/cards zwraca 401 dla unauthenticated
- [ ] Performance < 100ms dla typowych queries
- [ ] Logs nie zawierają sensitive data
- [ ] Rate limiting działa poprawnie

---

## 10. Podsumowanie

### Kluczowe Decyzje

1. **Service Layer:** Logika biznesowa wyodrębniona do `CardService` dla reusability i testability
2. **Zod Validation:** Silna walidacja query params z automatic coercion i defaults
3. **RLS Security:** Pełne poleganie na Row Level Security dla data isolation
4. **Error Handling:** Spójne error responses z pomocnymi details dla debugging
5. **Performance:** Wykorzystanie composite indexes i paginacji dla optimal performance

### Compliance z Wymaganiami

- ✅ US-010: Wyświetlanie wszystkich kart
- ✅ US-011: Filtrowanie po status i źródle
- ✅ US-012: Sortowanie po różnych kryteriach
- ✅ US-013: Wyszukiwanie pełnotekstowe
- ✅ US-028: RLS security na poziomie DB
- ✅ US-030: Input validation z Zod

### Alignment z Tech Stack

- ✅ Astro 5: Server Endpoints dla API routes
- ✅ TypeScript 5: Pełne type safety z Zod
- ✅ Supabase: PostgreSQL z RLS, SDK dla queries
- ✅ Best Practices: Early returns, guard clauses, error handling

### Success Metrics

- Response time < 100ms (p95)
- Error rate < 0.1%
- 100% coverage RLS policies
- Zero SQL injection vulnerabilities
- Zero cross-user data leaks

---

**Document Version:** 1.0.0  
**Created:** December 5, 2023  
**Status:** Ready for Implementation

