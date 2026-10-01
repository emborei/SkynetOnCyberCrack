#!/usr/bin/env python3
"""Build the static Aether demo site from the real repository artifacts.

Standard library only. No network access, no telemetry, no analytics, no
third-party asset and no paid service.

Every control-flow trace shipped with the site is produced by importing and
executing ``aether/planner.py`` here, at build time. The published page
therefore replays real library behaviour instead of hand-written examples,
and the build aborts when the unit tests do not pass.

Usage:
    python3 aether/demo/build.py [--out DIR] [--skip-tests]
"""

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent            # aether/demo
AETHER = HERE.parent                              # aether
SITE = HERE / "_site"

STATIC_FILES = ("index.html", "styles.css", "app.js")
TASK_RESULT_GLOB = "result_t*.json"

# The library under demonstration. Imported from the real source tree so the
# traces cannot drift from a copy.
sys.path.insert(0, str(AETHER))
from planner import Planner  # noqa: E402  (path setup must run first)


# --------------------------------------------------------------------------
# artifact loading
# --------------------------------------------------------------------------

def read_json(path):
    """Return parsed JSON, or None when the artifact is absent."""
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path):
    return path.read_text(encoding="utf-8") if path.exists() else None


def digest(path):
    """Short content hash so a reader can tell which source was published."""
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def load_results():
    """Map task id -> result artifact, keyed by the artifact's own task_id."""
    results = {}
    for path in sorted(AETHER.glob(TASK_RESULT_GLOB)):
        data = read_json(path)
        if isinstance(data, dict) and isinstance(data.get("task_id"), str):
            data = dict(data)
            data["artifact"] = f"aether/{path.name}"
            results[data["task_id"]] = data
    return results


ROLE_HEADING = re.compile(r"^##\s+([A-Z]+)\s+[—-]\s+(.+?)\s*$")


def load_roles():
    """Parse the five role definitions out of aether/agents.md."""
    text = read_text(AETHER / "agents.md")
    if not text:
        return []
    roles = []
    current = None
    for line in text.splitlines():
        match = ROLE_HEADING.match(line)
        if match:
            current = {
                "id": match.group(1),
                "subtitle": match.group(2).strip(),
                "paragraphs": [],
            }
            roles.append(current)
            continue
        if line.startswith("## "):
            current = None
            continue
        if current is not None:
            stripped = line.strip()
            if stripped.startswith("- "):
                # The binding framework section lists decisions, not a role.
                continue
            if stripped:
                current["paragraphs"].append(stripped)
    for role in roles:
        role["description"] = " ".join(role["paragraphs"][:2])
        del role["paragraphs"]
    return roles


def load_veto_rules():
    """Parse the acceptance table of aether/threat_model.md."""
    text = read_text(AETHER / "threat_model.md")
    if not text:
        return []
    rules = []
    for line in text.splitlines():
        if not line.startswith("| A-"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 3:
            rules.append({"rule": cells[0], "check": cells[1], "limit": cells[2]})
    return rules


def load_run_log():
    """Parse aether/run.log into structured, attributable entries."""
    text = read_text(AETHER / "run.log")
    if not text:
        return []
    entries = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) >= 4:
            entries.append({
                "role": parts[0],
                "scope": parts[1],
                "decision": parts[2],
                "reason": parts[3],
            })
    return entries


# --------------------------------------------------------------------------
# real verification: execute the unit tests during the build
# --------------------------------------------------------------------------

def run_tests():
    """Execute aether/test_planner.py and return a machine-readable report."""
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(AETHER), pattern="test_*.py")
    stream = _Tee(sys.stdout)
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    return {
        "command": "python3 -m unittest discover -s aether -p 'test_*.py' -v",
        "methods_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "ok": result.wasSuccessful(),
        "executed_at": now(),
        "log": stream.tail(400),
    }


class _Tee:
    """Capture test output for the report while still printing it to the log."""

    def __init__(self, stream):
        self._stream = stream
        self._buffer = []

    def write(self, text):
        self._stream.write(text)
        self._buffer.append(text)

    def flush(self):
        self._stream.flush()

    def tail(self, limit):
        return "".join(self._buffer)[-limit:]


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------
# scenario traces: real planner.py executions, recorded step by step
# --------------------------------------------------------------------------

def ready_ids(planner):
    return [task["id"] for task in planner.ready()]


