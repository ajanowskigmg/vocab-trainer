# Podsumowanie Rozmowy - Planning PRD dla Vocab Trainer MVP

## Decisions

1. **Grupa docelowa**: Użytkownicy średnio-zaawansowani w aplikacjach webowych - studenci, uczniowie, pracownicy IT
2. **Model AI**: GPT-4o-mini (optymalny koszt/wydajność)
3. **Limit tekstu wejściowego**: 1000-2000 znaków na generowanie
4. **Algorytm spaced repetition**: SM-2 (open-source)
5. **Metryka akceptacji**: Flagi w bazie danych (`is_rejected`, `ai_generated`)
6. **Onboarding**: Brak w MVP
7. **Dodatkowe metryki**: Brak w MVP (focus na core functionality)
8. **Stos technologiczny**: Astro 5, React 19, TypeScript 5, Tailwind 4, Shadcn/ui, Supabase, Openrouter.ai
9. **Bezpieczeństwo**: Supabase Auth + Row Level Security, zgoda RODO, bez trybu offline
10. **Zasoby**: 1 deweloper, projekt szkoleniowy
11. **Struktura fiszki**: Klasyczne pytanie (front) / odpowiedź (back)
12. **Organizacja**: Jedna globalna talia w MVP
13. **AI Logic**: Astro API routes
14. **Edycja fiszek**: Modal z formularzem
15. **Import/export**: Odłożone na później
16. **Staging area**: Fiszki AI trafiają do review przed dodaniem do talii
17. **Struktura bazy**: 3 tabele (`users`, `cards`, opcjonalnie `review_history`)
18. **Ocena trudności**: 4 przyciski (Again/Hard/Good/Easy) zgodnie z SM-2
19. **Limity sesji**: Brak sztywnych limitów - użytkownik kontroluje
20. **System promptów**: Hardcoded w kodzie
21. **Deployment**: DigitalOcean z Docker, GitHub Actions CI/CD

## Matched Recommendations

1. **Persony użytkowników**: Zdefiniowano 2-3 typy użytkowników (student, uczeń, pracownik IT) o zbliżonym poziomie zaawansowania technicznego
2. **Koszt AI**: GPT-4o-mini z przewidywanym kosztem ~$0.50-1.00 na 1000 fiszek, limit 500 fiszek/użytkownika lub $10/miesiąc cap
3. **Limity tekstu**: 1000-2000 znaków (ok. 0.5-1 strona A4), generowanie 5-8 fiszek per request
4. **Algorytm SM-2**: Implementacja jako open-source, brak zależności od płatnych API
5. **Metryka akceptacji**: Fiszka jest "akceptowana" jeśli nie jest oflagowana jako `is_rejected` w bazie
6. **Stos technologiczny**: Astro 5 + React 19 + TypeScript 5 + Tailwind 4 + Shadcn/ui + Supabase + Openrouter.ai - zero backend, wszystko w jednym repo, Docker deployment
7. **Row Level Security**: Supabase RLS z policies `user_id = auth.uid()` dla tabel `decks` i `cards`
8. **AI Generation Location**: Astro API routes (`src/pages/api/generate-cards.ts`)
9. **Edycja UI**: Modal z formularzem dla pojedynczej fiszki, lista z akcjami edit/delete/reject
10. **Struktura nawigacji**: 4 główne widoki - Dashboard/Lista, Dodaj fiszki, Sesja nauki, Profil
11. **Staging Area**: Review mode po generowaniu - użytkownik przegląda, edytuje lub odrzuca przed dodaniem do talii
12. **Schema bazy danych**: 
    - `cards`: id, user_id, front, back, is_ai_generated, is_rejected, next_review, interval, ease_factor, repetitions, created_at
    - Opcjonalnie `review_history` dla przyszłych analytics
