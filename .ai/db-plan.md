# Schemat Bazy Danych - Vocab Trainer MVP

## 0. Supabase Auth - Tabela użytkowników

### 0.0. Wyjaśnienie notacji PostgreSQL: `schema.table`

W PostgreSQL:
- `auth` = nazwa **schematu** (namespace/folder dla tabel)
- `users` = nazwa **tabeli**
- `auth.users` = pełna notacja: tabela `users` w schemacie `auth`

**Analogia do systemu plików:**
```
/auth/users     → auth.users (tabela users w schemacie auth)
/public/cards   → public.cards (tabela cards w schemacie public)
```

### Schematy w Supabase:

1. **Schemat `auth`** (zarządzany przez Supabase Auth)
   - `auth.users` - użytkownicy
   - `auth.sessions` - sesje logowania
   - `auth.refresh_tokens` - tokeny odświeżania
   - Inne tabele wewnętrzne Supabase Auth

2. **Schemat `public`** (nasze tabele aplikacyjne)
   - `public.cards` - nasze fiszki
   - `public.review_history` - nasza historia przeglądów
   - **To tutaj tworzymy nasze tabele!**

3. **Schemat `storage`** (Supabase Storage)
   - Tabele dla zarządzania plikami (jeśli używamy Storage)

**W queries można pominąć `public.` (domyślny schemat):**
```sql
-- Te zapytania są równoważne:
SELECT * FROM public.cards WHERE user_id = '...';
SELECT * FROM cards WHERE user_id = '...';  -- ← W praktyce używamy tego

-- Ale dla auth.users MUSIMY użyć pełnej notacji (gdybyśmy mieli dostęp):
SELECT * FROM auth.users WHERE id = '...';
```

**Wizualizacja struktury:**
```
PostgreSQL Database
│
├── Schemat: auth (zarządzany przez Supabase)
│   ├── users                 → auth.users
│   ├── sessions              → auth.sessions
│   └── refresh_tokens        → auth.refresh_tokens
│
└── Schemat: public (nasze tabele aplikacyjne)
    ├── cards                 → public.cards (lub po prostu: cards)
    └── review_history        → public.review_history (lub po prostu: review_history)
```

### 0.1. Tabela `users` w schemacie `auth` (zarządzana przez Supabase)

Supabase Auth automatycznie zarządza tabelą użytkowników w **schemacie `auth`**. **Nie tworzymy tej tabeli ręcznie** - jest już dostępna po włączeniu Supabase Auth.

**Najważniejsze kolumny w `auth.users`:**
- `id` - UUID, PRIMARY KEY, używany jako `user_id` w naszych tabelach
- `email` - email użytkownika
- `encrypted_password` - zaszyfrowane hasło
- `email_confirmed_at` - timestamp potwierdzenia emaila
- `created_at` - data utworzenia konta
- `updated_at` - data ostatniej aktualizacji
- `last_sign_in_at` - ostatnie logowanie

### 0.2. Czy potrzebujemy tabeli `profiles`?

**Dla MVP: NIE**

Typowo w aplikacjach Supabase tworzy się dodatkową tabelę `public.profiles` dla danych użytkownika, które wykraczają poza authentication (np. avatar, bio, preferencje, ustawienia).

**Analiza wymagań MVP:**
- ✅ Email użytkownika - dostępny w `auth.users.email`
- ✅ Data utworzenia konta - dostępna w `auth.users.created_at`
- ✅ Całkowita liczba fiszek - obliczana z tabeli `cards`
- ✅ Zmiana hasła - obsługiwana przez Supabase Auth API

**Wniosek:** W MVP wszystkie wymagane dane (US-025, US-026) są dostępne przez `auth.users` lub obliczane z tabeli `cards`. Tabela `profiles` **nie jest potrzebna w MVP**.

### 0.3. Potencjalne rozszerzenie (poza MVP)

Jeśli w przyszłości będziemy potrzebować dodatkowych danych użytkownika, możemy utworzyć:

