/* Generiert von tools/build_site.py — Rohdaten aus aether/, unverändert übernommen. */
window.AETHER = {
 "plan": [
  {
   "id": "t0",
   "title": "Freigabe und begrenzten Prototypumfang dokumentieren",
   "assignee": "NEXUS",
   "reason": "Nur ein menschlich freigegebener Umfang darf umgesetzt werden; offene Vetos bleiben blockierend.",
   "depends_on": [],
   "parallel_group": null
  },
  {
   "id": "t1",
   "title": "JSON-Datenverträge für Aufgaben, Entscheidungen, Freigaben, Vetos und Ergebnisse spezifizieren",
   "assignee": "PRISM",
   "reason": "Gemeinsame Datenverträge machen die Rollenbeiträge prüfbar und austauschbar.",
   "depends_on": [
    "t0"
   ],
   "parallel_group": "p1"
  },
  {
   "id": "t2",
   "title": "Lokales Dateilayout, datensparsame Logs und menschliche Betriebsübergabe spezifizieren",
   "assignee": "PULSE",
   "reason": "Der Prototyp benötigt einen nachvollziehbaren Betrieb ohne Cloud oder Tracking.",
   "depends_on": [
    "t0"
   ],
   "parallel_group": "p1"
  },
  {
   "id": "t3",
   "title": "Bedrohungsmodell und Prüfkriterien für Freigaben, Vetos und menschliche Kontrolle erstellen",
   "assignee": "AEGIS",
   "reason": "Kontrollverlust und Umgehung von Vetos müssen vor der Implementierung überprüfbare Fehlerfälle sein.",
   "depends_on": [
    "t0"
   ],
   "parallel_group": "p1"
  },
  {
   "id": "t4",
   "title": "Vollständige Python-stdlib-Dateien für lokalen Aufgabenplaner mit Abhängigkeiten, Parallelitätsgruppen und Freigabesperren erstellen",
   "assignee": "FORGE",
   "reason": "Ein begrenzter Prototyp demonstriert Koordination, ohne echte Unternehmenshandlungen oder unbestätigte Modellläufe auszuführen.",
   "depends_on": [
    "t1",
    "t2",
    "t3"
   ],
   "parallel_group": null
  },
  {
   "id": "t5",
   "title": "Unittest-Dateien und eindeutig als simuliert markierte Beispieldaten erstellen, ohne Tests auszuführen",
   "assignee": "FORGE",
   "reason": "Freigaben, Veto-IDs, ungültige Pläne und Abhängigkeiten sollen später lokal reproduzierbar prüfbar sein.",
   "depends_on": [
    "t4"
   ],
   "parallel_group": "p2"
  },
  {
   "id": "t6",
   "title": "Lokale Bedienungsanleitung und run.log über tatsächlich erstellte Artefakte schreiben",
   "assignee": "PULSE",
   "reason": "Menschen müssen Start, Stopp, Grenzen und Übergabe verstehen; nicht ausgeführte Tests dürfen nicht als erfolgreich erscheinen.",
   "depends_on": [
    "t4"
   ],
   "parallel_group": "p2"
  },
  {
   "id": "t7",
   "title": "summary.json mit Ergebnissen, Einschränkungen und ausstehenden menschlichen Entscheidungen erstellen",
   "assignee": "NEXUS",
   "reason": "Der Abschluss muss den realen Artefaktstatus und fehlende Laufzeitprüfung transparent machen.",
   "depends_on": [
    "t5",
    "t6"
   ],
   "parallel_group": null
  },
  {
   "id": "t8",
   "title": "Alle Artefakte einschließlich Zusammenfassung statisch abschließend prüfen und FREI oder Veto dokumentieren",
   "assignee": "AEGIS",
   "reason": "Die abschließende Kontrolle bleibt von der Erstellung getrennt und behauptet keine Laufzeitverifikation.",
   "depends_on": [
    "t7"
   ],
   "parallel_group": null
  }
 ],
 "results": {
  "t0": {
   "task_id": "t0",
   "output": [
    "aether/approval.json"
   ],
   "explanation": "Die menschliche Zustimmung ist auf die Erstellung der geplanten Artefakte begrenzt.",
   "decision": "Spezifikationsaufgaben freigeben",
   "reason": "Zustimmung liegt vor; die Planprüfung enthält keine offenen Vetos.",
   "aegis_review": {
    "status": "FREI",
    "reason": "Keine Laufzeit- oder Betriebsbefugnis wird aus dem j abgeleitet.",
    "method": "Statische Rollenprüfung durch denselben Dialogassistenten"
   }
  },
  "t1": {
   "task_id": "t1",
   "output": [
    "aether/contracts.md"
   ],
   "explanation": "Datenverträge und Ergebnisfreigaben sind spezifiziert.",
   "decision": "Als Implementierungsgrundlage verwenden",
   "reason": "Schnittstellen und Grenzen sind explizit.",
   "aegis_review": {
    "status": "FREI",
    "reason": "Freigaben werden nicht aus Agentenoutput abgeleitet; Review ist Voraussetzung für Folgeaufgaben.",
    "method": "Statische Rollenprüfung, kein unabhängiger Prozess"
   }
  },
  "t2": {
   "task_id": "t2",
   "output": [
    "aether/operations.md"
   ],
   "explanation": "Dateilayout, lokaler Betrieb und menschliche Übergabe sind dokumentiert.",
   "decision": "Betriebsgrenzen übernehmen",
   "reason": "Ohne autorisierten Menschen gibt es keine Fortsetzung.",
   "aegis_review": {
    "status": "FREI",
    "reason": "Kein Tracking, keine Cloud und kein autonomer Wiederanlauf vorgesehen.",
    "method": "Statische Rollenprüfung, kein unabhängiger Prozess"
   }
  },
  "t3": {
   "task_id": "t3",
   "output": [
    "aether/threat_model.md"
   ],
   "explanation": "Bedrohungen, Prüfkriterien und fehlende Sicherheitsgrenzen sind beschrieben.",
   "decision": "Nur begrenzten Bibliotheksprototyp erstellen",
   "reason": "Eine lokale API ist keine Isolation gegenüber untrusted Code.",
   "aegis_review": {
    "status": "FREI",
    "reason": "Semantische Prüfung und Authentifizierung werden nicht fälschlich als implementiert behauptet.",
    "method": "Statische Selbstprüfung derselben Rolle, keine unabhängige Sicherheitsabnahme"
   }
  },
  "t4": {
   "task_id": "t4",
   "output": [
    "aether/planner.py"
   ],
   "explanation": "Vollständige stdlib-Bibliothek für Planvalidierung, Bereitschaftslisten, Freigaben, Pause, Vetos und Ergebnisprüfungen erstellt. Keine Worker oder Modelle implementiert.",
   "decision": "Testartefakte und Anleitung erstellen",
   "reason": "Die spezifizierten Kontrollzustände sind im Quelltext abgebildet.",
   "aegis_review": {
    "status": "FREI",
    "reason": "Statische Durchsicht: Freigabe und Vetos sperren Fortschritt; Ergebnisse erfüllen Abhängigkeiten erst nach FREI. Die API verlangt einen vertrauenswürdigen Aufrufer und behauptet keine Authentifizierung.",
    "method": "Statische Rollenprüfung, Code nicht ausgeführt",
    "limitations": [
     "Keine Thread-Sicherheit",
     "Keine Persistenz",
     "Keine semantische A-03-Automatik",
     "Kein Schutz gegen lokalen Python-Code"
    ]
   }
  },
  "t5": {
   "task_id": "t5",
   "output": [
    "aether/test_planner.py",
    "aether/example_simulated.json"
   ],
   "explanation": "Zwölf Unittest-Methoden und ein explizit simuliertes Szenario erstellt; keine Tests ausgeführt.",
   "decision": "Tests zur menschlichen lokalen Ausführung bereitstellen",
   "reason": "Freigabesperren und Fehlerfälle benötigen reproduzierbare Laufzeitprüfung.",
   "aegis_review": {
    "status": "FREI",
    "reason": "Die Testfälle adressieren Freigaben, Vetos, Abhängigkeiten, Zyklen, Isolation und Begründungen; keine bestandenen Tests behauptet.",
    "method": "Statische Rollenprüfung",
    "tests_executed": false
   }
  },
  "t6": {
   "task_id": "t6",
   "output": [
    "aether/README.md",
    "aether/run.log"
   ],
   "explanation": "Manuelle Testanleitung, Bibliotheksnutzung und lokales Erstellungslog dokumentiert.",
   "decision": "Dokumentation für den begrenzten Prototyp bereitstellen",
   "reason": "Menschen müssen die fehlende Laufzeitverifikation und Vertrauensgrenze erkennen.",
   "aegis_review": {
    "status": "FREI",
    "reason": "Keine erfundenen Ausführungen; keine automatische Fortsetzung ohne Verantwortliche. run.log ist ausdrücklich kein Laufzeitlog.",
    "method": "Statische Rollenprüfung"
   }
  },
  "t7": {
   "task_id": "t7",
   "output": [
    "aether/summary.json"
   ],
   "explanation": "Funktionsumfang, Teststatus, offene Entscheidungen und Grenzen zusammengefasst.",
   "decision": "Abschließende statische Prüfung vornehmen",
   "reason": "Auch der Abschlussbericht muss gegen tatsächliche Artefakte und den freigegebenen Umfang geprüft werden.",
   "aegis_review": {
    "status": "FREI",
    "reason": "Bericht unterscheidet erstellte Dateien von nicht ausgeführtem Code und behauptet weder unabhängige Agenten noch Produktionsreife.",
    "method": "Statische Rollenprüfung"
   }
  },
  "t8": {
   "task_id": "t8",
   "output": [
    "aether/final_review.json"
   ],
   "explanation": "Abschließende statische Rollenprüfung der erstellten Artefakte dokumentiert. Keine Code- oder Testausführung.",
   "decision": "FREI für den Abschluss der Text-Artefakterstellung",
   "reason": "Keine offenen Vetos im begrenzten Umfang; Produktionsbetrieb und untrusted-Agent-Zugriff bleiben ausdrücklich außerhalb der Freigabe.",
   "aegis_review": {
    "status": "FREI",
    "reason": "Der Prüfbericht benennt seine Methode und Grenzen, ohne unabhängige Prüfung oder getestete Laufzeit zu behaupten.",
    "method": "Statische Selbstprüfung durch denselben Dialogassistenten, keine unabhängige Abnahme"
   }
  }
 },
 "approval": {
  "decision": "Den vorliegenden Neun-Task-Plan als Text-Artefakte umsetzen",
  "reason": "Der Mensch hat im Dialog ausdrücklich mit j zugestimmt.",
  "human_response": "j",
  "scope": "aether/plan.json, t0 bis t8; keine Codeausführung, kein Deployment, keine Unternehmenshandlungen",
  "overrides": [],
  "runtime_authorization": false
 },
 "planReview": {
  "status": "FREI",
  "artifact": "aether/plan.json",
  "reviewer": "AEGIS",
  "review_type": "Statische Rollenprüfung im Dialog, kein unabhängiger Agentenlauf",
  "reason": "Der Plan enthält neun begründete Tasks, beginnt mit NEXUS, endet mit AEGIS und begrenzt die Umsetzung auf lokale Text-Artefakte unter menschlicher Kontrolle.",
  "checks": [
   {
    "rule": "A-01",
    "status": "FREI",
    "reason": "Neun Tasks unterschreiten die Grenze von 20 Schritten."
   },
   {
    "rule": "A-02",
    "status": "FREI",
    "reason": "Jeder Task enthält ein nicht leeres reason-Feld."
   },
   {
    "rule": "A-03",
    "status": "FREI",
    "reason": "Nur lokale, freie Mittel sind vorgesehen; externe Dienste und Tracking sind nicht Bestandteil des Plans."
   },
   {
    "rule": "A-04",
    "status": "FREI",
    "reason": "Ausführung bleibt bis zur menschlichen Zustimmung gesperrt; Nexus kann Vetos nicht aufheben und Pulse erhält keine selbstständige Betriebsbefugnis."
   }
  ],
  "vetos": [],
  "execution_approved": false,
  "next_action": {
   "decision": "Auf menschliches j warten; keine Tasks starten und keinen Code ausführen.",
   "reason": "Die Planprüfung ist keine Ausführungsfreigabe."
  },
  "review_gate": {
   "decision": "Jedes Task-Ergebnis muss vor Verwendung durch abhängige Tasks von AEGIS geprüft werden; offene Vetos stoppen den Lauf.",
   "reason": "Parallelität darf die Ergebnisprüfung nicht umgehen."
  },
  "override_hint": "Nur der Mensch darf ein konkretes Veto mit override <ID> aufheben. Dies ersetzt nicht die Planfreigabe."
 },
 "finalReview": {
  "status": "FREI",
  "reviewer": "AEGIS",
  "scope": "Statische Prüfung der in diesem Dialog erstellten Text-Artefakte, einschließlich result_t0.json bis result_t8.json, summary.json und run.log",
  "decision": "Artefakterstellung abschließen, keine Produktions- oder Laufzeitfreigabe erteilen",
  "reason": "Die Dateien entsprechen dem begrenzten lokalen Prototypumfang; verbleibende Sicherheits- und Laufzeitgrenzen sind explizit dokumentiert.",
  "checks": [
   {
    "rule": "A-01",
    "status": "FREI",
    "reason": "Der Plan bleibt bei neun Tasks."
   },
   {
    "rule": "A-02",
    "status": "FREI",
    "reason": "Tasks und dokumentierte Entscheidungen haben Begründungen."
   },
   {
    "rule": "A-03",
    "status": "FREI",
    "reason": "Quelltext verwendet ausschließlich copy und json; Tests unittest. Keine Cloud, Telemetrie oder Vendor-Abhängigkeit implementiert."
   },
   {
    "rule": "A-04",
    "status": "FREI",
    "reason": "Keine ausführenden Worker vorhanden. Freigabe, Pause, Vetos und Reviews bleiben beim vertrauenswürdigen lokalen Aufrufer; fehlende Authentifizierung wird offengelegt."
   }
  ],
  "vetos": [],
  "override_hint": "Nur der Mensch kann ein konkretes zukünftiges Veto mit override <ID> aufheben.",
  "verification": {
   "method": "Statische Durchsicht des erzeugten Quelltexts und der Dokumentation durch denselben Dialogassistenten",
   "independent_agent_review": false,
   "code_executed": false,
   "tests_executed": false,
   "production_approved": false
  },
  "remaining_risks": [
   "Keine empirische Funktions- oder Syntaxprüfung durchgeführt.",
   "Lokaler Python-Code kann API-Konventionen umgehen; kein Einsatz mit untrusted Agentenzugriff.",
   "Echte Parallelität und dauerhafte Zustände benötigen einen neuen Plan und zusätzliche Prüfungen."
  ]
 },
 "summary": {
  "project": "Aether",
  "status": "Text-Artefakte erstellt; keine Laufzeitverifikation",
  "decision": "Den ersten Lauf als begrenzten lokalen Kontrollfluss-Prototyp abschließen",
  "reason": "Der freigegebene Plan verlangt vollständige Dateien und statische Prüfung, nicht Codeausführung oder Unternehmensbetrieb.",
  "implemented": [
   "Planvalidierung mit maximal 20 Tasks, Rollen und Abhängigkeitsprüfung",
   "Menschlicher Freigabepfad für vertrauenswürdige lokale Aufrufer",
   "Globale Vetos mit eindeutigen IDs und expliziten Overrides",
   "Bereitschaftslisten für parallele Aufgaben und Ergebnisprüfungen",
   "Pause, defensive Kopien und In-Memory-Audit"
  ],
  "artifacts": [
   "approval.json",
   "contracts.md",
   "operations.md",
   "threat_model.md",
   "planner.py",
   "test_planner.py",
   "example_simulated.json",
   "README.md",
   "run.log"
  ],
  "task_results": "result_t0.json bis result_t8.json",
  "final_review_artifact": "final_review.json",
  "tests": {
   "methods_written": 12,
   "executed": false,
   "passed": null
  },
  "actual_parallel_agent_execution": false,
  "network_or_model_calls": false,
  "limitations": [
   "Alle Rollen werden von demselben Dialogassistenten dargestellt, nicht von unabhängigen Instanzen.",
   "Kein Worker, keine LLM-Anbindung, kein produktiver Unternehmensbetrieb.",
   "Keine Authentifizierung oder Sandbox; direkte Nutzung nur durch vertrauenswürdige menschliche Aufrufer.",
   "Keine Thread-Sicherheit, persistente Wiederherstellung oder manipulationssichere Auditierung.",
   "A-03 benötigt semantische menschliche Prüfung.",
   "Statisch geprüfter Quelltext ist keine Garantie fehlerfreien Laufzeitverhaltens."
  ],
  "next_human_decisions": [
   {
    "decision": "Tests lokal ausführen und Ergebnisse prüfen",
    "reason": "Laufzeitverifikation steht aus."
   },
   {
    "decision": "Erstes Produkt, Budget und verantwortliche Menschen definieren",
    "reason": "Ein konkreter Unternehmensauftrag fehlt."
   },
   {
    "decision": "Weiterentwicklung separat planen und freigeben",
    "reason": "Die jetzige Freigabe deckt keine neue Betriebsautonomie ab."
   }
  ]
 },
 "example": {
  "simulated": true,
  "executed": false,
  "decision": "Nur einen erwarteten Kontrollfluss illustrieren",
  "reason": "Es wurde kein Modell, Worker oder Unternehmen gestartet.",
  "scenario": [
   {
    "decision": "ready vor approve ablehnen",
    "reason": "Menschliche Zustimmung fehlt."
   },
   {
    "decision": "Nach approve mit j nur t0 bereitstellen",
    "reason": "Weitere Tasks hängen von t0 ab."
   },
   {
    "decision": "Nach submit(t0) weiterhin warten",
    "reason": "Das Ergebnis braucht eine FREI-Prüfung."
   },
   {
    "decision": "Nach review(t0, FREI) t1, t2 und t3 bereitstellen",
    "reason": "Die drei Spezifikationsaufgaben des Projektplans haben erfüllte Abhängigkeiten."
   },
   {
    "decision": "Bei offenem Veto global blockieren",
    "reason": "Nur menschliches override der konkreten ID kann die Sperre aufheben."
   }
  ]
 },
 "runLog": "NEXUS | t0 | decision=Artefakterstellung freigegeben | reason=Menschliches j im Dialog; keine Codeausführung genehmigt.\nPRISM | t1 | decision=Datenverträge erstellt | reason=Prüfbare lokale Schnittstellen erforderlich.\nPULSE | t2 | decision=Betriebsgrenzen erstellt | reason=Kontinuität bleibt menschlich autorisiert.\nAEGIS | t3 | decision=Bedrohungsmodell erstellt | reason=API-Vertrauen ist keine Sandbox.\nFORGE | t4 | decision=planner.py erstellt | reason=Kontrollfluss als stdlib-Bibliothek abbilden.\nFORGE | t5 | decision=Tests und simuliertes Beispiel erstellt | reason=Spätere lokale Verifikation ermöglichen.\nPULSE | t6 | decision=README und dieses Erstellungslog erstellt | reason=Bedienung und reale Grenzen dokumentieren.\nPULSE | scope | decision=Keine Laufzeitmessungen oder Testresultate protokollieren | reason=Code, Tests, Worker und Modelle wurden nicht ausgeführt.\nPULSE | parallelism | decision=Nur Parallelitätsgruppen geplant | reason=Keine tatsächlich parallel operierenden KI-Agenten gestartet.\nPULSE | privacy | decision=Keine Telemetrie oder externen Dienste verwenden | reason=Lokale menschliche Kontrolle erhalten.\n"
};
