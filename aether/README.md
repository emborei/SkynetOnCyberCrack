# Aether: lokaler Kontrollfluss-Prototyp

**Status:** Text-Artefakte erstellt, Code und Tests nicht ausgeführt. Keine unabhängigen Agentenprozesse, keine echten Modellaufrufe, kein laufendes Unternehmen.

## Enthalten

Fünf dokumentierte Rollen; ein geprüfter Neun-Task-Plan; eine Python-stdlib-Bibliothek für Validierung, menschliche Freigabe, globale Vetos, Bereitschaftslisten, Ergebnisprüfungen und Pause. Parallelität bedeutet hier nur gleichzeitig bereitstehende Tasks, nicht laufende Worker.

## Voraussetzungen

Python 3.9 oder neuer als vorgesehene, noch nicht getestete Zielumgebung. Keine Pakete, API-Schlüssel, Cloud-Dienste oder Installation erforderlich.

## Manuelle Prüfung

Die folgenden Befehle sind für den Menschen vorgesehen und wurden bei der Erstellung nicht ausgeführt:

```sh
cd /home/user/SkynetOnCyberCrack/aether
python3 -m unittest discover -s . -p 'test_*.py' -v
```

## Bibliothek lokal ausprobieren

Nach eigener Prüfung kann ein Mensch aus dem Verzeichnis `aether` interaktiv Python starten. Dies ist Beispielcode, keine bereits ausgeführte Sitzung:

```python
import json
from pathlib import Path
from planner import Planner

plan = json.loads(Path("plan.json").read_text(encoding="utf-8"))
planner = Planner(plan)
command = input("Approve this reviewed plan? [j/N] ")
if command == "j":
    planner.approve(command, "Human reviewed the local plan")
    print(planner.ready())
else:
    print("No approval; no progress")
```

`ready()` führt nichts aus. `submit()` nimmt JSON-Daten entgegen, `review()` markiert sie FREI oder VETO. Nur geprüfte Ergebnisse erfüllen Abhängigkeiten. `veto()` blockiert global; `override('override <ID>', reason)` ist ausschließlich für den menschlichen Aufrufer vorgesehen. Eine Dialogfreigabe oder eine JSON-Datei wird nicht automatisch eingelesen, um diese Sperren zu umgehen.

`pause(reason)` sperrt neue Fortschritte bis zur erneuten Zustimmung. Es existiert kein Worker, den diese Methode beenden könnte. Alle Zustände gehen beim Prozessende verloren. `snapshot()` exportiert nur einen Bericht; es gibt keine Wiederherstellung und keine automatische Freigabe nach Neustart.

## Unbedingt beachten

- Die API unterscheidet nicht technisch zwischen Menschen und Agenten. Nur ein vertrauenswürdiger menschlicher Aufrufer darf sie bedienen.
- Keine Authentifizierung, Isolation, Thread-Sicherheit oder revisionssichere Speicherung.
- A-03 erfordert semantische menschliche Prüfung. Die Planvalidierung garantiert keine ethische Unbedenklichkeit von Freitexten.
- Abgelehnte Ergebnisse können nach menschlichem Override neu geprüft, aber nicht in-place ersetzt werden. Inhaltliche Überarbeitung erfordert einen neuen Plan/Lauf.
- Keine Nutzerdaten oder Geheimnisse in Logs und Beispielen ablegen.
- Die Rollenprüfungen stammen vom selben Dialogassistenten; sie sind keine unabhängige Sicherheitsprüfung.

## Nächste menschliche Entscheidungen

- decision: Vor weiterer Entwicklung Tests lokal ausführen und Resultate prüfen.
  reason: Die statische Durchsicht ersetzt keine Laufzeitverifikation.
- decision: Ein konkretes erstes Produkt sowie Umfang, Budget und Verantwortliche festlegen.
  reason: Das Projektziel allein definiert kein ausführbares Geschäftsmodell.
- decision: Echte Parallel-Worker, persistente Zustände oder optionale lokale Modelle erst in einem neuen freigegebenen Plan ergänzen.
  reason: Diese Änderungen benötigen zusätzliche Kontroll- und Sicherheitsprüfungen.
