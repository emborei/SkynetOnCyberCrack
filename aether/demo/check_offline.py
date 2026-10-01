#!/usr/bin/env python3
"""Fail the build when the site would load anything from outside itself.

Enforces veto rule A-03 mechanically instead of by promise: no remote script,
stylesheet, font, image or frame, no network API and no tracker.

Precision matters. The German copy on this very page states that it uses no
analytics, and the PRISM role description in aether/agents.md legitimately
mentions "Analytics" as a subject area. Prose is therefore not a violation:
patterns match a real external reference, a real network call or a real
tracker host/global - never a bare word.

Usage:
    python3 aether/demo/check_offline.py [SITE_DIR]
    python3 aether/demo/check_offline.py --self-test
"""

import re
import sys
from pathlib import Path

# (pattern, human readable label)
FORBIDDEN = [
    # --- resources pulled from another origin -----------------------------
    (r"<script[^>]+\bsrc\s*=\s*[\"']?\s*(?:https?:)?//", "externes Skript"),
    (r"<link[^>]+\bhref\s*=\s*[\"']?\s*(?:https?:)?//", "externe Ressource im link-Tag"),
    (r"@import\s+(?:url\()?\s*[\"']?\s*(?:https?:)?//", "CSS-Import von außen"),
    (r"\burl\(\s*[\"']?\s*(?:https?:)?//", "externe Datei in CSS"),
    (r"<img[^>]+\bsrc\s*=\s*[\"']?\s*(?:https?:)?//", "externes Bild"),
    (r"<iframe|<object\b|<embed\b", "eingebettetes Fremddokument"),
    (r"<video\b|<audio\b|<source[^>]+\bsrc\s*=", "externes Medium"),
    (r"\bimportScripts\s*\(", "Skriptimport im Worker"),
    # --- network APIs -----------------------------------------------------
    (r"\bfetch\s*\(", "fetch-Aufruf"),
    (r"\bXMLHttpRequest\b", "XMLHttpRequest"),
    (r"\bnavigator\s*\.\s*sendBeacon\b", "Beacon"),
    (r"\bnew\s+WebSocket\b", "WebSocket"),
    (r"\bEventSource\b", "EventSource"),
    # --- trackers, as host or as call, not as a word ----------------------
    (r"(?:google-analytics|googletagmanager|googlesyndication|doubleclick|"
     r"facebook|fbcdn|matomo|piwik|hotjar|mixpanel|amplitude|segmentio|"
     r"clarity|mouseflow)\.(?:com|net|org|io)", "Tracking-Domain"),
    (r"\b(?:gtag|fbq|_paq|dataLayer|mixpanel|amplitude|_hsq|twq)\s*"
     r"(?:\.\s*(?:push|track|identify|pageview)|\()", "Tracking-Aufruf"),
    (r"\bga\s*\(\s*[\"']", "Analytics-Aufruf"),
    # --- browser-side persistence -----------------------------------------
    (r"\b(?:localStorage|sessionStorage)\b", "browserseitige Speicherung"),
    (r"\bdocument\s*\.\s*cookie\b", "Cookie-Zugriff"),
]

COMPILED = [(re.compile(pattern, re.IGNORECASE), label)
            for pattern, label in FORBIDDEN]

SCANNED_SUFFIXES = {".html", ".css", ".js", ".json", ".svg", ".txt", ".mjs", ".webmanifest"}

# Known-good samples for --self-test: each must be reported.
POSITIVE_SAMPLES = [
    '<script src="https://cdn.example.com/lib.js"></script>',
    '<link rel="stylesheet" href="//fonts.example.com/x.css">',
    "@import url('https://example.com/theme.css');",
    ".bg { background: url(https://example.com/a.png); }",
    '<img src="https://example.com/pixel.gif">',
    "<iframe src=\"https://example.com\"></iframe>",
    "const r = fetch('https://example.com/log');",
    "navigator.sendBeacon('/collect', payload);",
    "window.dataLayer.push({event: 'pageview'});",
    "gtag('config', 'G-XXXX');",
    '<script async src="https://www.googletagmanager.com/gtag/js?id=G-1"></script>',
    "localStorage.setItem('visit', '1');",
    "document.cookie = 'id=1';",
]

# Known-benign samples: none of these may be reported. They are the false
# positives the earlier broad keyword rule produced.
NEGATIVE_SAMPLES = [
    "Keine Cookies, kein Analytics, keine Schriftarten von Dritten.",
    "Du bist Prism, verantwortlich für Daten, Analytics und Entscheidungsintelligenz.",
    "keine Cookies, kein Analytics, kein externer Aufruf",
    '<link rel="stylesheet" href="styles.css">',
    '<script src="data.js"></script>',
    "<a href=\"https://github.com/emborei/SkynetOnCyberCrack\">Quelle</a>",
    "background: url(tile.png);",
    "Der Begriff Tracking beschreibt hier die Abwesenheit von Überwachung.",
]


def scan_text(text):
    """Return [(line number, label, excerpt)] for one file's content."""
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        for pattern, label in COMPILED:
            if pattern.search(line):
                findings.append((number, label, line.strip()[:160]))
    return findings


def scan_file(path):
    return scan_text(path.read_text(encoding="utf-8", errors="replace"))


def self_test():
    """Prove the guard catches real violations and spares legitimate prose."""
    failures = 0
    for sample in POSITIVE_SAMPLES:
        if not scan_text(sample):
            failures += 1
            print(f"SELF-TEST MISS (should be flagged): {sample}", file=sys.stderr)
    for sample in NEGATIVE_SAMPLES:
        hits = scan_text(sample)
        if hits:
            failures += 1
            print(f"SELF-TEST FALSE POSITIVE: {sample} -> {hits[0][1]}",
                  file=sys.stderr)
    total = len(POSITIVE_SAMPLES) + len(NEGATIVE_SAMPLES)
    print(f"self-test: {total} samples, {failures} problems")
    return 1 if failures else 0


def main(argv):
    if "--self-test" in argv:
        return self_test()

    site = Path(argv[1]) if len(argv) > 1 else Path("aether/demo/_site")
    if not site.is_dir():
        print(f"ABORT: site directory not found: {site}", file=sys.stderr)
        return 2

    files = sorted(p for p in site.rglob("*") if p.is_file())
    if not files:
        print(f"ABORT: no files in {site}", file=sys.stderr)
        return 2

    total = 0
    scanned = 0
    for path in files:
        if path.suffix.lower() not in SCANNED_SUFFIXES:
            continue
        scanned += 1
        for number, label, excerpt in scan_file(path):
            total += 1
            print(f"VIOLATION {path.name}:{number} [{label}] {excerpt}",
                  file=sys.stderr)

    print(f"offline check: {scanned}/{len(files)} files scanned, {total} violations")
    if total:
        print("ABORT: the site must not load or report anything externally.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
