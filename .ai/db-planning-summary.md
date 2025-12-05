<conversation_summary>

<decisions>

1. **Staging area**: Implementacja w tej samej tabeli `cards` z polem `status` zamiast osobnej tabeli `generated_cards_staging`

2. **Tabela review_history**: Zostanie włączona do MVP dla zbierania danych historycznych od początku

3. **Sesje nauki z "Again"**: Obsługa przez logikę aplikacyjną (state management w React), bez persystencji w bazie danych

4. **Typ user_id**: UUID z referencją `REFERENCES auth.users(id) ON DELETE CASCADE`

5. **Indeksy**: Akceptacja wszystkich zalecanych indeksów dla wydajności (user_id + next_review, full-text search GIN, etc.)

6. **Constraints dla SM-2**: Dodanie CHECK constraints dla `ease_factor`, `interval`, `repetitions`

7. **Limit 500 fiszek**: Walidacja na poziomie aplikacji zamiast triggera bazodanowego

8. **Typy pól front/back**: TEXT bez sztywnego limitu długości

9. **RLS policies**: Osobne policies dla SELECT/INSERT/UPDATE/DELETE dla każdej tabeli

10. **Kaskadowe usuwanie**: `ON DELETE CASCADE` dla review_history

11. **Status fiszek**: Pole `status` z wartościami: `'staging'`, `'active'`, `'rejected'`

12. **Grupowanie generowań AI**: Dodanie pola `generation_batch_id UUID` dla śledzenia batchy

13. **Timestamp auditing**: Dodanie `created_at` i `updated_at` z automatycznym triggerem dla updated_at

14. **Metadane review_history**: Minimalna struktura w MVP (bez response_time, device_type, etc.)

15. **Wartości domyślne SM-2**: Użycie domyślnych wartości w schemacie (interval=0, ease_factor=2.5, repetitions=0)

16. **Full-text search**: Prosty GIN index bez dedykowanej kolumny `search_vector`

17. **Flaga is_ai_generated**: Zachowanie jako osobne pole boolean

18. **Strategia usuwania**: Hard delete (bez soft-delete/deleted_at)

19. **Migracje**: Użycie Supabase Migrations (wbudowane w Supabase CLI)

20. **Widoki (VIEWs)**: Brak widoków w MVP, bezpośrednie zapytania do tabel

</decisions>

<matched_recommendations>

1. **Tabela review_history w MVP**: Dane historyczne są nieodwracalne - lepiej zbierać od początku. Tabela jest prosta i umożliwi walidację metryk sukcesu MVP.

2. **UUID z ON DELETE CASCADE**: Zapewni automatyczne usunięcie wszystkich fiszek użytkownika przy usunięciu konta, zgodnie z wymaganiami RODO.

3. **Indeksy kompozytowe**: `CREATE INDEX idx_cards_user_next_review ON cards(user_id, next_review)` jest kluczowy dla wydajności głównego use case (wybór fiszek do nauki).

4. **CHECK constraints dla SM-2**: 
   - `ease_factor DECIMAL(3,2) CHECK (ease_factor >= 1.3 AND ease_factor <= 3.0)`
   - `interval INTEGER CHECK (interval >= 0)`
   - `repetitions INTEGER CHECK (repetitions >= 0)`
   Zapobiegnie błędom w logice aplikacyjnej.

5. **Walidacja limitu w aplikacji**: Defense in depth - aplikacja powinna sprawdzać limit przed INSERT dla lepszego UX (jasny komunikat użytkownikowi).

6. **TEXT dla front/back**: PostgreSQL nie ma różnicy w wydajności między TEXT a VARCHAR. TEXT daje elastyczność bez sztywnych limitów.

7. **Osobne RLS policies**: Większa przejrzystość i bezpieczeństwo niż jedna policy "ALL". Każda operacja (SELECT/INSERT/UPDATE/DELETE) ma dedykowaną policy.

8. **Pole status**: ENUM lub VARCHAR z wartościami `'staging'`, `'active'`, `'rejected'` jest bardziej czytelny i łatwiejszy do rozszerzenia niż kombinacja booleanów.

9. **generation_batch_id**: Umożliwi operacje "Zaakceptuj wszystkie" i przyszłe śledzenie jakości poszczególnych generowań AI.

10. **Timestamp z triggerem**: Automatyczna aktualizacja `updated_at` przez trigger zapewni dokładny audyt bez polegania na logice aplikacyjnej.

11. **GIN index dla search**: Dla MVP (limit 500 fiszek per user) prosty GIN index wystarczy. Dedykowana kolumna `search_vector` możliwa w przyszłości jeśli potrzebna.

12. **is_ai_generated jako osobne pole**: Upraszcza zapytania i jest explicite wymagane w PRD. Metryki sukcesu (AI Usage Rate) bazują bezpośrednio na tym polu.