class Trace:
    """Record a real planner run as a replayable list of steps."""

    def __init__(self, planner, key, title, claim):
        self.planner = planner
        self.key = key
        self.title = title
        self.claim = claim
        self.steps = []
        self._seen_events = 0

    def _state(self):
        snapshot = self.planner.snapshot()
        ready = None
        ready_error = None
        try:
            ready = ready_ids(self.planner)
        except Exception as exc:                      # noqa: BLE001 - reported
            ready_error = {"type": type(exc).__name__, "message": str(exc)}
        events = snapshot["events"]
        fresh = events[self._seen_events:]
        self._seen_events = len(events)
        reviews = snapshot["reviews"]
        return {
            "approved": snapshot["approved"],
            "ready": ready,
            "ready_error": ready_error,
            "submitted": sorted(snapshot["results"]),
            "accepted": sorted(k for k, v in reviews.items() if v["status"] == "FREI"),
            "rejected": sorted(k for k, v in reviews.items() if v["status"] != "FREI"),
            "vetos": [
                {"id": veto_id, "rule": v["rule"], "artifact": v["artifact"],
                 "reason": v["reason"], "overridden": v["overridden"],
                 "override_hint": v["override_hint"]}
                for veto_id, v in snapshot["vetos"].items()
            ],
            "open_vetos": [vid for vid, v in snapshot["vetos"].items()
                           if not v["overridden"]],
            "new_events": fresh,
            "event_count": len(events),
        }

    def step(self, label, actor, call, action, note=None):
        """Run one real API call and record outcome plus resulting state."""
        outcome = {"status": "ok"}
        try:
            value = action()
            if value is not None:
                outcome["value"] = value
        except Exception as exc:                      # noqa: BLE001 - reported
            outcome = {"status": "error", "type": type(exc).__name__,
                       "message": str(exc)}
        entry = {
            "index": len(self.steps),
            "label": label,
            "actor": actor,
            "call": call,
            "outcome": outcome,
            "state": self._state(),
        }
        if note:
            entry["note"] = note
        self.steps.append(entry)

    def as_dict(self):
        return {
            "key": self.key,
            "title": self.title,
            "claim": self.claim,
            "steps": self.steps,
            "step_count": len(self.steps),
        }

    def complete(self, task_id, results, status="FREI", reason=None):
        """Submit a real result artifact and let AEGIS review it."""
        artifact = results.get(task_id, {})
        self.step(
            f"Ergebnis {task_id} einreichen", artifact.get("assignee") or "ROLLE",
            f'planner.submit("{task_id}", output, explanation)',
            lambda: self.planner.submit(
                task_id,
                artifact.get("output", []),
                artifact.get("explanation", "Ergebnisartefakt aus dem Repository"),
            ),
        )
        review = artifact.get("aegis_review") or {}
        self.step(
            f"Ergebnis {task_id} prüfen: {status}", "AEGIS",
            f'planner.review("{task_id}", "{status}", reason)',
            lambda: self.planner.review(
                task_id, status, reason or review.get("reason", "Statische Prüfung"),
            ),
        )


def scenario_gate(plan):
    """Approval is a gate: nothing is ready before an exact human 'j'."""
    trace = Trace(
        Planner(plan), "gate", "Sperre vor der Freigabe",
        "Ohne exaktes menschliches 'j' liefert ready() einen Fehler. "
        "Ähnliche Befehle werden nicht akzeptiert.",
    )
    trace.step("Bereitschaft ohne Freigabe abfragen", "SYSTEM", "planner.ready()",
               lambda: ready_ids(trace.planner))
    for command in ("nein", "J", "yes", " j", "j\n"):
        trace.step(
            "Freigabe mit unzulässigem Befehl", "HUMAN",
            f"planner.approve({command!r}, reason)",
            lambda command=command: trace.planner.approve(
                command, "Versuch ohne das exakte menschliche Kommando"),
            note="Nur die exakte Zeichenfolge 'j' wird akzeptiert.",
        )
    trace.step("Bereitschaft weiterhin abfragen", "SYSTEM", "planner.ready()",
               lambda: ready_ids(trace.planner))
    return trace


