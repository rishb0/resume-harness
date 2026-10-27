#!/usr/bin/env python3
"""Copy the final files into exports/vN/ with employer-ready names.

Names: FirstName_LastName_Resume.pdf, FirstName_LastName_Resume.docx, and, for the documents the
start menu asked for, FirstName_LastName_Resume_Photo.pdf, FirstName_LastName_Cover-Letter.pdf and
FirstName_LastName_CV.pdf / .docx. The LaTeX source and the Overleaf zip are copied too. Each export
goes into a new folder (v1, v2, ...), so nothing is ever overwritten.

Python 3.9+, standard library only.
"""
from __future__ import annotations

import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Tuple

import rhlib
from rhlib import RHError


def file_stem_from_name(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    words = [w for w in re.split(r"[^A-Za-z0-9]+", ascii_name) if w]
    return "_".join(w[:1].upper() + w[1:] for w in words) or "Candidate"


def export(root: Path, person: str, app_id: str) -> Dict[str, Any]:
    d = rhlib.app_dir(root, person, app_id)
    contact = rhlib.load_contact(root, person)
    if not contact.get("name"):
        raise RHError("No private contact name saved, so the file name cannot be made.",
                      f"Open the private form: python scripts/rh.py contact form {person}")
    app = rhlib.read_json(d / "app.json")
    st = rhlib.app_settings(root, person, app_id)
    build = app.get("build") or {}
    build_version = build.get("version")
    if not isinstance(build_version, int) or build_version < 1:
        build_version = None

    def pick(stem: str, ext: str):
        """The file from the recorded build, or the newest file for an older application."""
        if build_version is not None:
            path = d / f"{stem}.v{build_version}.{ext}"
            return (build_version, path) if path.exists() else None
        return rhlib.latest_version(d, stem, ext)

    pdf = pick("resume", "pdf")
    docx = pick("resume", "docx")
    if not pdf and not docx:
        raise RHError("Nothing to export from the current build yet.",
                      "Build first: python scripts/rh.py build <person> <app>")
    tex = pick("resume", "tex")
    overleaf = pick("overleaf-resume", "zip")
    photo = pick("resume-photo", "pdf") if st["photo"] else None
    letter = pick("cover-letter", "pdf") if st["cover_letter"] else None
    cv_pdf = pick("cv", "pdf") if st["cv"] else None
    cv_docx = pick("cv", "docx") if st["cv"] else None
    missing: List[str] = []
    if not pdf:
        missing.append("no PDF was made by the current build")
    if not docx:
        missing.append("no Word file was made by the current build")
    if st["photo"] and not photo:
        missing.append("the photo is on but the current build has no photo PDF")
    if st["cover_letter"] and not letter:
        missing.append("the cover letter is on but the current build has no cover-letter PDF")
    if st["cv"] and (not cv_pdf or not cv_docx):
        missing.append("the CV is on but the current build is missing a CV file")
    base = file_stem_from_name(contact["name"])
    exports = d / "exports"
    exports.mkdir(exist_ok=True)
    n = 1
    while (exports / f"v{n}").exists():
        n += 1
    target = exports / f"v{n}"
    target.mkdir()
    copied: List[Path] = []
    items: List[Tuple[str, Path]] = []
    for src, name, role in (
            (pdf, f"{base}_Resume.pdf", "Resume (PDF) - send this one"),
            (docx, f"{base}_Resume.docx", "Resume (Word file)"),
            (photo, f"{base}_Resume_Photo.pdf", "Resume with photo (PDF)"),
            (letter, f"{base}_Cover-Letter.pdf", "Cover letter (PDF)"),
            (cv_pdf, f"{base}_CV.pdf", "CV (PDF)"),
            (cv_docx, f"{base}_CV.docx", "CV (Word file)"),
            (tex, f"{base}_Resume.tex", "LaTeX source"),
            (overleaf, f"{base}_Overleaf.zip", "Overleaf project (zip)")):
        if src:
            dest = target / name
            with open(dest, "xb") as handle:
                handle.write(src[1].read_bytes())
            copied.append(dest)
            items.append((role, dest))
    reports = rhlib.latest_version(d, "ats-report", "md")
    warnings: List[str] = []
    if missing:
        warnings.append("Rebuild before sending: " + "; ".join(missing) + ".")
    if not reports:
        warnings.append("No ATS check has been run on this application. Run: python scripts/rh.py check <person> <app>")
    else:
        if pdf and reports[1].stat().st_mtime < pdf[1].stat().st_mtime:
            warnings.append("The newest PDF is newer than the last ATS check. Run the check again before sending.")
        fails = rhlib.report_fail_count(reports[1])
        if fails is None:
            warnings.append("The last ATS check report could not be read. Run the check again before sending.")
        elif fails:
            warnings.append(f"The last ATS check reported {fails} FAIL. Fix them and run the check again before sending.")
    return {"folder": target, "files": copied, "items": items,
            "warning": " ".join(warnings) if warnings else None, "version": n}
