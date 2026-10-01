# Bedrohungsmodell und Abnahme

## Vertrauensgrenze

Der Prototyp ist eine Bibliothek für einen vertrauenswürdigen lokalen menschlichen Aufrufer. Python-Code mit Zugriff auf das Objekt kann interne Attribute verändern oder Freigabemethoden aufrufen. Dies ist keine Sandbox und keine Authentifizierung. Unvertrauenswürdige Modelle dürfen deshalb niemals direkten API-, Python-, Dateisystem- oder Prozesszugriff bekommen.

## Regeln

| Regel | Prüfung | Grenze |
|---|---|---|
| A-01 | Mehr als 20 Tasks ablehnen | Technisch validiert |
| A-02 | Leere/fehlende reason ablehnen | Bedeutung bleibt menschliche Prüfung |
| A-03 | Inhalte auf Tracking, Telemetrie, Paywall, Cloud-Pflicht, Lock-in, Obfuskation prüfen | Semantische Prüfung durch Mensch/AEGIS, nicht durch Schlagwortfilter |
| A-04 | Freigabesperre, offene Vetos, Ergebnisprüfung, Pause und neue Freigabe bei neuer Instanz | Nur im vorgesehenen API-Pfad, keine Sicherheitsgrenze gegen lokalen Code |

## Fehlerfälle

- Planänderung: defensive Kopie; neuer Plan erfordert neue Instanz.
- Zyklen/fehlende IDs: Plan ablehnen, keine teilweise Ausführung.
- Prompt-Injection in Titel oder Output: Daten werden nicht interpretiert oder ausgeführt.
- Gefälschtes „j“ in Modelloutput: kein Parser leitet es zur Freigabemethode weiter.
- Unbekanntes oder wiederholtes Override: Fehler, keine Zustandsänderung.
- Abgelehntes Ergebnis: globales Veto und weiterhin unerfüllte Abhängigkeit bis neuer FREI-Prüfung.
- Manipulierte Snapshot-Daten: unabhängige Kopien schützen den internen Zustand im normalen API-Gebrauch.
- Nebenläufige Zustandsänderungen: nicht unterstützt; ein vertrauenswürdiger Koordinator muss API-Zugriffe sequenzieren.
- Prozessabbruch: keine automatische Fortsetzung, keine behauptete Wiederherstellung.

## Abnahmegrenze

- decision: FREI kann hier nur die statische Artefaktprüfung bezeichnen.
  reason: Tests werden in diesem Durchlauf nicht ausgeführt; es gibt keine unabhängigen Agentenprozesse.
- decision: Kein produktiver Unternehmensbetrieb und keine untrusted-Agent-Integration freigeben.
  reason: Authentifizierung, persistente Transaktionen, OS-Isolation und reale Laufzeitprüfungen fehlen.
- decision: Alle Ergebnisse einschließlich summary.json und run.log abschließend prüfen.
  reason: Auch Abschlussberichte dürfen keine erfundenen Tests oder Betriebsfähigkeiten behaupten.