```sql
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  avatar_url TEXT,
  display_name VARCHAR(100),
  timezone VARCHAR(50),
  daily_goal INTEGER,
  notification_enabled BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Przykładowe use cases dla tabeli profiles:**
- Personalizacja interfejsu (avatar, nazwa wyświetlana)
- Preferencje użytkownika (timezone, cele dzienne)
- Ustawienia notyfikacji
- Analytics użytkownika

## 1. Tabele aplikacyjne (schemat `public`)

**Wszystkie nasze tabele są tworzone w schemacie `public`** - domyślnym schemacie dla aplikacji użytkownika.

Pełne nazwy:
- `public.cards` (w praktyce piszemy po prostu `cards`)
- `public.review_history` (w praktyce piszemy po prostu `review_history`)

### 1.1. Tabela `cards` (pełna nazwa: `public.cards`)

Centralna tabela przechowująca wszystkie fiszki użytkownika (staging, aktywne i odrzucone).

| Kolumna | Typ | Ograniczenia | Wartość domyślna | Opis |
|---------|-----|--------------|------------------|------|
| `id` | UUID | PRIMARY KEY NOT NULL | `gen_random_uuid()` | Unikalny identyfikator fiszki |
| `user_id` | UUID | NOT NULL, REFERENCES auth.users(id) ON DELETE CASCADE | - | Identyfikator właściciela fiszki |
| `front` | TEXT | NOT NULL | - | Pytanie/przednia strona fiszki |
| `back` | TEXT | NOT NULL | - | Odpowiedź/tylna strona fiszki |
| `status` | VARCHAR(20) | NOT NULL, CHECK (status IN ('staging', 'active', 'rejected')) | - | Status fiszki w systemie |
| `is_ai_generated` | BOOLEAN | NOT NULL | - | Flaga określająca czy fiszka została wygenerowana przez AI |
| `generation_batch_id` | UUID | NULL | - | Identyfikator batcha generowania AI (grupowanie) |
| `interval` | INTEGER | NOT NULL, CHECK (interval >= 0) | `0` | Interwał dni do następnej powtórki (SM-2) |
| `ease_factor` | DECIMAL(3,2) | NOT NULL, CHECK (ease_factor >= 1.3 AND ease_factor <= 3.0) | `2.50` | Współczynnik łatwości (SM-2) |
| `repetitions` | INTEGER | NOT NULL, CHECK (repetitions >= 0) | `0` | Liczba udanych powtórzeń (SM-2) |
| `next_review` | TIMESTAMP WITH TIME ZONE | NOT NULL | `NOW()` | Data i czas następnej powtórki |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | `NOW()` | Data i czas utworzenia |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | `NOW()` | Data i czas ostatniej modyfikacji |

### 1.2. Tabela `review_history` (pełna nazwa: `public.review_history`)

Tabela przechowująca historię wszystkich przeglądów fiszek dla analytics i walidacji metryk sukcesu.

| Kolumna | Typ | Ograniczenia | Wartość domyślna | Opis |
|---------|-----|--------------|------------------|------|
| `id` | UUID | PRIMARY KEY NOT NULL | `gen_random_uuid()` | Unikalny identyfikator wpisu historii |
| `card_id` | UUID | NOT NULL, REFERENCES cards(id) ON DELETE CASCADE | - | Identyfikator przeglądanej fiszki |
| `user_id` | UUID | NOT NULL, REFERENCES auth.users(id) ON DELETE CASCADE | - | Identyfikator użytkownika |
| `quality` | INTEGER | NOT NULL, CHECK (quality IN (0, 3, 4, 5)) | - | Ocena trudności: 0=Again, 3=Hard, 4=Good, 5=Easy |
| `reviewed_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | `NOW()` | Data i czas przeglądu |

## 2. Relacje między tabelami

**Uwaga:** Wszystkie relacje odwołują się do `auth.users(id)` - czyli tabeli `users` w schemacie `auth`, zarządzanej przez Supabase Auth. Ta tabela już istnieje i nie musimy jej tworzyć.

**Notacja:** `auth.users` = schemat `auth` + tabela `users` (NIE jest to kropka w nazwie!)

### 2.1. auth.users → cards (ONE-TO-MANY)
- Jeden użytkownik może posiadać wiele fiszek (limit 500 walidowany w aplikacji)
- Foreign key: `cards.user_id` → `auth.users.id`
- Kaskadowe usuwanie: usunięcie użytkownika usuwa wszystkie jego fiszki (RODO compliance)
- **Supabase Auth:** Usunięcie konta przez `supabase.auth.admin.deleteUser()` automatycznie usunie wszystkie powiązane dane

