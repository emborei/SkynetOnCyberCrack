"""Paritätsprüfung: aether/planner.py (Python) gegen docs-src/assets/planner.js.

Beide Implementationen erhalten denselben Skript aus Szenario-Schritten
(einschlichlich erwarteter Fehlerfälle). Nach jedem Schritt werden
Rückgabewert bzw. Fehlername und Fehlermeldung verglichen; am Ende werden
die vollständigen Snapshots verglichen. Ein Markerobjekt
{"$float": "nan"} steht auf beiden Seiten für float("nan") / NaN, damit die
strenge JSON-Ablehnung identisch geprüft wird.

Ausführung:  python3 tools/parity_check.py      (benötigt Node.js)
Exit-Code 0 und die Meldung PARITÄT OK bedeuten: alle Schritte identisch.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = str(ROOT)
sys.path.insert(0, str(ROOT / "aether"))

from planner import Planner, validate_plan  # noqa: E402


def sample_plan():
    return [
        {"id": "t0", "title": "Scope", "assignee": "NEXUS", "reason": "Keep human control",
         "depends_on": [], "parallel_group": None},
        {"id": "t1", "title": "Contract", "assignee": "PRISM", "reason": "Define data",
         "depends_on": ["t0"], "parallel_group": "p1"},
        {"id": "t2", "title": "Operations", "assignee": "PULSE", "reason": "Define local operations",
         "depends_on": ["t0"], "parallel_group": "p1"},
        {"id": "t3", "title": "Review", "assignee": "AEGIS", "reason": "Check all results",
         "depends_on": ["t1", "t2"], "parallel_group": None},
    ]


def bad_plans():
    base = sample_plan()
    import copy

    cases = {"empty": [], "too_many": base * 6}
    missing_reason = copy.deepcopy(base)
    missing_reason[0]["reason"] = " "
    cases["blank_reason"] = missing_reason
    bad_role = copy.deepcopy(base)
    bad_role[0]["assignee"] = "UNKNOWN"
    cases["unknown_role"] = bad_role
    missing_dep = copy.deepcopy(base)
    missing_dep[0]["depends_on"] = ["nope"]
    cases["missing_dep"] = missing_dep
    self_dep = copy.deepcopy(base)
    self_dep[0]["depends_on"] = ["t0"]
    cases["self_dep"] = self_dep
    blank_group = copy.deepcopy(base)
    blank_group[0]["parallel_group"] = ""
    cases["blank_group"] = blank_group
    dup_id = copy.deepcopy(base)
    dup_id[1]["id"] = "t0"
    cases["duplicate_id"] = dup_id
    cycle = copy.deepcopy(base)
    cycle[1]["depends_on"] = ["t2"]
    cycle[2]["depends_on"] = ["t1"]
    cases["cycle"] = cycle
    bad_last = copy.deepcopy(base)
    bad_last[-1]["assignee"] = "FORGE"
    cases["last_not_aegis"] = bad_last
    bad_first = copy.deepcopy(base)
    bad_first[0]["id"] = "t9"
    cases["first_not_t0"] = bad_first
    deps_not_list = copy.deepcopy(base)
    deps_not_list[0]["depends_on"] = "t1"
    cases["deps_not_list"] = deps_not_list
    return cases


def steps():
    """(plan, methode, args) – ein "neuer Plan"-Schritt beginnt einen Lauf."""
    s = [["new", "sample", None]]
    s += [
        ["ready", None, None],
        ["approve", None, ["J", "wrong command"]],
        ["approve", None, ["j", ""]],
        ["approve", None, ["j", "Human approval"]],
        ["ready", None, None],
        ["submit", None, ["t2", {"simulated": True}, "too early"]],
        ["submit", None, ["t0", {"simulated": True}, "proposal"]],
        ["ready", None, None],
        ["review", None, ["t1", "FREI", "no result yet"]],
        ["review", None, ["t0", "MAYBE", "invalid status"]],
        ["review", None, ["t0", "FREI", "static example review"]],
        ["review", None, ["t0", "VETO", "immutable retry"]],
        ["ready", None, None],
        ["submit", None, ["t0", {}, "already submitted"]],
        ["veto", None, ["v1", "A-05", "x", "unknown rule"]],
        ["veto", None, ["v1", "A-03", " ", "blank artifact"]],
        ["veto", None, ["v1", "A-03", "example", "human review required"]],
        ["veto", None, ["v1", "A-04", "example", "duplicate id"]],
        ["ready", None, None],
        ["review", None, ["t1", "FREI", "blocked by veto"]],
        ["approve", None, ["j", "veto blocks approval"]],
        ["override", None, ["v1", "missing prefix"]],
        ["override", None, ["override v9", "unknown id"]],
        ["override", None, ["override v1", "human exception"]],
        ["override", None, ["override v1", "repeat"]],
        ["ready", None, None],
        ["submit", None, ["t1", {"value": {"$float": "nan"}}, "not strict json"]],
        ["submit", None, ["t1", {"items": []}, "second proposal"]],
        ["review", None, ["t1", "VETO", "further scrutiny"]],
        ["ready", None, None],
        ["override", None, ["override review-t1-1", "human accepts exception"]],
        ["ready", None, None],
        ["review", None, ["t1", "FREI", "reviewed after human exception"]],
        ["submit", None, ["t2", {"simulated": True}, "ops contract"]],
        ["review", None, ["t2", "FREI", "static review"]],
        ["ready", None, None],
        ["submit", None, ["t3", {"simulated": True}, "final check"]],
        ["review", None, ["t3", "FREI", "all covered"]],
        ["ready", None, None],
        ["snapshot", None, None],
        ["pause", None, [""]],
        ["pause", None, ["human stop"]],
        ["ready", None, None],
        ["approve", None, ["j", "re-approved"]],
        ["snapshot", None, None],
        ["new", "real", None],
        ["ready", None, None],
        ["approve", None, ["j", "demo run"]],
        ["ready", None, None],
        ["submit", None, ["t0", {"simulated": True, "artifacts": ["aether/approval.json"]},
                          "replayed"]],
        ["review", None, ["t0", "FREI", "no runtime authority from j"]],
        ["ready", None, None],
        ["snapshot", None, None],
    ]
    return s


def revive(value):
    """Ersetzt den NaN-Marker durch das echte float-nan."""
    if isinstance(value, list):
        return [revive(v) for v in value]
    if isinstance(value, dict):
        if set(value) == {"$float"}:
            return float("nan")
        return {k: revive(v) for k, v in value.items()}
    return value


def run_python(plans, script):
    from planner import validate_plan as vp  # noqa: F811
    trace = []
    planner = None
    for index, step in enumerate(script):
        method = step[0]
        try:
            if method == "new":
                planner = Planner(json.loads(json.dumps(plans[step[1]])))
                value = "created"
            elif method == "validatePlan":
                vp(plans[step[1]])
                value = "ok"
            else:
                args = revive(step[2]) if step[2] is not None else []
                result = getattr(planner, method)(*args)
                value = result
            trace.append({"step": index, "ok": True, "value": value})
        except Exception as error:  # noqa: BLE001
            trace.append({"step": index, "ok": False,
                          "error": {"name": type(error).__name__, "message": str(error)}})
    return trace


JS_HARNESS = """
"use strict";
const path = require("path");
const { Planner, validatePlan } = require(path.join(REPO_DIR, "docs-src", "assets", "planner.js"));
const scenario = JSON.parse(process.argv[2]);