13. **Hard delete**: Zgodne z US-015 o permanentnym usunięciu i braku undo. KISS dla MVP.

14. **Supabase Migrations**: Wbudowane narzędzie z integracją GitHub Actions, wersjonowaniem i rollback support. Brak dodatkowych zależności.

15. **Brak VIEWs w MVP**: Queries są proste, lepiej trzymać logikę w aplikacji dla elastyczności. Można rozważyć później jeśli będą powtarzające się złożone zapytania.

</matched_recommendations>

<database_planning_summary>

## Schemat bazy danych dla Vocab Trainer MVP

### Główne encje

#### 1. **Tabela `cards`** (główna tabela fiszek)
Centralna tabela przechowująca wszystkie fiszki użytkownika, zarówno te w staging, aktywne, jak i odrzucone.

**Struktura:**
- `id` UUID PRIMARY KEY (default: gen_random_uuid())
- `user_id` UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
- `front` TEXT NOT NULL (pytanie)
- `back` TEXT NOT NULL (odpowiedź)
- `status` VARCHAR(20) NOT NULL CHECK (status IN ('staging', 'active', 'rejected'))
- `is_ai_generated` BOOLEAN NOT NULL
- `generation_batch_id` UUID NULL (dla grupowania fiszek z jednego generowania AI)
- **Parametry SM-2:**
  - `interval` INTEGER DEFAULT 0 NOT NULL CHECK (interval >= 0)
  - `ease_factor` DECIMAL(3,2) DEFAULT 2.50 NOT NULL CHECK (ease_factor >= 1.3 AND ease_factor <= 3.0)
  - `repetitions` INTEGER DEFAULT 0 NOT NULL CHECK (repetitions >= 0)
  - `next_review` TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
- **Auditing:**
  - `created_at` TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
  - `updated_at` TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL

**Indeksy:**
- `idx_cards_user_next_review` ON (user_id, next_review) - kluczowy dla sesji nauki
- `idx_cards_user_status` ON (user_id, status) - dla filtrowania
- `idx_cards_user_ai_generated` ON (user_id, is_ai_generated) - dla metryk
- `idx_cards_search` GIN ON to_tsvector('english', coalesce(front, '') || ' ' || coalesce(back, '')) - full-text search

#### 2. **Tabela `review_history`** (historia przeglądów)
Przechowuje historię każdej sesji nauki dla analytics i walidacji metryk.

**Struktura:**
- `id` UUID PRIMARY KEY (default: gen_random_uuid())
- `card_id` UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE
- `user_id` UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
- `quality` INTEGER NOT NULL CHECK (quality IN (0, 3, 4, 5)) - wartości SM-2 (Again=0, Hard=3, Good=4, Easy=5)
- `reviewed_at` TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL

**Indeksy:**
- `idx_review_history_card` ON (card_id)
- `idx_review_history_user` ON (user_id, reviewed_at)

### Relacje między encjami

1. **auth.users (Supabase Auth) → cards**: ONE-TO-MANY
   - Jeden użytkownik może mieć wiele fiszek (do 500)
   - Cascading delete: usunięcie użytkownika usuwa wszystkie jego fiszki

2. **auth.users → review_history**: ONE-TO-MANY
   - Jeden użytkownik może mieć wiele wpisów historii
   - Cascading delete: usunięcie użytkownika usuwa całą historię

3. **cards → review_history**: ONE-TO-MANY
   - Jedna fiszka może mieć wiele wpisów historii (każde powtórzenie)
   - Cascading delete: usunięcie fiszki usuwa jej historię

4. **cards → cards (via generation_batch_id)**: Logiczne grupowanie
   - Fiszki z tego samego generowania AI mają wspólny `generation_batch_id`
   - Brak enforced foreign key, tylko logiczne powiązanie

### Bezpieczeństwo (Row Level Security)

**Dla tabeli `cards`:**
```sql
ALTER TABLE cards ENABLE ROW LEVEL SECURITY;

CREATE POLICY select_own_cards ON cards FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY insert_own_cards ON cards FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY update_own_cards ON cards FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY delete_own_cards ON cards FOR DELETE
  USING (auth.uid() = user_id);
```

**Dla tabeli `review_history`:**
```sql
ALTER TABLE review_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY select_own_reviews ON review_history FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY insert_own_reviews ON review_history FOR INSERT
  WITH CHECK (auth.uid() = user_id);
```

### Triggery i funkcje

**1. Auto-update dla updated_at:**
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_cards_updated_at 
BEFORE UPDATE ON cards
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Walidacja i ograniczenia biznesowe

1. **Limit 500 fiszek**: Walidacja na poziomie aplikacji (Astro API route)
   - Przed INSERT sprawdzenie: `SELECT COUNT(*) FROM cards WHERE user_id = ? AND status != 'staging'`
   - Komunikat użytkownikowi jeśli limit osiągnięty

