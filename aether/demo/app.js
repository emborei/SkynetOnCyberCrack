/* Aether demo renderer.
 *
 * Reads the precomputed traces from data.js and replays them. It performs no
 * network request, stores nothing in the browser and loads no third-party
 * code. All behaviour shown here was produced by aether/planner.py during the
 * site build; this file only displays it.
 */
(function () {
  "use strict";

  var DATA = window.AETHER_DEMO;

  /* ---------------------------------------------------------------- utils */

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (key) {
        if (key === "class") { node.className = attrs[key]; }
        else if (key === "text") { node.textContent = attrs[key]; }
        else if (key === "html") { node.innerHTML = attrs[key]; }
        else if (key.slice(0, 2) === "on") {
          node.addEventListener(key.slice(2), attrs[key]);
        } else if (attrs[key] !== null && attrs[key] !== undefined) {
          node.setAttribute(key, attrs[key]);
        }
      });
    }
    (children || []).forEach(function (child) {
      if (child === null || child === undefined) { return; }
      node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
    });
    return node;
  }

  function fill(id) { return document.getElementById(id); }

  function clear(node) { while (node.firstChild) { node.removeChild(node.firstChild); } }

  function mono(text) { return el("code", { text: String(text) }); }

  /* --------------------------------------------------------------- status */

  function chip(label, value, tone) {
    return el("span", { class: "chip" + (tone ? " " + tone : "") }, [
      label + " ", el("b", { text: String(value) })
    ]);
  }

  function renderStatus() {
    var meta = DATA.meta;
    var tests = meta.tests;
    var host = fill("status-chips");
    clear(host);

    if (tests && tests.ok === true) {
      host.appendChild(chip("Tests", tests.methods_run + "/" + tests.methods_run + " bestanden", "ok"));
    } else if (tests && tests.ok === false) {
      host.appendChild(chip("Tests", "fehlgeschlagen", "err"));
    } else {
      host.appendChild(chip("Tests", "beim Build übersprungen", "warn"));
    }

    var steps = DATA.scenarios.reduce(function (sum, s) { return sum + s.step_count; }, 0);
    host.appendChild(chip("Echte Planner-Schritte", steps));
    host.appendChild(chip("Tasks im Plan", DATA.plan.length));
    host.appendChild(chip("Build", meta.build_host === "GitHub Actions" ? "GitHub Actions" : "lokal"));
    host.appendChild(chip("Erzeugt", meta.generated_at));
    if (meta.source_commit) {
      host.appendChild(chip("Commit", meta.source_commit.slice(0, 7)));
    }
    host.appendChild(chip("Tracker", "0", "ok"));
  }

  /* --------------------------------------------------------------- replay */

  var current = { scenario: 0, step: -1, timer: null };

  function scenario() { return DATA.scenarios[current.scenario]; }

  function renderTabs() {
    var host = fill("scenario-tabs");
    clear(host);
    DATA.scenarios.forEach(function (item, index) {
      host.appendChild(el("button", {
        type: "button",
        class: "tab",
        role: "tab",
        id: "tab-" + item.key,
        "aria-selected": index === current.scenario ? "true" : "false",
        text: item.title,
        onclick: function () { selectScenario(index); }
      }));
    });
  }

  function selectScenario(index) {
    stopPlay();
    current.scenario = index;
    current.step = -1;
    renderTabs();
    fill("scenario-claim").textContent = scenario().claim;
    renderBoard();
    next();
  }

  function renderControls() {
    var total = scenario().step_count;
    fill("progress").textContent =
      total === 0 ? "0 / 0" : (current.step + 1) + " / " + total;
    fill("btn-prev").disabled = current.step <= 0;
    fill("btn-next").disabled = current.step >= total - 1;
  }

  function outcomeBlock(outcome) {
    if (outcome.status === "ok") {
      var parts = [el("span", { class: "tag", text: "OK" })];
      if (outcome.value !== undefined) {
        parts.push(document.createTextNode("  →  "));
        parts.push(mono(Array.isArray(outcome.value)
          ? (outcome.value.length ? outcome.value.join(", ") : "[]")
          : outcome.value));
      } else {
        parts.push(document.createTextNode("  Zustand geändert, kein Rückgabewert."));
      }
      return el("div", { class: "outcome ok" }, parts);
    }
    return el("div", { class: "outcome error" }, [
      el("span", { class: "tag", text: outcome.type }),
      document.createTextNode("  " + outcome.message)
    ]);
  }

  function renderStep() {
    var host = fill("step-card");
    clear(host);
    if (current.step < 0) {
      host.appendChild(el("p", { class: "muted", text: "Weiter drücken, um den ersten Schritt zu sehen." }));
      return;
    }
    var step = scenario().steps[current.step];

    host.appendChild(el("div", { class: "step-head" }, [
      el("span", { class: "step-title", text: step.label }),
      el("span", { class: "actor " + step.actor, text: step.actor })
    ]));
    host.appendChild(el("div", { class: "call", text: step.call }));
    host.appendChild(outcomeBlock(step.outcome));
    if (step.note) { host.appendChild(el("p", { class: "note", text: step.note })); }
  }

  function cell(key, value, tone) {
    return el("div", { class: "state-cell" }, [
      el("span", { class: "k", text: key }),
      el("span", { class: "v" + (tone ? " " + tone : ""), text: value })
    ]);
  }

  function listOr(ids, fallback) {
    return ids && ids.length ? ids.join(", ") : fallback;
  }

  function renderState() {
    var host = fill("state-card");
    clear(host);
    if (current.step < 0) { return; }
    var state = scenario().steps[current.step].state;

    host.appendChild(el("h3", { text: "Zustand nach diesem Schritt" }));
    var grid = el("div", { class: "state-grid" });
    grid.appendChild(cell("approved", state.approved ? "true" : "false",
      state.approved ? "yes" : "no"));
    grid.appendChild(cell("ready()",
      state.ready_error ? state.ready_error.type : listOr(state.ready, "[]"),
      state.ready_error ? "no" : (state.ready && state.ready.length ? "yes" : "")));
    grid.appendChild(cell("offene Vetos", state.open_vetos.length
      ? state.open_vetos.join(", ") : "keine",
      state.open_vetos.length ? "no" : "yes"));
    grid.appendChild(cell("FREI geprüft", listOr(state.accepted, "–"), "yes"));
    grid.appendChild(cell("eingereicht", listOr(state.submitted, "–")));
    if (state.rejected.length) { grid.appendChild(cell("abgelehnt", state.rejected.join(", "), "no")); }
    grid.appendChild(cell("Audit-Ereignisse", String(state.event_count)));
    host.appendChild(grid);
  }

  function taskState(taskId, state) {
    if (state.accepted.indexOf(taskId) !== -1) { return ["accepted", "FREI"]; }
    if (state.rejected.indexOf(taskId) !== -1) { return ["rejected", "ABGELEHNT"]; }
    if (state.submitted.indexOf(taskId) !== -1) { return ["submitted", "EINGEREICHT"]; }
    if (state.ready && state.ready.indexOf(taskId) !== -1) { return ["ready", "BEREIT"]; }
    if (state.ready_error) { return ["blocked", "GESPERRT"]; }
    return ["waiting", "WARTET"];
  }

  function renderBoard() {
    var host = fill("plan-board");
    clear(host);
    var state = current.step >= 0 ? scenario().steps[current.step].state : null;

    DATA.plan.forEach(function (task) {
      var status = state ? taskState(task.id, state) : ["waiting", "–"];
      var result = DATA.results[task.id];
      var meta = [];
      if (task.depends_on && task.depends_on.length) {
        meta.push("abhängig von " + task.depends_on.join(", "));
      } else {
        meta.push("keine Abhängigkeit");
      }
      if (task.parallel_group) { meta.push("Gruppe " + task.parallel_group); }

      var kids = [
        el("div", { class: "task-top" }, [
          el("span", { class: "task-id", text: task.id }),
          el("span", { class: "actor " + task.assignee, text: task.assignee }),
          el("span", { class: "task-state", text: status[1] })
        ]),
        el("div", { class: "task-title", text: task.title }),
        el("div", { class: "task-meta", text: meta.join(" · ") })
      ];
      if (result && status[0] === "accepted" && Array.isArray(result.output)) {
        kids.push(el("div", { class: "task-meta", text: "→ " + result.output.join(", ") }));
      }
      host.appendChild(el("li", { class: "task s-" + status[0] }, kids));
    });
  }

  function renderAudit() {
    var host = fill("audit-log");
    clear(host);
    var events = [];
    for (var i = 0; i <= current.step; i++) {
      var state = scenario().steps[i].state;
      (state.new_events || []).forEach(function (event) { events.push(event); });
    }
    fill("audit-count").textContent = events.length ? "(" + events.length + ")" : "";
    if (!events.length) {
      host.appendChild(el("li", { class: "audit-empty", text: "Noch kein zustandsänderndes Ereignis." }));
      return;
    }
    events.forEach(function (event) {
      host.appendChild(el("li", {}, [
        el("span", { class: "d", text: event.decision }),
        el("span", { class: "r", text: "reason: " + event.reason })
      ]));
    });
    host.scrollTop = host.scrollHeight;
  }

  function renderReplay() { renderControls(); renderStep(); renderState(); renderBoard(); renderAudit(); }

  function next() {
    if (current.step < scenario().step_count - 1) { current.step++; renderReplay(); }
    if (current.step >= scenario().step_count - 1) { stopPlay(); }
  }

  function prev() {
    if (current.step > 0) { current.step--; renderReplay(); }
  }

  function reset() { stopPlay(); current.step = -1; renderReplay(); }

  function stopPlay() {
    if (current.timer) { clearInterval(current.timer); current.timer = null; }
    var button = fill("btn-play");
    button.textContent = "▶ Abspielen";
  }

  function togglePlay() {
    if (current.timer) { stopPlay(); return; }
    if (current.step >= scenario().step_count - 1) { current.step = -1; }
    fill("btn-play").textContent = "⏸ Pause";
    next();
    current.timer = setInterval(next, 1600);
  }

  /* ------------------------------------------------------- static content */

  var GATES = [
    ["Freigabesperre", "ready() und review() werfen PermissionError, bis ein Mensch exakt 'j' übergibt. 'J', 'yes' oder ' j' werden abgelehnt."],
    ["Globales Veto", "Ein offenes Veto blockiert Bereitstellung und Ergebnisannahme. Nur 'override <ID>' durch einen Menschen hebt dieses eine Veto auf – es ist keine Freigabe."],
    ["Ergebnisprüfung", "submit() speichert nur einen Vorschlag. Eine Abhängigkeit gilt erst als erfüllt, wenn AEGIS mit FREI geprüft hat."],
    ["Pause und neue Instanz", "pause() entzieht die Freigabe. Ein neuer Planner braucht ein neues 'j'; es gibt keinen automatischen Wiederanlauf."]
  ];

  function renderGates() {
    var host = fill("gates");
    clear(host);
    GATES.forEach(function (gate) {
      host.appendChild(el("div", { class: "gate" }, [
        el("h3", { text: gate[0] }),
        el("p", { text: gate[1] })
      ]));
    });
  }

  function renderRoles() {
    var host = fill("role-cards");
    clear(host);
    DATA.roles.forEach(function (role) {
      host.appendChild(el("div", { class: "role" }, [
        el("div", { class: "id", text: role.id }),
        el("h3", { text: role.subtitle }),
        el("p", { text: role.description })
      ]));
    });
  }

  function renderRules() {
    var body = fill("rules-table").querySelector("tbody");
    clear(body);
    DATA.veto_rules.forEach(function (rule) {
      body.appendChild(el("tr", {}, [
        el("td", { text: rule.rule }),
        el("td", { text: rule.check }),
        el("td", { text: rule.limit })
      ]));
    });
  }

  function checkItem(check) {
    return el("li", {}, [
      el("span", { class: "badge " + check.status, text: check.status }),
      el("b", { text: check.rule }),
      document.createTextNode(" – " + check.reason)
    ]);
  }

  function renderReview() {
    var checks = fill("review-checks");
    clear(checks);
    (DATA.final_review.checks || []).forEach(function (check) {
      checks.appendChild(checkItem(check));
    });

    var facts = fill("verification-facts");
    clear(facts);
    var meta = DATA.meta;
    var tests = meta.tests || {};
    var verification = DATA.final_review.verification || {};
    var factList = [
      [tests.ok === true, "Unit-Tests beim Build ausgeführt: " + tests.methods_run + " Methoden, " +
        tests.failures + " Fehler, " + tests.errors + " Ausnahmen."],
      [true, "Alle gezeigten Abläufe sind echte planner.py-Aufrufe aus dem Build, keine Handbeispiele."],
      [verification.code_executed === false, "Im dokumentierten Erstdurchlauf wurde kein Code ausgeführt – die Laufzeitprüfung stand damals aus."],
      [verification.independent_agent_review === false, "Keine unabhängige Agentenprüfung: Rollen wurden von einem Dialogassistenten dargestellt."],
      [verification.production_approved === false, "Kein Produktionsbetrieb freigegeben."],
      [true, "Integrität: planner.py Hash " + (meta.integrity["aether/planner.py"] || "–") + "."]
    ];
    factList.forEach(function (fact) {
      facts.appendChild(el("li", {}, [
        el("span", { class: "badge " + (fact[0] ? "FREI" : "VETO"), text: fact[0] ? "BELEGT" : "OFFEN" }),
        document.createTextNode(fact[1])
      ]));
    });

    var risks = fill("remaining-risks");
    clear(risks);
    (DATA.final_review.remaining_risks || []).forEach(function (risk) {
      risks.appendChild(el("li", { text: risk }));
    });
  }

  function renderLimits() {
    var limits = fill("limitations");
    clear(limits);
    (DATA.summary.limitations || []).forEach(function (item) {
      limits.appendChild(el("li", { text: item }));
    });

    var decisions = fill("next-decisions");
    clear(decisions);
    (DATA.summary.next_human_decisions || []).forEach(function (item) {
      decisions.appendChild(el("li", {}, [
        el("b", { text: item.decision }),
        el("br"),
        el("span", { class: "muted", text: item.reason })
      ]));
    });

    var log = fill("run-log");
    clear(log);
    (DATA.run_log || []).forEach(function (entry) {
      log.appendChild(el("li", { text: entry.role + " · " + entry.scope + " – " + entry.reason }));
    });
  }

  function renderProvenance() {
    var host = fill("provenance-body");
    clear(host);
    var meta = DATA.meta;

    host.appendChild(el("div", { class: "callout", text: meta.rebuild_note }));

    var table = el("table", { class: "kv" }, []);
    var body = el("tbody");
    [
      ["Erzeugt", meta.generated_at + " (UTC)"],
      ["Generator", meta.generator],
      ["Build-Umgebung", meta.build_host + ", Python " + meta.python_version],
      ["Quelle-Commit", meta.source_commit || "lokaler Build ohne CI-Kontext"],
      ["Quelle-Ref", meta.source_ref || "–"],
      ["Hash aether/planner.py", meta.integrity["aether/planner.py"] || "–"],
      ["Hash aether/plan.json", meta.integrity["aether/plan.json"] || "–"],
      ["Hash aether/test_planner.py", meta.integrity["aether/test_planner.py"] || "–"],
      ["Testbefehl", (meta.tests || {}).command || "–"]
    ].forEach(function (row) {
      body.appendChild(el("tr", {}, [
        el("th", { scope: "row", text: row[0] }),
        el("td", { text: String(row[1]) })
      ]));
    });
    table.appendChild(body);
    host.appendChild(table);

    if (meta.tests && meta.tests.log) {
      host.appendChild(el("h3", { text: "Testprotokoll des Builds" }));
      host.appendChild(el("pre", { class: "log", text: meta.tests.log }));
    }
  }

  /* ----------------------------------------------------------------- init */

  function init() {
    if (!DATA) {
      fill("lede").textContent =
        "data.js fehlt. Bitte die Seite mit 'python3 aether/demo/build.py' neu erzeugen.";
      return;
    }
    renderStatus();
    renderTabs();
    fill("scenario-claim").textContent = scenario().claim;
    renderGates();
    renderRoles();
    renderRules();
    renderReview();
    renderLimits();
    renderProvenance();
    renderReplay();

    fill("btn-next").addEventListener("click", next);
    fill("btn-prev").addEventListener("click", prev);
    fill("btn-play").addEventListener("click", togglePlay);
    fill("btn-reset").addEventListener("click", reset);
    document.addEventListener("keydown", function (event) {
      if (event.target && /input|textarea/i.test(event.target.tagName)) { return; }
      if (event.key === "ArrowRight") { next(); }
      if (event.key === "ArrowLeft") { prev(); }
    });

    fill("foot-meta").textContent =
      "Aether-Demo · erzeugt " + DATA.meta.generated_at + " · " +
      DATA.scenarios.length + " Abläufe, " +
      DATA.scenarios.reduce(function (s, x) { return s + x.step_count; }, 0) +
      " echte Planner-Schritte · keine Cookies, kein Analytics, kein externer Aufruf";
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
