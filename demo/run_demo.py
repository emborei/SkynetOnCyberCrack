"""Deterministische End-to-End-Demo des lokalen Aether-Kontrollflusses.

Diese Datei führt die echte Bibliothek `aether/planner.py` mit dem geprüften
Neun-Task-Plan (`aether/plan.json`) durch eine skriptierte Sequenz:

1. Blocker vor der Freigabe (ready, unexaktes Kommando),
2. menschliche Freigabe mit exakt „j“,
3. Ablauf aller Tasks mit simulierten Ergebnissen und FREI-Prüfungen,
4. ein demonstrativer AEGIS-Veto (VETO-Prüfung von t5), globale Sperre,
   menschliches „override <ID>“ und erneute Prüfung,
5. Pause und erneute Freigabe,
6. Abschlusskontrolle über snapshot().

Alle Task-Ergebnisse sind eindeutig als simuliert markiert. Es werden keine
Modelle, Worker, Netzwerke oder Unternehmen gestartet. Keine Zeitstempel:
Die Ausgabe ist deterministisch und wird von tools/build_site.py als
Transkript für die GitHub-Pages-Demo eingefangen.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "aether"))

from planner import Planner, validate_plan  # noqa: E402


def load_plan():
    return json.loads((ROOT / "aether" / "plan.json").read_text(encoding="utf-8"))


def simulated_result(task_id):
    """Ergebnisdaten als Rekonstruktion des ersten Laufs, klar simuliert."""
    path = ROOT / "aether" / f"result_{task_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "simulated": True,
        "executed": False,
        "replay_of": f"aether/result_{task_id}.json",
        "output": data["output"],
        "decision": data.get("decision", "Simulierter Demo-Eintrag"),
        "reason": data.get("reason", "Nur Demonstrationszwecke im lokalen Script."),
    }


def review_note(task_id):
    path = ROOT / "aether" / f"result_{task_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("aegis_review", {}).get(
        "reason", "Statische Demo-Prüfung; kein Modelllauf."
    )


def show(*args):
    print(" ".join(str(a) for a in args))


def task_line(task):
    deps = ", ".join(task["depends_on"]) or "keine"
    group = task["parallel_group"] or "—"
    return f'{task["id"]} [{task["assignee"]:5s}] deps={deps:10s} parallel_group={group}'


def expect_blocked(label, action):
    try:
        action()
    except (PermissionError, ValueError) as error:
        show(f"  {label} -> {type(error).__name__}: {error}  (erwartet und korrekt abgewiesen)")
        return
    raise SystemExit(f"DEMO FAILED: {label} hätte blockieren müssen, tat es aber nicht.")


def main():
    show("=" * 78)
    show("Aether-Kontrollfluss-Demo  |  echte Bibliothek aether/planner.py")
    show("Alle Task-Ergebnisse sind simuliert (simulated=true, executed=false).")
    show("=" * 78)
    show()

    plan = load_plan()
    validate_plan(plan)
    show(f"[0] Planvalidierung: {len(plan)} Tasks, Regel A-01 (max. 20) eingehalten.")
    for task in plan:
        show(f"    {task_line(task)}")
    show()

    planner = Planner(plan)

    show("[1] Blocker ohne menschliche Freigabe")
    expect_blocked("ready() vor approve", planner.ready)
    for command in ("J", "ja", " j"):
        expect_blocked(f'approve("{command}")', lambda c=command: planner.approve(c, "Demo"))
    show()

    show('[2] Menschliche Freigabe mit exakt "j"')
    planner.approve("j", "Demo im Sandbox-Umfeld; keine Produktions- oder Betriebsfreigabe.")
    ready = planner.ready()
    show("    Freigabe erteilt. Bereitschaftsliste:", [t["id"] for t in ready])
    show()

    show("[3] Regelablauf: Aufgabe abgeben, Ergebnis prüfen, Abhängigkeit erfüllen")
    rejected_once = False
    while True:
        ready = planner.ready()
        if not ready:
            break
        if not rejected_once and any(t["id"] == "t5" for t in ready):
            show('    --- demonstrativer AEGIS-Veto gegen "t5" (Regel A-04) ---')
            planner.submit("t5", simulated_result("t5"), "Demo-Eintrag vor bewusster Ablehnung")
            planner.review("t5", "VETO", "Demo: Prüfer lehnt ab; ein VETO blockiert global.")
            expect_blocked("ready() mit offenem Veto", planner.ready)
            planner.override("override review-t5-1", "Demo: Mensch hebt genau dieses Veto auf.")
            show("    override review-t5-1 akzeptiert; die Sperre ist weg, t5 fehlt aber weiter.")
            expect_blocked("erneuter override von review-t5-1",
                           lambda: planner.override("override review-t5-1", "Wiederholung"))
            planner.review("t5", "FREI", "Demo: zweite Prüfung nach menschlichem Override bestanden.")
            show("    t5 jetzt FREI geprüft. Hinweis: Ein Override ersetzt nie die FREI-Prüfung.")
            rejected_once = True
            continue
        task = ready[0]
        task_id = task["id"]
        extras = [t["id"] for t in ready[1:]]
        note = f" (zurückgestellt: {', '.join(extras)})" if extras else ""
        show(f"    {task_id}: Ergebnis abgegeben{note}")
        planner.submit(task_id, simulated_result(task_id), "Demo-Eintrag; repliziert result_"
                       f"{task_id}.json als simulierte Ausgabe")
        planner.review(task_id, "FREI", review_note(task_id))
        show(f"    {task_id}: AEGIS-Prüfung FREI -> Abhängigkeit erfüllt")
    show("    Alle neun Tasks sind FREI geprüft; die Bereitschaftsliste ist leer.")
    show()

    show("[4] Pause ist jederzeit möglich und erfordert neue Freigabe")
    planner.pause("Demo: menschlicher Stopp.")
    expect_blocked("ready() nach pause", planner.ready)
    planner.approve("j", "Demo: erneute Freigabe nach Pause.")
    show("    Nach erneuter Freigabe bleibt ready() leer (alles erledigt):", planner.ready())
    show()

    snapshot = planner.snapshot()
    show("[5] Abschlusskontrolle (snapshot, In-Memory-Audit)")
    show(f"    approved={snapshot['approved']}  results={len(snapshot['results'])}  "
         f"reviews={len(snapshot['reviews'])}  events={len(snapshot['events'])}")
    open_vetos = [v for v in snapshot["vetos"].values() if not v["overridden"]]
    show(f"    offene Vetos: {len(open_vetos)}  (Demo-Veto wurde vom Menschen overridden)")
    show()

    all_free = (
        set(snapshot["results"]) == {t["id"] for t in plan}
        and all(r["status"] == "FREI" for r in snapshot["reviews"].values())
        and snapshot["approved"]
        and not open_vetos
    )
    if not all_free:
        raise SystemExit("DEMO FAILED: Abschlusszustand unerwartet.")
    show("=" * 78)
    show("DEMO OK  |  Freigabe-, Veto- und Prüfsperren haben wie spezifiziert gearbeitet.")
    show("Dies ist kein Laufzeitbeweis für Produktionsfähigkeit und keine Abnahme.")
    show("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