2. **Walidacja długości tekstu**: Na poziomie aplikacji
   - Input do generowania AI: 10-2000 znaków (frontend + backend validation)
   - Pola front/back: opcjonalna walidacja w aplikacji (np. max 1000 znaków)

3. **Walidacja statusu fiszek**: CHECK constraint w bazie
   - Status może być tylko: 'staging', 'active', 'rejected'

### Skalowalność i wydajność

**Architektura dla 500 fiszek per user:**
- Composite index (user_id, next_review) zapewnia O(log n) dla głównego query
- GIN index dla full-text search efektywny dla małych zbiorów danych
- Brak potrzeby partycjonowania przy obecnych limitach
- Connection pooling przez Supabase

**Metryki do monitorowania:**
- Query execution time dla głównych operacji (< 100ms cel)
- Index hit rate (> 95%)
- Database connections usage
- Storage (500 fiszek * średnio 200 znaków ≈ 100KB per user)

### Strategia migracji

**Narzędzie:** Supabase Migrations (CLI)

**Struktura:**
```
/supabase/migrations/
  20231205000001_initial_schema.sql      # Tabele cards, review_history
  20231205000002_rls_policies.sql        # RLS policies
  20231205000003_indexes.sql             # Wszystkie indeksy
  20231205000004_triggers.sql            # Trigger dla updated_at
```

**CI/CD:** GitHub Actions z automatycznym uruchomieniem migracji przy deploy

### Flow danych dla kluczowych operacji

**1. Generowanie fiszek AI:**
- API route wywołuje OpenRouter.ai
- Zwrócone fiszki zapisywane z `status = 'staging'`, `generation_batch_id = UUID`
- Użytkownik przegląda i akceptuje → `UPDATE cards SET status = 'active' WHERE generation_batch_id = ?`
- Użytkownik odrzuca → `UPDATE cards SET status = 'rejected' WHERE id = ?`

**2. Sesja nauki:**
- Query: `SELECT * FROM cards WHERE user_id = ? AND status = 'active' AND next_review <= NOW() ORDER BY RANDOM()`
- Po każdej ocenie:
  - `UPDATE cards SET interval = ?, ease_factor = ?, repetitions = ?, next_review = ? WHERE id = ?`
  - `INSERT INTO review_history (card_id, user_id, quality) VALUES (?, ?, ?)`

**3. Wyszukiwanie:**
- Query: `SELECT * FROM cards WHERE user_id = ? AND status = 'active' AND to_tsvector('english', front || ' ' || back) @@ plainto_tsquery('english', ?)`

### Compliance i RODO

- ON DELETE CASCADE zapewnia pełne usunięcie danych użytkownika przy usunięciu konta
- RLS na poziomie bazy danych zapewnia izolację danych między użytkownikami
- Brak soft-delete - permanentne usunięcie zgodne z "prawem do bycia zapomnianym"
- Treść fiszek przesyłana do OpenRouter.ai - wymaga zgody RODO w procesie rejestracji

</database_planning_summary>

<unresolved_issues>

1. **Typ pola status**: Czy użyć PostgreSQL ENUM vs VARCHAR? 
   - ENUM jest bardziej wydajny (1 bajt vs ~10 bajtów) ale trudniejszy w modyfikacji
   - VARCHAR jest elastyczniejszy ale wymaga walidacji przez CHECK constraint
   - **Rekomendacja do ustalenia**: VARCHAR(20) z CHECK constraint dla elastyczności w MVP

2. **Nazewnictwo kolumny generation_batch_id**: Czy alternatywna nazwa byłaby bardziej intuicyjna?
   - Opcje: `ai_batch_id`, `generation_id`, `batch_id`
   - **Rekomendacja**: Zachować `generation_batch_id` dla jasności

3. **Tabela generation_batches**: Czy w przyszłości potrzebna będzie osobna tabela dla metadanych generowania?
   - Potencjalne pola: input_text, model_used, cost, tokens_used, created_at
   - **Dla MVP**: Nie jest wymagana, można dodać później jeśli potrzebna szczegółowa analityka kosztów AI

4. **Timezone dla użytkowników**: Czy przechowywać timezone użytkownika dla precyzyjnego wyświetlania "następna sesja"?
   - TIMESTAMP WITH TIME ZONE przechowuje UTC, ale UI może wymagać lokalizacji
   - **Dla MVP**: Wyświetlanie w lokalnym timezone użytkownika po stronie frontendu wystarczy

5. **Index na generation_batch_id**: Czy potrzebny dla operacji "Zaakceptuj wszystkie"?
   - Query: `UPDATE cards SET status = 'active' WHERE generation_batch_id = ?`
   - **Rekomendacja**: Opcjonalny - dodać jeśli operacja będzie wolna, ale dla max 8 fiszek per batch raczej nie potrzebny

</unresolved_issues>

</conversation_summary>