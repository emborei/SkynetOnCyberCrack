"""Unexecuted unit tests. Run manually from this directory."""

import copy
import unittest

from planner import Planner, validate_plan


def sample_plan():
    return [
        {"id": "t0", "title": "Scope", "assignee": "NEXUS",
         "reason": "Keep human control", "depends_on": [], "parallel_group": None},
        {"id": "t1", "title": "Contract", "assignee": "PRISM",
         "reason": "Define data", "depends_on": ["t0"], "parallel_group": "p1"},
        {"id": "t2", "title": "Operations", "assignee": "PULSE",
         "reason": "Define local operations", "depends_on": ["t0"], "parallel_group": "p1"},
        {"id": "t3", "title": "Review", "assignee": "AEGIS",
         "reason": "Check all results", "depends_on": ["t1", "t2"], "parallel_group": None},
    ]


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.p = Planner(sample_plan())

    def approve(self):
        self.p.approve("j", "Human approved this example")

    def complete(self, task_id):
        self.p.submit(task_id, {"simulated": True}, "Example only")
        self.p.review(task_id, "FREI", "Static example review")

    def test_approval_required(self):
        with self.assertRaises(PermissionError):
            self.p.ready()
        for command in ("J", "yes", " j", "j\n"):
            with self.assertRaises(ValueError):
                self.p.approve(command, "Not the exact command")
        self.approve()
        self.assertEqual([t["id"] for t in self.p.ready()], ["t0"])

    def test_results_need_review_and_allow_parallel_ready_tasks(self):
        self.approve()
        self.p.submit("t0", {}, "Proposal")
        self.assertEqual(self.p.ready(), [])
        self.p.review("t0", "FREI", "Reviewed")
        self.assertEqual([t["id"] for t in self.p.ready()], ["t1", "t2"])
        self.complete("t1")
        self.assertEqual([t["id"] for t in self.p.ready()], ["t2"])
        self.complete("t2")
        self.complete("t3")
        self.assertEqual(self.p.ready(), [])

    def test_veto_blocks_and_override_does_not_approve(self):
        self.p.veto("v1", "A-03", "example", "Human review required")
        with self.assertRaises(PermissionError):
            self.approve()
        with self.assertRaises(ValueError):
            self.p.override("override missing", "Unknown ID")
        self.p.override("override v1", "Human accepts this specific exception")
        with self.assertRaises(PermissionError):
            self.p.ready()
        with self.assertRaises(ValueError):
            self.p.override("override v1", "Repeated command")
        self.approve()
        self.assertEqual(len(self.p.ready()), 1)

    def test_review_veto_requires_override_and_new_review(self):
        self.approve()
        self.p.submit("t0", {}, "Proposal")
        self.p.review("t0", "VETO", "Further human scrutiny required")
        with self.assertRaises(PermissionError):
            self.p.ready()
        self.p.override("override review-t0-1", "Human accepts exception")
        self.assertEqual(self.p.ready(), [])
        self.p.review("t0", "FREI", "Reviewed after human exception")
        self.assertEqual(len(self.p.ready()), 2)

    def test_pause(self):
        self.approve()
        self.p.pause("Human requested a stop")
        with self.assertRaises(PermissionError):
            self.p.ready()
        self.approve()
        self.assertEqual(len(self.p.ready()), 1)

    def test_plan_and_snapshot_isolation(self):
        plan = sample_plan()
        planner = Planner(plan)
        plan[0]["reason"] = "changed"
        snapshot = planner.snapshot()
        snapshot["plan"][0]["reason"] = "tampered"
        snapshot["approved"] = True
        self.assertEqual(planner.snapshot()["plan"], sample_plan())
        with self.assertRaises(PermissionError):
            planner.ready()
        with self.assertRaises(PermissionError):
            Planner(sample_plan()).ready()

    def test_bad_plans(self):
        base = sample_plan()
        cases = [[], base * 6]
        for field, value in (("reason", " "), ("assignee", "UNKNOWN"),
                             ("depends_on", ["missing"]),
                             ("depends_on", ["t0"]), ("parallel_group", "")):
            plan = copy.deepcopy(base)
            plan[0][field] = value
            cases.append(plan)
        duplicate = copy.deepcopy(base)
        duplicate[1]["id"] = "t0"
        cases.append(duplicate)
        cycle = copy.deepcopy(base)
        cycle[1]["depends_on"] = ["t2"]
        cycle[2]["depends_on"] = ["t1"]
        cases.append(cycle)
        last = copy.deepcopy(base)
        last[-1]["assignee"] = "FORGE"
        cases.append(last)
        for plan in cases:
            with self.subTest(plan=plan), self.assertRaises(ValueError):
                validate_plan(plan)

    def test_invalid_result_does_not_change_state(self):
        self.approve()
        with self.assertRaises(ValueError):
            self.p.submit("t1", {}, "Too early")
        with self.assertRaises(ValueError):
            self.p.submit("t0", float("nan"), "Not strict JSON")
        self.assertEqual(self.p.snapshot()["results"], {})

    def test_result_data_isolation(self):
        self.approve()
        output = {"items": []}
        self.p.submit("t0", output, "Proposal")
        output["items"].append("tampered")
        self.assertEqual(self.p.snapshot()["results"]["t0"]["output"], {"items": []})

    def test_reason_required_before_mutation(self):
        before = self.p.snapshot()
        with self.assertRaises(ValueError):
            self.p.approve("j", "")
        with self.assertRaises(ValueError):
            self.p.veto("v1", "A-04", "plan", "")
        self.assertEqual(self.p.snapshot(), before)

    def test_events_have_reasons(self):
        self.approve()
        self.complete("t0")
        self.p.pause("Stop example")
        for event in self.p.snapshot()["events"]:
            self.assertTrue(event["decision"])
            self.assertTrue(event["reason"])

    def test_veto_ids_cannot_be_reused(self):
        self.p.veto("v1", "A-04", "plan", "Check control")
        with self.assertRaises(ValueError):
            self.p.veto("v1", "A-04", "plan", "Duplicate ID")


if __name__ == "__main__":
    unittest.main()
