# Aether-Demo (statisch, GitHub Pages)

Interaktive, rein statische Demonstration des Kontrollflusses aus
`aether/planner.py`: Freigabesperre, globale Vetos, Ergebnisprüfung und Pause.

## Herkunft – ausdrücklich kein übernommener Altstand

Diese Demo wurde **neu erstellt**. Der in einer früheren Sitzung lokal
vorbereitete Commit `493daf9` war nicht auffindbar: nicht im Repository, nicht
im Reflog, nicht unter verwaisten Objekten (`git fsck`) und nicht auf GitHub
(`422 No commit found for SHA`). Er wurde nie gepusht und ist nicht
wiederherstellbar. Nichts in diesem Verzeichnis stammt aus diesem Commit.

## Was hier echt ist

`build.py` importiert beim Bauen das echte `aether/planner.py`, führt die
Unit-Tests aus und zeichnet fünf Abläufe Schritt für Schritt auf:

| Ablauf | Zeigt |
|---|---|
| `gate` | `ready()` vor der Freigabe; `nein`, `J`, `yes`, `" j"`, `"j\n"` werden abgelehnt |
| `main` | Der freigegebene Neun-Task-Lauf t0–t8 einschließlich Parallelitätsgruppe p1 |
| `veto` | Offenes Veto blockiert die Freigabe; Override ist keine Freigabe |
| `review` | Abgelehntes Ergebnis blockiert Nachfolger bis zu einer neuen FREI-Prüfung |
| `pause` | `pause()` entzieht die Freigabe; ein neues `j` ist nötig |

Angezeigte Fehler sind die tatsächlich geworfenen Ausnahmen. Die Task-Daten
stammen aus `plan.json`, die eingereichten Ergebnisse aus `result_t*.json`.
`data.js` wird erzeugt und enthält Hashes der Quelldateien.

Der Browser führt **nichts** aus und ruft **nichts** ab: keine Skripte,
Styles, Schriften oder Bilder von Dritten, kein `fetch`, kein Analytics, keine
Cookies, keine Webstorage-Nutzung. `check_offline.py` erzwingt das als
Build-Schritt (Veto-Regel A-03 mechanisch statt als Versprechen).

## Lokal bauen und ansehen

```sh
cd /home/user/SkynetOnCyberCrack
python3 aether/demo/build.py
python3 -m http.server 8000 --directory aether/demo/_site
```

Dann <http://localhost:8000/> öffnen. `data.js` wird als Skript eingebunden,
die Seite funktioniert daher auch direkt aus dem Dateisystem ohne Server.
`aether/demo/_site/` ist erzeugt und steht in `.gitignore`.

## Veröffentlichen

`.github/workflows/demo-pages.yml` führt bei Änderungen an `aether/**` auf
`main` die Tests aus, baut die Seite, prüft sie auf externe Referenzen und
deployt sie über `actions/deploy-pages`. Bei Pull Requests läuft nur die
Verifikation, es wird nichts veröffentlicht.

**Einmalige Voraussetzung, die kein Token und kein Workflow übernehmen kann:**
Das Anlegen einer Pages-Site verlangt Repository-Administrationsrechte
(`Create a GitHub Pages site`: „must be a repository administrator,
maintainer, or have the 'manage GitHub Pages settings' permission"). Ein
`GITHUB_TOKEN` kann `pages: write`, aber nie `administration: write` erhalten.
Deshalb muss ein Administrator einmal **Settings → Pages → Build and
deployment → Source: „GitHub Actions"** wählen. Danach läuft jedes Deployment
automatisch. Kostenfrei, weil das Repository öffentlich ist und die Seite aus
einem öffentlichen Repository stammt.

Öffentliche Adresse nach dem ersten erfolgreichen Deployment:
<https://emborei.github.io/SkynetOnCyberCrack/>

## Grenzen

Die Demo ist eine Visualisierung eines lokalen Bibliotheksprototyps. Sie ist
kein Server, kein Agentensystem und keine Betriebsfreigabe. Die in
`aether/summary.json` und `aether/threat_model.md` dokumentierten Grenzen
gelten unverändert; sie sind auf der Seite selbst ausgewiesen.
