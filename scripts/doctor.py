#!/usr/bin/env python3
"""Setup check for users:  python scripts/rh.py doctor

Answers one question clearly: is this computer ready to use the Resume Harness?
It changes nothing and never touches saved data. It builds a test PDF from the fictional
example files, in memory, to prove the PDF engine really works.

Required items (Python, harness files, a usable data folder) decide the exit code.
PDF output, the ATS text tool, and an OpenCode or Claude Code command are reported
separately, because the harness still makes the Word file and the Overleaf zip without them.

Python 3.9+, standard library only.
"""
from __future__ import annotations

import json
import platform
import shutil
import sys
import tempfile
from pathlib import Path
from typing import List

import build_resume
import rhlib

EXPECTED_SKILLS = ["resume-workflow", "onboard-profile", "company-recon", "job-analysis",
                   "resume-strategy", "resume-writer", "latex-builder", "ats-and-review"]
REQUIRED_FILES = ["AGENTS.md", "config/settings.json", "config/profile_schema.json", "config/regions.json",
                  "templates/latex/ats-classic/template.tex"]


def _tex_hint() -> str:
    system = platform.system()
    if system == "Linux":
        return ("On Debian or Ubuntu run: sudo apt install texlive-latex-base texlive-latex-extra poppler-utils "
                "(other Linux systems: install the equivalent TeX Live packages).")
    if system == "Darwin":
        return "On macOS with Homebrew run: brew install --cask mactex-no-gui (large), or brew install tectonic (small)."
    if system == "Windows":
        return "On Windows install MiKTeX from miktex.org and let it install missing packages automatically, or install tectonic."
    return "Install a TeX distribution that provides pdflatex (TeX Live or MiKTeX), or tectonic."


def _pdf_text_hint() -> str:
    system = platform.system()
    if system == "Linux":
        return "Run: sudo apt install poppler-utils   (or: pip install pypdf)"
    if system == "Darwin":
        return "Run: brew install poppler   (or: pip install pypdf)"
    return "Run: pip install pypdf   (or install poppler)"


def _nearest_existing(path: Path) -> Path:
    while not path.exists() and path != path.parent:
        path = path.parent
    return path


def run() -> int:
    lines: List[str] = []
    required_failed = False
    pdf_ready = False

    def ok(text: str) -> None:
        lines.append(f"OK    {text}")

    def need(text: str, hint: str) -> None:
        nonlocal required_failed
        required_failed = True
        lines.append(f"FIX   (required) {text}")
        lines.append(f"      {hint}")

    def optional(text: str, hint: str) -> None:
        lines.append(f"NOTE  (optional) {text}")
        lines.append(f"      {hint}")

    # 1. Python
    v = sys.version_info
    command = rhlib.python_command()
    if v >= (3, 9):
        ok(f"Python {v.major}.{v.minor}.{v.micro} at {sys.executable}")
        ok(f"Run harness commands as: {command} scripts/rh.py <command>")
        if command != "python":
            lines.append(f"      Use that form if plain 'python' is not found on this machine.")
    else:
        need(f"Python {v.major}.{v.minor} is too old.", "Install Python 3.9 or newer from python.org, then run this check again.")

    # 2. harness files
    root = rhlib.HARNESS_ROOT
    missing = [f for f in REQUIRED_FILES if not (root / f).exists()]
    skills_dir = root / ".claude" / "skills"
    missing += [f".claude/skills/{s}/SKILL.md" for s in EXPECTED_SKILLS if not (skills_dir / s / "SKILL.md").exists()]
    if missing:
        need("Some harness files are missing: " + ", ".join(missing[:6]) + (" ..." if len(missing) > 6 else ""),
             "Download the harness again. The hidden folders .claude and .opencode must be copied as well.")
    else:
        ok("All harness files and the 8 skills are present")

    # 3. data folder
    data_root = rhlib.resolve_data_root()
    if data_root == root or rhlib._inside(data_root, root):
        need(f"The data folder is inside the harness folder: {data_root}",
             "Choose a folder outside it: python scripts/rh.py set-data-dir <folder>")
    elif data_root.exists() and not data_root.is_dir():
        need(f"The data folder path is a file, not a folder: {data_root}",
             "Choose a folder path: python scripts/rh.py set-data-dir <folder>")
    elif (data_root / rhlib.MARKER_NAME).exists():
        people = len(list((data_root / "people").iterdir())) if (data_root / "people").exists() else 0
        ok(f"Data folder exists: {data_root} ({people} saved people)")
    elif data_root.exists() and any(data_root.iterdir()):
        need(f"{data_root} exists and is not a Resume Harness data folder.",
             "Choose another folder: python scripts/rh.py set-data-dir <folder>")
    else:
        try:
            with tempfile.TemporaryFile(dir=_nearest_existing(data_root)):
                pass
            ok(f"Data folder will be created on first use: {data_root}")
        except OSError:
            need(f"Cannot write to {data_root}.", "Choose a folder you can write to: python scripts/rh.py set-data-dir <folder>")

    # 4. PDF engine, proven with a real test build
    engine = build_resume.find_engine()
    if not engine:
        optional("No TeX engine found, so PDF files cannot be made. The Word file (DOCX) and the Overleaf zip still work.", _tex_hint())
    else:
        try:
            ex = root / "examples"
            md = (ex / "example-resume.md").read_text(encoding="utf-8")
            contact = json.loads((ex / "example-contact.json").read_text(encoding="utf-8"))
            tex, _warnings, _doc = build_resume.build_latex(md, contact, "a4", "doctor", rhlib.settings()["autofit_presets"][2])
            res = build_resume.compile_tex(tex, passes=1)
        except Exception as exc:  # noqa: BLE001
            res = {"pdf": None, "info": f"{type(exc).__name__}: {exc}", "pages": None}
        if res["pdf"]:
            pdf_ready = True
            ok(f"PDF engine works ({engine}): a test resume was built, {res['pages']} page")
        else:
            first = " ".join(str(res["info"]).split())[:200]
            optional(f"A TeX engine ({engine}) was found, but a test PDF could not be built: {first}",
                     "A LaTeX package is probably missing. " + _tex_hint())

    # 5. text tool for the ATS check
    if shutil.which("pdftotext"):
        ok("PDF text tool found (pdftotext): the ATS check can run")
    else:
        try:
            import pypdf  # type: ignore  # noqa: F401
            ok("PDF text tool found (pypdf): the ATS check can run")
        except ImportError:
            optional("No PDF text tool found, so the ATS check cannot read a PDF.", _pdf_text_hint())

    # 6. AI agent
    found = [name for name in ("opencode", "claude") if shutil.which(name)]
    if found:
        ok("OpenCode or Claude Code found: " + ", ".join(found))
    else:
        optional("No OpenCode or Claude Code command found on this computer's PATH.",
                 "Install one of them, or use another capable agent and ignore this note. "
                 "See docs/AGENT-INSTALL.md for all agents, or docs/INSTALL.md for the harness steps.")

    print("Resume Harness setup check")
    print("-" * 26)
    for line in lines:
        print(line)
    print()
    if required_failed:
        print("NOT READY: fix the items marked FIX (required), then run this check again.")
        return 1
    if pdf_ready:
        print("READY: everything needed is in place, including PDF output.")
    else:
        print("READY, without PDF output: you can use the harness and get the Word file and the Overleaf zip. "
              "Fix the NOTE items above to get PDFs.")
    return 0
