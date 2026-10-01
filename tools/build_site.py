"""Baut die statische GitHub-Pages-Seite unter docs/ — Standardbibliothek, keine Netzzugriffe.

Quellen:
  aether/*.md            → docs/doku/*.html   (minimale Markdown-Konvertierung)
  aether/*.json, run.log → docs/assets/artifacts.js (eingebettete Rohdaten für die Demo)
  demo/run_demo.py       → docs/doku/transcript.html (frisch ausgeführtes Transkript)
  docs-src/**            → docs/**            (statische Seiten, 1:1 kopiert)

Das Ergebnis wird committet, damit der Pages-Workflow kein Build-Toolchain braucht.
Rebuild nach Änderungen an aether/, demo/ oder docs-src/:  python3 tools/build_site.py
"""

import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AETHER = ROOT / "aether"
SRC = ROOT / "docs-src"
OUT = ROOT / "docs"
DOKU = OUT / "doku"

DOC_PAGES = [
    ("readme", "README.md", "Aether-README"),
    ("goal", "goal.md", "Ziel & Leitplanke"),
    ("agents", "agents.md", "Rollen & Rahmen"),
    ("contracts", "contracts.md", "Datenverträge"),
    ("operations", "operations.md", "Betrieb & Übergabe"),
    ("threat_model", "threat_model.md", "Bedrohungsmodell"),
]

NAV = [
    ("../index.html", "Start"),
    ("../demo.html", "Interaktive Demo"),
    ("transcript.html", "Skript-Transkript"),
    ("readme.html", "Doku"),
    ("artefakte.html", "Artefakte"),
    ("https://github.com/emborei/SkynetOnCyberCrack", "Repository"),
]


def escape(value):
    return html.escape(str(value), quote=True)


def inline_markdown(line):
    """Escaped Inline-Markdown: Code, Fett, Links (numerisch referenziert verboten)."""
    placeholders = []

    def stash(fragment):
        placeholders.append(fragment)
        return f"\x00{len(placeholders) - 1}\x00"

    def code(match):
        return stash(f"<code>{match.group(1)}</code>")

    line = re.sub(r"`([^`]+)`", lambda m: code(m), line)

    def link(match):
        text, url = match.group(1), match.group(2)
        return stash(f'<a href="{url}">{text}</a>')

    line = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, line)
    line = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", line)
    for index, fragment in enumerate(placeholders):
        line = line.replace(f"\x00{index}\x00", fragment)
    return line


def markdown_to_html(source):
    """Minimaler Markdown-Teilmengen-Konverter für die repo-eigenen Dokumente.

    Unterstützt: Überschriften, Absätze, Codezäune, Blockquotes, Aufzählungen,
    Tabellen, Inline-Auszeichnung. Bewusst kein voller Markdown-Parser.
    """
    out = []
    lines = source.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped.startswith("```"):
            index += 1
            buffer = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                buffer.append(lines[index])
                index += 1
            index += 1
            out.append("<pre><code>" + escape("\n".join(buffer)) + "</code></pre>")
            continue
        match = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if match:
            level = len(match.group(1))
            out.append(f"<h{level}>{inline_markdown(escape(match.group(2)))}</h{level}>")
            index += 1
            continue
        if stripped.startswith(">"):
            buffer = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                buffer.append(lines[index].strip().lstrip(">").strip())
                index += 1
            out.append("<blockquote>" + inline_markdown(escape(" ".join(
                part for part in buffer if part))) + "</blockquote>")
            continue
        if stripped.startswith("|") and index + 1 < len(lines) and \
                re.match(r"^\|[\s:|-]+\|$", lines[index + 1].strip()):
            header = [c.strip() for c in stripped.strip("|").split("|")]
            index += 2
            rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append([c.strip() for c in lines[index].strip().strip("|").split("|")])
                index += 1
            table = ["<table><thead><tr>"]
            table += [f"<th>{inline_markdown(escape(cell))}</th>" for cell in header]
            table.append("</tr></thead><tbody>")
            for row in rows:
                table.append("<tr>")
                table += [f"<td>{inline_markdown(escape(cell))}</td>" for cell in row]
                table.append("</tr>")
            table.append("</tbody></table>")
            out.append("".join(table))
            continue
        if re.match(r"^[-*]\s+", stripped):
            items = []
            while index < len(lines) and re.match(r"^\s*[-*]\s+", lines[index]):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[index]))
                index += 1
            out.append("<ul>" + "".join(
                f"<li>{inline_markdown(escape(item))}</li>" for item in items) + "</ul>")
            continue
        if not stripped:
            index += 1
            continue
        buffer = []
        while index < len(lines) and lines[index].strip() and \
                not re.match(r"^(#{1,4}\s|```|>|\||[-*]\s)", lines[index].strip()):
            buffer.append(lines[index].strip())
            index += 1
        out.append("<p>" + inline_markdown(escape(" ".join(buffer))) + "</p>")
    return "\n".join(out)


