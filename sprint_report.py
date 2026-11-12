#!/usr/bin/env python3
"""
Skrypt do generowania podsumowania sprintu z Jira.
Pobiera informacje o Story Points na początku sprintu, dodanych w trakcie oraz ukończonych zadaniach.
"""

import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json
import sys
import re


def parse_jira_date(date_string: str) -> Optional[datetime]:
    """
    Parsuje datę z Jira - obsługuje formaty +0100 i Z.
    
    Args:
        date_string: String z datą z API Jira
        
    Returns:
        Obiekt datetime lub None
    """
    if not date_string:
        return None
    # Zamień Z na +00:00
    date_string = date_string.replace('Z', '+00:00')
    # Zamień +0100 na +01:00 (i inne strefy czasowe)
    date_string = re.sub(r'([+-])(\d{2})(\d{2})$', r'\1\2:\3', date_string)
    return datetime.fromisoformat(date_string)


class JiraSprintReporter:
    """Klasa do generowania raportów ze sprintów Jira."""
    
    def __init__(self, jira_url: str, email: str, api_token: str):
        """
        Inicjalizacja reportera.
        
        Args:
            jira_url: URL instancji Jira (np. https://gratka.atlassian.net)
            email: Email użytkownika Jira
            api_token: Token API Jira
        """
        self.jira_url = jira_url.rstrip('/')
        self.auth = (email, api_token)
        self.headers = {"Content-Type": "application/json"}
        # ID pola Story Points dla gratka.atlassian.net
        self.story_points_field = "customfield_10024"
    
    def _make_request(self, endpoint: str) -> Optional[Dict]:
        """
        Wykonuje request do API Jira.
        
        Args:
            endpoint: Endpoint API (bez base URL)
            
        Returns:
            Odpowiedź JSON lub None w przypadku błędu
        """
        url = f"{self.jira_url}{endpoint}"
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Błąd podczas requestu: {e}")
            return None
    
    def get_sprint_info(self, sprint_id: int) -> Optional[Dict]:
        """
        Pobiera informacje o sprincie.

        Args:
            sprint_id: ID sprintu

        Returns:
            Dane sprintu lub None
        """
        print(f"📊 Pobieram informacje o sprincie {sprint_id}...")
        return self._make_request(f"/rest/agile/1.0/sprint/{sprint_id}")

    def get_sprint_issues(self, sprint_id: int) -> List[Dict]:
        """
        Pobiera wszystkie zadania w sprincie wraz z historią zmian.

        Args:
            sprint_id: ID sprintu

        Returns:
            Lista zadań
        """
        print(f"📋 Pobieram zadania ze sprintu...")
        all_issues = []
        start_at = 0
        max_results = 100

        while True:
            endpoint = (
                f"/rest/agile/1.0/sprint/{sprint_id}/issue"
                f"?startAt={start_at}"
                f"&maxResults={max_results}"
                f"&fields=summary,status,{self.story_points_field},created"
                f"&expand=changelog"
            )

            data = self._make_request(endpoint)
            if not data:
                break

            issues = data.get('issues', [])
            all_issues.extend(issues)

            # Sprawdź czy są jeszcze wyniki
            total = data.get('total', 0)
            if start_at + max_results >= total:
                break

            start_at += max_results

        print(f"✅ Pobrano {len(all_issues)} zadań")
        return all_issues

    def _get_story_points(self, issue: Dict) -> float:
        """
        Pobiera Story Points z zadania.

        Args:
            issue: Dane zadania

        Returns:
            Liczba Story Points (0 jeśli brak)
        """
        fields = issue.get('fields', {})
        sp = fields.get(self.story_points_field)
        return float(sp) if sp is not None else 0.0

    def _is_completed(self, issue: Dict) -> bool:
        """
        Sprawdza czy zadanie jest ukończone.

        Preferuje kategorię statusu Jira (statusCategory.key == 'done'),
        bo nazwy statusów bywają lokalne (np. "Gotowe" zamiast "Done").
        Fallback: znane nazwy statusów ukończenia.
        
        Args:
            issue: Dane zadania
            
        Returns:
            True jeśli ukończone
        """
        status = issue.get('fields', {}).get('status') or {}
        category_key = (status.get('statusCategory') or {}).get('key', '')
        if category_key == 'done':
            return True

        # Fallback na wypadek braku statusCategory w odpowiedzi API
        status_name = status.get('name', '')
        completed_statuses = {
            'Done', 'Closed', 'Resolved', 'Ukończone', 'Zamknięte', 'Gotowe',
        }
        return status_name in completed_statuses

    def _get_sprint_add_date(self, issue: Dict, sprint_id: int) -> Optional[datetime]:
        """
        Znajduje datę dodania zadania do sprintu.

        Args:
            issue: Dane zadania
            sprint_id: ID sprintu

        Returns:
            Data dodania do sprintu lub None
        """
        changelog = issue.get('changelog', {})
        histories = changelog.get('histories', [])

        sprint_id_str = str(sprint_id)

        for history in histories:
            created = history.get('created')
            items = history.get('items', [])

            for item in items:
                if item.get('field') == 'Sprint':
                    # Sprawdź czy sprint został dodany (jest w 'to' ale nie było w 'from')
                    from_value = item.get('from', '') or ''
                    to_value = item.get('to', '') or ''

                    # Parsuj ID sprintów (są rozdzielone przecinkami)
                    from_sprints = [s.strip() for s in from_value.split(',') if s.strip()]
                    to_sprints = [s.strip() for s in to_value.split(',') if s.strip()]

                    # Jeśli sprint jest w 'to' ale nie był w 'from', to został dodany
                    if sprint_id_str in to_sprints and sprint_id_str not in from_sprints:
                        return parse_jira_date(created)

        return None

    def analyze_sprint(self, sprint_id: int) -> Dict:
        """
        Analizuje sprint i przygotowuje podsumowanie.

        Args:
            sprint_id: ID sprintu

        Returns:
            Słownik z danymi podsumowania
        """
        # Pobierz dane sprintu
        sprint_info = self.get_sprint_info(sprint_id)
        if not sprint_info:
            return {}

        sprint_name = sprint_info.get('name', 'N/A')
        sprint_state = sprint_info.get('state', 'N/A')
        start_date_str = sprint_info.get('startDate')
        end_date_str = sprint_info.get('endDate')

        sprint_start = None
        if start_date_str:
            sprint_start = parse_jira_date(start_date_str)

        # Pobierz zadania
        issues = self.get_sprint_issues(sprint_id)

        # Analizuj zadania
        initial_sp = 0.0
        added_sp = 0.0
        completed_count = 0
        total_sp = 0.0
        completed_sp = 0.0

        initial_issues = []
        added_issues = []
        completed_issues = []

        for issue in issues:
            sp = self._get_story_points(issue)
            total_sp += sp
            is_completed = self._is_completed(issue)

            issue_key = issue.get('key')
            issue_summary = issue.get('fields', {}).get('summary', 'N/A')
            issue_status = issue.get('fields', {}).get('status', {}).get('name', 'N/A')

            # Sprawdź kiedy zadanie zostało dodane do sprintu
            add_date = self._get_sprint_add_date(issue, sprint_id)

            was_added_during = False
            if add_date and sprint_start:
                was_added_during = add_date > sprint_start

            if was_added_during:
                added_sp += sp
                added_issues.append({
                    'key': issue_key,
                    'summary': issue_summary,
                    'sp': sp,
                    'added_date': add_date.strftime('%Y-%m-%d %H:%M') if add_date else 'N/A'
                })
            else:
                initial_sp += sp
                initial_issues.append({
                    'key': issue_key,
                    'summary': issue_summary,
                    'sp': sp
                })

            if is_completed:
                completed_count += 1
                completed_sp += sp
                completed_issues.append({
                    'key': issue_key,
                    'summary': issue_summary,
                    'status': issue_status,
                    'sp': sp
                })

        return {
            'sprint_name': sprint_name,
            'sprint_state': sprint_state,
            'sprint_start': sprint_start.strftime('%Y-%m-%d %H:%M') if sprint_start else 'N/A',
            'sprint_end': parse_jira_date(end_date_str).strftime('%Y-%m-%d %H:%M') if end_date_str else 'N/A',
            'initial_sp': initial_sp,
            'added_sp': added_sp,
            'total_sp': total_sp,
            'completed_sp': completed_sp,
            'completed_count': completed_count,
            'total_count': len(issues),
            'initial_issues': initial_issues,
            'added_issues': added_issues,
            'completed_issues': completed_issues
        }

    def print_report(self, analysis: Dict):
        """
        Wyświetla raport ze sprintu.

        Args:
            analysis: Dane analizy ze sprintu
        """
        if not analysis:
            print("❌ Brak danych do wyświetlenia")
            return

        print("\n" + "="*70)
        print(f"📊 RAPORT ZE SPRINTU: {analysis['sprint_name']}")
        print("="*70)
        print(f"Status: {analysis['sprint_state']}")
        print(f"Start: {analysis['sprint_start']}")
        print(f"Koniec: {analysis['sprint_end']}")
        print()

        print("📈 STORY POINTS:")
        print("-" * 70)
        print(f"  SP na początku sprintu:        {analysis['initial_sp']:.1f}")
        print(f"  SP dodane w trakcie sprintu:   {analysis['added_sp']:.1f}")
        print(f"  SP zamknięte:                  {analysis['completed_sp']:.1f} ({analysis['completed_sp']/analysis['total_sp']*100 if analysis['total_sp'] > 0 else 0:.1f}%)")
        print(f"  ────────────────────────────────────────")
        print(f"  RAZEM:                         {analysis['total_sp']:.1f}")
        print()

        print("✅ ZADANIA UKOŃCZONE:")
        print("-" * 70)
        print(f"  Ukończone: {analysis['completed_count']} z {analysis['total_count']} zadań")
        print()

        if analysis['completed_issues']:
            print("  Lista ukończonych zadań:")
            for issue in analysis['completed_issues']:
                print(f"    • {issue['key']}: {issue['summary']} [{issue['sp']:.1f} SP]")
        print()

        if analysis['added_issues']:
            print("➕ ZADANIA DODANE W TRAKCIE SPRINTU:")
            print("-" * 70)
            for issue in analysis['added_issues']:
                print(f"  • {issue['key']}: {issue['summary']} [{issue['sp']:.1f} SP]")
                print(f"    Dodano: {issue['added_date']}")

        print("\n" + "="*70)


