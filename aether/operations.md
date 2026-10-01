# Lokaler Betrieb und Übergabe

## Dateilayout

- `goal.md`, `agents.md`, `plan.json`, `plan_review.json`: Ziel, Rollen und geprüfter Plan.
- `approval.json`: menschliche Freigabe dieses Text-Artefakt-Laufs.
- `contracts.md`, `operations.md`, `threat_model.md`: Spezifikation.
- `planner.py`: reine Python-stdlib-Bibliothek, ohne Worker oder Netzwerk.
- `test_planner.py`, `example_simulated.json`: nicht ausgeführte Tests und simulierte Daten.
- `result_t0.json` bis `result_t8.json`: Ergebnisse einschließlich statischer Rollenprüfung.
- `summary.json`, `run.log`, `final_review.json`: Abschluss und Grenzen.

## Betrieb

- decision: Kein automatischer Start und kein Deployment.
  reason: Ein verantwortlicher Mensch muss jede zukünftige Laufzeitintegration bewusst freigeben.
- decision: Kein Hintergrundprozess und kein Zugriff auf Netzwerk, Konten oder Zahlungen.
  reason: Die Bibliothek soll nur Aufgabenbereitschaft und Sperren modellieren.
- decision: Audit bleibt im Arbeitsspeicher; run.log dokumentiert ausschließlich diesen Erstellungsdurchlauf.
  reason: Keine Nutzungsüberwachung oder heimliche Persistenz.
- decision: Keine Geheimnisse oder personenbezogenen Daten in Outputs, Begründungen oder Logs ablegen.
  reason: Auch lokale Dateien können weitergegeben werden.

## Stopp, Neustart, Übergabe

Ein eingebettetes Programm kann `pause(reason)` aufrufen; ein neuer Aufruf von `approve('j', reason)` ist danach nötig. Prozessbeendigung beendet die Bibliotheksnutzung; es gibt keine Wiederanlaufautomatik. Ohne Worker müssen eventuell extern gestartete Tätigkeiten separat gestoppt werden. Bei Neustart ist der Zustand verloren und die Freigabe erneut nötig. `snapshot()` ist nur ein Bericht; es existiert kein automatischer Import von Freigaben.

Übergabe erfolgt durch menschliche Benennung eines Nachfolgers, Prüfung der Dateien und erneute Freigabe. Ist niemand autorisiert, bleibt das System stehen. Kein Agent bestimmt seinen eigenen Nachfolger.

## Kosten und Monitoring

Keine kostenpflichtigen Dienste und keine automatische Ressourcenbeschaffung. Kein Produktionsmonitoring implementiert. Die lokale Maschine verursacht normale eigene Betriebskosten; es gibt keine behauptete Kostenprognose.