13. **Interfejs nauki**: 4 przyciski oceny trudności zgodnie z algorytmem SM-2
14. **Feedback po sesji**: Prosty summary screen z liczbą przerobowych fiszek i datą następnej sesji
15. **Error handling**: Basic - toast messages dla użytkownika, manual retry, brak automatic retry
16. **System promptów**: Few-shot examples z instrukcjami o formacie i atomowych pytaniach
17. **Deployment**: DigitalOcean z Docker image + Supabase (500MB, 50K users), GitHub Actions CI/CD pipeline z auto-deploy

## PRD Planning Summary

### Problem Statement
Manualne tworzenie wysokiej jakości fiszek edukacyjnych jest czasochłonne, co zniechęca do korzystania z efektywnej metody nauki jaką jest spaced repetition.

### Target Users
- **Persona**: Użytkownicy średnio-zaawansowani technicznie
- **Przykłady**: Studenci, uczniowie, pracownicy IT
- **Charakterystyka**: Korzystają na codzień z aplikacji webowych, szukają efektywnych narzędzi do nauki

### Core Features (MVP)

#### 1. AI-Powered Flashcard Generation
- **Input**: Tekst 1000-2000 znaków (kopiuj-wklej)
- **Output**: 5-8 fiszek generowanych przez GPT-4o-mini
- **Flow**: 
  1. Użytkownik wkleja tekst
  2. Klika "Generuj"
  3. Fiszki trafiają do staging area (review mode)
  4. Użytkownik może: zaakceptować, edytować lub odrzucić każdą fiszkę
  5. Zaakceptowane fiszki trafiają do talii
- **Format**: Klasyczne pytanie/odpowiedź (plain text)

#### 2. Manual Flashcard Creation
- **UI**: Prosty formularz z polami "Pytanie" i "Odpowiedź"
- **Editing**: Modal z opcjami Save/Cancel
- **Actions**: Edytuj, usuń, oznacz jako odrzucona

#### 3. Flashcard Management
- **Organizacja**: Jedna globalna talia w MVP (wszystkie fiszki w jednej puli)
- **Widok**: Lista/karty z akcjami (edit, delete, flag as rejected)
- **Metadane**: Każda fiszka ma flagę `is_ai_generated` i `is_rejected`

#### 4. Spaced Repetition Learning
- **Algorytm**: SM-2 (SuperMemo 2)
- **Sesja nauki**:
  1. Użytkownik klika "Ucz się"
  2. System pokazuje fiszki zaplanowane na dziś
  3. Użytkownik widzi pytanie → odkrywa odpowiedź → ocenia trudność
  4. Algorytm planuje następne powtórzenie
- **Ocena trudności**: 4 przyciski - Again (0), Hard (3), Good (4), Easy (5)
- **Kontrola**: Licznik "X fiszek do powtórzenia", przycisk "Zakończ sesję", brak sztywnych limitów
- **Feedback**: Prosty summary po zakończeniu ("Przerobione: X fiszek, Następna sesja: [data]")

#### 5. User Authentication
- **Provider**: Supabase Auth
- **Security**: Row Level Security (RLS) z policies `user_id = auth.uid()`
- **Compliance**: Zgoda RODO na przetwarzanie treści przez AI w regulaminie

### Technical Architecture

#### Frontend
- **Framework**: Astro 5 z React 19 dla komponentów interaktywnych
- **Styling**: Tailwind 4
- **UI Components**: Shadcn/ui
- **Language**: TypeScript 5
- **Navigation**: 4 główne strony
  1. Dashboard/Lista fiszek
  2. Dodaj fiszki (manual + AI)
  3. Sesja nauki
  4. Profil/Ustawienia

#### Backend
- **Database**: Supabase (PostgreSQL)
- **BaaS**: Supabase SDK (Backend-as-a-Service)
- **API**: Astro API routes (`src/pages/api/generate-cards.ts`)
- **AI Integration**: Openrouter.ai (dostęp do OpenAI, Anthropic, Google i innych modeli)
- **Auth**: Supabase Auth + RLS

