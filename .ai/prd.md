# Dokument wymagań produktu (PRD) - Vocab Trainer MVP

## 1. Przegląd produktu

Vocab Trainer to aplikacja webowa wykorzystująca sztuczną inteligencję do automatycznego generowania fiszek edukacyjnych na podstawie wprowadzonego tekstu. Aplikacja integruje generowanie fiszek przez AI z algorytmem powtórek rozmieszczonych w czasie (spaced repetition), co pozwala użytkownikom efektywnie uczyć się nowych treści bez czasochłonnego manualnego tworzenia materiałów edukacyjnych.

Produkt jest przeznaczony dla użytkowników średnio-zaawansowanych technicznie, takich jak studenci, uczniowie, pracownicy biurowi, którzy korzystają na codzień z aplikacji webowych i szukają efektywnych narzędzi do nauki.

Kluczowe cechy produktu:
- Automatyczne generowanie fiszek przez GPT-4o-mini na podstawie tekstu 10-2000 znaków
- Staging area umożliwiający przegląd, edycję i odrzucenie wygenerowanych fiszek przed dodaniem do talii
- Manualne tworzenie i zarządzanie fiszkami
- Algorytm powtórek SM-2 (SuperMemo 2) do optymalnego planowania sesji nauki
- System uwierzytelniania użytkowników z zabezpieczeniem Row Level Security
- Pełna integracja w jednym repozytorium bez potrzeby osobnego backendu

Stos technologiczny:
- Frontend: Astro 5 z React 19, Tailwind 4, Shadcn/ui, TypeScript 5
- Backend: Astro API routes, Supabase (PostgreSQL + SDK jako BaaS)
- AI: Openrouter.ai (dostęp do wielu modeli: OpenAI, Anthropic, Google)
- Auth: Supabase Auth z Row Level Security
- CI/CD: GitHub Actions
- Deployment: DigitalOcean (Docker container) + Supabase

Projekt jest realizowany jako inicjatywa szkoleniowa przez jednego dewelopera full-stack z elastycznym timeframe i focusem na learning experience.

## 2. Problem użytkownika

Manualne tworzenie wysokiej jakości fiszek edukacyjnych jest czasochłonne i demotywujące, co stanowi znaczącą barierę w wykorzystaniu efektywnej metody nauki jaką jest spaced repetition.

Szczegółowy opis problemu:
- Tworzenie jednej dobrej fiszki wymaga przemyślenia pytania, sformułowania zwięzłej odpowiedzi i upewnienia się, że fiszka jest atomowa (dotyczy jednego konkretnego faktu)
- Przekształcenie strony notatek na fiszki może zająć 30-60 minut, co zniechęca do regularnego korzystania z metody
- Użytkownicy często rezygnują z tworzenia fiszek pomimo znajomości korzyści płynących ze spaced repetition
- Istniejące narzędzia albo nie oferują automatyzacji (Anki, Quizlet w wersji podstawowej), albo są zbyt drogie dla indywidualnych użytkowników
- Brak narzędzia, które łączy łatwość generowania z kontrolą nad jakością i treścią fiszek

Konsekwencje problemu:
- Marnowanie czasu na mniej efektywne metody nauki (wielokrotne czytanie, podkreślanie)
- Brak systematycznego wykorzystania spaced repetition mimo świadomości jego skuteczności
- Frustracja związana z czasochłonnym przygotowaniem materiałów edukacyjnych
- Niższa efektywność nauki i gorsza retencja wiedzy

Rozwiązanie oferowane przez Vocab Trainer:
- Redukcja czasu tworzenia fiszek z 30-60 minut do 2-5 minut dzięki AI
- Zachowanie kontroli nad jakością przez staging area z możliwością edycji i odrzucenia
- Połączenie automatyzacji z przetestowanym algorytmem powtórek SM-2
- Niski koszt wdrożenia (~$0.50-1.00 na 1000 fiszek) dostępny dla indywidualnych użytkowników
- Prosta, intuicyjna aplikacja webowa bez potrzeby instalacji

## 3. Wymagania funkcjonalne

### 3.1. Generowanie fiszek przez AI

Input:
- Pole tekstowe akceptujące 10-2000 znaków
- Możliwość wklejenia tekstu przez kopiuj-wklej
- Licznik znaków widoczny dla użytkownika
- Walidacja długości tekstu przed wysłaniem

Processing:
- Wywołanie Openrouter.ai API przez Astro API route (src/pages/api/generate-cards.ts)
- Możliwość wyboru modelu (domyślnie GPT-4o-mini dla optymalnego kosztu/wydajności)
- Few-shot prompting z 2-3 przykładami dobrych fiszek
- Instrukcje w prompcie o tworzeniu atomowych, konkretnych pytań
- Generowanie 5-8 fiszek per request
- System promptów hardcoded w kodzie
- Limit finansowy ustawiony w Openrouter.ai ($10/miesiąc)

Output:
- Fiszki trafiają do staging area (review mode)
- Format: klasyczne pytanie (front) / odpowiedź (back) w plain text
- Każda fiszka oznaczona flagą is_ai_generated = true
- Wyświetlenie wszystkich wygenerowanych fiszek w trybie przeglądu

Staging Area Flow:
- Użytkownik przegląda każdą wygenerowaną fiszkę
- Dla każdej fiszki może: zaakceptować (dodać do talii), edytować (modal z formularzem), odrzucić (ustawienie is_rejected = true)
- Wizualne rozróżnienie między fiszkami zaakceptowanymi, do przeglądu i odrzuconymi
- Przycisk "Zaakceptuj wszystkie" dla szybkiego dodania całego zestawu

Error Handling:
- API failure: Toast "Coś poszło nie tak, spróbuj ponownie" + przycisk retry
- Invalid JSON response: "Nie udało się wygenerować fiszek"
- Rate limit (429): "Przekroczono limit, spróbuj za chwilę"
- Wszystkie retry manualne (bez automatic retry)

### 3.2. Manualne tworzenie fiszek

