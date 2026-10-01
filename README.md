# SkynetOnCyberCrack

Enthält **Aether**, einen lokalen, prüfbaren Kontrollfluss-Prototypen unter
[`aether/`](aether/), und eine statische Demonstration davon unter
[`aether/demo/`](aether/demo/).

## Demo

**Öffentlich:** <https://emborei.github.io/SkynetOnCyberCrack/>

Die Seite replayt echte Abläufe von `aether/planner.py` – Freigabesperre,
globale Vetos, Ergebnisprüfung und Pause – Schritt für Schritt, einschließlich
der tatsächlich geworfenen Ausnahmen. Fünf Abläufe mit 57 Schritten werden beim
Bauen der Seite durch die reale Bibliothek erzeugt; angezeigte Fehler sind
keine nachgestellten Meldungen.

Sie ist vollständig statisch: keine Cookies, kein Analytics, keine Schriften
oder Bibliotheken von Dritten, kein einziger Netzwerkaufruf aus dem Browser.
Kostenfrei gehostet auf GitHub Pages aus einem öffentlichen Repository.

Lokal bauen und ansehen:

```sh
python3 aether/demo/build.py
python3 -m http.server 8000 --directory aether/demo/_site
```

Der Build führt die Unit-Tests aus und bricht ab, wenn sie fehlschlagen; aus
einem roten Build wird nichts veröffentlicht. Zusätzlich prüft er, dass die
Seite keine externe Referenz lädt (`check_offline.py`, Veto-Regel A-03) und dass
`app.js` keine Element-ID anspricht, die `index.html` nicht definiert.

## Verifikationsstand

`aether/summary.json` und `aether/final_review.json` dokumentieren den ersten
Erstellungsdurchlauf, in dem Code und Tests ausdrücklich **nicht** ausgeführt
wurden. Diese Grenze ist inzwischen geschlossen: die 12 Unittest-Methoden aus
`aether/test_planner.py` werden lokal und in jedem CI-Lauf ausgeführt und
bestehen. Die historischen Artefakte wurden dabei nicht nachträglich verändert –
sie beschreiben weiterhin zutreffend ihren eigenen Durchlauf.

Unverändert gültig bleiben die dokumentierten Einschränkungen: keine
unabhängigen Agentenprozesse, keine echten Modellaufrufe, keine Sandbox oder
Authentifizierung, kein Produktionsbetrieb.

## Herkunft der Demo

Die Demo ist ein **Neubau** dieser Sitzung. Ein in einer früheren Sitzung lokal
vorbereiteter Commit `493daf9` war nicht auffindbar – nicht im Repository, im
Reflog, unter verwaisten Objekten (`git fsck`) oder auf GitHub
(`422 No commit found for SHA`) – und ist nicht wiederherstellbar. Kein Teil
dieser Demo stammt aus ihm.
