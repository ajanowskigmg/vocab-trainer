#!/usr/bin/env python3
"""
Raport spalonych Story Points po reestymacji przy zamknięciu sprintu.

Uruchamiaj po zamknięciu poprzedniego sprintu — podajesz tylko ID nowego sprintu.
Skrypt szuka zadań dodanych do tego sprintu (przeniesionych z poprzedniego)
i wykrywa obniżenie SP w changelogu (np. 8 → 5). Spalone SP = stara − nowa wartość.
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import requests


def parse_jira_date(date_string: str) -> Optional[datetime]:
    """Parsuje datę z Jira — obsługuje formaty +0100 i Z."""
    if not date_string:
        return None
    date_string = date_string.replace("Z", "+00:00")
    date_string = re.sub(r"([+-])(\d{2})(\d{2})$", r"\1\2:\3", date_string)
    return datetime.fromisoformat(date_string)


def truncate_text(text: str, max_length: int) -> str:
    """Skraca tekst z wielokropkiem, jeśli jest za długi."""
    if len(text) <= max_length:
        return text
    if max_length <= 1:
        return text[:max_length]
    return text[: max_length - 1] + "…"


def get_assignee_name(issue: Dict) -> str:
    """Zwraca display name assignee lub placeholder."""
    assignee = issue.get("fields", {}).get("assignee")
    if not assignee:
        return "—"
    return assignee.get("displayName") or assignee.get("name") or "—"


def format_sp(value: float) -> str:
    """Formatuje Story Points jako liczbę całkowitą."""
    return str(int(value))
    """Formatuje Story Points jako liczbę całkowitą."""
    return str(int(value))


def parse_sp_value(raw_value: Optional[str]) -> Optional[float]:
    """Konwertuje wartość Story Points z changelogu na float."""
    if raw_value is None:
        return None
    text = str(raw_value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


class JiraReestimationReporter:
    """Raport reestymacji SP dla zadań przeniesionych do nowego sprintu."""

    def __init__(self, jira_url: str, email: str, api_token: str):
        self.jira_url = jira_url.rstrip("/")
        self.auth = (email, api_token)
        self.headers = {"Content-Type": "application/json"}
        self.story_points_field = "customfield_10024"
        self.story_points_field_names = {
            "Story Points",
            "Story point estimate",
            self.story_points_field,
        }
        self.reestimation_window_days = 14

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        url = f"{self.jira_url}{endpoint}"
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            print(f"❌ Błąd podczas requestu: {exc}")
            return None

    def get_sprint_info(self, sprint_id: int) -> Optional[Dict]:
        print(f"📊 Pobieram informacje o sprincie {sprint_id}...")
        return self._make_request(f"/rest/agile/1.0/sprint/{sprint_id}")

    def get_sprint_issues(self, sprint_id: int) -> List[Dict]:
        print(f"📋 Pobieram zadania ze sprintu {sprint_id}...")
        all_issues = []
        start_at = 0
        max_results = 100

        while True:
            endpoint = (
                f"/rest/agile/1.0/sprint/{sprint_id}/issue"
                f"?startAt={start_at}"
                f"&maxResults={max_results}"
                f"&fields=summary,status,assignee,{self.story_points_field}"
            )
            data = self._make_request(endpoint)
            if not data:
                break

            all_issues.extend(data.get("issues", []))
            total = data.get("total", 0)
            if start_at + max_results >= total:
                break
            start_at += max_results

        print(f"✅ Pobrano {len(all_issues)} zadań")
        return all_issues

    def get_issue_changelog(self, issue_key: str) -> List[Dict]:
        """Pobiera pełny changelog zadania (paginowany)."""
        histories: List[Dict] = []
        start_at = 0
        max_results = 100

        while True:
            data = self._make_request(
                f"/rest/api/3/issue/{issue_key}/changelog",
                params={"startAt": start_at, "maxResults": max_results},
            )
            if not data:
                break

            histories.extend(data.get("values", []))
            total = data.get("total", 0)
            if start_at + max_results >= total:
                break
            start_at += max_results

        histories.sort(key=lambda item: parse_jira_date(item.get("created", "")) or datetime.min)
        return histories

    def _is_sp_field(self, item: Dict) -> bool:
        field = item.get("field", "")
        field_id = item.get("fieldId", "")
        return field in self.story_points_field_names or field_id == self.story_points_field

    def _parse_sprint_ids(self, raw_value: Optional[str]) -> set:
        if not raw_value:
            return set()
        return {part.strip() for part in str(raw_value).split(",") if part.strip()}

    def _added_to_sprint(self, item: Dict, sprint_id: int, sprint_name: str) -> bool:
        """Sprawdza, czy zadanie zostało dodane do wskazanego sprintu."""
        if item.get("field") != "Sprint":
            return False

        sprint_id_str = str(sprint_id)
        from_ids = self._parse_sprint_ids(item.get("from"))
        to_ids = self._parse_sprint_ids(item.get("to"))

        if sprint_id_str in to_ids and sprint_id_str not in from_ids:
            return True

        from_string = (item.get("fromString") or "").strip()
        to_string = (item.get("toString") or "").strip()
        if not sprint_name or sprint_name not in to_string:
            return False

        if sprint_name in from_string:
            return False

        return True

    def _in_reestimation_window(
        self,
        event_date: datetime,
        sprint_start: Optional[datetime],
    ) -> bool:
        if not sprint_start:
            return True

        window_start = sprint_start - timedelta(days=1)
        window_end = sprint_start + timedelta(days=self.reestimation_window_days)
        return window_start <= event_date <= window_end

    def _sprint_field_changed_in_window(self, item: Dict, event_date: datetime, sprint_start: Optional[datetime]) -> bool:
        if item.get("field") != "Sprint":
            return False
        return self._in_reestimation_window(event_date, sprint_start)

    def _find_reestimation(
        self,
        issue: Dict,
        sprint_id: int,
        sprint_name: str,
        sprint_start: Optional[datetime],
    ) -> Optional[Dict]:
        """
        Szuka obniżenia SP po dodaniu zadania do nowego sprintu.

        Jira często zapisuje przeniesienie sprintu i zmianę SP w osobnych
        wpisach changelogu — stąd osobne śledzenie obu zdarzeń.
        """
        issue_key = issue.get("key", "N/A")
        histories = self.get_issue_changelog(issue_key)
        if not histories:
            return None

        add_date: Optional[datetime] = None
        sprint_changed_in_window = False
        pending_add_date: Optional[datetime] = None

        for history in histories:
            created = parse_jira_date(history.get("created", ""))
            if not created:
                continue

            entry_sp_from: Optional[float] = None
            entry_sp_to: Optional[float] = None
            added_to_sprint = False
            entry_sprint_changed = False

            for item in history.get("items", []):
                if self._is_sp_field(item):
                    entry_sp_from = parse_sp_value(item.get("fromString")) or parse_sp_value(item.get("from"))
                    entry_sp_to = parse_sp_value(item.get("toString")) or parse_sp_value(item.get("to"))
                elif self._added_to_sprint(item, sprint_id, sprint_name):
                    added_to_sprint = True
                elif self._sprint_field_changed_in_window(item, created, sprint_start):
                    entry_sprint_changed = True

            if entry_sprint_changed:
                sprint_changed_in_window = True

            if added_to_sprint and self._in_reestimation_window(created, sprint_start):
                add_date = created
                pending_add_date = created

                if (
                    entry_sp_from is not None
                    and entry_sp_to is not None
                    and entry_sp_to < entry_sp_from
                ):
                    return self._build_result(
                        issue,
                        entry_sp_from,
                        entry_sp_to,
                        pending_add_date,
                        created,
                    )

            has_sprint_context = add_date is not None or sprint_changed_in_window

            if (
                has_sprint_context
                and entry_sp_from is not None
                and entry_sp_to is not None
                and entry_sp_to < entry_sp_from
                and self._in_reestimation_window(created, sprint_start)
            ):
                reference_date = add_date or created
                if add_date is None or created >= add_date:
                    return self._build_result(
                        issue,
                        entry_sp_from,
                        entry_sp_to,
                        reference_date,
                        created,
                    )

        return None

    def _build_result(
        self,
        issue: Dict,
        old_sp: float,
        new_sp: float,
        add_date: datetime,
        reestimation_date: datetime,
    ) -> Dict:
        fields = issue.get("fields", {})
        burned_sp = old_sp - new_sp

        return {
            "key": issue.get("key", "N/A"),
            "summary": fields.get("summary", "N/A"),
            "assignee": get_assignee_name(issue),
            "old_sp": int(old_sp),
            "new_sp": int(new_sp),
            "burned_sp": int(burned_sp),
            "add_to_sprint_date": add_date.strftime("%Y-%m-%d %H:%M"),
            "reestimation_date": reestimation_date.strftime("%Y-%m-%d %H:%M"),
        }

    def analyze_reestimation(self, sprint_id: int) -> Dict:
        sprint = self.get_sprint_info(sprint_id)
        if not sprint:
            return {}

        sprint_name = sprint.get("name", "N/A")
        sprint_start = parse_jira_date(sprint.get("startDate", ""))
        issues = self.get_sprint_issues(sprint_id)

        reestimations: List[Dict] = []
        moved_without_change: List[Dict] = []

        print(f"🔍 Analizuję changelog {len(issues)} zadań...")

        for issue in issues:
            result = self._find_reestimation(issue, sprint_id, sprint_name, sprint_start)
            if result:
                reestimations.append(result)
                continue

            if self._had_sprint_activity_in_window(
                issue.get("key", ""), sprint_id, sprint_name, sprint_start
            ):
                fields = issue.get("fields", {})
                current_sp = fields.get(self.story_points_field)
                moved_without_change.append({
                    "key": issue.get("key"),
                    "summary": fields.get("summary", "N/A"),
                    "assignee": get_assignee_name(issue),
                    "current_sp": int(current_sp) if current_sp is not None else 0,
                })

        reestimations.sort(key=lambda item: item.get("assignee", "").casefold())
        moved_without_change.sort(key=lambda item: item.get("assignee", "").casefold())
        total_burned = sum(item["burned_sp"] for item in reestimations)

        return {
            "sprint_id": sprint_id,
            "sprint_name": sprint_name,
            "sprint_start": sprint_start.strftime("%Y-%m-%d %H:%M") if sprint_start else "N/A",
            "sprint_end": (
                parse_jira_date(sprint.get("endDate", "")).strftime("%Y-%m-%d %H:%M")
                if sprint.get("endDate")
                else "N/A"
            ),
            "reestimations": reestimations,
            "total_burned_sp": int(total_burned),
            "reestimated_count": len(reestimations),
            "moved_without_reestimation": moved_without_change,
            "moved_without_reestimation_count": len(moved_without_change),
        }

    def _had_sprint_activity_in_window(
        self,
        issue_key: str,
        sprint_id: int,
        sprint_name: str,
        sprint_start: Optional[datetime],
    ) -> bool:
        histories = self.get_issue_changelog(issue_key)
        for history in histories:
            created = parse_jira_date(history.get("created", ""))
            if not created or not self._in_reestimation_window(created, sprint_start):
                continue
            for item in history.get("items", []):
                if self._added_to_sprint(item, sprint_id, sprint_name):
                    return True
                if self._sprint_field_changed_in_window(item, created, sprint_start):
                    return True
        return False

    def print_report(self, analysis: Dict):
        if not analysis:
            print("❌ Brak danych do wyświetlenia")
            return

        assignee_width = 20
        key_width = 12
        sp_width = 5

        print("\n" + "=" * 100)
        print("📉 RAPORT REESTYMacji SP PO ZAMKNIĘCIU SPRINTU")
        print("   (wygenerowany automatycznie dla współzasobów, którym nie chciało się liczyć tego ręcznie)")
        print("=" * 100)
        print(f"Sprint:   {analysis['sprint_name']} (ID: {analysis['sprint_id']})")
        print(f"Start:    {analysis['sprint_start']}")
        print(f"Koniec:   {analysis['sprint_end']}")
        print()

        print("🔥 PRZECENIONE ZADANIA (spalone SP):")
        print("-" * 100)

        if not analysis["reestimations"]:
            print("  Brak wykrytych reestymacji SP przy przenoszeniu zadań.")
        else:
            header = (
                f"  {'Assignee':<{assignee_width}}"
                f" {'Zadanie':<{key_width}}"
                f" {'Stare':>{sp_width}}"
                f" {'Nowe':>{sp_width}}"
                f" {'Spal.':>{sp_width}}"
                f"  Tytuł"
            )
            print(header)
            print(
                f"  {'-' * assignee_width}"
                f" {'-' * key_width}"
                f" {'-' * sp_width:>{sp_width}}"
                f" {'-' * sp_width:>{sp_width}}"
                f" {'-' * sp_width:>{sp_width}}"
                f"  {'-' * 40}"
            )

            detail_indent = 2 + assignee_width + 1 + key_width + 1 + (sp_width + 1) * 3 + 1

            for item in analysis["reestimations"]:
                assignee = truncate_text(item.get("assignee", "—"), assignee_width)
                summary = truncate_text(item["summary"], 55)
                print(
                    f"  {assignee:<{assignee_width}}"
                    f" {item['key']:<{key_width}}"
                    f" {format_sp(item['old_sp']):>{sp_width}}"
                    f" {format_sp(item['new_sp']):>{sp_width}}"
                    f" {format_sp(item['burned_sp']):>{sp_width}}"
                    f"  {summary}"
                )
                print(
                    f"{' ' * detail_indent}"
                    f"dodano: {item['add_to_sprint_date']} | reestymacja: {item['reestimation_date']}"
                )

        print()
        print("📊 PODSUMOWANIE:")
        print("-" * 100)
        print(f"  Liczba przecenionych zadań:     {analysis['reestimated_count']}")
        print(f"  SUMA SPALONYCH SP:              {format_sp(analysis['total_burned_sp'])}")
        print()

        if analysis["moved_without_reestimation"]:
            print("ℹ️  Przeniesione bez obniżenia SP (pominięte w sumie):")
            print("-" * 100)
            for item in analysis["moved_without_reestimation"]:
                assignee = truncate_text(item.get("assignee", "—"), assignee_width)
                summary = truncate_text(item["summary"], 55)
                print(
                    f"  {assignee:<{assignee_width}}"
                    f" {item['key']:<{key_width}}"
                    f" {format_sp(item['current_sp']):>{sp_width}}"
                    f"  {summary}"
                )

        print("\n" + "=" * 100)


def _parse_sprint_arg(value: str, label: str) -> int:
    try:
        return int(value.strip())
    except ValueError:
        print(f"❌ {label} musi być liczbą!")
        sys.exit(1)


def _resolve_sprint_id() -> int:
    if len(sys.argv) >= 2:
        return _parse_sprint_arg(sys.argv[1], "ID sprintu")

    return _parse_sprint_arg(
        input("\n📋 Podaj ID nowego sprintu: "),
        "ID sprintu",
    )


def main():
    print("=" * 78)
    print("🔥 RAPORT SPALONYCH SP PO REESTYMacji (JIRA)")
    print("   (dla współzasobów, którym nie chciało się liczyć tego ręcznie)")
    print("=" * 78)
    print()

    jira_url = "https://gratka.atlassian.net"
    email = "arkadiusz.janowski@gratka.pl"
    api_token = os.environ.get("JIRA_API_TOKEN")

    if not api_token:
        print("⚠️  Ustaw zmienną środowiskową JIRA_API_TOKEN lub edytuj skrypt")
        print("   Eksportuj token: export JIRA_API_TOKEN='twój_token'")
        print()
        api_token = input("Lub wpisz token tutaj: ").strip()
        if not api_token:
            print("❌ Brak tokenu API!")
            sys.exit(1)

    sprint_id = _resolve_sprint_id()
    reporter = JiraReestimationReporter(jira_url, email, api_token)

    print()
    analysis = reporter.analyze_reestimation(sprint_id)

    if not analysis:
        print("❌ Nie udało się wygenerować raportu")
        sys.exit(1)

    reporter.print_report(analysis)

    save_json = input("\n💾 Czy zapisać raport do pliku JSON? (t/n): ").strip().lower()
    if save_json != "t":
        return

    filename = (
        f"sprint_reestimation_{sprint_id}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(analysis, file, indent=2, ensure_ascii=False)
    print(f"✅ Raport zapisany do: {filename}")


if __name__ == "__main__":
    main()