Interface:
- Prosty formularz z dwoma polami: "Pytanie" (front) i "Odpowiedź" (back)
- Oba pola jako textarea dla wieloliniowego tekstu
- Przycisk "Zapisz" do dodania fiszki do talii
- Przycisk "Anuluj" do wyczyszczenia formularza
- Walidacja: oba pola muszą być wypełnione

Storage:
- Fiszki zapisywane bezpośrednio do tabeli cards
- is_ai_generated = false
- is_rejected = false
- next_review ustawione na bieżącą datę (dostępne od razu do nauki)
- Domyślne wartości SM-2: interval = 0, ease_factor = 2.5, repetitions = 0

### 3.3. Zarządzanie fiszkami

Widok listy:
- Wyświetlenie wszystkich fiszek użytkownika w jednej globalnej talii
- Dostępne widoki: lista lub karty (grid)
- Filtrowanie: wszystkie / AI-generated / manualne / odrzucone
- Sortowanie: data utworzenia / następna data przeglądu / alfabetycznie
- Wyszukiwanie po treści pytania lub odpowiedzi

Metadane wyświetlane dla każdej fiszki:
- Treść pytania (front)
- Ikona lub tag oznaczający źródło (AI vs manual)
- Status (aktywna, odrzucona)
- Następna data przeglądu
- Liczba powtórzeń

Akcje dla pojedynczej fiszki:
- Edytuj: otwiera modal z formularzem edycji (pola front i back), przyciski Save/Cancel
- Usuń: dialog potwierdzenia, permanentne usunięcie z bazy danych
- Oznacz jako odrzucona / Przywróć: toggle flagi is_rejected (odrzucone fiszki nie pojawiają się w sesjach nauki)

Edycja w modalu:
- Pre-wypełnione pola z bieżącą treścią
- Możliwość edycji zarówno pytania jak i odpowiedzi
- Zapisanie zmian aktualizuje rekord w bazie danych
- Brak wpływu na metadane SM-2 (zachowanie postępu nauki)

### 3.4. System powtórek rozmieszonych w czasie (Spaced Repetition)

Algorytm: SM-2 (SuperMemo 2)
- Open-source implementacja
- Parametry przechowywane w tabeli cards: next_review, interval, ease_factor, repetitions
- Automatyczne obliczanie następnej daty przeglądu na podstawie oceny trudności

Rozpoczęcie sesji nauki:
- Przycisk "Ucz się" na dashboardzie
- System wybiera fiszki gdzie next_review <= bieżąca data
- Licznik "X fiszek do powtórzenia" widoczny przed rozpoczęciem sesji
- Brak sztywnych limitów - użytkownik kontroluje długość sesji

Przebieg sesji:
1. Wyświetlenie pytania (front) fiszki
2. Przycisk "Pokaż odpowiedź" (lub odkrycie przez kliknięcie na kartę)
3. Wyświetlenie odpowiedzi (back)
4. Użytkownik ocenia trudność przyciskami: Again (0), Hard (3), Good (4), Easy (5)
5. System oblicza nowe wartości według algorytmu SM-2:
   - Again: repetitions = 0, interval = 0 (powtórzenie dziś)
   - Hard: obniżenie ease_factor, krótszy interval
   - Good: standardowy wzrost interval
   - Easy: wyższy ease_factor, dłuższy interval
6. Przejście do kolejnej fiszki
7. Licznik postępu: "X / Y fiszek"

Kontrola sesji:
- Przycisk "Zakończ sesję" dostępny w każdym momencie
- Postęp zapisywany na bieżąco (każda ocena od razu aktualizuje bazę danych)
- Możliwość wznowienia sesji później (pozostałe fiszki nadal zaplanowane na dziś)

Feedback po zakończeniu:
- Summary screen z informacjami:
  - "Przerobione: X fiszek"
  - "Następna sesja: [data najbliższego przeglądu]"
  - Podział na kategorie: Again (X), Hard (X), Good (X), Easy (X)
- Przycisk "Powrót do dashboardu"
- Przycisk "Kontynuuj naukę" (jeśli są jeszcze fiszki na dziś)

Dodatkowe zachowania:
- Nowe fiszki (repetitions = 0) włączane do sesji
- Fiszki z is_rejected = true wykluczane z sesji
- Randomizacja kolejności fiszek w ramach sesji
- Opcjonalnie: zapisywanie historii przeglądów do tabeli review_history (dla przyszłych analytics)

### 3.5. Uwierzytelnianie i autoryzacja użytkowników

Provider: Supabase Auth
- Wsparcie dla email + hasło jako podstawowej metody rejestracji/logowania
- Możliwość rozszerzenia o social providers (Google, GitHub) w przyszłości
- Zarządzanie sesją przez Supabase (refresh tokens, expiration)

Rejestracja:
- Formularz z polami: email, hasło, potwierdzenie hasła
- Walidacja siły hasła (minimum 8 znaków)
- Weryfikacja email (link aktywacyjny wysyłany przez Supabase)
- Akceptacja zgody RODO na przetwarzanie treści przez AI (checkbox przed rejestracją)
- Po aktywacji konta automatyczne przekierowanie do dashboardu

Logowanie:
- Formularz z polami: email, hasło
- Opcja "Zapamiętaj mnie"
- Link "Zapomniałem hasła" (reset przez email)
- Komunikaty błędów: nieprawidłowy email/hasło, konto nieaktywne

Wylogowanie:
- Przycisk "Wyloguj" w menu profilu/ustawień
- Wyczyszczenie sesji i przekierowanie na stronę logowania

Security: Row Level Security (RLS)
- Policy dla tabeli cards: user_id = auth.uid()
- Użytkownik może odczytywać, tworzyć, edytować i usuwać tylko własne fiszki
- Policy dla tabeli review_history (jeśli istnieje): analogicznie przez card_id
- Brak dostępu do fiszek innych użytkowników na poziomie bazy danych

