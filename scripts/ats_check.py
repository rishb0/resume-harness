#!/usr/bin/env python3
"""Truth check and ATS check for a built application.

truth check : every bullet traces to profile entries; skills and employers exist
              in the profile; numbers in bullets appear in the cited evidence.
ats check   : extracts the PDF text the way many ATS parsers do and checks reading
              order, headings, contact data, page count, odd characters, and keyword
              coverage against the saved job analysis.

Python 3.9+, standard library only (uses pdftotext if installed, else pypdf if installed).
"""
from __future__ import annotations

import difflib
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import build_resume
import lint_resume
import rhlib
from rhlib import RHError

Finding = Dict[str, str]
SUMMARY_TITLES = {"summary", "professional summary", "profile"}


def _f(level: str, msg: str) -> Finding:
    return {"level": level, "msg": msg}


def normalize(text: str) -> str:
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    t = t.replace("**", "").replace("`", "")
    t = re.sub(r"\s+", " ", t).strip().lower()
    return t.rstrip(".")


_NUM_RX = re.compile(r"\d[\d,]*(?:\.\d+)?%?")


def numbers_in(text: str) -> set:
    return {m.group(0).replace(",", "") for m in _NUM_RX.finditer(text)}


def contains_term(haystack: str, term: str) -> bool:
    term = term.strip()
    if not term:
        return False
    rx = r"(?<![A-Za-z0-9])" + re.escape(term.lower()) + r"(?![A-Za-z0-9])"
    return re.search(rx, haystack.lower()) is not None


def parse_evidence_map(text: str) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for raw in text.splitlines():
        line = raw.strip()
        line = re.sub(r"^[-*]\s+", "", line)
        if " => " not in line:
            continue
        claim, ids = line.rsplit(" => ", 1)
        id_list = [x for x in re.split(r"[,\s]+", ids.strip()) if x]
        key = "SUMMARY" if claim.strip().upper() == "SUMMARY" else normalize(claim)
        out[key] = {"claim": claim.strip(), "ids": id_list}
    return out


# --------------------------------------------------------------------------
# truth check
# --------------------------------------------------------------------------