def main():
    """Główna funkcja skryptu."""
    print("="*70)
    print("🚀 GENERATOR RAPORTU SPRINTU JIRA")
    print("="*70)
    print()

    # Konfiguracja - możesz zmienić te wartości
    JIRA_URL = "https://gratka.atlassian.net"
    EMAIL = "arkadiusz.janowski@gratka.pl"

    # Pobierz token z argumentu lub zmiennej środowiskowej
    import os
    API_TOKEN = os.environ.get('JIRA_API_TOKEN')

    if not API_TOKEN:
        print("⚠️  Ustaw zmienną środowiskową JIRA_API_TOKEN lub edytuj skrypt")
        print("   Eksportuj token: export JIRA_API_TOKEN='twój_token'")
        print()
        API_TOKEN = input("Lub wpisz token tutaj: ").strip()
        if not API_TOKEN:
            print("❌ Brak tokenu API!")
            sys.exit(1)

    # Zapytaj o ID sprintu
    sprint_id_input = input("\n📋 Podaj ID sprintu: ").strip()

    try:
        sprint_id = int(sprint_id_input)
    except ValueError:
        print("❌ ID sprintu musi być liczbą!")
        sys.exit(1)

    # Stwórz reporter i wygeneruj raport
    reporter = JiraSprintReporter(JIRA_URL, EMAIL, API_TOKEN)
    
    print()
    analysis = reporter.analyze_sprint(sprint_id)
    
    if analysis:
        reporter.print_report(analysis)
        
        # Opcjonalnie zapisz do pliku JSON
        save_json = input("\n💾 Czy zapisać raport do pliku JSON? (t/n): ").strip().lower()
        if save_json == 't':
            filename = f"sprint_{sprint_id}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            print(f"✅ Raport zapisany do: {filename}")
    else:
        print("❌ Nie udało się wygenerować raportu")
        sys.exit(1)


if __name__ == "__main__":
    main()