Compliance:
- Zgoda RODO na przetwarzanie treści przez AI w regulaminie podczas rejestracji
- Informacja o wykorzystaniu Openrouter.ai (pośrednik do modeli AI) i potencjalnym przesyłaniu danych poza UE
- Brak trybu offline w MVP (dane zawsze przechowywane w chmurze)

### 3.6. Nawigacja i struktura aplikacji

Główne strony:
1. Dashboard / Lista fiszek: przegląd wszystkich fiszek, licznik do powtórzenia, szybki dostęp do nauki
2. Dodaj fiszki: zakładki "Manual" i "AI Generation" w jednym widoku
3. Sesja nauki: interfejs do przeglądania fiszek i oceny trudności
4. Profil / Ustawienia: zmiana hasła, statystyki, opcja usunięcia konta

Topbar / Navbar:
- Logo / Nazwa aplikacji (link do dashboardu)
- Linki do głównych sekcji: Dashboard, Dodaj, Ucz się
- Ikona profilu / Menu użytkownika (dropdown z opcją Ustawienia, Wyloguj)

Responsywność:
- Pełna funkcjonalność na desktop
- Responsywny design dla mobile (burger menu, zmiana layoutu)
- MVP skupiony na doświadczeniu web, bez dedykowanej aplikacji mobilnej

### 3.7. Limity i ograniczenia

Limity dla użytkownika:
- Maksymalnie 500 fiszek na użytkownika (ograniczenie dla projektu szkoleniowego)
- Maksymalnie 2000 znaków na jedno generowanie AI
- Generowanie 5-8 fiszek per request

Limity kosztowe:
- Cap $10/miesiąc dla całego projektu (projekt szkoleniowy) ustawiony w Openrouter.ai
- Przewidywany koszt: ~$0.50-1.00 na 1000 wygenerowanych fiszek (zależnie od modelu)
- Monitoring kosztów przez dashboard Openrouter.ai

Limity infrastruktury:
- Supabase: 500MB storage, 50K users, 2GB bandwidth
- DigitalOcean: Droplet ~$5-10/miesiąc (1-2GB RAM, 1 vCPU)
- Openrouter.ai: $10/miesiąc cap

Rate limiting:
- Konkretne wartości do ustalenia w trakcie implementacji
- Podstawowa ochrona przed nadużyciami (np. max 10 requests/minute dla API generowania)

## 4. Granice produktu

Poniższe funkcjonalności NIE wchodzą w zakres MVP i mogą być rozważone w przyszłych iteracjach produktu:

Zaawansowane algorytmy i personalizacja:
- Algorytmy powtórek bardziej zaawansowane niż SM-2
- Konfigurowalny system promptów dla użytkowników
- Personalizacja na podstawie historii nauki użytkownika
- Machine learning do predykcji optymalnych interwałów

Import i integracje:
- Import fiszek z wielu formatów (PDF, DOCX, JSON, CSV)
- Export do innych platform (Anki, Quizlet)
- Integracje z platformami edukacyjnymi (Moodle, Canvas)
- API dla deweloperów zewnętrznych
- Web scraping / parsowanie stron internetowych

Współdzielenie i społeczność:
- Publiczne zestawy fiszek
- Współdzielenie zestawów między użytkownikami
- Komentarze i oceny zestawów
- Ranking najlepszych zestawów
- Profile użytkowników
- System followersów

Zaawansowane typy treści:
- Fiszki z obrazkami, audio, wideo
- Fiszki typu luki (fill-in-the-blank)
- Fiszki multiple choice
- Diagramy i infografiki
- Obsługa formuł matematycznych (LaTeX)
- Obsługa code snippets z syntax highlighting

Organizacja i zarządzanie:
- Wiele talii / zestawów na użytkownika
- Tagi i kategoryzacja fiszek
- Foldery i hierarchie talii
- Bulk operations (masowe edytowanie, usuwanie)
- Duplikat detection
- Archiwizacja starych fiszek

Aplikacje mobilne i offline:
- Dedykowane aplikacje na iOS i Android
- Tryb offline z synchronizacją
- Progressive Web App (PWA)
- Powiadomienia push o zaplanowanych sesjach

Analytics i gamification:
- Szczegółowe statystyki nauki (retention curves, accuracy over time)
- Heatmapy aktywności
- Streaks i dzienne cele
- Achievements i badges
- Leaderboards
- Dzienne/tygodniowe raporty postępu

Onboarding i pomoc:
- Interactive tutorial dla nowych użytkowników
- Przykładowe zestawy fiszek
- Tooltips i contextual help
- Video tutorials
- FAQ i dokumentacja
- Live chat support

DevOps i środowiska (poza MVP, choć Docker ułatwia dodanie w przyszłości):
- Staging environment (możliwe dzięki Docker)
- Advanced CI/CD features (obecnie podstawowy pipeline w GitHub Actions)
- Automated testing (unit, integration, e2e)
- A/B testing infrastructure
- Feature flags
- Advanced monitoring i alerting (Sentry, LogRocket)

Inne:
- Zaawansowane wyszukiwanie (full-text search, filtry)
- Backup strategy i disaster recovery
- Multi-language interface
- Accessibility features (WCAG compliance)
- Dark mode
- Keyboard shortcuts
- Bulk import tysięcy fiszek
- Collaboration features (shared decks editing)

## 5. Historyjki użytkowników

### US-001: Rejestracja nowego użytkownika

Jako nowy użytkownik
Chcę utworzyć konto w aplikacji
Aby móc przechowywać i zarządzać własnymi fiszkami

Kryteria akceptacji:
- Formularz rejestracji zawiera pola: email, hasło, potwierdzenie hasła
- Hasło musi mieć minimum 8 znaków
- System waliduje zgodność hasła z potwierdzeniem
- System waliduje poprawność formatu email
- Checkbox zgody RODO jest wymagany przed rejestracją (informacja o Openrouter.ai)
- Po wysłaniu formularza użytkownik otrzymuje email z linkiem aktywacyjnym
- Komunikat sukcesu informuje o konieczności aktywacji konta przez email
- Błędne dane wyświetlają konkretny komunikat błędu (np. "Email jest już zarejestrowany", "Hasła nie są zgodne")
- Po kliknięciu linku aktywacyjnego konto zostaje aktywowane
- Użytkownik zostaje automatycznie zalogowany i przekierowany do dashboardu