function revive(value) {
  if (Array.isArray(value)) return value.map(revive);
  if (value && typeof value === "object") {
    const keys = Object.keys(value);
    if (keys.length === 1 && keys[0] === "$float") {
      return value.$float === "nan" ? NaN : Number(value.$float);
    }
    const out = {};
    for (const key of keys) out[key] = revive(value[key]);
    return out;
  }
  return value;
}

const trace = [];
let planner = null;
scenario.script.forEach((step, index) => {
  const entry = { step: index };
  try {
    let value;
    if (step[0] === "new") {
      planner = new Planner(revive(JSON.parse(JSON.stringify(scenario.plans[step[1]]))));
      value = "created";
    } else if (step[0] === "validatePlan") {
      validatePlan(revive(JSON.parse(JSON.stringify(scenario.plans[step[1]]))));
      value = "ok";
    } else {
      const args = step[2] === null ? [] : revive(step[2]);
      value = planner[step[0]](...args);
    }
    entry.ok = true;
    entry.value = value === undefined ? null : JSON.parse(JSON.stringify(value));
  } catch (error) {
    entry.ok = false;
    entry.error = { name: error.name, message: error.message };
  }
  trace.push(entry);
});
process.stdout.write(JSON.stringify(trace));
"""


def run_js(plans, script):
    scenario = json.dumps({"plans": plans, "script": script})
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as handle:
        handle.write(JS_HARNESS.replace("REPO_DIR", json.dumps(REPO)))
        harness = handle.name
    try:
        result = subprocess.run(
            ["node", harness, scenario], capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise SystemExit("Node-Harness fehlgeschlagen:\n" + result.stderr)
        return json.loads(result.stdout)
    finally:
        Path(harness).unlink(missing_ok=True)


def main():
    plans = {
        "sample": sample_plan(),
        "real": json.loads((ROOT / "aether" / "plan.json").read_text(encoding="utf-8")),
    }
    script = steps()
    bad = bad_plans()
    for name, plan in bad.items():
        script.append(["validatePlan", name, None])
    plans.update(bad)

    py = run_python(plans, script)
    js = run_js(plans, script)

    py_norm = json.dumps(py, sort_keys=True, ensure_ascii=False)
    js_norm = json.dumps(js, sort_keys=True, ensure_ascii=False)
    if py_norm == js_norm:
        errors = sum(1 for entry in py if not entry["ok"])
        print(f"PARITÄT OK | {len(script)} Schritte identisch "
              f"({len(script) - errors} erfolgreiche, {errors} korrekte Fehlerabweisungen)")
        return 0

    mismatch = 0
    for left, right in zip(py, js):
        if json.dumps(left, sort_keys=True) != json.dumps(right, sort_keys=True):
            mismatch += 1
            print(f"SCHRITT {left['step']} ABWEICHEND")
            print("  python:", json.dumps(left, ensure_ascii=False))
            print("  js    :", json.dumps(right, ensure_ascii=False))
            if mismatch > 5:
                break
    print(f"PARITÄT FEHLGESCHLAGEN ({mismatch} Abweichungen)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