### 2.2. auth.users → review_history (ONE-TO-MANY)
- Jeden użytkownik może mieć wiele wpisów w historii przeglądów
- Foreign key: `review_history.user_id` → `auth.users.id`
- Kaskadowe usuwanie: usunięcie użytkownika usuwa całą jego historię

### 2.3. cards → review_history (ONE-TO-MANY)
- Jedna fiszka może mieć wiele wpisów w historii (każde powtórzenie tworzy nowy wpis)
- Foreign key: `review_history.card_id` → `cards.id`
- Kaskadowe usuwanie: usunięcie fiszki usuwa jej historię przeglądów

### 2.4. cards → cards (logiczne grupowanie przez generation_batch_id)
- Fiszki z tego samego generowania AI mają wspólny `generation_batch_id`
- Brak enforced foreign key - tylko logiczne powiązanie
- Umożliwia operacje "Zaakceptuj wszystkie" na całym batchu

## 3. Indeksy

### 3.1. Indeksy dla tabeli `cards`

#### idx_cards_user_next_review (kompozytowy, priorytet wysoki)
```sql
CREATE INDEX idx_cards_user_next_review ON cards(user_id, next_review);
```
**Cel:** Optymalizacja głównego use case - wybór fiszek do nauki dla użytkownika.  
**Query:** `SELECT * FROM cards WHERE user_id = ? AND status = 'active' AND next_review <= NOW()`

#### idx_cards_user_status (kompozytowy)
```sql
CREATE INDEX idx_cards_user_status ON cards(user_id, status);
```
**Cel:** Szybkie filtrowanie fiszek według statusu.  
**Query:** Dashboard - wyświetlanie fiszek w różnych statusach (staging, active, rejected)

#### idx_cards_user_ai_generated (kompozytowy)
```sql
CREATE INDEX idx_cards_user_ai_generated ON cards(user_id, is_ai_generated);
```
**Cel:** Obliczanie metryk sukcesu MVP (AI Usage Rate).  
**Query:** `SELECT COUNT(*) FROM cards WHERE user_id = ? AND is_ai_generated = true`

#### idx_cards_search (GIN, full-text search)
```sql
CREATE INDEX idx_cards_search ON cards USING GIN (
  to_tsvector('english', coalesce(front, '') || ' ' || coalesce(back, ''))
);
```
**Cel:** Wyszukiwanie pełnotekstowe w pytaniach i odpowiedziach.  
**Query:** `SELECT * FROM cards WHERE to_tsvector('english', front || ' ' || back) @@ plainto_tsquery('english', ?)`

### 3.2. Indeksy dla tabeli `review_history`

#### idx_review_history_card
```sql
CREATE INDEX idx_review_history_card ON review_history(card_id);
```
**Cel:** Szybkie pobieranie historii przeglądów dla konkretnej fiszki.  
**Query:** Analiza postępów nauki dla pojedynczej fiszki

#### idx_review_history_user (kompozytowy)
```sql
CREATE INDEX idx_review_history_user ON review_history(user_id, reviewed_at);
```
**Cel:** Analiza aktywności użytkownika w czasie, statystyki.  
**Query:** `SELECT * FROM review_history WHERE user_id = ? AND reviewed_at >= ? ORDER BY reviewed_at DESC`

## 4. Row Level Security (RLS) Policies

### 4.1. Policies dla tabeli `cards`

#### Włączenie RLS
```sql
ALTER TABLE cards ENABLE ROW LEVEL SECURITY;
```

#### Policy: select_own_cards
```sql
CREATE POLICY select_own_cards ON cards 
  FOR SELECT
  USING (auth.uid() = user_id);
```
**Cel:** Użytkownik może czytać tylko własne fiszki.

#### Policy: insert_own_cards
```sql
CREATE POLICY insert_own_cards ON cards 
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);
```
**Cel:** Użytkownik może tworzyć fiszki tylko dla siebie.

#### Policy: update_own_cards
```sql
CREATE POLICY update_own_cards ON cards 
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
```
**Cel:** Użytkownik może modyfikować tylko własne fiszki.