def truth_findings(root: Path, person: str, app_id: str) -> List[Finding]:
    findings: List[Finding] = []
    md = rhlib.app_latest(root, person, app_id, "resume-md")
    if not md:
        raise RHError("No resume Markdown saved for this application yet.")
    emap_latest = rhlib.app_latest(root, person, app_id, "evidence-map")
    prof = rhlib.load_profile(root, person)
    by_id = {e["id"]: e for e in prof["entries"]}
    prof_text = rhlib.profile_text(prof)
    doc = build_resume.parse_resume_md(md[1].read_text(encoding="utf-8"))

    if not emap_latest:
        findings.append(_f("FAIL", "No evidence map saved. Every bullet must map to profile ids."))
        emap: Dict[str, Dict[str, Any]] = {}
    else:
        emap = parse_evidence_map(emap_latest[1].read_text(encoding="utf-8"))
    used_keys = set()

    def check_claim(label: str, claim: str, key: str) -> None:
        entry = emap.get(key)
        if entry is None and key != "SUMMARY":
            close = difflib.get_close_matches(key, list(emap.keys()), n=1, cutoff=0.9)
            if close:
                entry = emap[close[0]]
                used_keys.add(close[0])
                findings.append(_f("WARN", f"{label}: evidence-map text differs slightly from the resume text: \"{claim[:70]}\""))
        elif entry is not None:
            used_keys.add(key)
        if entry is None:
            findings.append(_f("FAIL", f"{label}: no evidence-map line for: \"{claim[:80]}\""))
            return
        if not entry["ids"]:
            findings.append(_f("FAIL", f"{label}: evidence-map line has no profile ids: \"{claim[:80]}\""))
            return
        cited_text = ""
        for i in entry["ids"]:
            if i not in by_id:
                findings.append(_f("FAIL", f"{label}: unknown profile id '{i}' for: \"{claim[:60]}\""))
            else:
                cited_text += "\n" + rhlib.entry_text(by_id[i])
        have = numbers_in(cited_text)
        for n in sorted(numbers_in(claim) - have):
            findings.append(_f("WARN", f"{label}: number '{n}' is not in the cited evidence ({', '.join(entry['ids'])}). "
                                       f"Confirm it is true and record it in the profile, or remove it."))

    for sec in doc["sections"]:
        title = sec["title"].strip().lower()
        is_skills = title in build_resume.SKILL_SECTION_TITLES
        for kind, value in sec["blocks"]:
            if kind == "entry":
                for field_name, field in (("title", value[0]), ("organization", value[1])):
                    if field and not contains_term(prof_text, re.sub(r"\*\*|`", "", field)):
                        findings.append(_f("WARN", f"Heading in '{sec['title']}': {field_name} \"{field}\" does not appear in the profile."))
            elif kind == "bullets" and is_skills:
                for item in value:
                    if ": " not in item:
                        continue
                    for skill in re.split(r"[,;]", item.split(": ", 1)[1]):
                        skill = re.sub(r"\*\*|`", "", skill).strip()
                        if skill and not contains_term(prof_text, skill):
                            findings.append(_f("FAIL", f"Skill \"{skill}\" is not in the profile. Add it only if the user confirms it is true, otherwise remove it."))
            elif kind == "bullets":
                for b in value:
                    check_claim(f"[{sec['title']}]", b, normalize(b))
            elif kind == "para" and title in SUMMARY_TITLES:
                check_claim(f"[{sec['title']}]", value, "SUMMARY")
                used_keys.add("SUMMARY")
    stale = [v["claim"] for k, v in emap.items() if k not in used_keys]
    for claim in stale[:10]:
        findings.append(_f("WARN", f"Evidence-map line not found in the resume (stale?): \"{claim[:70]}\""))
    if not [x for x in findings if x["level"] in ("FAIL", "WARN")]:
        findings.append(_f("PASS", "Every bullet maps to profile evidence; all skills, employers and numbers are supported."))
    return findings


# --------------------------------------------------------------------------
# ATS check
# --------------------------------------------------------------------------

def extract_pdf_text(pdf: Path) -> Tuple[str, Optional[int], str]:
    if shutil.which("pdftotext"):
        res = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), "-"], capture_output=True)
        text = res.stdout.decode("utf-8", errors="replace")
        pages = text.count("\f") or None
        return text, pages, "pdftotext"
    try:
        from pypdf import PdfReader  # type: ignore
        reader = PdfReader(str(pdf))
        return "\f".join((p.extract_text() or "") for p in reader.pages), len(reader.pages), "pypdf"
    except ImportError:
        raise RHError("No PDF text extractor found.",
                      "Install poppler-utils (provides pdftotext), or run: pip install pypdf")


def page_texts(text: str) -> List[str]:
    """Per-page text prepared for searching: lowercase, single spaces, split words rejoined."""
    pages = []
    for page in text.split("\f"):
        page = re.sub(r"-\s*\n\s*", "", page)                    # a word split by a hyphen at a line break
        page = re.sub(r"[^A-Za-z0-9]+", " ", page).lower()
        pages.append(" " + re.sub(r"\s+", " ", page).strip() + " ")
    return pages


def find_page(pages: List[str], phrase: str) -> Optional[int]:
    """The 0-based page a phrase lands on, or None when it cannot be found reliably."""
    words = re.findall(r"[A-Za-z0-9]+", phrase.lower())
    for size in (7, 5, 3):
        probe = words[:size]
        if len(probe) < 3:
            continue
        needle = " " + " ".join(probe) + " "
        for index, page in enumerate(pages):
            if needle in page:
                return index
    return None


