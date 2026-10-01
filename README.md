# SkynetOnCyberCrack

Sammelrepository für den Prototyp **Aether** (*Autonomous Entity for Human-Aligned
Enterprise Realization*): ein streng lokal gehaltener, menschlich kontrollierter
Kontrollfluss für Planung, Freigabe, Vetos und Ergebnisprüfung.

> **Ehrlicher Status:** Es existiert ein validierbarer Prototyp-Baukasten mit
> dokumentierten Grenzen — kein laufendes Unternehmen, keine autonomen Agenten,
> keine Modellläufe, keine Produktionsfreigabe.

## Struktur

| Pfad | Inhalt |
| --- | --- |
| `aether/` | Geprüfter Prototyp: Rollen, Plan, Datenverträge, `planner.py`, Tests, Artefakte des ersten Laufs |
| `demo/` | Deterministische End-to-End-Demo, die die echten Gates von `aether/planner.py` durchspielt |
| `docs-src/` | Quelltext der statischen Seite (inkl. getreuer Browser-Port des Planners) |
| `docs/` | Gebaute, statische GitHub-Pages-Seite (keine externen Ressourcen, kein Tracking) |
| `tools/` | `build_site.py` (Seitenbau), `parity_check.py` (Python↔JS-Paritätsbeweis) |
| `.github/workflows/pages.yml` | Optionaler Pages-Deploy aus `docs/` bei Merge nach `main` |

## Schnellstart (Python 3.9+, nur Standardbibliothek)

```sh
# 1) Unit-Tests der Bibliothek
cd aether && python3 -m unittest discover -s . -p 'test_*.py' -v && cd ..

# 2) Skriptierte Demo der Gates (Freigabe, Veto, Override, Pause)
python3 demo/run_demo.py

# 3) Parität Python-Original ↔ Browser-Port (benötigt Node.js)
python3 tools/parity_check.py

# 4) Statische Seite bauen (schreibt ausschließlich docs/)
python3 tools/build_site.py
```

Die fertige Seite liegt unter `docs/` und lässt sich ohne Webserver direkt öffnen
(`docs/index.html`); `docs/demo.html` funktioniert vollständig offline. Nach einem
Merge nach `main` deployt der Workflow die Seite optional auf GitHub Pages.

## Verifikationsstand

- 2026-10-01, Sandbox-Lauf (Python 3.11.2): **12/12 Unit-Tests bestanden**
  (`aether/test_planner.py`, unverändert seit PR #1).
- 2026-10-01: **Paritätsprüfung bestanden** — 66/66 Schritte inkl. 34
  Fehlerabweisungen identisch zwischen `aether/planner.py` und dem Browser-Port.
- Die Transkripte der Seitenbau-Läufe sind in `docs/doku/transcript.html` eingebettet.

Diese Ergebnisse belegen Verhalten der getesteten API in einer Sandbox. Sie sind
keine Abnahme, kein Sicherheitsnachweis und keine Betriebsfreigabe — die
[Vertrauensgrenze](aether/threat_model.md) bleibt: Die API unterscheidet nicht
technisch zwischen Menschen und Agenten.

## Leitplanke

> Maximiere Nutzen und Autonomie für den einzelnen Menschen,
> minimiere die Möglichkeit, dass das System selbst zu einem neuen Macht- und
> Ausbeutungsinstrument wird.

Freigabe erfolgt ausschließlich durch ein menschliches `j`; offene Vetos blockieren
global; nur `override <ID>` durch den Menschen hebt ein konkretes Veto auf. Details
in [`aether/goal.md`](aether/goal.md) und [`aether/contracts.md`](aether/contracts.md).