#### Policy: delete_own_cards
```sql
CREATE POLICY delete_own_cards ON cards 
  FOR DELETE
  USING (auth.uid() = user_id);
```
**Cel:** Użytkownik może usuwać tylko własne fiszki.

### 4.2. Policies dla tabeli `review_history`

#### Włączenie RLS
```sql
ALTER TABLE review_history ENABLE ROW LEVEL SECURITY;
```

#### Policy: select_own_reviews
```sql
CREATE POLICY select_own_reviews ON review_history 
  FOR SELECT
  USING (auth.uid() = user_id);
```
**Cel:** Użytkownik może czytać tylko własną historię przeglądów.

#### Policy: insert_own_reviews
```sql
CREATE POLICY insert_own_reviews ON review_history 
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);
```
**Cel:** Użytkownik może tworzyć wpisy historii tylko dla siebie.

**Uwaga:** Brak policies dla UPDATE i DELETE - historia przeglądów jest immutable (tylko INSERT i SELECT).

## 5. Triggery i funkcje

### 5.1. Auto-update dla kolumny `updated_at`

#### Funkcja trigger
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

#### Trigger dla tabeli cards
```sql
CREATE TRIGGER update_cards_updated_at 
  BEFORE UPDATE ON cards
  FOR EACH ROW 
  EXECUTE FUNCTION update_updated_at_column();
```

**Cel:** Automatyczna aktualizacja timestamp `updated_at` przy każdej modyfikacji fiszki, zapewnia dokładny audyt bez polegania na logice aplikacyjnej.

## 6. Uwagi dotyczące implementacji

### 6.1. Walidacja biznesowa w aplikacji

#### Limit 500 fiszek na użytkownika
- **Implementacja:** Walidacja na poziomie Astro API route przed INSERT
- **Query:** `SELECT COUNT(*) FROM cards WHERE user_id = ? AND status != 'staging'`
- **Komunikat:** "Osiągnąłeś limit 500 fiszek. Usuń nieużywane fiszki, aby dodać nowe."
- **Uzasadnienie:** Lepszy UX niż database trigger, pozwala na jasny komunikat użytkownikowi

#### Walidacja długości tekstu
- **Input do AI:** 10-2000 znaków (walidacja frontend + backend)
- **Pola front/back:** Opcjonalna walidacja max 5000 znaków w aplikacji
- **Typ TEXT:** Brak sztywnego limitu w bazie, elastyczność na przyszłość

### 6.2. Flow danych dla kluczowych operacji

#### Generowanie fiszek przez AI
1. API route wywołuje OpenRouter.ai z tekstem użytkownika
2. Zwrócone fiszki zapisywane jako: `status = 'staging'`, `generation_batch_id = UUID (nowy)`
3. Staging area: użytkownik akceptuje/edytuje/odrzuca
4. Akceptacja: `UPDATE cards SET status = 'active' WHERE id IN (?)`
5. Odrzucenie: `UPDATE cards SET status = 'rejected' WHERE id = ?`
6. "Zaakceptuj wszystkie": `UPDATE cards SET status = 'active' WHERE generation_batch_id = ?`

#### Sesja nauki (spaced repetition)
1. Wybór fiszek: 
   ```sql
   SELECT * FROM cards 
   WHERE user_id = ? 
     AND status = 'active' 
     AND next_review <= NOW() 
   ORDER BY RANDOM()
   ```
2. Po każdej ocenie fiszki (Again/Hard/Good/Easy):
   - Obliczenie nowych wartości SM-2 w aplikacji
   - Update fiszki:
     ```sql
     UPDATE cards 
     SET interval = ?, 
         ease_factor = ?, 
         repetitions = ?, 
         next_review = ? 
     WHERE id = ?
     ```
   - Zapis do historii:
     ```sql
     INSERT INTO review_history (card_id, user_id, quality) 
     VALUES (?, ?, ?)
     ```

#### Wyszukiwanie fiszek
```sql
SELECT * FROM cards 
WHERE user_id = ? 
  AND status = 'active' 
  AND to_tsvector('english', front || ' ' || back) @@ plainto_tsquery('english', ?)
```