def page_break_findings(doc: Dict[str, Any], text: str, pages: Optional[int]) -> List[Finding]:
    """An entry that starts on one page and finishes on the next reads badly in print."""
    if not pages or pages < 2:
        return []
    page_list = page_texts(text)
    out: List[Finding] = []
    checked = 0
    for sec in doc["sections"]:
        heading: Optional[List[str]] = None
        for kind, value in sec["blocks"]:
            if kind == "entry":
                heading = value
            elif kind == "bullets" and heading:
                fields = [x for x in heading[:2] if x]
                start = find_page(page_list, " ".join(fields))
                if start is None and fields:
                    start = find_page(page_list, fields[0])
                end = find_page(page_list, value[-1])
                if start is not None and end is not None:
                    checked += 1
                    if end > start:
                        out.append(_f("WARN", f"\"{heading[0]}\" starts on page {start + 1} and runs onto "
                                             f"page {end + 1}. Shorten it, or move a bullet, then build again."))
                heading = None
    if not out and checked >= 3:
        out.append(_f("PASS", f"No entry is split across a page break ({checked} entries checked)."))
    return out


def ats_findings(root: Path, person: str, app_id: str, pdf: Optional[Path] = None,
                 max_pages: Optional[int] = None) -> Tuple[List[Finding], Dict[str, List[str]]]:
    findings: List[Finding] = []
    coverage: Dict[str, List[str]] = {"good": [], "opportunity": [], "gap": []}
    if pdf is None:
        latest = rhlib.latest_version(rhlib.app_dir(root, person, app_id), "resume", "pdf")
        if not latest:
            raise RHError("No PDF built yet for this application.", "Build it first: python scripts/rh.py build <person> <app>")
        pdf = latest[1]
    text, pages, tool = extract_pdf_text(pdf)
    target_pages = int(rhlib.app_settings(root, person, app_id).get("pages", 1))
    max_pages = max_pages or max(int(rhlib.settings()["default_max_pages"]), target_pages)
    findings.append(_f("PASS", f"Text extracted with {tool}: {len(text)} characters."))
    if len(text.strip()) < 300:
        findings.append(_f("FAIL", "Almost no text could be extracted. An ATS would see an empty resume."))
    if pages is None:
        pages = build_resume.page_count(pdf)
    if pages:
        if pages > max_pages:
            findings.append(_f("FAIL", f"Resume has {pages} pages; the limit for this check is {max_pages}."))
        else:
            findings.append(_f("PASS", f"Page count: {pages} (limit {max_pages})."))
    if "\ufffd" in text or "(cid:" in text or re.search("[\ue000-\uf8ff]", text):
        findings.append(_f("FAIL", "Extracted text contains broken or private-use characters; fonts are not extractable."))
    else:
        findings.append(_f("PASS", "No broken characters in the extracted text."))

    contact = rhlib.load_contact(root, person)
    flat = re.sub(r"\s+", " ", text)
    digits_only = re.sub(r"\D", "", text)
    if contact.get("email"):
        findings.append(_f("PASS", "Email found in text.") if contact["email"].lower() in flat.lower()
                        else _f("FAIL", "Email is not in the extracted text."))
    if contact.get("phone"):
        want = re.sub(r"\D", "", contact["phone"])
        findings.append(_f("PASS", "Phone found in text.") if want and want in digits_only
                        else _f("FAIL", "Phone number is not in the extracted text."))
    if contact.get("name"):
        first_lines = " ".join(text.strip().splitlines()[:3]).lower()
        findings.append(_f("PASS", "Name appears at the top.") if all(t in first_lines for t in contact["name"].lower().split())
                        else _f("WARN", "Name was not found in the first lines of the extracted text."))

    md = rhlib.app_latest(root, person, app_id, "resume-md")
    if md:
        doc = build_resume.parse_resume_md(md[1].read_text(encoding="utf-8"))
        # header order in the extracted text: name, then designation, then contact
        if contact.get("name") and doc["headline"]:
            low = text.lower()
            name_at = low.find(contact["name"].lower())
            head_at = low.find(doc["headline"].split("|")[0].strip().lower(), max(name_at, 0))
            contact_at = min([low.find(x.lower()) for x in (contact.get("email", ""), contact.get("phone", "")) if x and low.find(x.lower()) >= 0] or [-1])
            if 0 <= name_at < head_at and (contact_at < 0 or head_at < contact_at):
                findings.append(_f("PASS", "Extracted text starts with name, then designation, then contact."))
            else:
                findings.append(_f("FAIL", "Header order in the extracted text is not name, designation, contact."))
        app_rec = rhlib.read_json(rhlib.app_dir(root, person, app_id) / "app.json")
        info = app_rec.get("build") or {}
        sparse = float(rhlib.settings().get("lint", {}).get("sparse_fill_warn", 0.6))
        if info.get("fill") is not None and (info.get("pages") or 1) == 1 and info["fill"] < sparse:
            findings.append(_f("WARN", f"The page is only {int(info['fill'] * 100)}% full. Add more true, relevant evidence "
                                       "(do not pad with filler); a fuller page reads as a stronger resume."))
        elif info.get("fill") is not None:
            findings.append(_f("PASS", f"Last page is {int(info['fill'] * 100)}% full (layout preset '{info.get('preset')}')."))
        standard = {h.lower() for h in rhlib.settings()["standard_headings"]}
        position = -1
        in_order = True
        for sec in doc["sections"]:
            title = sec["title"]
            if standard and title.lower() not in standard:
                findings.append(_f("WARN", f"Heading \"{title}\" is not a standard heading; an ATS may not recognise it."))
            m = re.search(r"^\s*" + re.escape(title) + r"\s*$", text, re.I | re.M)
            if not m:
                findings.append(_f("FAIL", f"Heading \"{title}\" was not found as its own line in the extracted text."))
                continue
            if m.start() < position:
                in_order = False
            position = m.start()
        if in_order:
            findings.append(_f("PASS", "Section headings appear in the same order as in the resume source."))
        else:
            findings.append(_f("FAIL", "Section headings are out of order in the extracted text (reading-order problem)."))

        # Entry cohesion: an entry's organisation, location and dates must appear before the
        # next heading or entry starts (otherwise a parser attaches them to the wrong entry).
        lines = [re.sub(r"\s+", " ", ln).strip().lower() for ln in text.splitlines()]

        def clean(value: str) -> str:
            return re.sub(r"\s+", " ", re.sub(r"\*\*|`", "", value)).strip().lower()

        marks = []  # (line index or None, kind, payload)
        cursor = 0
        for sec in doc["sections"]:
            title_l = clean(sec["title"])
            idx = next((i for i in range(cursor, len(lines)) if lines[i] == title_l), None)
            if idx is not None:
                cursor = idx + 1
            marks.append((idx, "h", None))
            for kind, value in sec["blocks"]:
                if kind != "entry" or not value[0]:
                    continue
                prim = clean(value[0])
                idx = next((i for i in range(cursor, len(lines))
                            if lines[i] and (prim in lines[i] or (len(lines[i]) >= 8 and lines[i] in prim))), None)
                if idx is not None:
                    cursor = idx + 1
                marks.append((idx, "e", value))
        broken = []
        for n, (idx, kind, value) in enumerate(marks):
            if kind != "e" or idx is None:
                continue
            nxt_idx = next((m[0] for m in marks[n + 1:] if m[0] is not None), len(lines))
            block = " ".join(lines[idx:nxt_idx])
            for other in value[1:]:
                other_n = clean(other)
                if other_n and other_n not in block:
                    broken.append(f"\"{value[0]}\" is separated from \"{other}\"")
        if broken:
            findings.append(_f("FAIL", "Reading-order problem: an entry's details are not next to its heading in the extracted text: "
                               + "; ".join(broken[:4])))
        else:
            findings.append(_f("PASS", "Each entry's organisation, location and dates stay next to its heading in the extracted text."))

        findings.extend(page_break_findings(doc, text, pages))

    app = rhlib.read_json(rhlib.app_dir(root, person, app_id) / "app.json")
    analysis = rhlib.analysis_latest(root, app["company"], app["job"])
    if not analysis:
        findings.append(_f("WARN", "No saved job analysis; keyword coverage was skipped."))
    else:
        prof_text = rhlib.profile_text(rhlib.load_profile(root, person))
        for kw in analysis[1].get("keywords", []):
            in_resume, in_profile = contains_term(text, kw), contains_term(prof_text, kw)
            if in_resume and in_profile:
                coverage["good"].append(kw)
            elif in_profile:
                coverage["opportunity"].append(kw)
            elif not in_resume:
                coverage["gap"].append(kw)
            else:
                findings.append(_f("FAIL", f"Keyword \"{kw}\" is in the resume but not in the profile (unsupported claim)."))
        total = len(analysis[1].get("keywords", [])) or 1
        findings.append(_f("PASS" if coverage["good"] else "WARN",
                           f"Keyword coverage: {len(coverage['good'])} of {total} job keywords are in the resume and supported by the profile."))
        if coverage["opportunity"]:
            findings.append(_f("WARN", "Supported by the profile but missing from the resume: " + ", ".join(coverage["opportunity"])))
        if coverage["gap"]:
            findings.append(_f("WARN", "Not supported by the profile (real gaps; never add these unless true): " + ", ".join(coverage["gap"])))
    return findings, coverage


