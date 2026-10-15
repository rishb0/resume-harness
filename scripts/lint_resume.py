#!/usr/bin/env python3
"""Resume policy checks and writing lint (run on the resume Markdown, before and after the build).

Policy (FAIL when broken):
  - Header order is name, designation (Headline), contact. A Headline line is required.
  - No social media links or handles. Professional links only, at most 3.
  - No personal data that does not belong on a resume (date of birth, marital status, ...).
  - Photo only where the region allows it and a photo is saved.
Lint (WARN): filler phrases, first-person pronouns, repeated opening verbs, long or short bullets,
long summary, wrong tense for finished jobs, mixed date styles, wrong date order, employment gaps.

Python 3.9+, standard library only.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import build_resume
import rhlib

Finding = Dict[str, str]
SUMMARY_TITLES = {"summary", "professional summary", "profile"}
WORK_TITLES = {"experience", "professional experience", "work experience", "internships", "internship"}
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
PRESENT_WORDS = {"present", "current", "ongoing", "now", "till date", "to date"}


def _f(level: str, msg: str) -> Finding:
    return {"level": level, "msg": msg}


def _term_rx(term: str) -> "re.Pattern[str]":
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])", re.I)


def _snippet(text: str, n: int = 70) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= n else text[:n - 3] + "..."


# --------------------------------------------------------------------------
# date parsing
# --------------------------------------------------------------------------

def _parse_token(token: str) -> Optional[Tuple[Any, str]]:
    t = token.strip().lower().replace(".", "")
    if t in PRESENT_WORDS:
        return "present", "present"
    m = re.fullmatch(r"([a-z]{3,9})\s+(\d{4})", t)
    if m and m.group(1)[:3] in MONTHS:
        return (int(m.group(2)), MONTHS[m.group(1)[:3]]), "monthname"
    m = re.fullmatch(r"(\d{4})[-/](\d{1,2})", t)
    if m and 1 <= int(m.group(2)) <= 12:
        return (int(m.group(1)), int(m.group(2))), "numeric"
    m = re.fullmatch(r"(\d{1,2})[-/](\d{4})", t)
    if m and 1 <= int(m.group(1)) <= 12:
        return (int(m.group(2)), int(m.group(1))), "numeric"
    m = re.fullmatch(r"(\d{4})", t)
    if m:
        return (int(m.group(1)), None), "year"
    return None


def parse_range(text: str) -> Optional[Dict[str, Any]]:
    """Returns start/end as month indexes (year*12+month), end_present flag, and token styles."""
    if not text.strip():
        return None
    parts = re.split(r"\s+(?:-|\u2013|\u2014|to)\s+", text.strip(), maxsplit=1)
    first = _parse_token(parts[0])
    if not first:
        return None
    last = _parse_token(parts[1]) if len(parts) > 1 else first
    if not last:
        return None
    today = dt.date.today()

    def idx(value: Any, is_end: bool) -> int:
        if value == "present":
            return today.year * 12 + today.month
        year, month = value
        return year * 12 + (month if month else (12 if is_end else 1))

    return {"start": idx(first[0], False), "end": idx(last[0], True), "present": last[0] == "present",
            "styles": {first[1], last[1]} - {"present"}}


# --------------------------------------------------------------------------
# policy
# --------------------------------------------------------------------------

def policy_findings(root: Path, person: str, app_id: str, md_text: str) -> List[Finding]:
    out: List[Finding] = []
    conf = rhlib.settings()
    regions = rhlib.load_regions()
    app = rhlib.app_settings(root, person, app_id)
    region = regions[app["region"]]
    doc = build_resume.parse_resume_md(md_text)
    prof_text = rhlib.profile_text(rhlib.load_profile(root, person))

    # header: name, designation, contact
    if not doc["headline"]:
        out.append(_f("FAIL", "No 'Headline:' line. The header must be: name, then designation, then contact. "
                              "Add a line such as 'Headline: Application Security Engineer | Web Testing' under the name."))
    else:
        first = doc["headline"].split("|")[0].strip().lower()
        honest = any(first.startswith(p) or (" " + p) in (" " + first) for p in conf.get("headline_honest_prefixes", []))
        if first and first in prof_text.lower():
            out.append(_f("PASS", "Header order is name, designation, contact; the designation matches a title in the profile."))
        elif honest:
            out.append(_f("PASS", "Header order is name, designation, contact; the designation is worded as a target or level."))
        else:
            out.append(_f("WARN", f"Designation \"{doc['headline'].split('|')[0].strip()}\" is not a title in the profile and has no qualifier "
                                  "(such as 'Aspiring', 'Graduate', 'Seeking'). Use the person's real title, or state the target role honestly."))

    # personal data that does not belong on a resume
    scan_text = re.sub(r"\{\{[A-Z_]+\}\}", " ", md_text)
    for term in conf.get("personal_data_terms", []):
        if _term_rx(term).search(scan_text):
            out.append(_f("FAIL", f"Personal detail \"{term}\" appears in the resume. Remove it (if it is not a personal detail, reword it)."))
    if re.search(r"\baddress\s*:", scan_text, re.I):
        out.append(_f("FAIL", "A full 'Address:' line appears. Use city and country only, in the contact line."))
    if not region["nationality"] and _term_rx("nationality").search(scan_text):
        out.append(_f("FAIL", f"'Nationality' appears, but it is not used on resumes for {region['label']}. Remove it."))
    if not any(x["level"] == "FAIL" and "Personal detail" in x["msg"] for x in out):
        out.append(_f("PASS", "No date of birth, marital status, religion, gender, parents' names, or ID numbers in the resume."))

    # links and social media
    bad_links = []
    for label, url in re.findall(r"\[([^\]]*)\]\(([^)\s]+)\)", md_text):
        try:
            rhlib.check_link(label, url)
        except rhlib.RHError as exc:
            bad_links.append(str(exc))
    for url in re.findall(r"https?://[^\s)\]]+", md_text):
        try:
            rhlib.check_link("link", url)
        except rhlib.RHError as exc:
            bad_links.append(str(exc))
    for word in conf.get("blocked_link_words", []):
        if word in ("insta", "threads"):
            continue
        if _term_rx(word).search(scan_text):
            bad_links.append(f"The resume text mentions '{word}'.")
    contact = rhlib.load_contact(root, person)
    try:
        rhlib.validate_contact_links(contact)
    except rhlib.RHError as exc:
        bad_links.append("Saved contact: " + str(exc))
    if bad_links:
        for msg in sorted(set(bad_links))[:5]:
            out.append(_f("FAIL", "Social media or too many links: " + msg))
    else:
        out.append(_f("PASS", "Links are professional only and within the limit."))

    # photo
    if app["photo"]:
        if region["photo"] == "never":
            out.append(_f("FAIL", f"Photo is switched on, but photos are not used in {region['label']}."))
        elif not rhlib.latest_photo(root, person):
            out.append(_f("FAIL", "Photo is switched on, but no photo is saved for this person."))
        else:
            out.append(_f("PASS", "Photo version will be built as an extra file; the ATS version never contains a photo."))
    out.append(_f("PASS", f"Region: {region['label']} (paper {app['paper'].upper()}, photo {'on' if app['photo'] else 'off'}, {app['pages']} page target)."))
    return out


# --------------------------------------------------------------------------
# lint
# --------------------------------------------------------------------------

def lint_findings(md_text: str) -> List[Finding]:
    conf = rhlib.settings()
    lc = conf.get("lint", {})
    doc = build_resume.parse_resume_md(md_text)
    warns: Dict[str, List[str]] = {}

    def warn(category: str, msg: str) -> None:
        warns.setdefault(category, []).append(msg)

    bullets: List[Tuple[str, str, Optional[Dict[str, Any]]]] = []  # (section, text, entry range)
    intervals: List[Tuple[int, int, str]] = []
    styles_seen: Dict[str, str] = {}
    texts: List[Tuple[str, str]] = []

    if doc["headline"]:
        texts.append(("Headline", doc["headline"]))

    for sec in doc["sections"]:
        title = sec["title"].strip().lower()
        entry_name, entry_range, entry_bullets = "", None, 0
        prev_end = None
        for kind, value in sec["blocks"]:
            if kind == "entry":
                if entry_bullets > 5:
                    warn("many", f"\"{entry_name}\" has {entry_bullets} bullets; keep the best 2 to 5.")
                entry_name, entry_bullets = value[0], 0
                rng = parse_range(value[3])
                entry_range = rng
                if value[3] and not rng:
                    warn("date", f"Dates not understood for \"{value[0]}\": \"{value[3]}\" (use 2024, Jun 2024, 2024-06, or Present).")
                if title in WORK_TITLES and not value[3]:
                    warn("date", f"\"{value[0]}\" in {sec['title']} has no dates.")
                if rng:
                    for style in rng["styles"]:
                        styles_seen.setdefault(style, value[0])
                    if prev_end is not None and (rng["end"], rng["start"]) > prev_end:
                        warn("order", f"In {sec['title']}, \"{value[0]}\" is newer than the entry above it; list the newest first.")
                    prev_end = (rng["end"], rng["start"])
                    if title in WORK_TITLES:
                        intervals.append((rng["start"], rng["end"], value[0]))
            elif kind == "bullets":
                if title in build_resume.SKILL_SECTION_TITLES:
                    continue
                for b in value:
                    bullets.append((sec["title"], b, entry_range))
                    texts.append((sec["title"], b))
                    entry_bullets += 1
            elif kind == "para":
                texts.append((sec["title"], value))
                if title in SUMMARY_TITLES:
                    words = len(value.split())
                    sentences = len([s for s in re.split(r"[.!?]+\s", value.strip()) if s.strip()])
                    if words > int(lc.get("summary_max_words", 60)):
                        warn("summary", f"Summary has {words} words; aim for {lc.get('summary_max_words', 60)} or fewer.")
                    if sentences > int(lc.get("summary_max_sentences", 3)):
                        warn("summary", f"Summary has {sentences} sentences; aim for {lc.get('summary_max_sentences', 3)} or fewer.")
        if entry_bullets > 5:
            warn("many", f"\"{entry_name}\" has {entry_bullets} bullets; keep the best 2 to 5.")

    # filler phrases and pronouns
    for section, text in texts:
        for phrase in conf.get("banned_phrases", []):
            pat = r"(?<![A-Za-z0-9])" + re.escape(phrase) + (r"\.?" if phrase == "etc" else "") + r"(?![A-Za-z0-9])"
            if re.search(pat, text, re.I):
                warn("filler", f"Filler wording \"{phrase}\" in: \"{_snippet(text)}\"")
        if re.search(r"(?<![/\w])I(?![/\w'])", text) or re.search(r"(?<![\w/])(my|me|we|our)(?![\w/])", text, re.I):
            warn("pronoun", f"First-person pronoun in: \"{_snippet(text)}\"")

    # bullet shape
    openers: Dict[str, int] = {}
    for section, text, rng in bullets:
        plain = re.sub(r"\*\*|`|\[([^\]]*)\]\([^)]*\)", r"\1", text)
        words = plain.split()
        if len(words) > int(lc.get("bullet_max_words", 30)):
            warn("length", f"Long bullet ({len(words)} words): \"{_snippet(text)}\"")
        if len(words) < int(lc.get("bullet_min_words", 5)):
            warn("length", f"Very short bullet ({len(words)} words): \"{_snippet(text)}\"")
        if words:
            first = re.sub(r"[^a-z]", "", words[0].lower())
            openers[first] = openers.get(first, 0) + 1
            if rng and not rng["present"] and first:
                if first.endswith("ing") or (first.endswith("s") and not first.endswith("ss") and len(first) > 3):
                    warn("tense", f"Finished role but the bullet starts in present tense (\"{words[0]}\"): \"{_snippet(text)}\"")
    for word, n in openers.items():
        if word and n > int(lc.get("repeat_opener_limit", 2)):
            warn("repeat", f"Opening word \"{word}\" is used {n} times. Vary the verb, but only with a verb that is true.")

    # date consistency, gaps, overlaps
    if "monthname" in styles_seen and "numeric" in styles_seen:
        warn("datestyle", "Dates mix month names (Jun 2024) and numbers (2024-06). Use one style.")
    work = sorted(intervals)
    gap_limit = int(lc.get("gap_months_warn", 6))
    for (s1, e1, n1), (s2, e2, n2) in zip(work, work[1:]):
        if s2 - e1 > gap_limit:
            warn("gap", f"About {s2 - e1} months between \"{n1}\" and \"{n2}\". Be ready to explain it, or add true activity (study, projects) for that time.")
        elif s2 < e1 - 1:
            warn("overlap", f"\"{n1}\" and \"{n2}\" overlap in time. Fine if true (for example part-time work); check the dates.")

    out: List[Finding] = []
    labels = {"filler": "Wording", "pronoun": "Wording", "repeat": "Verbs", "length": "Bullet length", "summary": "Summary",
              "tense": "Tense", "datestyle": "Dates", "date": "Dates", "order": "Date order", "gap": "Gap",
              "overlap": "Overlap", "many": "Bullets per entry"}
    for category, items in warns.items():
        for msg in items[:6]:
            out.append(_f("WARN", f"{labels.get(category, category)}: {msg}"))
        if len(items) > 6:
            out.append(_f("WARN", f"{labels.get(category, category)}: {len(items) - 6} more of the same kind."))
    if not out:
        out.append(_f("PASS", "Writing lint clean: no filler, pronouns, repeated openers, tense or date problems."))
    return out


# --------------------------------------------------------------------------
# entry points
# --------------------------------------------------------------------------

def run_lint(root: Path, person: str, app_id: str) -> Tuple[List[Finding], Path]:
    md = rhlib.app_latest(root, person, app_id, "resume-md")
    if not md:
        raise rhlib.RHError("No resume Markdown saved yet.", "Save it first: python scripts/rh.py app save <person> <app> resume-md --file <file>")
    text = md[1].read_text(encoding="utf-8")
    findings = policy_findings(root, person, app_id, text) + lint_findings(text)
    import ats_check  # local import: ats_check also imports this module
    d = rhlib.app_dir(root, person, app_id)
    path = rhlib.save_versioned(d, "lint-report", "md", ats_check.render_report("Policy and writing lint report", findings))
    return findings, path
