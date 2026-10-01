/* UI-Logik der Browser-Demo; die Gate-Semantik liegt vollständig in planner.js. */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const PLAN = window.AETHER.plan;
  const REPLAY_RESULTS = window.AETHER.results;

  let planner = null;
  let stepNo = 0;
  let replaying = false;

  function reset() {
    planner = new window.AetherPlanner.Planner(JSON.parse(JSON.stringify(PLAN)));
    stepNo = 0;
    $("log").innerHTML = "";
    log("info", "Neue Instanz erzeugt. Ohne Freigabe blockiert ready() — try it.");
    render();
  }

  function log(kind, message) {
    stepNo += 1;
    const line = document.createElement("div");
    line.className = kind;
    const prefix = String(stepNo).padStart(2, "0") + " · ";
    line.textContent = prefix + message;
    $("log").appendChild(line);
    $("log").scrollTop = $("log").scrollHeight;
  }

  /* Führt einen Planner-Aufruf aus; Fehler sind hier Show, nicht Versagen. */
  function call(label, action, okNote) {
    if (replaying) return null;
    try {
      const value = action();
      if (okNote) log("ok", label + " → " + okNote);
      render();
      return value;
    } catch (error) {
      log("err", label + " → " + error.name + ": " + error.message);
      render();
      return null;
    }
  }

  function readyIds() {
    try {
      return planner.ready().map((t) => t.id);
    } catch (error) {
      return { blocked: error.message };
    }
  }

  function statusOf(task, ready, snap) {
    if (snap.reviews[task.id] && snap.reviews[task.id].status === "FREI") return "free";
    if (snap.reviews[task.id] && snap.reviews[task.id].status === "VETO") return "rejected";
    if (task.id in snap.results) return "pending";
    if (Array.isArray(ready) && ready.includes(task.id)) return "ready";
    return "blocked";
  }

  const LABELS = {
    free: "FREI geprüft",
    rejected: "VETO / abgelehnt",
    pending: "wartet auf Prüfung",
    ready: "bereit",
    blocked: "blockiert",
  };

  function render() {
    const snap = planner.snapshot();
    const ready = readyIds();
    $("gate-state").textContent = snap.approved ? "freigegeben (j)" : "nicht freigegeben";
    $("gate-state").className = "badge " + (snap.approved ? "good" : "bad");
    $("plan-size").textContent = snap.plan.length;

    const banner = $("veto-banner");
    const open = Object.entries(snap.vetos).filter(([, v]) => !v.overridden);
    if (open.length > 0) {
      banner.hidden = false;
      banner.textContent =
        "Offenes Veto blockiert global: " +
        open.map(([id]) => id).join(", ") +
        " — nur „override <ID>“ hebt genau diese Sperre auf.";
    } else {
      banner.hidden = true;
    }

    const vetosBox = $("vetos");
    vetosBox.innerHTML = "";
    Object.entries(snap.vetos).forEach(([id, v]) => {
      const line = document.createElement("div");
      line.className = "veto-line" + (v.overridden ? " overridden" : "");
      line.textContent = `${v.overridden ? "✓" : "✕"} ${id} · ${v.rule} · ${v.artifact} · ${v.reason}`;
      vetosBox.appendChild(line);
    });

    const box = $("tasks");
    box.innerHTML = "";
    snap.plan.forEach((task) => {
      const status = typeof ready === "object" && ready.blocked && !Array.isArray(ready)
        ? "blocked"
        : statusOf(task, ready, snap);
      const card = document.createElement("div");
      card.className = "task";
      const head = document.createElement("div");
      head.className = "head";
      head.innerHTML =
        `<span class="id">${task.id}</span>` +
        `<span class="role">${task.assignee}</span>` +
        `<span class="status ${status}">${LABELS[status]}</span>`;
      const title = document.createElement("div");
      title.className = "title";
      title.textContent = task.title;
      const meta = document.createElement("div");
      meta.className = "meta";
      meta.textContent =
        "depends_on=[" + (task.depends_on.join(", ") || "—") + "]" +
        "  parallel_group=" + (task.parallel_group === null ? "null" : task.parallel_group);
      const actions = document.createElement("div");
      actions.className = "actions";

      const reason = document.createElement("input");
      reason.type = "text";
      reason.placeholder = "Grund (Pflicht)";
      reason.className = "reason";

      if (status === "ready") {
        const submit = document.createElement("button");
        submit.textContent = "simuliert abgeben";
        submit.className = "primary";
        submit.onclick = () =>
          call(`${task.id}: submit()`, () =>
            planner.submit(task.id, { simulated: true, source: "Browser-Demo" },
              "manueller Demo-Klick")
          , "Ergebnis gespeichert, wartet auf AEGIS-Prüfung");
        actions.appendChild(submit);
      }
      if (status === "pending" || status === "rejected") {
        const frei = document.createElement("button");
        frei.textContent = "Prüfung FREI";
        frei.className = "good";
        frei.onclick = () =>
          call(`${task.id}: review(FREI)`, () =>
            planner.review(task.id, "FREI", reason.value.trim() || "Browser-Demo-Prüfung")
          , "Abhängigkeit erfüllt");
        const vetoBtn = document.createElement("button");
        vetoBtn.textContent = "Prüfung VETO";
        vetoBtn.className = "danger";
        vetoBtn.onclick = () =>
          call(`${task.id}: review(VETO)`, () =>
            planner.review(task.id, "VETO", reason.value.trim() || "abgelehnt in der Demo")
          , "globales Veto wurde erzeugt");
        actions.appendChild(frei);
        actions.appendChild(vetoBtn);
        actions.appendChild(reason);
      }
      if (status === "free") {
        const note = document.createElement("span");
        note.className = "meta";
        note.textContent = "Review ist unveränderlich; Änderungen nur über neuen Plan/Lauf.";
        actions.appendChild(note);
      }

      card.append(head, title, meta, actions);
      box.appendChild(card);
    });

    if (!$("snapshot-panel").hidden) {
      $("snapshot-json").textContent = JSON.stringify(snap, null, 2);
    }
  }

  /* ---------- Bedienung ---------- */
  $("btn-approve").onclick = () =>
    call("approve()", () =>
      planner.approve($("cmd").value, $("approve-reason").value)
    , "Fortschritte freigeschaltet — nur Bereitschaft, keine Ausführungsrechte.");

  $("btn-pause").onclick = () =>
    call("pause()", () => planner.pause("Menschliche Pause in der Browser-Demo"),
      "Freigabe entzogen; neue Freigabe nötig");

  $("btn-veto").onclick = () =>
    call("veto()", () =>
      planner.veto($("veto-id").value, $("veto-rule").value, $("veto-artifact").value,
        $("veto-reason").value)
    , "globale Sperre aktiv");

  $("btn-override").onclick = () =>
    call("override()", () =>
      planner.override($("override-cmd").value, $("override-reason").value)
    , "genau dieses Veto aufgehoben");

  $("btn-reset").onclick = () => { if (!replaying) reset(); };

  $("btn-snapshot").onclick = () => {
    const panel = $("snapshot-panel");
    panel.hidden = !panel.hidden;
    render();
  };

  /* ---------- Replay des ersten Laufs ---------- */
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));

  function replaySubmit(taskId) {
    const data = REPLAY_RESULTS[taskId];
    planner.submit(taskId, JSON.parse(JSON.stringify(data.output)),
      "Replay des ersten Laufs — nur simulierte Ergebnisdaten");
  }
  function replayFree(taskId) {
    const data = REPLAY_RESULTS[taskId];
    planner.review(taskId, "FREI",
      (data.aegis_review && data.aegis_review.reason) || "statische Demo-Prüfung (Replay)");
  }

  async function replay() {
    if (replaying) return;
    replaying = true;
    $("btn-replay").disabled = true;
    $("btn-reset").disabled = true;
    try {
      reset();
      log("info", "Replay beginnt: exakt die Abfolge aus demo/run_demo.py.");
      planner.approve("j", "Replay-Freigabe durch die Demo (entspricht dem menschlichen j).");
      render();
      await wait(260);
      const ids = PLAN.map((t) => t.id);
      for (const id of ids) {
        if (id === "t5") {
          replaySubmit("t5");
          log("ok", "t5: submit() (Replay-Daten)");
          await wait(220);
          planner.review("t5", "VETO", "Demo: Prüfer lehnt ab; ein VETO blockiert global.");
          log("ok", "t5: review(VETO) → globales Veto review-t5-1");
          render();
          await wait(260);
          try { planner.ready(); } catch (e) { log("err", "ready() → " + e.name + ": " + e.message); }
          planner.override("override review-t5-1", "Demo: Mensch hebt genau dieses Veto auf.");
          log("ok", "override review-t5-1 akzeptiert");
          render();
          await wait(220);
          replayFree("t5");
          log("ok", "t5: zweite Prüfung FREI (Override ersetzt nie die Prüfung)");
          render();
          await wait(240);
          continue;
        }
        replaySubmit(id);
        log("ok", id + ": submit() (Replay-Daten)");
        await wait(160);
        replayFree(id);
        log("ok", id + ": review FREI");
        render();
        await wait(200);
      }
      const snap = planner.snapshot();
      log("ok", `Replay fertig: ${snap.results.size ?? Object.keys(snap.results).length} Ergebnisse, ` +
        `${Object.keys(snap.reviews).length} FREI-Prüfungen, ${snap.events.length} Audit-Ereignisse, ` +
        `keine offenen Vetos.`);
    } finally {
      replaying = false;
      $("btn-replay").disabled = false;
      $("btn-reset").disabled = false;
      render();
    }
  }

  $("btn-replay").onclick = replay;

  reset();
})();