### 6.3. Dostęp do danych użytkownika (Supabase Auth)

#### Pobieranie danych użytkownika w aplikacji

**Backend (Astro API routes):**
```typescript
// Pobranie aktualnie zalogowanego użytkownika
const { data: { user } } = await supabase.auth.getUser();
// user.id - UUID użytkownika
// user.email - email użytkownika
// user.created_at - data utworzenia konta
```

**Frontend (React components):**
```typescript
// Hook do pobierania sesji
const { data: { session } } = await supabase.auth.getSession();
// session?.user - obiekt użytkownika
```

#### Użycie w queries do bazy danych

Supabase SDK automatycznie ustawia `auth.uid()` w kontekście RLS policies:

```typescript
// To query automatycznie filtruje po user_id dzięki RLS
const { data: cards } = await supabase
  .from('cards')
  .select('*')
  .eq('status', 'active');

// RLS policy zapewnia że zwrócone będą tylko fiszki użytkownika
// WHERE user_id = auth.uid() jest automatycznie dodawane
```

#### Dostęp do tabeli auth.users

**WAŻNE:** Tabela `auth.users` jest **niedostępna** bezpośrednio przez Supabase Client dla użytkowników (security reasons).

**Dostępne metody:**
- ✅ `supabase.auth.getUser()` - pobranie własnych danych
- ✅ `supabase.auth.updateUser()` - aktualizacja własnych danych
- ✅ `supabase.auth.admin.deleteUser()` - usunięcie (tylko admin/service_role)
- ❌ `supabase.from('auth.users').select()` - **ZABLOKOWANE**

**Dla US-025 (profil użytkownika):**
```typescript
// Pobranie danych profilu
const { data: { user } } = await supabase.auth.getUser();

// Pobranie statystyk fiszek
const { count: totalCards } = await supabase
  .from('cards')
  .select('*', { count: 'exact', head: true })
  .neq('status', 'staging');

const { count: aiCards } = await supabase
  .from('cards')
  .select('*', { count: 'exact', head: true })
  .eq('is_ai_generated', true)
  .neq('status', 'staging');

// Wyświetlenie w UI:
// Email: user.email
// Data utworzenia: user.created_at
// Liczba fiszek: totalCards
// Fiszki AI / manualne: aiCards / (totalCards - aiCards)
```

### 6.4. Strategia migracji

#### Narzędzie
Supabase Migrations (CLI) z integracją GitHub Actions

#### Struktura plików
```
/supabase/migrations/
  20231205000001_initial_schema.sql      # Tabele: cards, review_history (NIE auth.users - już istnieje)
  20231205000002_rls_policies.sql        # RLS policies dla cards i review_history
  20231205000003_indexes.sql             # Wszystkie indeksy wydajnościowe
  20231205000004_triggers.sql            # Trigger dla updated_at
```

**Uwaga:** Tabela `auth.users` jest automatycznie tworzona przez Supabase Auth i **nie powinna być** w naszych migracjach. Tworzymy tylko tabele w schemacie `public`.

**Przykład tworzenia tabeli w migracji:**
```sql
-- To automatycznie tworzy tabelę w schemacie public (domyślny)
CREATE TABLE cards (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  -- ↑ Odwołanie do tabeli users w schemacie auth
  ...
);

-- Równoważne zapisy (explicit schema):
CREATE TABLE public.cards (...);  -- Jawne określenie schematu
CREATE TABLE cards (...);         -- Domyślnie public
```

#### CI/CD
GitHub Actions automatycznie uruchamia migracje przy deploy do production

### 6.5. Metryki wydajności

#### Oczekiwana wydajność dla 500 fiszek per user
- Query execution time: < 100ms (cel)
- Index hit rate: > 95%
- Composite index (user_id, next_review): O(log n) dla głównego query

#### Storage estimate
- 500 fiszek × średnio 200 znaków × 2 (front + back) = ~200KB per user
- Review history: ~10 KB per user per miesiąc przy codziennej nauce

#### Monitoring
- Query execution time przez Supabase Dashboard
- Database connections usage
- Index usage statistics: `pg_stat_user_indexes`

### 6.6. Compliance RODO