#### Database Schema
```
users (zarządzane przez Supabase Auth)

cards
- id (uuid)
- user_id (uuid, FK)
- front (text)
- back (text)
- is_ai_generated (boolean)
- is_rejected (boolean)
- next_review (timestamp)
- interval (integer)
- ease_factor (float)
- repetitions (integer)
- created_at (timestamp)

review_history (opcjonalnie)
- id (uuid)
- card_id (uuid, FK)
- quality (integer)
- reviewed_at (timestamp)
```

#### AI Prompt Strategy
- **Type**: Few-shot prompting
- **Content**: 
  - Instrukcje o formacie fiszek
  - 2-3 przykłady dobrych fiszek
  - Wymaganie atomowych, konkretnych pytań
- **Configuration**: Hardcoded w kodzie (nie konfigurowalny w MVP)

#### Error Handling
- API failure → Toast "Coś poszło nie tak, spróbuj ponownie" + retry button
- Invalid JSON response → "Nie udało się wygenerować fiszek"
- Rate limit (429) → "Przekroczono limit, spróbuj za chwilę"
- Manual retry (bez automatic retry)

### Success Metrics
1. **AI Acceptance Rate**: 75% fiszek wygenerowanych przez AI jest akceptowane (nie są oflagowane jako `is_rejected`)
2. **AI Usage Rate**: 75% fiszek tworzonych z wykorzystaniem AI

### Deployment
- **Hosting**: DigitalOcean (Docker container)
- **Database**: Supabase (500MB, 50K users)
- **CI/CD**: GitHub Actions pipeline
- **Deployment flow**: GitHub → GitHub Actions build → Docker image → DigitalOcean auto-deploy
- **Containerization**: Dockerfile z multi-stage build dla optymalizacji

### Cost Estimation
- **AI**: ~$0.50-1.00 na 1000 wygenerowanych fiszek (zależnie od wybranego modelu w Openrouter.ai)
- **Limits**: 500 fiszek/użytkownika, $10/miesiąc cap w Openrouter.ai dla projektu szkoleniowego
- **Infrastructure**: DigitalOcean (~$5-10/miesiąc) + Supabase free tier

### Project Constraints
- **Team**: 1 deweloper full-stack
- **Type**: Projekt szkoleniowy
- **Timeline**: Elastyczny, focus na learning
- **Scope**: Strictly MVP - bez feature creep

### Out of Scope (MVP)
- Zaawansowany algorytm powtórek (beyond SM-2)
- Import wielu formatów (PDF, DOCX)
- Współdzielenie zestawów między użytkownikami
- Integracje z innymi platformami
- Aplikacje mobilne
- Onboarding tutorial
- Dodatkowe metryki i analytics
- Organizacja w wiele talii/zestawów
- Zaawansowane typy fiszek (luki, multiple choice, obrazki)
- Import/export fiszek
- Tryb offline
- Konfigurowalny system promptów
- Staging environment (może być dodany później dzięki Docker)

## Unresolved Issues

Brak nierozwiązanych kwestii krytycznych. Wszystkie kluczowe decyzje zostały podjęte. Potencjalne obszary do doprecyzowania w trakcie development:

1. **Dokładna treść system promptu** - wymaga iteracji i testowania na różnych typach treści
2. **Szczegóły UX/UI** - wireframes i konkretny design system (kolory, typography, spacing) nie zostały określone
3. **Dokładna treść komunikatów błędów** - do ustalenia w trakcie implementacji
4. **Limity rate limiting** - konkretne wartości dla API calls (requests per minute/hour/day)
5. **Backup strategy** - brak planu dla disaster recovery (choć dla projektu szkoleniowego nie jest krytyczne)
6. **Testing strategy** - nie określono podejścia do testowania (manual, automated, scope)

Wszystkie powyższe punkty są naturalnymi elementami do doprecyzowania w trakcie development i nie blokują rozpoczęcia prac nad MVP.