def scenario_main(plan, results):
    """The approved nine-task run, including the real parallel group."""
    trace = Trace(
        Planner(plan), "main", "Freigegebener Neun-Task-Lauf",
        "Nach dem 'j' wird t0 bereit. Abhängigkeiten und die "
        "Parallelitätsgruppe p1 steuern, was als Nächstes folgt.",
    )
    trace.step("Plan validieren und Instanz erzeugen", "SYSTEM",
               "Planner(plan.json)",
               lambda: f"{len(plan)} Tasks validiert (A-01: max. 20)")
    trace.step("Freigabe durch den Menschen", "HUMAN",
               'planner.approve("j", reason)',
               lambda: trace.planner.approve(
                   "j", "Menschliche Zustimmung im Dialog, begrenzt auf Artefakte"))
    for task in plan:
        trace.complete(task["id"], results)
    trace.step("Abschluss: Bereitschaft nach t8", "SYSTEM", "planner.ready()",
               lambda: ready_ids(trace.planner))
    return trace


def scenario_veto(plan):
    """An open veto blocks everything; an override is not an approval."""
    trace = Trace(
        Planner(plan), "veto", "Veto blockiert, Override ist keine Freigabe",
        "Ein offenes Veto sperrt auch die Freigabe. Ein Override hebt nur "
        "dieses Veto auf - die Freigabe bleibt ein eigener Schritt.",
    )
    trace.step("Globales Veto vor jeder Freigabe", "AEGIS",
               'planner.veto("v-demo", "A-03", artifact, reason)',
               lambda: trace.planner.veto(
                   "v-demo", "A-03", "aether/demo",
                   "Semantische A-03-Prüfung muss ein Mensch übernehmen"))
    trace.step("Freigabe trotz offenem Veto", "HUMAN",
               'planner.approve("j", reason)',
               lambda: trace.planner.approve("j", "Versuch trotz offenem Veto"))
    trace.step("Override mit unbekannter ID", "HUMAN",
               'planner.override("override v-falsch", reason)',
               lambda: trace.planner.override("override v-falsch", "Unbekannte ID"))
    trace.step("Override der konkreten ID", "HUMAN",
               'planner.override("override v-demo", reason)',
               lambda: trace.planner.override(
                   "override v-demo",
                   "Mensch übernimmt ausdrücklich die Verantwortung"))
    trace.step("Bereitschaft nach Override ohne Freigabe", "SYSTEM",
               "planner.ready()", lambda: ready_ids(trace.planner),
               note="Der Override hat den Plan nicht freigegeben.")
    trace.step("Freigabe erneut erteilen", "HUMAN",
               'planner.approve("j", reason)',
               lambda: trace.planner.approve("j", "Freigabe nach aufgehobenem Veto"))
    trace.step("Bereitschaft nach Freigabe", "SYSTEM", "planner.ready()",
               lambda: ready_ids(trace.planner))
    return trace


def scenario_review(plan, results):
    """A rejected result keeps its successors blocked until a new FREI."""
    trace = Trace(
        Planner(plan), "review", "Abgelehntes Ergebnis blockiert Nachfolger",
        "Ein VETO im Review erzeugt ein globales Veto. Auch nach dessen "
        "Override bleibt die Abhängigkeit unerfüllt, bis neu FREI geprüft wird.",
    )
    trace.step("Freigabe durch den Menschen", "HUMAN",
               'planner.approve("j", reason)',
               lambda: trace.planner.approve("j", "Begrenzter Artefaktlauf"))
    trace.complete("t0", results)
    artifact = results.get("t1", {})
    trace.step("Ergebnis t1 einreichen", "PRISM",
               'planner.submit("t1", output, explanation)',
               lambda: trace.planner.submit(
                   "t1", artifact.get("output", []),
                   artifact.get("explanation", "Ergebnisartefakt")))
    trace.step("Ergebnis t1 ablehnen", "AEGIS",
               'planner.review("t1", "VETO", reason)',
               lambda: trace.planner.review(
                   "t1", "VETO", "Beispielhafte Ablehnung zur Demonstration der Sperre"))
    trace.step("Bereitschaft bei offenem Veto", "SYSTEM", "planner.ready()",
               lambda: ready_ids(trace.planner))
    trace.step("Veto durch Menschen aufheben", "HUMAN",
               'planner.override("override review-t1-1", reason)',
               lambda: trace.planner.override(
                   "override review-t1-1", "Mensch akzeptiert die Ausnahme"))
    trace.step("Bereitschaft nach Override", "SYSTEM", "planner.ready()",
               lambda: ready_ids(trace.planner),
               note="t1 bleibt ohne FREI; t4 hängt weiter an t1.")
    trace.complete("t2", results)
    trace.complete("t3", results)
    trace.step("Bereitschaft vor neuer Prüfung von t1", "SYSTEM",
               "planner.ready()", lambda: ready_ids(trace.planner),
               note="t4 ist blockiert, obwohl t2 und t3 FREI sind.")
    trace.step("Ergebnis t1 neu prüfen", "AEGIS",
               'planner.review("t1", "FREI", reason)',
               lambda: trace.planner.review(
                   "t1", "FREI", "Neue Prüfung nach behobener Beanstandung"))
    trace.step("Bereitschaft nach neuer FREI-Prüfung", "SYSTEM",
               "planner.ready()", lambda: ready_ids(trace.planner))
    return trace