#### Right to be forgotten
- `ON DELETE CASCADE` zapewnia automatyczne pełne usunięcie danych użytkownika
- Usunięcie konta: wszystkie fiszki i historia przeglądów są automatycznie usuwane

#### Data isolation
- RLS policies na poziomie bazy danych zapewniają izolację między użytkownikami
- Niemożliwy dostęp do danych innych użytkowników nawet przy manipulacji requestów

#### Consent
- Zgoda RODO wymagana podczas rejestracji (checkbox)
- Informacja o przesyłaniu treści fiszek do OpenRouter.ai (poza UE)

### 6.7. Skalowalność i przyszłe rozszerzenia

#### Potencjalne optymalizacje (poza MVP)
- Partycjonowanie tabeli `review_history` po dacie jeśli historia urośnie
- Dedykowana kolumna `search_vector` typu TSVECTOR dla szybszego full-text search
- Materialized views dla złożonych statystyk użytkownika
- Tabela `generation_batches` dla metadanych generowania AI (model, koszt, tokeny)

#### Granice obecnego projektu
- Limit 500 fiszek per user - wystarczający dla MVP
- Brak partycjonowania - niepotrzebne przy obecnych limitach
- Proste indeksy - wystarczające dla małych zbiorów danych

## 7. Podsumowanie decyzji projektowych

### Kluczowe wybory
1. **Schematy PostgreSQL:** Nasze tabele w `public` (cards, review_history), Supabase Auth w `auth` (users). Notacja `auth.users` = schemat + tabela, NIE kropka w nazwie.
2. **Supabase Auth bez dodatkowej tabeli profiles:** W MVP wykorzystujemy tylko `auth.users` - wszystkie wymagane dane (email, created_at) są tam dostępne. Tabela `profiles` nie jest potrzebna dla obecnych wymagań.
3. **Jedna tabela dla wszystkich statusów fiszek:** Pole `status` zamiast osobnych tabel - upraszcza queries i migracje statusów
4. **TEXT bez limitu:** Elastyczność na przyszłość, brak różnicy w wydajności vs VARCHAR w PostgreSQL
5. **CHECK constraints dla SM-2:** Ochrona przed błędami w logice aplikacyjnej
6. **UUID dla wszystkich ID:** Zgodność z Supabase Auth, bezpieczeństwo (nieprzewidywalne ID)
7. **Osobne RLS policies per operacja:** Większa przejrzystość i security niż jedna policy "ALL"
8. **generation_batch_id jako nullable UUID:** Logiczne grupowanie bez enforced FK, elastyczność
9. **Review history jako immutable:** Tylko INSERT i SELECT, historia nie jest edytowalna
10. **Hard delete:** Zgodne z US-015, bez soft-delete (deleted_at), KISS dla MVP
11. **Timestamp WITH TIME ZONE:** UTC storage, lokalizacja timezone po stronie frontendu
12. **Composite indexes:** Optymalizacja dla najbardziej częstych queries (user_id + inne pole)
13. **Foreign keys do auth.users z ON DELETE CASCADE:** Automatyczne czyszczenie danych użytkownika przy usunięciu konta (RODO compliance)

### Alignment z PRD
- ✅ US-001/002: Rejestracja i logowanie przez Supabase Auth
- ✅ US-025: Profil użytkownika - dane z `auth.users` (email, created_at)
- ✅ US-026: Zmiana hasła - `supabase.auth.updateUser()`
- ✅ US-028: RLS policies zabezpieczają dostęp do własnych fiszek
- ✅ US-005: Manualne dodawanie (is_ai_generated = false)
- ✅ US-006/007: Staging area (status = 'staging')
- ✅ US-017-022: Sesja nauki z algorytmem SM-2 (parametry w cards)
- ✅ Metryki sukcesu: Możliwość obliczenia AI Acceptance Rate i AI Usage Rate

### Bezpieczeństwo
- **Authentication:** Supabase Auth z weryfikacją emaila, hashowanie haseł (bcrypt), session management
- **Database level:** RLS policies z `auth.uid()`, CHECK constraints, foreign keys z CASCADE
- **Application level:** Walidacja limitów, sanityzacja inputów, rate limiting
- **Infrastructure level:** Supabase connection pooling, backup strategy, SSL/TLS dla połączeń