def page(title, body, active=None, subtitle=""):
    nav = []
    for href, label in NAV:
        marker = ' class="active"' if href == active else ""
        nav.append(f'<a{marker} href="{href}">{label}</a>')
    subtitle_html = f'<p class="lead">{subtitle}</p>' if subtitle else ""
    return (
        "<!DOCTYPE html>\n<html lang=\"de\">\n<head>\n"
        "<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{escape(title)} · Aether-Demo</title>\n"
        f'<meta name="description" content="{escape(title)} — lokale Aether-Demo ohne Tracking.">\n'
        "<link rel=\"stylesheet\" href=\"../assets/style.css\">\n</head>\n<body>\n"
        "<header class=\"site\"><div class=\"wrap nav\">"
        "<span class=\"brand\">AETHER<span>·</span>SKYNET<span>·</span>DEMO</span>"
        + "".join(nav) + "</div></header>\n"
        "<main class=\"wrap\">\n" + f"<h1>{escape(title)}</h1>\n" + subtitle_html + body +
        "\n</main>\n<footer class=\"site\"><div class=\"wrap\">"
        "Erzeugt von <code>tools/build_site.py</code> aus den Repo-Artefakten · "
        "keine Cookies, keine Analysen, keine externen Ressourcen</div></footer>\n"
        "</body>\n</html>\n"
    )


def load_json(name):
    return json.loads((AETHER / name).read_text(encoding="utf-8"))


def build_artifacts_js():
    results = {}
    for path in sorted(AETHER.glob("result_t*.json"),
                       key=lambda p: int(re.search(r"t(\d+)", p.stem).group(1))):
        results[path.stem.split("_", 1)[1]] = json.loads(path.read_text(encoding="utf-8"))
    data = {
        "plan": json.loads((AETHER / "plan.json").read_text(encoding="utf-8")),
        "results": results,
        "approval": load_json("approval.json"),
        "planReview": load_json("plan_review.json"),
        "finalReview": load_json("final_review.json"),
        "summary": load_json("summary.json"),
        "example": load_json("example_simulated.json"),
        "runLog": (AETHER / "run.log").read_text(encoding="utf-8"),
    }
    rendered = json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/")
    OUT.joinpath("assets").mkdir(parents=True, exist_ok=True)
    (OUT / "assets" / "artifacts.js").write_text(
        "/* Generiert von tools/build_site.py — Rohdaten aus aether/, unverändert übernommen. */\n"
        "window.AETHER = " + rendered + ";\n", encoding="utf-8")
    return data


def build_docs():
    DOKU.mkdir(parents=True, exist_ok=True)
    for slug, filename, title in DOC_PAGES:
        body = markdown_to_html((AETHER / filename).read_text(encoding="utf-8"))
        (DOKU / f"{slug}.html").write_text(
            page(title, body, active=f"{slug}.html",
                 subtitle=f"Quelle: <code>aether/{filename}</code> (unverändert konvertiert)."),
            encoding="utf-8")


