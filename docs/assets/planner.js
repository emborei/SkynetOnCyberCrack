/*
 * Aether Planner — Browser-Port von aether/planner.py (Demonstration).
 *
 * Bewusst identische Semantik und identische Fehlermeldungen wie das
 * Python-Original; tools/parity_check.py vergleicht beide Implementationen
 * Schritt für Schritt. Dies ist eine didaktische Nachbildung, keine
 * Sicherheitsgrenze und keine zweite Autoritätsquelle: massgeblich bleibt
 * ausschliesslich aether/planner.py im Repository.
 *
 * Wie im Original: kein Netzwerk, kein Storage, keine Worker, keine Modelle.
 * Der Zustand lebt nur im Seitenspeicher und verschwindet beim Neuladen.
 */
(function (global) {
  "use strict";

  const ROLES = new Set(["NEXUS", "FORGE", "PRISM", "AEGIS", "PULSE"]);
  const RULES = new Set(["A-01", "A-02", "A-03", "A-04"]);

  function permissionError(message) {
    const error = new Error(message);
    error.name = "PermissionError";
    return error;
  }

  function valueError(message) {
    const error = new Error(message);
    error.name = "ValueError";
    return error;
  }

  function isNonEmptyString(value) {
    return typeof value === "string" && value.trim().length > 0;
  }

  function text(value, name) {
    if (!isNonEmptyString(value)) {
      throw valueError(name + " must be non-empty text");
    }
    return value;
  }

  function deepClone(value) {
    return structuredClone(value);
  }

  /* Spiegelt json.dumps(..., allow_nan=False): echte JSON-Daten, sonst Fehler. */
  function strictJsonRoundTrip(value) {
    const seen = new WeakSet();
    (function walk(node) {
      if (node === null) return;
      const type = typeof node;
      if (type === "number") {
        if (!Number.isFinite(node)) {
          throw valueError("Out of range float values are not JSON compliant");
        }
        return;
      }
      if (type === "string" || type === "boolean") return;
      if (type !== "object") {
        throw valueError("Object of type " + type + " is not JSON serializable");
      }
      if (seen.has(node)) {
        throw valueError("Circular reference is not JSON serializable");
      }
      seen.add(node);
      if (Array.isArray(node)) {
        node.forEach(walk);
      } else {
        Object.values(node).forEach(walk);
      }
      seen.delete(node);
    })(value);
    return JSON.parse(JSON.stringify(value));
  }

  function validatePlan(plan) {
    if (!Array.isArray(plan) || plan.length < 1 || plan.length > 20) {
      throw valueError("A-01: expected 1 to 20 tasks");
    }
    const ids = new Set();
    for (const task of plan) {
      if (task === null || typeof task !== "object" || Array.isArray(task)) {
        throw valueError("Task must be an object");
      }
      for (const field of ["id", "title", "assignee", "reason"]) {
        text(task[field], field);
      }
      if (ids.has(task.id)) throw valueError("Duplicate task ID");
      ids.add(task.id);
      if (!ROLES.has(task.assignee)) throw valueError("Unknown role");
      const deps = task.depends_on;
      if (!Array.isArray(deps) || !deps.every((d) => typeof d === "string")) {
        throw valueError("Dependencies must be a list of task IDs");
      }
      if (new Set(deps).size !== deps.length) throw valueError("Duplicate dependency");
      if (!("parallel_group" in task)) throw valueError("Missing parallel_group");
      if (task.parallel_group !== null) text(task.parallel_group, "parallel_group");
    }
    if (plan[0].id !== "t0" || plan[0].assignee !== "NEXUS") {
      throw valueError("First task must be t0 assigned to NEXUS");
    }
    if (plan[plan.length - 1].assignee !== "AEGIS") {
      throw valueError("Last task must be assigned to AEGIS");
    }
    for (const task of plan) {
      if (task.depends_on.some((d) => !ids.has(d) || d === task.id)) {
        throw valueError("Missing or self dependency");
      }
    }
    const resolved = new Set();
    while (resolved.size < plan.length) {
      const batch = plan
        .filter((t) => !resolved.has(t.id) && t.depends_on.every((d) => resolved.has(d)))
        .map((t) => t.id);
      if (batch.length === 0) throw valueError("Dependency cycle");
      batch.forEach((id) => resolved.add(id));
    }
  }

  class Planner {
    constructor(plan) {
      validatePlan(plan);
      this._plan = deepClone(plan);
      this._approved = false;
      /* Null-Prototypen wie Python-dicts: kein "constructor"-Geister-Key. */
      this._vetos = Object.create(null);
      this._results = Object.create(null);
      this._reviews = Object.create(null);
      this._events = [];
    }

    _record(decision, reason) {
      text(reason, "reason");
      this._events.push({ decision: decision, reason: reason });
    }

    _openVetos() {
      return Object.values(this._vetos).filter((v) => !v.overridden);
    }

    _gate() {
      if (!this._approved) throw permissionError("Human approval required");
      if (this._openVetos().length > 0) throw permissionError("Open veto blocks progress");
    }

    approve(command, reason) {
      text(reason, "reason");
      if (command !== "j") throw valueError("Expected exact human command: j");
      if (this._openVetos().length > 0) {
        throw permissionError("Approval cannot override a veto");
      }
      this._approved = true;
      this._record("approve", reason);
    }

    pause(reason) {
      text(reason, "reason");
      this._approved = false;
      this._record("pause", reason);
    }

    veto(vetoId, rule, artifact, reason) {
      text(vetoId, "veto_id");
      text(artifact, "artifact");
      text(reason, "reason");
      if (!RULES.has(rule)) throw valueError("Unknown veto rule");
      if (vetoId in this._vetos) throw valueError("Veto ID already exists");
      this._vetos[vetoId] = {
        rule: rule,
        artifact: artifact,
        reason: reason,
        overridden: false,
        override_hint: "override " + vetoId,
      };
      this._record("veto " + vetoId, reason);
    }

    override(command, reason) {
      text(reason, "reason");
      text(command, "command");
      if (!command.startsWith("override ")) throw valueError("Expected override <ID>");
      const vetoId = command.slice("override ".length);
      if (!(vetoId in this._vetos) || this._vetos[vetoId].overridden) {
        throw valueError("Unknown or already overridden veto");
      }
      this._vetos[vetoId].overridden = true;
      this._record(command, reason);
    }

    ready() {
      this._gate();
      const completed = new Set(
        Object.keys(this._reviews).filter((k) => this._reviews[k].status === "FREI")
      );
      return deepClone(
        this._plan.filter(
          (t) =>
            !(t.id in this._results) && t.depends_on.every((d) => completed.has(d))
        )
      );
    }

    submit(taskId, output, explanation) {
      text(taskId, "task_id");
      text(explanation, "explanation");
      if (!this.ready().some((t) => t.id === taskId)) {
        throw valueError("Task is not ready or was already submitted");
      }
      const isolated = strictJsonRoundTrip(output);
      this._results[taskId] = {
        task_id: taskId,
        output: isolated,
        explanation: explanation,
      };
      this._record("submit " + taskId, "Store proposal pending AEGIS review");
    }

    review(taskId, status, reason) {
      this._gate();
      text(taskId, "task_id");
      text(reason, "reason");
      if (!(taskId in this._results)) throw valueError("No result to review");
      if (status !== "FREI" && status !== "VETO") throw valueError("Expected FREI or VETO");
      if (taskId in this._reviews && this._reviews[taskId].status === "FREI") {
        throw valueError("Accepted reviews are immutable; raise a global veto instead");
      }
      if (status === "VETO") {
        let index = 1;
        while (("review-" + taskId + "-" + index) in this._vetos) index += 1;
        this.veto("review-" + taskId + "-" + index, "A-04", taskId, reason);
      }
      this._reviews[taskId] = { status: status, reason: reason };
      this._record("review " + taskId + ": " + status, reason);
    }

    snapshot() {
      return deepClone({
        plan: this._plan,
        approved: this._approved,
        vetos: this._vetos,
        results: this._results,
        reviews: this._reviews,
        events: this._events,
      });
    }
  }

  const api = { Planner: Planner, validatePlan: validatePlan, ROLES: ROLES, RULES: RULES };
  global.AetherPlanner = api;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
