#!/usr/bin/env python3
"""Resume policy checks and writing lint (run on the resume Markdown, before and after the build).

Policy (FAIL when broken):
  - Header order is name, designation (Headline), contact. A Headline line is required.
  - No social media links or handles. Professional links only, at most 3.
  - No personal data that does not belong on a resume (date of birth, marital status, ...).
  - Photo only where the region allows it and a photo is saved.
Lint (WARN): filler phrases, first-person pronouns, repeated opening verbs, long or short bullets,
long summary, wrong tense for finished jobs, mixed date styles, wrong date order, employment gaps,
likely typos, repeated words, a missing space after a full stop, and British and American spelling
mixed in one document. A resume with no findings in the first four groups is the goal; the rest are
questions for the writer to answer, never a reason to fail a build.

Python 3.9+, standard library only.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

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
    doc = build_resume.parse_resume_md(md_text, require_sections=False)
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
# spelling and word errors (WARN only: a warning is a question, not a failure)
# --------------------------------------------------------------------------

# Words that are almost always a typo, and the word they were meant to be.
# Keys and values are lowercase; matching is on whole words only, so a name or a
# product that contains one of these as a part is never touched.
MISSPELLINGS = {
    "acheive": "achieve", "acheived": "achieved", "acheivement": "achievement",
    "acheivements": "achievements", "acheiving": "achieving",
    "acomplished": "accomplished", "acomplishment": "accomplishment", "acomplishments": "accomplishments",
    "aditional": "additional", "adress": "address", "adressed": "addressed", "alot": "a lot",
    "arguement": "argument", "assisstance": "assistance", "attatched": "attached",
    "begining": "beginning", "buisness": "business", "busines": "business", "carrer": "career",
    "collabrated": "collaborated", "collabration": "collaboration", "comittee": "committee",
    "comunication": "communication", "concious": "conscious",
    "definately": "definitely", "developement": "development", "developper": "developer",
    "developped": "developed", "efficent": "efficient", "efficency": "efficiency",
    "enginering": "engineering", "enviroment": "environment", "enviornment": "environment",
    "excelent": "excellent", "experiance": "experience", "familar": "familiar",
    "faciliate": "facilitate", "facilited": "facilitated", "futher": "further",
    "goverment": "government", "guarentee": "guarantee", "higest": "highest",
    "immediatly": "immediately", "independant": "independent", "intergrated": "integrated",
    "knowlege": "knowledge", "liason": "liaison", "maintainance": "maintenance",
    "maintainence": "maintenance", "managable": "manageable", "managment": "management",
    "mangement": "management", "neccessary": "necessary", "neccesary": "necessary",
    "necesary": "necessary", "occured": "occurred", "occuring": "occurring",
    "perfomance": "performance", "performace": "performance", "persmission": "permission",
    "positon": "position", "profesionally": "professionally", "profesionals": "professionals",
    "proffesional": "professional", "recomend": "recommend", "recomended": "recommended",
    "recomendation": "recommendation", "recieve": "receive", "recieved": "received",
    "recieving": "receiving", "relevent": "relevant", "responsability": "responsibility",
    "responsabilities": "responsibilities", "responsibile": "responsible", "responsibilty": "responsibility",
    "resposible": "responsible", "seperate": "separate", "seperated": "separated",
    "seperately": "separately", "similiar": "similar", "specificaly": "specifically",
    "strenght": "strength", "succes": "success", "succesful": "successful",
    "succesfully": "successfully", "sucess": "success", "sucesses": "successes",
    "sucessful": "successful", "sucessfully": "successfully", "supoprt": "support",
    "suport": "support", "teh": "the", "thier": "their", "tommorow": "tomorrow",
    "untill": "until", "wich": "which", "withing": "within", "writting": "writing",
}

# A doubled word is only worth reporting for these, so that a name such as
# "Bhatt and Bhatt" is never flagged.
REPEATED_WORDS = ["a", "an", "and", "as", "at", "by", "for", "from", "in", "is", "it",
                  "of", "on", "or", "our", "that", "the", "this", "to", "we", "with"]

# British and American spellings. Both are correct English somewhere, so finding two
# forms of the same word in one document is reported as a question ("pick one"), not as
# an error. Only full words are listed, and only where the pair is unambiguous; words
# that are correct in both senses (program, licence, practice) are deliberately absent.
BRITISH_AMERICAN: List[Tuple[List[str], List[str]]] = [
    (["analyse", "analysed", "analysing"], ["analyze", "analyzed", "analyzing"]),
    (["organisation", "organisations", "organise", "organised", "organising"],
     ["organization", "organizations", "organize", "organized", "organizing"]),
    (["recognise", "recognised", "recognising"], ["recognize", "recognized", "recognizing"]),
    (["prioritise", "prioritised", "prioritising"], ["prioritize", "prioritized", "prioritizing"]),
    (["optimise", "optimised", "optimising"], ["optimize", "optimized", "optimizing"]),
    (["utilise", "utilised", "utilising"], ["utilize", "utilized", "utilizing"]),
    (["minimise", "minimised", "minimising"], ["minimize", "minimized", "minimizing"]),
    (["maximise", "maximised", "maximising"], ["maximize", "maximized", "maximizing"]),
    (["summarise", "summarised", "summarising"], ["summarize", "summarized", "summarizing"]),
    (["standardise", "standardised", "standardising"], ["standardize", "standardized", "standardizing"]),
    (["specialise", "specialised", "specialising"], ["specialize", "specialized", "specializing"]),
    (["customise", "customised", "customising"], ["customize", "customized", "customizing"]),
    (["centre", "centres"], ["center", "centers"]),
    (["behaviour", "behaviours"], ["behavior", "behaviors"]),
    (["colour", "colours"], ["color", "colors"]),
    (["favour", "favours", "favoured"], ["favor", "favors", "favored"]),
    (["defence", "defences"], ["defense", "defenses"]),
    (["catalogue", "catalogues"], ["catalog", "catalogs"]),
    (["modelling"], ["modeling"]),
    (["travelled", "travelling"], ["traveled", "traveling"]),
    (["cancelled", "cancelling"], ["canceled", "canceling"]),
    (["labelled", "labelling"], ["labeled", "labeling"]),
    (["enrolment"], ["enrollment"]),
    (["fulfilment"], ["fulfillment"]),
]


def markdown_to_plain(text: str) -> str:
    """Drop link addresses and markup, so that a spelling check sees only prose."""
    text = re.sub(r"\[([^\]]*)\]\(([^)]*)\)", r"\1", text)
    text = re.sub(r"https?://\S+|\bwww\.\S+|\b[\w.-]+\.(?:com|org|net|io|dev|ai|co)\b\S*", " ", text)
    return re.sub(r"[*`|_]", " ", text)


def _word_hits(low: str, words: List[str]) -> List[str]:
    return [w for w in words if re.search(r"(?<![A-Za-z])" + re.escape(w) + r"(?![A-Za-z])", low)]


def spelling_warnings(text: str, allow: Optional[Set[str]] = None) -> List[str]:
    """Typos, repeated words, and a missing space after a full stop. Call once per bullet or paragraph."""
    allow = allow or set()
    plain = markdown_to_plain(text)
    low = plain.lower()
    out: List[str] = []
    seen: Set[str] = set()
    for word in re.findall(r"[a-z][a-z'-]*", low):
        fix = MISSPELLINGS.get(word)
        if fix and word not in allow and word not in seen:
            seen.add(word)
            out.append(f"\"{word}\" looks like a typo for \"{fix}\".")
    for word in REPEATED_WORDS:
        if re.search(r"(?<![A-Za-z])" + word + r"\s+" + word + r"(?![A-Za-z])", low):
            out.append(f"\"{word} {word}\" is repeated.")
    m = re.search(r"[a-z]{2}\.[A-Z][a-z]{2,}", plain)
    if m:
        out.append(f"A space seems to be missing after a full stop, near \"{m.group(0)}\".")
    return out


def variant_warnings(text: str, allow: Optional[Set[str]] = None) -> List[str]:
    """Mixed British and American spelling. Pass the whole document, not one bullet."""
    allow = allow or set()
    low = markdown_to_plain(text).lower()
    out: List[str] = []
    for british, american in BRITISH_AMERICAN:
        b = _word_hits(low, british)
        a = _word_hits(low, american)
        if b and a and not set(b + a) <= allow:
            out.append(f"Mixes British and American spelling: \"{b[0]}\" and \"{a[0]}\". Pick one and use it throughout.")
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

    # spelling and word errors (WARN only)
    allow = {str(w).lower() for w in lc.get("spell_allow", [])}
    counted: Dict[str, int] = {}
    for _, item in texts:
        for msg in spelling_warnings(item, allow):
            counted[msg] = counted.get(msg, 0) + 1
    for msg, n in counted.items():
        warn("spelling", msg if n == 1 else f"{msg} (appears {n} times)")
    for msg in variant_warnings(" ".join(t for _, t in texts), allow):
        warn("spelling", msg)

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
              "overlap": "Overlap", "many": "Bullets per entry", "spelling": "Spelling"}
    for category, items in warns.items():
        for msg in items[:6]:
            out.append(_f("WARN", f"{labels.get(category, category)}: {msg}"))
        if len(items) > 6:
            out.append(_f("WARN", f"{labels.get(category, category)}: {len(items) - 6} more of the same kind."))
    if not out:
        out.append(_f("PASS", "Writing lint clean: no filler, pronouns, repeated openers, tense, date or spelling problems."))
    return out


# --------------------------------------------------------------------------
# cover letter and longer CV
# --------------------------------------------------------------------------

def _prefix(label: str, findings: List[Finding]) -> List[Finding]:
    return [{"level": item["level"], "msg": f"{label}: {item['msg']}"} for item in findings]


def prose_findings(text: str) -> List[Finding]:
    """Spelling and filler checks for cover-letter prose (first person is normal there)."""
    conf = rhlib.settings()
    lc = conf.get("lint", {})
    allow = {str(w).lower() for w in lc.get("spell_allow", [])}
    doc = build_resume.parse_letter_md(text)
    paragraphs = doc["paragraphs"]
    out: List[Finding] = []
    for paragraph in paragraphs:
        for msg in spelling_warnings(paragraph, allow):
            out.append(_f("WARN", f"Spelling: {msg}"))
        for phrase in conf.get("banned_phrases", []):
            pat = r"(?<![A-Za-z0-9])" + re.escape(phrase) + (r"\.?" if phrase == "etc" else "") + r"(?![A-Za-z0-9])"
            if re.search(pat, paragraph, re.I):
                out.append(_f("WARN", f"Wording: Filler wording \"{phrase}\" in: \"{_snippet(paragraph)}\""))
    for msg in variant_warnings(" ".join(paragraphs), allow):
        out.append(_f("WARN", f"Spelling: {msg}"))
    if not out:
        out.append(_f("PASS", "Writing lint clean: no filler or spelling problems."))
    return out


def extra_document_findings(root: Path, person: str, app_id: str) -> List[Finding]:
    """Policy and writing checks for the saved cover letter and longer CV.

    The evidence-map truth gate stays resume-specific; these checks catch the
    policy and writing errors that are mechanical. The writer still has to keep
    every claim in these documents true to the profile.
    """
    out: List[Finding] = []
    for stage, label in (("cover-letter", "Cover letter"), ("cv-md", "Longer CV")):
        latest = rhlib.app_latest(root, person, app_id, stage)
        if not latest:
            continue
        text = latest[1].read_text(encoding="utf-8")
        try:
            out.extend(_prefix(label, policy_findings(root, person, app_id, text)))
        except rhlib.RHError as exc:
            out.append(_f("FAIL", f"{label}: {exc}"))
        if stage == "cv-md":
            try:
                out.extend(_prefix(label, lint_findings(text)))
            except rhlib.RHError as exc:
                out.append(_f("FAIL", f"{label}: {exc}"))
        else:
            try:
                out.extend(_prefix(label, prose_findings(text)))
            except rhlib.RHError as exc:
                out.append(_f("FAIL", f"{label}: {exc}"))
    return out


# --------------------------------------------------------------------------
# entry points
# --------------------------------------------------------------------------

def run_lint(root: Path, person: str, app_id: str) -> Tuple[List[Finding], Path]:
    md = rhlib.app_latest(root, person, app_id, "resume-md")
    if not md:
        raise rhlib.RHError("No resume Markdown saved yet.", "Save it first: python scripts/rh.py app save <person> <app> resume-md --file <file>")
    text = md[1].read_text(encoding="utf-8")
    findings = (policy_findings(root, person, app_id, text) + lint_findings(text)
                + extra_document_findings(root, person, app_id))
    import ats_check  # local import: ats_check also imports this module
    d = rhlib.app_dir(root, person, app_id)
    path = rhlib.save_versioned(d, "lint-report", "md", ats_check.render_report("Policy and writing lint report", findings))
    return findings, path
