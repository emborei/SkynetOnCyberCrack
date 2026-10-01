"""Local planning gates, not a worker engine or a security boundary.

Only a trusted human-facing coordinator may call approval, override and review.
No code, network requests, subprocesses or model calls are executed here.
"""

import copy
import json


ROLES = {"NEXUS", "FORGE", "PRISM", "AEGIS", "PULSE"}
RULES = {"A-01", "A-02", "A-03", "A-04"}


def text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value


def validate_plan(plan):
    if not isinstance(plan, list) or not 1 <= len(plan) <= 20:
        raise ValueError("A-01: expected 1 to 20 tasks")
    ids = set()
    for task in plan:
        if not isinstance(task, dict):
            raise ValueError("Task must be an object")
        for field in ("id", "title", "assignee", "reason"):
            text(task.get(field), field)
        if task["id"] in ids:
            raise ValueError("Duplicate task ID")
        ids.add(task["id"])
        if task["assignee"] not in ROLES:
            raise ValueError("Unknown role")
        deps = task.get("depends_on")
        if not isinstance(deps, list) or not all(isinstance(d, str) for d in deps):
            raise ValueError("Dependencies must be a list of task IDs")
        if len(deps) != len(set(deps)):
            raise ValueError("Duplicate dependency")
        if "parallel_group" not in task:
            raise ValueError("Missing parallel_group")
        if task["parallel_group"] is not None:
            text(task["parallel_group"], "parallel_group")
    if plan[0]["id"] != "t0" or plan[0]["assignee"] != "NEXUS":
        raise ValueError("First task must be t0 assigned to NEXUS")
    if plan[-1]["assignee"] != "AEGIS":
        raise ValueError("Last task must be assigned to AEGIS")
    for task in plan:
        if any(d not in ids or d == task["id"] for d in task["depends_on"]):
            raise ValueError("Missing or self dependency")
    resolved = set()
    while len(resolved) < len(plan):
        batch = {t["id"] for t in plan if t["id"] not in resolved
                 and set(t["depends_on"]) <= resolved}
        if not batch:
            raise ValueError("Dependency cycle")
        resolved.update(batch)


class Planner:
    """Sequential, in-memory state. Private attributes are not a sandbox."""

    def __init__(self, plan):
        validate_plan(plan)
        self._plan = copy.deepcopy(plan)
        self._approved = False
        self._vetos = {}
        self._results = {}
        self._reviews = {}
        self._events = []

    def _record(self, decision, reason):
        self._events.append({"decision": decision, "reason": text(reason, "reason")})

    def _gate(self):
        if not self._approved:
            raise PermissionError("Human approval required")
        if any(not v["overridden"] for v in self._vetos.values()):
            raise PermissionError("Open veto blocks progress")

    def approve(self, command, reason):
        text(reason, "reason")
        if command != "j":
            raise ValueError("Expected exact human command: j")
        if any(not v["overridden"] for v in self._vetos.values()):
            raise PermissionError("Approval cannot override a veto")
        self._approved = True
        self._record("approve", reason)

    def pause(self, reason):
        text(reason, "reason")
        self._approved = False
        self._record("pause", reason)

    def veto(self, veto_id, rule, artifact, reason):
        text(veto_id, "veto_id")
        text(artifact, "artifact")
        text(reason, "reason")
        if not isinstance(rule, str) or rule not in RULES:
            raise ValueError("Unknown veto rule")
        if veto_id in self._vetos:
            raise ValueError("Veto ID already exists")
        self._vetos[veto_id] = {
            "rule": rule, "artifact": artifact, "reason": reason,
            "overridden": False, "override_hint": f"override {veto_id}"
        }
        self._record(f"veto {veto_id}", reason)

    def override(self, command, reason):
        text(reason, "reason")
        text(command, "command")
        if not command.startswith("override "):
            raise ValueError("Expected override <ID>")
        veto_id = command[len("override "):]
        if veto_id not in self._vetos or self._vetos[veto_id]["overridden"]:
            raise ValueError("Unknown or already overridden veto")
        self._vetos[veto_id]["overridden"] = True
        self._record(command, reason)

    def ready(self):
        self._gate()
        completed = {key for key, value in self._reviews.items()
                     if value["status"] == "FREI"}
        return copy.deepcopy([
            task for task in self._plan
            if task["id"] not in self._results
            and set(task["depends_on"]) <= completed
        ])

    def submit(self, task_id, output, explanation):
        text(task_id, "task_id")
        text(explanation, "explanation")
        if task_id not in {t["id"] for t in self.ready()}:
            raise ValueError("Task is not ready or was already submitted")
        # A strict JSON round trip rejects non-JSON outputs and isolates data.
        isolated = json.loads(json.dumps(output, allow_nan=False))
        self._results[task_id] = {
            "task_id": task_id, "output": isolated, "explanation": explanation
        }
        self._record(f"submit {task_id}", "Store proposal pending AEGIS review")

    def review(self, task_id, status, reason):
        self._gate()
        text(task_id, "task_id")
        text(reason, "reason")
        if task_id not in self._results:
            raise ValueError("No result to review")
        if status not in ("FREI", "VETO"):
            raise ValueError("Expected FREI or VETO")
        if self._reviews.get(task_id, {}).get("status") == "FREI":
            raise ValueError("Accepted reviews are immutable; raise a global veto instead")
        if status == "VETO":
            index = 1
            while f"review-{task_id}-{index}" in self._vetos:
                index += 1
            self.veto(f"review-{task_id}-{index}", "A-04", task_id, reason)
        self._reviews[task_id] = {"status": status, "reason": reason}
        self._record(f"review {task_id}: {status}", reason)

    def snapshot(self):
        return copy.deepcopy({
            "plan": self._plan, "approved": self._approved,
            "vetos": self._vetos, "results": self._results,
            "reviews": self._reviews, "events": self._events
        })