def build_artifacts_page(data):
    sections = []
    titles = {"approval": "approval.json", "plan": "plan.json",
              "planReview": "plan_review.json", "finalReview": "final_review.json",
              "summary": "summary.json", "example": "example_simulated.json"}
    sections.append("<p>Unveränderte Kopien der Text-Artefakte aus dem ersten Lauf. "
                    "Sie sind Dokumentation — keine automatische Laufzeitfreigabe.</p>")
    for key in ("approval", "plan", "planReview", "finalReview"):
        rendered = json.dumps(data[key], ensure_ascii=False, indent=2)
        heading = "Aether-Plan (9 Tasks)" if key == "plan" else titles[key]
        sections.append(f"<h2>{escape(heading)}</h2>\n<pre><code>{escape(rendered)}</code></pre>")
    task_blocks = []
    for task_id, result in data["results"].items():
        review = result.get("aegis_review", {})
        task_blocks.append(
            f"<h3>result_{task_id}.json</h3>\n"
            f"<pre><code>{escape(json.dumps(result, ensure_ascii=False, indent=2))}</code></pre>"
            + (f"<p>Die eingebettete Rollenprüfung: <strong>{escape(review.get('status', '—'))}</strong> — "
               f"{escape(review.get('reason', ''))}</p>" if review else "")
        )
    sections.append("<h2>Task-Ergebnisse t0 bis t8</h2>" + "".join(task_blocks))
    for key, title in (("summary", "summary.json"), ("example", "example_simulated.json")):
        rendered = json.dumps(data[key], ensure_ascii=False, indent=2)
        sections.append(f"<h2>{title}</h2>\n<pre><code>{escape(rendered)}</code></pre>")
    sections.append("<h2>run.log</h2>\n<pre><code>" + escape(data["runLog"]) + "</code></pre>")
    (DOKU / "artefakte.html").write_text(
        page("Artefakte des ersten Laufs", "\n".join(sections), active="artefakte.html"),
        encoding="utf-8")


def build_transcript():
    run = subprocess.run([sys.executable, str(ROOT / "demo" / "run_demo.py")],
                         capture_output=True, text=True, timeout=120, cwd=ROOT)
    if run.returncode != 0:
        raise SystemExit("Demo fehlgeschlagen:\n" + run.stderr)
    body = (
        "<p>Erzeugt bei jedem Aufruf von <code>python3 tools/build_site.py</code> durch "
        "Ausführung von <code>python3 demo/run_demo.py</code> gegen die echte Bibliothek "
        f"<code>aether/planner.py</code> (dieser Build lief mit Python {escape(sys.version.split()[0])}). "
        "Deterministisch: keine Zeitstempel, keine Pfade des Build-Rechners.</p>"
        "<pre><code>" + escape(run.stdout) + "</code></pre>"
    )
    (DOKU / "transcript.html").write_text(
        page("Skript-Transkript der echten Gates", body, active="transcript.html"),
        encoding="utf-8")


def copy_static():
    for path in SRC.iterdir():
        if path.suffix == ".html":
            OUT.joinpath(path.name).write_bytes(path.read_bytes())
    assets_src = SRC / "assets"
    assets_out = OUT / "assets"
    assets_out.mkdir(parents=True, exist_ok=True)
    for path in assets_src.iterdir():
        if path.name != "artifacts.js":
            assets_out.joinpath(path.name).write_bytes(path.read_bytes())
    (OUT / ".nojekyll").write_text("", encoding="utf-8")


def main():
    data = build_artifacts_js()
    build_docs()
    build_artifacts_page(data)
    build_transcript()
    copy_static()
    files = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file())
    print(f"SITE OK | {len(files)} Dateien unter docs/:")
    for name in files:
        print("  ", name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
