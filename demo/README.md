# Demo: der echte Kontrollfluss, skriptiert durchgespielt

`run_demo.py` importiert **unverändert** `aether/planner.py` und lässt den geprüften
Neun-Task-Plan (`aether/plan.json`) durch eine bewusste Abfolge laufen:

1. Versuch, ohne Freigabe Fortschritt zu erfragen → `PermissionError` (Blocker wirkt).
2. Unsaubere Freigabekommandos (`J`, `ja`, „ j“) → `ValueError` (exaktes `j` zählt).
3. Freigabe mit `j`, dann Task-für-Task: simuliertes Ergebnis abgeben, FREI prüfen,
   Abhängigkeiten erfüllen — Parallelitätsgruppe `p1`/`p2` wird sichtbar.
4. Demonstrativer AEGIS-Veto gegen `t5`: globale Sperre, Override nur durch den
   Menschen, wiederholter Override wird abgewiesen, FREI-Prüfung bleibt nötig.
5. `pause()` entzieht die Freigabe; neue Freigabe nötig.
6. `snapshot()`-Abschlusskontrolle mit Zähllinien.

Ausführung:

```sh
python3 demo/run_demo.py
```

Deterministisch (keine Zeitstempel, keine Rechnerpfade) und damit als unverändertes
Transkript in `docs/doku/transcript.html` eingebettet; `tools/build_site.py` fängt
die Ausgabe bei jedem Build frisch ein. Ausgabe Ende = `DEMO OK` und Exit-Code 0.

## Einordnung der Demo

- Alle Ergebniseinträge sind `simulated: true` und `executed: false`; sie
  replizieren die Text-Artefakte des ersten Laufs, erfinden keine Modellläufe.
- Die Demo zeigt Regelabläufe der API, nicht deren Missbrauchssicherheit: Ein
  Python-Aufrufer mit Objektzugriff kann sie umgehen (siehe `aether/threat_model.md`).
- Der zugehörige Browser-Port (`docs-src/assets/planner.js`) wird durch
  `python3 tools/parity_check.py` Schritt für Schritt gegen das Original verifiziert
  (Stand 2026-10-01: 66/66 identisch, Python 3.11.2 + Node 22).