### US-002: Logowanie do aplikacji

Jako zarejestrowany użytkownik
Chcę zalogować się do swojego konta
Aby uzyskać dostęp do moich fiszek

Kryteria akceptacji:
- Formularz logowania zawiera pola: email, hasło
- Checkbox "Zapamiętaj mnie" pozwala na dłuższą sesję
- Przycisk "Zaloguj" wysyła dane do weryfikacji
- Poprawne dane logują użytkownika i przekierowują do dashboardu
- Niepoprawne dane wyświetlają komunikat "Nieprawidłowy email lub hasło"
- Link "Zapomniałem hasła" przekierowuje do strony resetowania hasła
- Nieaktywne konto wyświetla komunikat "Konto wymaga aktywacji - sprawdź email"
- Po zalogowaniu sesja jest zapisywana i użytkownik pozostaje zalogowany między odwiedzinami

### US-003: Reset hasła

Jako użytkownik, który zapomniał hasła
Chcę móc zresetować moje hasło
Aby odzyskać dostęp do mojego konta

Kryteria akceptacji:
- Strona resetowania hasła zawiera pole email
- Po wysłaniu emaila system wysyła link resetujący (jeśli email istnieje w bazie)
- System wyświetla komunikat sukcesu niezależnie od tego czy email istnieje (security best practice)
- Link resetujący jest ważny przez 24 godziny
- Kliknięcie linku przekierowuje do formularza z polami: nowe hasło, potwierdzenie hasła
- Nowe hasło musi spełniać te same wymagania co przy rejestracji (minimum 8 znaków)
- Po udanym resecie użytkownik zostaje przekierowany do strony logowania z komunikatem sukcesu
- Stary link resetujący staje się nieważny po użyciu

### US-004: Wylogowanie z aplikacji

Jako zalogowany użytkownik
Chcę móc się wylogować
Aby zakończyć sesję i zabezpieczyć moje konto

Kryteria akceptacji:
- Przycisk "Wyloguj" jest dostępny w menu profilu/ustawień
- Kliknięcie "Wyloguj" czyści sesję użytkownika
- Po wylogowaniu użytkownik zostaje przekierowany do strony logowania
- Próba dostępu do chronionych stron po wylogowaniu przekierowuje do logowania
- Komunikat "Zostałeś wylogowany" jest wyświetlany po zakończeniu sesji

### US-005: Manualne dodanie fiszki

Jako użytkownik
Chcę ręcznie stworzyć fiszkę
Aby dodać do mojej talii konkretne pytanie i odpowiedź

Kryteria akceptacji:
- Strona "Dodaj fiszki" zawiera zakładkę "Manual"
- Formularz zawiera dwa pola textarea: "Pytanie" i "Odpowiedź"
- Oba pola są wymagane - brak wypełnienia powoduje wyświetlenie błędu walidacji
- Przycisk "Zapisz" dodaje fiszkę do bazy danych
- Przycisk "Anuluj" czyści formularz bez zapisywania
- Po zapisaniu wyświetlany jest komunikat sukcesu "Fiszka została dodana"
- Nowa fiszka ma is_ai_generated = false
- Nowa fiszka ma next_review ustawione na bieżącą datę (dostępna od razu do nauki)
- Nowa fiszka ma domyślne wartości SM-2: interval = 0, ease_factor = 2.5, repetitions = 0
- Po zapisaniu formularz jest czyszczony i gotowy do dodania kolejnej fiszki

### US-006: Generowanie fiszek przez AI - wprowadzenie tekstu

Jako użytkownik
Chcę wkleić tekst do formularza
Aby wygenerować z niego fiszki przy użyciu AI

Kryteria akceptacji:
- Strona "Dodaj fiszki" zawiera zakładkę "AI Generation"
- Formularz zawiera duże pole textarea na tekst wejściowy
- Licznik znaków jest widoczny i aktualizuje się w czasie rzeczywistym
- Tekst krótszy niż 10 znaków wyświetla komunikat "Wprowadź minimum 10 znaków"
- Tekst dłuższy niż 2000 znaków wyświetla komunikat "Maksymalnie 2000 znaków" i blokuje dalsze wpisywanie
- Przycisk "Generuj" jest nieaktywny jeśli tekst nie mieści się w przedziale 10-2000 znaków
- Przycisk "Wyczyść" czyści pole tekstowe
- Podczas generowania wyświetlany jest loader/spinner i komunikat "Generowanie fiszek..."
- Przycisk "Generuj" jest zablokowany podczas trwania generowania

### US-007: Generowanie fiszek przez AI - otrzymanie wyników

Jako użytkownik, który wysłał tekst do generowania
Chcę otrzymać wygenerowane fiszki i móc je przejrzeć
Aby zdecydować które fiszki chcę dodać do mojej talii

Kryteria akceptacji:
- Po pomyślnym generowaniu wyświetlana jest staging area z 5-8 fiszkami
- Każda fiszka wyświetla pytanie (front) i odpowiedź (back)
- Każda fiszka ma trzy akcje: "Zaakceptuj", "Edytuj", "Odrzuć"
- Fiszki są wizualnie rozróżnione (np. zielona ramka = zaakceptowana, czerwona = odrzucona, neutralna = do przeglądu)
- Licznik "X z Y zaakceptowanych" jest widoczny u góry
- Przycisk "Zaakceptuj wszystkie" dodaje wszystkie fiszki do talii jednym kliknięciem
- Przycisk "Zapisz zaakceptowane" dodaje tylko zaakceptowane fiszki do bazy danych
- Wszystkie fiszki mają is_ai_generated = true
- Po zapisaniu wyświetlany jest komunikat "Dodano X fiszek do talii"
- Użytkownik zostaje przekierowany do dashboardu lub dostaje opcję wygenerowania kolejnych fiszek

