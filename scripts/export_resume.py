#!/usr/bin/env python3
"""Copy the final files into exports/vN/ with employer-ready names.

Names: FirstName_LastName_Resume.pdf, FirstName_LastName_Resume.docx and, if a photo version
exists, FirstName_LastName_Resume_Photo.pdf. Each export goes into a new folder (v1, v2, ...),
so nothing is ever overwritten.

Python 3.9+, standard library only.
"""
from __future__ import annotations

import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any, Dict, List

import rhlib
from rhlib import RHError


def file_stem_from_name(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    words = [w for w in re.split(r"[^A-Za-z0-9]+", ascii_name) if w]
    return "_".join(w[:1].upper() + w[1:] for w in words) or "Resume"


def export(root: Path, person: str, app_id: str) -> Dict[str, Any]:
    d = rhlib.app_dir(root, person, app_id)
    contact = rhlib.load_contact(root, person)
    if not contact.get("name"):
        raise RHError("No contact name saved, so the file name cannot be made.", "Run: python scripts/rh.py contact set <person> --name ...")
    pdf = rhlib.latest_version(d, "resume", "pdf")
    docx = rhlib.latest_version(d, "resume", "docx")
    if not pdf and not docx:
        raise RHError("Nothing to export yet.", "Build first: python scripts/rh.py build <person> <app>")
    photo = rhlib.latest_version(d, "resume-photo", "pdf")
    base = file_stem_from_name(contact["name"])
    exports = d / "exports"
    exports.mkdir(exist_ok=True)
    n = 1
    while (exports / f"v{n}").exists():
        n += 1
    target = exports / f"v{n}"
    target.mkdir()
    copied: List[Path] = []
    for src, name in ((pdf, f"{base}_Resume.pdf"), (docx, f"{base}_Resume.docx"), (photo, f"{base}_Resume_Photo.pdf")):
        if src:
            dest = target / name
            with open(dest, "xb") as handle:
                handle.write(src[1].read_bytes())
            copied.append(dest)
    reports = rhlib.latest_version(d, "ats-report", "md")
    warning = None
    if not reports:
        warning = "No ATS check has been run on this application. Run: python scripts/rh.py check <person> <app>"
    elif pdf and reports[1].stat().st_mtime < pdf[1].stat().st_mtime:
        warning = "The newest PDF is newer than the last ATS check. Run the check again before sending."
    return {"folder": target, "files": copied, "warning": warning, "version": n}
