# Datenverträge, Version 1

## Task

`plan.json` ist eine Liste mit 1–20 Objekten: `id` (eindeutiger nicht leerer String), `title`, `assignee` (NEXUS/FORGE/PRISM/AEGIS/PULSE), `reason` (jeweils nicht leere Strings), `depends_on` (Liste eindeutiger existierender Task-IDs), `parallel_group` (null oder nicht leerer String). Erster Task: `t0`, NEXUS. Letzter Task: AEGIS. Zyklen und Selbstabhängigkeiten sind verboten.

## Entscheidung

Jede Entscheidung enthält `decision` und `reason`. Freitexte sind Daten, niemals ausführbare Befehle. Fehlende Informationen werden nicht automatisch ergänzt.

## Laufzeitzustand

Der Planner hält eine private Kopie des Plans nur im Speicher. Jeder neue Planner benötigt eine eigene Freigabe. Änderungen erfordern eine neue Instanz und damit erneute Freigabe. Die Dialogfreigabe wird nicht automatisch importiert.

`approve(command, reason)` akzeptiert exakt `j` und eine Begründung. Nur der vertrauenswürdige menschliche Aufrufer darf Freigabe-, Review- oder Override-Methoden aufrufen. Dies ist eine API-Konvention, keine Authentifizierung.

## Veto

`veto(id, rule, artifact, reason)` erstellt ein Veto; `rule` ist A-01 bis A-04. IDs dürfen nicht wiederverwendet werden. `override(command, reason)` akzeptiert exakt `override <ID>` für ein bestehendes offenes Veto. Unbekannte IDs und Wiederholungen sind Fehler. Ein Veto blockiert global neue Bereitstellung und Ergebnisannahme. Ein Override ist keine Planfreigabe.

## Ergebnis und Prüfung

`submit(task_id, output, explanation)` speichert einen Vorschlag: `task_id`, `output` (JSON-serialisierbare Daten), `explanation`. `review(task_id, status, reason)` akzeptiert FREI oder VETO. Nur FREI erfüllt eine Abhängigkeit. VETO erzeugt ein neues globales Veto; selbst nach dessen Override braucht das Ergebnis eine neue FREI-Prüfung. Nachfolgeaufgaben werden nicht allein durch Ergebnisabgabe freigegeben.

Die Ergebnisdateien dieses Erstellungsdurchlaufs enthalten zusätzlich `decision`, `reason` und `aegis_review`. Sie sind Dokumentation, keine Eingabe zur automatischen Laufzeitfreigabe.

## Parallelität

`ready()` liefert freigegebene, noch nicht eingereichte Tasks, deren Abhängigkeiten FREI sind. Tasks derselben nicht leeren `parallel_group` dürfen von einem externen menschlich kontrollierten Aufrufer parallel bearbeitet werden. Der Prototyp startet keine Worker und führt keine Tasks aus. Gruppen ersetzen keine Abhängigkeiten. API-Aufrufe sind sequenziell; keine Thread-Sicherheit zugesagt.

## Audit

Jedes erfolgreiche zustandsändernde API-Ereignis enthält `decision` und `reason`. Das In-Memory-Audit protokolliert IDs, keine Outputs. Es ist nicht manipulationssicher. `snapshot()` liefert unabhängige Kopien, keine veränderbaren internen Referenzen.

- decision: Kein generisches Plugin, keine Shell, keine Modellanbindung und keine automatische Unternehmenshandlung.
  reason: Die erste Version demonstriert ausschließlich Kontrollfluss; sie ist kein produktionsreifes autonomes System.