### US-008: Edycja wygenerowanej fiszki w staging area

Jako użytkownik przeglądający wygenerowane fiszki
Chcę móc edytować treść fiszki przed dodaniem do talii
Aby poprawić lub dostosować pytanie lub odpowiedź

Kryteria akceptacji:
- Kliknięcie "Edytuj" otwiera modal z formularzem edycji
- Formularz zawiera dwa pola: "Pytanie" i "Odpowiedź" pre-wypełnione bieżącą treścią
- Przycisk "Zapisz" zamyka modal i aktualizuje treść fiszki w staging area
- Przycisk "Anuluj" zamyka modal bez zapisywania zmian
- Edytowana fiszka jest automatycznie oznaczana jako zaakceptowana
- Zmiany są widoczne natychmiast w staging area
- Modal można zamknąć przez kliknięcie poza nim lub przycisk X

### US-009: Obsługa błędów generowania AI

Jako użytkownik próbujący wygenerować fiszki
Chcę otrzymać jasny komunikat w przypadku błędu
Aby wiedzieć co poszło nie tak i móc spróbować ponownie

Kryteria akceptacji:
- Błąd API wyświetla toast "Coś poszło nie tak, spróbuj ponownie" i przycisk "Retry"
- Kliknięcie "Retry" ponawia request z tym samym tekstem
- Invalid JSON response wyświetla komunikat "Nie udało się wygenerować fiszek"
- Rate limit (429) wyświetla komunikat "Przekroczono limit, spróbuj za chwilę"
- Limit finansowy Openrouter.ai wyświetla komunikat "Osiągnięto miesięczny limit kosztów"
- Brak połączenia z internetem wyświetla komunikat "Brak połączenia - sprawdź internet"
- Każdy komunikat błędu pozostaje widoczny przez 5 sekund lub do kliknięcia X
- Po błędzie formularz z tekstem pozostaje wypełniony (użytkownik nie traci wprowadzonych danych)
- Błędy są logowane do konsoli dla debugowania

### US-010: Przeglądanie listy wszystkich fiszek

Jako użytkownik
Chcę zobaczyć listę wszystkich moich fiszek
Aby mieć przegląd zgromadzonych materiałów

Kryteria akceptacji:
- Dashboard wyświetla wszystkie fiszki użytkownika
- Dostępne są dwa widoki: lista (vertical) i karty (grid)
- Każda fiszka wyświetla: pytanie (front), tag AI/manual, status, następną datę przeglądu
- Przełącznik widoku (ikony list/grid) pozwala zmienić sposób wyświetlania
- Domyślnie fiszki są sortowane po dacie utworzenia (najnowsze na górze)
- Pusta lista wyświetla komunikat "Nie masz jeszcze żadnych fiszek" z linkiem do dodawania
- Lista jest paginowana lub używa infinite scroll jeśli fiszek jest więcej niż 50

### US-011: Filtrowanie fiszek

Jako użytkownik z wieloma fiszkami
Chcę móc filtrować fiszki według źródła i statusu
Aby łatwiej znaleźć interesujące mnie fiszki

Kryteria akceptacji:
- Dostępne są filtry: "Wszystkie" / "AI-generated" / "Manualne" / "Odrzucone"
- Kliknięcie filtru natychmiast aktualizuje listę fiszek
- Aktywny filtr jest wizualnie wyróżniony
- Licznik przy każdym filtrze pokazuje liczbę fiszek w kategorii (np. "AI-generated (42)")
- Filtrowanie działa razem z wyszukiwaniem (AND logic)
- URL aktualizuje się po wybraniu filtru (możliwość sharowania/bookmarkowania)

### US-012: Sortowanie fiszek

Jako użytkownik
Chcę móc sortować fiszki według różnych kryteriów
Aby łatwiej zarządzać moją talią

Kryteria akceptacji:
- Dropdown sortowania zawiera opcje: "Data utworzenia", "Następna data przeglądu", "Alfabetycznie"
- Możliwość wyboru kierunku: rosnąco / malejąco (toggle arrow icon)
- Wybór opcji sortowania natychmiast aktualizuje listę
- Sortowanie działa razem z filtrowaniem i wyszukiwaniem
- Wybrane sortowanie jest zapisywane w localStorage (pamiętane między sesjami)

### US-013: Wyszukiwanie fiszek

Jako użytkownik
Chcę móc wyszukać fiszki po treści
Aby szybko znaleźć konkretną fiszkę

Kryteria akceptacji:
- Pole wyszukiwania jest widoczne nad listą fiszek
- Wyszukiwanie działa na treści pytania (front) i odpowiedzi (back)
- Wyniki aktualizują się w czasie rzeczywistym (debounce 300ms)
- Wyszukiwanie jest case-insensitive
- Brak wyników wyświetla komunikat "Nie znaleziono fiszek pasujących do '[query]'"
- Przycisk X w polu wyszukiwania czyści query i przywraca pełną listę
- Wyszukiwanie działa razem z filtrowaniem i sortowaniem

### US-014: Edycja istniejącej fiszki

Jako użytkownik
Chcę móc edytować treść mojej fiszki
Aby poprawić błędy lub zaktualizować informacje

Kryteria akceptacji:
- Każda fiszka ma przycisk/ikonę "Edytuj"
- Kliknięcie "Edytuj" otwiera modal z formularzem
- Formularz zawiera pola "Pytanie" i "Odpowiedź" pre-wypełnione bieżącą treścią
- Oba pola są wymagane
- Przycisk "Zapisz" zapisuje zmiany, zamyka modal i aktualizuje widok listy
- Przycisk "Anuluj" zamyka modal bez zapisywania
- Edycja nie wpływa na metadane SM-2 (next_review, interval, ease_factor, repetitions)
- Edycja nie zmienia flagi is_ai_generated
- Toast "Fiszka została zaktualizowana" pojawia się po zapisaniu

### US-015: Usuwanie fiszki