def scenario_pause(plan, results):
    """Pause withdraws approval; a new 'j' is required."""
    trace = Trace(
        Planner(plan), "pause", "Pause entzieht die Freigabe",
        "pause() setzt die Freigabe zurück. Fortschritt erfordert ein neues "
        "menschliches 'j' - es gibt keinen automatischen Wiederanlauf.",
    )
    trace.step("Freigabe durch den Menschen", "HUMAN",
               'planner.approve("j", reason)',
               lambda: trace.planner.approve("j", "Begrenzter Artefaktlauf"))
    trace.complete("t0", results)
    trace.step("Pause auslösen", "PULSE", "planner.pause(reason)",
               lambda: trace.planner.pause("Verantwortlicher Mensch beendet die Sitzung"))
    trace.step("Bereitschaft nach der Pause", "SYSTEM", "planner.ready()",
               lambda: ready_ids(trace.planner))
    trace.step("Freigabe erneut erteilen", "HUMAN",
               'planner.approve("j", reason)',
               lambda: trace.planner.approve("j", "Neue Sitzung, neue Freigabe"))
    trace.step("Bereitschaft nach neuer Freigabe", "SYSTEM", "planner.ready()",
               lambda: ready_ids(trace.planner))
    return trace


def build_scenarios(plan, results):
    builders = (scenario_gate, scenario_main, scenario_veto, scenario_review,
                scenario_pause)
    traces = []
    for builder in builders:
        if builder in (scenario_gate, scenario_veto):
            traces.append(builder(plan))
        else:
            traces.append(builder(plan, results))
    return [trace.as_dict() for trace in traces]


# --------------------------------------------------------------------------
# site assembly
# --------------------------------------------------------------------------

def provenance(tests):
    return {
        "generated_at": now(),
        "generator": "aether/demo/build.py",
        "python_version": platform.python_version(),
        "source_commit": os.environ.get("GITHUB_SHA"),
        "source_ref": os.environ.get("GITHUB_REF_NAME"),
        "build_host": "GitHub Actions" if os.environ.get("GITHUB_ACTIONS") else "local",
        "integrity": {
            "aether/planner.py": digest(AETHER / "planner.py"),
            "aether/plan.json": digest(AETHER / "plan.json"),
            "aether/test_planner.py": digest(AETHER / "test_planner.py"),
        },
        "tests": tests,
        "rebuild_note": (
            "Diese Demo wurde in der aktuellen Sitzung neu erstellt. Der in der "
            "vorherigen Sitzung lokal vorbereitete Commit 493daf9 war weder im "
            "Repository, im Reflog, unter verwaisten Objekten noch auf GitHub "
            "auffindbar und ist nicht wiederherstellbar. Nichts hier stammt aus "
            "diesem Commit."
        ),
    }