# --------------------------------------------------------------------------
# reports
# --------------------------------------------------------------------------

def render_report(title: str, findings: List[Finding], coverage: Optional[Dict[str, List[str]]] = None) -> str:
    counts = {k: len([x for x in findings if x["level"] == k]) for k in ("FAIL", "WARN", "PASS")}
    lines = [f"# {title}", "", f"Generated: {rhlib.now_iso()}", "",
             f"Result: {counts['FAIL']} FAIL, {counts['WARN']} WARN, {counts['PASS']} PASS", ""]
    for level in ("FAIL", "WARN", "PASS"):
        items = [x for x in findings if x["level"] == level]
        if items:
            lines.append(f"## {level}")
            lines.extend(f"- {x['msg']}" for x in items)
            lines.append("")
    if coverage:
        lines += ["## Keyword coverage detail",
                  f"- In resume and supported: {', '.join(coverage['good']) or 'none'}",
                  f"- Supported but missing from resume: {', '.join(coverage['opportunity']) or 'none'}",
                  f"- Not supported by profile: {', '.join(coverage['gap']) or 'none'}", ""]
    return "\n".join(lines)


def run_truth(root: Path, person: str, app_id: str) -> Tuple[List[Finding], Path]:
    findings = truth_findings(root, person, app_id)
    d = rhlib.app_dir(root, person, app_id)
    path = rhlib.save_versioned(d, "truth-report", "md", render_report("Truth check report", findings))
    return findings, path


def run_ats(root: Path, person: str, app_id: str, pdf: Optional[Path] = None,
            max_pages: Optional[int] = None) -> Tuple[List[Finding], Path]:
    findings, coverage = ats_findings(root, person, app_id, pdf, max_pages)
    md = rhlib.app_latest(root, person, app_id, "resume-md")
    md_text = md[1].read_text(encoding="utf-8")
    findings = (truth_findings(root, person, app_id)
                + lint_resume.policy_findings(root, person, app_id, md_text)
                + lint_resume.lint_findings(md_text)
                + lint_resume.extra_document_findings(root, person, app_id)
                + findings)
    d = rhlib.app_dir(root, person, app_id)
    path = rhlib.save_versioned(d, "ats-report", "md", render_report("ATS, policy, lint and truth check report", findings, coverage))
    return findings, path