Jako użytkownik
Chcę móc usunąć fiszkę
Aby pozbyć się nieaktualnych lub niepotrzebnych materiałów

Kryteria akceptacji:
- Każda fiszka ma przycisk/ikonę "Usuń"
- Kliknięcie "Usuń" otwiera dialog potwierdzenia "Czy na pewno chcesz usunąć tę fiszkę?"
- Dialog zawiera przyciski "Usuń" (czerwony) i "Anuluj" (neutralny)
- Kliknięcie "Usuń" w dialogu permanentnie usuwa fiszkę z bazy danych
- Kliknięcie "Anuluj" zamyka dialog bez usuwania
- Fiszka znika z listy natychmiast po usunięciu
- Toast "Fiszka została usunięta" pojawia się po usunięciu
- Usunięcie jest nieodwracalne (brak undo w MVP)

### US-016: Oznaczanie fiszki jako odrzuconej

Jako użytkownik
Chcę móc oznaczyć fiszkę jako odrzuconą bez jej usuwania
Aby wykluczyć ją z nauki ale zachować w bazie danych

Kryteria akceptacji:
- Każda fiszka ma przycisk/ikonę "Odrzuć" lub toggle "Aktywna/Odrzucona"
- Kliknięcie "Odrzuć" ustawia is_rejected = true
- Odrzucone fiszki są wizualnie wyróżnione (np. szare tło, półprzezroczyste)
- Odrzucone fiszki nie pojawiają się w sesjach nauki
- Odrzucone fiszki są widoczne tylko po wybraniu filtru "Odrzucone"
- Możliwość przywrócenia fiszki przez kliknięcie "Przywróć" (is_rejected = false)
- Toast "Fiszka została odrzucona/przywrócona" pojawia się po zmianie statusu

### US-017: Rozpoczęcie sesji nauki

Jako użytkownik
Chcę rozpocząć sesję nauki
Aby powtórzyć fiszki zaplanowane na dziś

Kryteria akceptacji:
- Dashboard wyświetla licznik "X fiszek do powtórzenia"
- Przycisk "Ucz się" jest widoczny i aktywny jeśli licznik > 0
- Jeśli licznik = 0, przycisk jest nieaktywny z komunikatem "Brak fiszek do powtórzenia"
- Kliknięcie "Ucz się" przekierowuje do widoku sesji nauki
- System wybiera fiszki gdzie next_review <= bieżąca data
- Fiszki z is_rejected = true są wykluczane
- Kolejność fiszek w sesji jest randomizowana
- Licznik "1 / X" jest widoczny u góry widoku sesji
- Przycisk "Zakończ sesję" jest dostępny w każdym momencie

### US-018: Przeglądanie fiszki podczas sesji nauki

Jako użytkownik w sesji nauki
Chcę zobaczyć pytanie, odkryć odpowiedź i ocenić trudność
Aby efektywnie się uczyć według algorytmu spaced repetition

Kryteria akceptacji:
- Fiszka wyświetla się w widoku pytania: widoczne jest tylko pytanie (front)
- Przycisk "Pokaż odpowiedź" jest widoczny na środku lub na dole
- Kliknięcie "Pokaż odpowiedź" odkrywa odpowiedź (back) poniżej pytania
- Alternatywnie: kliknięcie na kartę odkrywa odpowiedź (flip animation)
- Po odkryciu odpowiedzi wyświetlają się 4 przyciski: "Again", "Hard", "Good", "Easy"
- Przyciski są wizualnie wyróżnione kolorami (czerwony, pomarańczowy, zielony, niebieski)
- Każdy przycisk pokazuje następny interwał (np. "Good (3 dni)")
- Licznik postępu "X / Y" aktualizuje się po każdej fiszce

### US-019: Ocena trudności fiszki (Again)

Jako użytkownik w sesji nauki
Chcę ocenić fiszkę jako "Again"
Aby powtórzyć ją jeszcze raz w bieżącej sesji

Kryteria akceptacji:
- Przycisk "Again" jest dostępny po odkryciu odpowiedzi
- Kliknięcie "Again" ustawia: repetitions = 0, interval = 0, next_review = bieżąca data
- Fiszka zostaje dodana z powrotem do kolejki bieżącej sesji (pojawi się ponownie)
- Jeśli review_history istnieje, zapis z quality = 0
- Przejście do kolejnej fiszki (lub ponowne wyświetlenie tej samej jeśli to ostatnia)
- Brak komunikatu sukcesu (płynne przejście do następnej fiszki)

### US-020: Ocena trudności fiszki (Hard)

Jako użytkownik w sesji nauki
Chcę ocenić fiszkę jako "Hard"
Aby zaznaczyć trudność i zobaczyć ją ponownie w krótszym interwale

Kryteria akceptacji:
- Przycisk "Hard" jest dostępny po odkryciu odpowiedzi
- Kliknięcie "Hard" stosuje algorytm SM-2 z quality = 3
- ease_factor jest obniżany (minimum 1.3)
- interval jest krótszy niż dla "Good"
- next_review jest ustawione na (bieżąca data + interval)
- repetitions jest zwiększane o 1
- Jeśli review_history istnieje, zapis z quality = 3
- Przejście do kolejnej fiszki
- Fiszka nie pojawi się ponownie w bieżącej sesji

### US-021: Ocena trudności fiszki (Good)

Jako użytkownik w sesji nauki
Chcę ocenić fiszkę jako "Good"
Aby zastosować standardowy interwał według algorytmu SM-2

Kryteria akceptacji:
- Przycisk "Good" jest dostępny po odkryciu odpowiedzi
- Kliknięcie "Good" stosuje algorytm SM-2 z quality = 4
- ease_factor pozostaje bez zmian
- interval jest obliczany standardowo: interval *= ease_factor
- next_review jest ustawione na (bieżąca data + interval)
- repetitions jest zwiększane o 1
- Jeśli review_history istnieje, zapis z quality = 4
- Przejście do kolejnej fiszki
- Jest to zalecana opcja dla większości poprawnych odpowiedzi