def collect(skip_tests):
    plan = read_json(AETHER / "plan.json")
    if not isinstance(plan, list) or not plan:
        raise SystemExit("aether/plan.json fehlt oder ist keine Task-Liste")

    # Attach the assignee to each result so traces can attribute steps.
    results = load_results()
    assignees = {task["id"]: task["assignee"] for task in plan}
    for task_id, artifact in results.items():
        artifact["assignee"] = assignees.get(task_id)

    tests = ({"ok": None, "methods_run": 0, "failures": 0, "errors": 0,
              "skipped": 0, "command": "übersprungen", "executed_at": now(),
              "log": ""} if skip_tests else run_tests())

    summary = read_json(AETHER / "summary.json") or {}
    final_review = read_json(AETHER / "final_review.json") or {}
    plan_review = read_json(AETHER / "plan_review.json") or {}

    return {
        "meta": provenance(tests),
        "plan": plan,
        "results": results,
        "roles": load_roles(),
        "veto_rules": load_veto_rules(),
        "run_log": load_run_log(),
        "approval": read_json(AETHER / "approval.json") or {},
        "plan_review_checks": plan_review.get("checks", []),
        "final_review": {
            "status": final_review.get("status"),
            "reviewer": final_review.get("reviewer"),
            "decision": final_review.get("decision"),
            "reason": final_review.get("reason"),
            "checks": final_review.get("checks", []),
            "verification": final_review.get("verification", {}),
            "remaining_risks": final_review.get("remaining_risks", []),
        },
        "summary": {
            "status": summary.get("status"),
            "decision": summary.get("decision"),
            "reason": summary.get("reason"),
            "implemented": summary.get("implemented", []),
            "limitations": summary.get("limitations", []),
            "next_human_decisions": summary.get("next_human_decisions", []),
        },
        "scenarios": build_scenarios(plan, results),
    }


def escape_for_script(payload):
    """Serialize so that no artifact text can terminate the <script> element."""
    return json.dumps(payload, ensure_ascii=False, indent=2).replace("</", "<\\/")


ID_REFERENCE = re.compile(r"""(?:getElementById|fill)\(\s*["']([^"']+)["']\s*\)""")
HTML_ID = re.compile(r"""\bid\s*=\s*["']([^"']+)["']""")
LOCAL_ASSET = re.compile(r"""(?:\bsrc|\bhref)\s*=\s*["']([^"'#][^"']*)["']""")


def verify_site(out):
    """Validate the generated site against its own contract, stdlib only.

    Catches the silent breakage a static page cannot report by itself: app.js
    addressing an element id that index.html does not define, or index.html
    referencing a local file that was never written.
    """
    html = read_text(Path(out) / "index.html") or ""
    app = read_text(Path(out) / "app.js") or ""

    defined = set(HTML_ID.findall(html))
    referenced = set(ID_REFERENCE.findall(app))
    missing_ids = sorted(referenced - defined)
    if missing_ids:
        raise SystemExit("ABORT: app.js references unknown element ids: "
                         + ", ".join(missing_ids))

    external = [a for a in LOCAL_ASSET.findall(html)
                if a.startswith(("http://", "https://", "//"))]
    if external:
        raise SystemExit("ABORT: index.html must not reference remote assets: "
                         + ", ".join(external))
    unresolved = sorted(a for a in LOCAL_ASSET.findall(html)
                        if not (Path(out) / a).exists())
    if unresolved:
        raise SystemExit("ABORT: index.html references missing local files: "
                         + ", ".join(unresolved))

    return {"element_ids_checked": len(referenced),
            "local_assets": sorted(LOCAL_ASSET.findall(html))}



def write_site(data, out_dir):
    out = Path(out_dir)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    for name in STATIC_FILES:
        source = HERE / name
        if not source.exists():
            raise SystemExit(f"Statische Datei fehlt: {source}")
        shutil.copyfile(source, out / name)

    body = escape_for_script(data)
    (out / "data.js").write_text(
        "// Generated by aether/demo/build.py - do not edit by hand.\n"
        f"// Built {data['meta']['generated_at']} from real repository artifacts.\n"
        f"window.AETHER_DEMO = {body};\n",
        encoding="utf-8",
    )
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(SITE),
                        help="output directory (default: aether/demo/_site)")
    parser.add_argument("--skip-tests", action="store_true",
                        help="do not execute the unit tests during the build")
    args = parser.parse_args(argv)

    print("== Aether demo build ==")
    data = collect(args.skip_tests)

    tests = data["meta"]["tests"]
    print(f"tests: {tests['methods_run']} run, {tests['failures']} failures, "
          f"{tests['errors']} errors -> ok={tests['ok']}")
    if tests["ok"] is False:
        print("ABORT: unit tests failed; nothing is published from a red build.",
              file=sys.stderr)
        return 1

    steps = sum(s["step_count"] for s in data["scenarios"])
    print(f"scenarios: {len(data['scenarios'])} traced, {steps} real planner steps")

    out = write_site(data, args.out)
    contract = verify_site(out)
    print(f"site: {out} ({len(list(out.iterdir()))} files)")
    print(f"contract: {contract['element_ids_checked']} element ids resolved, "
          f"local assets: {', '.join(contract['local_assets'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