### US-022: Ocena trudności fiszki (Easy)

Jako użytkownik w sesji nauki
Chcę ocenić fiszkę jako "Easy"
Aby zaznaczyć łatwość i zobaczyć ją ponownie w dłuższym interwale

Kryteria akceptacji:
- Przycisk "Easy" jest dostępny po odkryciu odpowiedzi
- Kliknięcie "Easy" stosuje algorytm SM-2 z quality = 5
- ease_factor jest zwiększany (maksimum ~2.5-3.0)
- interval jest dłuższy niż dla "Good"
- next_review jest ustawione na (bieżąca data + interval)
- repetitions jest zwiększane o 1
- Jeśli review_history istnieje, zapis z quality = 5
- Przejście do kolejnej fiszki
- Jest to opcja dla fiszek które użytkownik pamięta bardzo dobrze

### US-023: Zakończenie sesji nauki

Jako użytkownik w trakcie sesji nauki
Chcę móc zakończyć sesję w dowolnym momencie
Aby przerwać naukę i wrócić do niej później

Kryteria akceptacji:
- Przycisk "Zakończ sesję" jest widoczny i dostępny w każdym momencie sesji
- Kliknięcie "Zakończ sesję" przerywa sesję i wyświetla summary screen
- Wszystkie oceny dokonane do momentu zakończenia są zapisane w bazie danych
- Nieocenione fiszki pozostają z oryginalnym next_review (nadal zaplanowane na dziś)
- Możliwość wznowienia sesji później (przez kliknięcie "Ucz się" ponownie)

### US-024: Wyświetlenie podsumowania po sesji nauki

Jako użytkownik, który zakończył sesję nauki
Chcę zobaczyć podsumowanie mojej sesji
Aby wiedzieć co osiągnąłem i kiedy następna sesja

Kryteria akceptacji:
- Summary screen wyświetla: "Przerobione: X fiszek"
- Wyświetlona jest "Następna sesja: [data najbliższego przeglądu]"
- Podział na kategorie: Again (X), Hard (X), Good (X), Easy (X)
- Przycisk "Powrót do dashboardu" przekierowuje do dashboardu
- Przycisk "Kontynuuj naukę" jest widoczny jeśli są jeszcze fiszki na dziś
- Jeśli nie ma więcej fiszek na dziś, wyświetlany jest komunikat "Świetna robota! Wrócisz [data]"
- Summary pozostaje dostępny do momentu kliknięcia jednego z przycisków

### US-025: Przeglądanie profilu i statystyk podstawowych

Jako użytkownik
Chcę zobaczyć podstawowe informacje o moim koncie
Aby mieć przegląd mojej aktywności

Kryteria akceptacji:
- Strona profilu wyświetla email użytkownika
- Wyświetlana jest data utworzenia konta
- Wyświetlana jest całkowita liczba fiszek
- Wyświetlany jest podział: X fiszek AI / Y fiszek manualnych
- Wyświetlana jest liczba fiszek odrzuconych
- Link "Zmień hasło" przekierowuje do formularza zmiany hasła
- Przycisk "Wyloguj" jest widoczny

### US-026: Zmiana hasła

Jako zalogowany użytkownik
Chcę móc zmienić moje hasło
Aby zaktualizować zabezpieczenia mojego konta

Kryteria akceptacji:
- Formularz zmiany hasła zawiera pola: "Obecne hasło", "Nowe hasło", "Potwierdź nowe hasło"
- Wszystkie pola są wymagane
- Nowe hasło musi mieć minimum 8 znaków
- "Nowe hasło" i "Potwierdź nowe hasło" muszą się zgadzać
- Przycisk "Zmień hasło" wysyła request do Supabase
- Niepoprawne obecne hasło wyświetla błąd "Obecne hasło jest nieprawidłowe"
- Po udanej zmianie wyświetlany jest komunikat sukcesu i przekierowanie do profilu
- Użytkownik pozostaje zalogowany po zmianie hasła


### US-028: Row Level Security - dostęp tylko do własnych fiszek

Jako użytkownik
Chcę mieć pewność, że inni użytkownicy nie mają dostępu do moich fiszek
Aby moje dane były bezpieczne i prywatne

Kryteria akceptacji:
- Policy RLS w tabeli cards: SELECT, INSERT, UPDATE, DELETE tylko gdy user_id = auth.uid()
- Próba odczytu fiszek innego użytkownika przez manipulację requestu zwraca pusty wynik
- Próba modyfikacji fiszki innego użytkownika przez manipulację requestu zwraca błąd 403
- Zapytania SQL w aplikacji zawsze filtrują po user_id
- Testy bezpieczeństwa potwierdzają niemożliwość dostępu do danych innych użytkowników
- Logi Supabase nie pokazują żadnych nieautoryzowanych dostępów

### US-029: Wyświetlanie licznika fiszek do powtórzenia

Jako użytkownik
Chcę widzieć na dashboardzie ile fiszek czeka na powtórzenie
Aby wiedzieć czy muszę dziś się uczyć

Kryteria akceptacji:
- Dashboard wyświetla widoczny licznik "X fiszek do powtórzenia"
- Licznik pokazuje liczbę fiszek gdzie next_review <= bieżąca data
- Fiszki z is_rejected = true nie są wliczane
- Licznik aktualizuje się po zakończeniu sesji nauki
- Jeśli licznik = 0, wyświetlany jest komunikat "Brak fiszek do powtórzenia dziś"
- Kliknięcie licznika przekierowuje do rozpoczęcia sesji nauki

### US-030: Limit znaków w generowaniu AI - walidacja frontend

Jako użytkownik wprowadzający tekst do generowania
Chcę otrzymać natychmiastową informację o limitach
Aby wiedzieć czy mogę kontynuować

Kryteria akceptacji:
- Licznik znaków wyświetla "X / 2000 znaków"
- Gdy tekst < 10: licznik czerwony, komunikat "Minimum 10 znaków"
- Gdy tekst 10-2000: licznik zielony, przycisk "Generuj" aktywny
- Gdy tekst > 2000: blokada dalszego wpisywania, komunikat "Osiągnięto limit 2000 znaków"
- Wklejenie tekstu > 2000 znaków automatycznie obcina do 2000 i wyświetla komunikat
- Walidacja działa w czasie rzeczywistym (aktualizacja przy każdym keystroke)

### US-032: Responsywny design - mobile view

Jako użytkownik korzystający z urządzenia mobilnego
Chcę móc używać aplikacji na telefonie
Aby uczyć się w dowolnym miejscu

Kryteria akceptacji:
- Na mobile widok menu to burger menu (hamburger icon)
- Kliknięcie burgera otwiera sidebar lub dropdown z linkami nawigacyjnymi
- Formularze są responsywne i łatwe do wypełnienia na małym ekranie
- Fiszki w sesji nauki wyświetlają się na pełnym ekranie z dużym tekstem
- Przyciski są wystarczająco duże do kliknięcia palcem (min 44x44px)
- Grid view fiszek zmienia się na single column na mobile
- Wszystkie funkcjonalności dostępne na desktop działają na mobile

### US-035: Loader podczas generowania AI

Jako użytkownik oczekujący na wygenerowanie fiszek
Chcę widzieć jasny feedback że operacja trwa
Aby wiedzieć że muszę poczekać

Kryteria akceptacji:
- Po kliknięciu "Generuj" wyświetlany jest spinner/loader
- Komunikat "Generowanie fiszek... Może to potrwać do 30 sekund" jest widoczny
- Przycisk "Generuj" jest zablokowany podczas trwania operacji
- Pole tekstowe pozostaje wypełnione ale nieaktywne
- Po otrzymaniu wyników loader znika i wyświetla się staging area
- Timeout po 60 sekundach z komunikatem błędu i opcją retry

### US-036: Dostęp do chronionej strony bez logowania

Jako niezalogowany użytkownik próbujący otworzyć chronioną stronę
Chcę zostać przekierowany do logowania
Aby móc się zalogować i uzyskać dostęp

Kryteria akceptacji:
- Próba dostępu do dashboardu, dodawania fiszek, sesji nauki lub profilu bez logowania przekierowuje do strony logowania
- URL docelowy jest zapisywany i użytkownik zostaje przekierowany tam po zalogowaniu
- Komunikat "Musisz być zalogowany aby uzyskać dostęp" jest wyświetlany
- Dostęp do stron publicznych (landing page, rejestracja, logowanie) jest możliwy bez logowania

## 6. Metryki sukcesu

### 6.1. Metryki kluczowe (KPI)

AI Acceptance Rate (priorytet 1):
- Definicja: Procent wygenerowanych fiszek które nie są oflagowane jako is_rejected = true
- Cel MVP: 75% lub więcej
- Obliczanie: (liczba_fiszek_AI - liczba_is_rejected) / liczba_fiszek_AI × 100%
- Pomiar: Query do bazy danych, raportowanie co tydzień
- Akcja jeśli < 75%: Iteracja na system promptów, dodanie przykładów few-shot, analiza odrzuconych fiszek

AI Usage Rate (priorytet 1):
- Definicja: Procent fiszek tworzonych z wykorzystaniem AI
- Cel MVP: 75% lub więcej
- Obliczanie: liczba_fiszek_gdzie_is_ai_generated = true / liczba_wszystkich_fiszek × 100%
- Pomiar: Query do bazy danych, raportowanie co tydzień
- Akcja jeśli < 75%: Poprawa UX generowania AI, analiza czemu użytkownicy preferują manual

### 6.2. Metryki dodatkowe (monitoring)

Engagement:
- Liczba aktywnych użytkowników tygodniowo (WAU - Weekly Active Users)
- Średnia liczba sesji nauki na użytkownika w tygodniu
- Średnia długość sesji nauki (liczba fiszek per sesja)
- Retention rate: % użytkowników którzy wracają po 1 tygodniu / 1 miesiącu

Jakość produktu:
- Średnia liczba fiszek na użytkownika
- Stosunek fiszek aktywnych do odrzuconych
- Liczba błędów API (failed generations)
- Średni czas odpowiedzi API generowania

Koszty i limity:
- Całkowity koszt OpenAI API per miesiąc
- Średni koszt per użytkownik per miesiąc
- Liczba użytkowników którzy osiągnęli limit 500 fiszek
- Wykorzystanie free tier Vercel i Supabase (% dostępnych zasobów)

Techniczne:
- Uptime aplikacji (cel: > 99%)
- Średni czas odpowiedzi stron (cel: < 2s)
- Liczba zgłoszonych błędów (bug reports)
- Liczba naruszeń bezpieczeństwa (cel: 0)
- Czas deploymentu przez GitHub Actions (monitoring)

### 6.3. Sposób zbierania metryk

MVP (minimalna implementacja):
- Podstawowe query do bazy danych dla AI Acceptance Rate i AI Usage Rate
- Manualne sprawdzanie raz w tygodniu
- Dashboard Openrouter.ai dla kosztów API i wyboru modeli
- Dashboard DigitalOcean dla zasobów serwera
- Dashboard Supabase dla wykorzystania bazy danych

### 6.4. Kryteria uznania MVP za sukces

Minimalny próg akceptacji (must-have):
- AI Acceptance Rate >= 70%
- AI Usage Rate >= 70%
- Działająca aplikacja bez critical bugs
- Supabase RLS poprawnie zabezpiecza dane użytkowników
- Koszt miesięczny AI <= $10, infrastruktura ~$5-10
- Deployment przez GitHub Actions działa poprawnie

Kryteria pełnego sukcesu (target):
- AI Acceptance Rate >= 75%
- AI Usage Rate >= 75%
- Minimum 5 aktywnych użytkowników testujących przez co najmniej 2 tygodnie
- Average session: min 10 fiszek per sesja
- Retention: >= 50% użytkowników wraca po 1 tygodniu
- Pozytywny feedback od użytkowników (informal interviews/surveys)

