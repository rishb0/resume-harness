#!/usr/bin/env python3
"""Resume Harness command line tool. Python 3.9+, standard library only.

The agent uses this tool for EVERY read and write of user data. It chooses all
file names, refuses to overwrite, detects duplicates, and prints a NEXT: hint.

Run:  python scripts/rh.py --help      (use python3 if 'python' is not found)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ats_check  # noqa: E402
import build_resume  # noqa: E402
import doctor  # noqa: E402
import export_resume  # noqa: E402
import lint_resume  # noqa: E402
import rhlib  # noqa: E402
from rhlib import RHError  # noqa: E402


def out(*lines: str) -> None:
    for line in lines:
        print(line)


def nxt(text: str) -> None:
    print(f"NEXT: {text}")


def load_json_arg(path_str: str) -> Any:
    text = rhlib.read_input(path_str)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RHError(f"The input is not valid JSON: {exc}", "Fix the JSON syntax (quotes, commas, brackets) and retry.")


def root_for_write() -> Path:
    return rhlib.ensure_root(create=True)


def root_for_read() -> Path:
    return rhlib.ensure_root(create=True)


def reindex(root: Path) -> None:
    rhlib.write_index(root)


# --------------------------------------------------------------------------
# global commands
# --------------------------------------------------------------------------

def cmd_doctor(a) -> None:
    sys.exit(doctor.run())


def cmd_where(a) -> None:
    root = rhlib.resolve_data_root()
    exists = (root / rhlib.MARKER_NAME).exists()
    out(f"Data folder: {root}", f"Exists: {'yes' if exists else 'no (created automatically on first save)'}",
        f"Harness folder: {rhlib.HARNESS_ROOT}")


def cmd_set_data_dir(a) -> None:
    path = Path(a.path).expanduser().resolve()
    if path == rhlib.HARNESS_ROOT or rhlib._inside(path, rhlib.HARNESS_ROOT):
        raise RHError("The data folder must be outside the harness folder.")
    rhlib.POINTER_FILE.write_text(str(path) + "\n", encoding="utf-8")
    out(f"Data folder set to: {path}",
        "This choice is stored in config/data_location.txt (local to this computer, not shared).")
    nxt("Run: python scripts/rh.py init")


def cmd_init(a) -> None:
    root = rhlib.ensure_root(create=True)
    reindex(root)
    out(f"Data folder ready: {root}")
    nxt("python scripts/rh.py status")


def cmd_status(a) -> None:
    root = root_for_read()
    people = rhlib.list_people(root)
    companies = rhlib.list_companies(root)
    jobs = sum(len(rhlib.list_jobs(root, c["slug"])) for c in companies)
    apps = sum(len(rhlib.list_apps(root, p["slug"])) for p in people)
    out(f"Data folder: {root}", f"People: {len(people)}", f"Companies: {len(companies)}",
        f"Jobs: {jobs}", f"Applications: {apps}", f"Human-readable index: {root / 'INDEX.md'}")
    reindex(root)
    nxt("python scripts/rh.py person list")


def cmd_index(a) -> None:
    root = root_for_read()
    out(f"Index written: {rhlib.write_index(root)}")


def cmd_clean_scratch(a) -> None:
    n = rhlib.clean_scratch()
    out(f"Removed {n} temporary file(s) from scratch/.")


def cmd_backup(a) -> None:
    root = root_for_read()
    out(f"Backup written: {rhlib.backup(root, a.out)}")


def cmd_reset(a) -> None:
    root = rhlib.resolve_data_root()
    rhlib.reset_all(root, a.confirm)
    out(f"All data deleted: {root}", "The harness is now fresh. A new empty data folder is created on the next save.")


def cmd_forget(a) -> None:
    root = root_for_read()
    dangling = rhlib.forget(root, a.kind, a.slug, a.confirm)
    out(f"Deleted {a.kind} '{a.slug}'.")
    if dangling:
        out(f"Note: {dangling} application(s) still refer to this company; their files were kept.")
    reindex(root)


# --------------------------------------------------------------------------
# people / contact / profile
# --------------------------------------------------------------------------

def cmd_person(a) -> None:
    root = root_for_write()
    if a.action == "list":
        people = rhlib.list_people(root)
        if not people:
            out("No people saved yet.")
            nxt("Create one: python scripts/rh.py person create --name \"Full Name\"")
            return
        for p in people:
            prof = rhlib.read_json(rhlib.person_dir(root, p["slug"]) / "profile.json")
            out(f"{p['slug']}  |  {p['name']}  |  profile entries: {len(prof['entries'])}  |  updated: {p['updated']}")
        nxt("Ask the user which person this is, or create a new one.")
    elif a.action == "find":
        found = rhlib.find_people(root, a.query)
        if not found:
            out(f"No person matches '{a.query}'.")
            nxt("python scripts/rh.py person create --name \"Full Name\"")
            return
        for p in found:
            out(f"MATCH: {p['slug']}  |  {p['name']}  |  updated {p['updated']}")
        nxt("Ask the user: reuse this person's saved profile, or is this someone else?")
    elif a.action == "create":
        p = rhlib.create_person(root, a.name, a.allow_duplicate)
        reindex(root)
        out(f"Created person: {p['slug']} ({p['name']})")
        nxt(f"Collect the profile: python scripts/rh.py profile add {p['slug']} --file <json file>")
    elif a.action == "show":
        d = rhlib.person_dir(root, a.slug)
        person = rhlib.read_json(d / "person.json")
        prof = rhlib.load_profile(root, a.slug)
        contact = rhlib.load_contact(root, a.slug)
        counts = rhlib.profile_counts(prof)
        out(f"Person: {person['name']} ({person['slug']})", f"Created: {person['created']}", f"Updated: {person['updated']}",
            "Profile entries: " + (", ".join(f"{k}={v}" for k, v in counts.items()) or "none"),
            "Contact fields saved: " + (", ".join(k for k in rhlib.CONTACT_FIELDS if contact.get(k)) or "none")
            + (f", links={len(contact['links'])}" if contact.get("links") else ""))
        apps = rhlib.list_apps(root, a.slug)
        out(f"Applications: {len(apps)}")
        for ap in apps:
            out(f"  {ap['id']}  [{ap['status']}]  {ap['company_name']} - {ap['job_title']}")
        nxt("Ask the user: use this profile as it is, update it, or both?")


def cmd_contact(a) -> None:
    root = root_for_write()
    if a.action == "show":
        c = rhlib.load_contact(root, a.person)
        out(json.dumps(c, indent=2, ensure_ascii=False) if c else "No contact details saved yet.")
        return
    fields: Dict[str, str] = {}
    links: List[Tuple[str, str]] = []
    if a.file:
        data = load_json_arg(a.file)
        for k, v in data.items():
            if k == "links":
                links += [(x["label"], x["url"]) for x in v]
            else:
                fields[k] = v
    for key in rhlib.CONTACT_FIELDS:
        value = getattr(a, key)
        if value:
            fields[key] = value
    for item in a.link or []:
        if "=" not in item:
            raise RHError(f"Link '{item}' must be written as LABEL=URL.")
        label, url = item.split("=", 1)
        links.append((label, url))
    if not fields and not links and not a.remove_link:
        raise RHError("Nothing to save.", "Pass --name, --email, --phone, --location, --link LABEL=URL, --remove-link LABEL, or --file.")
    _contact, warnings = rhlib.set_contact(root, a.person, fields, links, a.remove_link)
    if a.file:
        rhlib.consume_scratch(a.file)
    reindex(root)
    out("Contact details saved (private; used only when the PDF is built).")
    for w in warnings:
        out(f"WARN: {w}")
    nxt("Continue with the workflow.")


def _entries_from_json(data: Any, default_section: Optional[str]) -> List[Tuple[str, Dict[str, Any]]]:
    if isinstance(data, dict) and "entries" in data:
        data = data["entries"]
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
        raise RHError("Profile input must be an object, a list of objects, or {\"entries\": [...]}.")
    items = []
    for i, obj in enumerate(data, 1):
        section = obj.get("section") or default_section
        if not section:
            raise RHError(f"Item {i} has no 'section' and --section was not given.")
        items.append((section, obj))
    return items


def cmd_profile(a) -> None:
    root = root_for_write()
    if a.action == "add":
        items = _entries_from_json(load_json_arg(a.file), a.section)
        ids = rhlib.profile_add(root, a.person, items, a.allow_duplicate)
        rhlib.consume_scratch(a.file)
        reindex(root)
        out(f"Saved {len(ids)} entr{'y' if len(ids) == 1 else 'ies'}: " + ", ".join(ids))
        nxt(f"python scripts/rh.py profile validate {a.person}")
    elif a.action == "update":
        entry = rhlib.profile_update(root, a.person, a.id, load_json_arg(a.file))
        rhlib.consume_scratch(a.file)
        reindex(root)
        out(f"Updated {entry['id']} (previous version kept in history/).")
    elif a.action == "remove":
        rhlib.profile_remove(root, a.person, a.id)
        reindex(root)
        out(f"Removed {a.id} (kept in the profile's 'removed' list and in history/).")
    elif a.action == "show":
        prof = rhlib.load_profile(root, a.person)
        out(json.dumps(prof, indent=2, ensure_ascii=False) if a.json else rhlib.render_profile(prof, a.section))
    elif a.action == "validate":
        errors, warnings = rhlib.profile_validate(root, a.person)
        for e in errors:
            out(f"ERROR: {e}")
        for w in warnings:
            out(f"WARN: {w}")
        out(f"Result: {len(errors)} error(s), {len(warnings)} warning(s).")
        nxt("Fix errors. Ask the user about warnings (missing metrics are worth asking about). Then continue.")


# --------------------------------------------------------------------------
# companies / recon
# --------------------------------------------------------------------------

def cmd_company(a) -> None:
    root = root_for_write()
    if a.action == "list":
        companies = rhlib.list_companies(root)
        if not companies:
            out("No companies saved yet.")
        for c in companies:
            recons = rhlib.recon_list(root, c["slug"])
            last = f"{recons[-1]['date']} ({recons[-1]['age_days']} days old)" if recons else "no recon yet"
            out(f"{c['slug']}  |  {c['name']}  |  recon: {last}  |  jobs: {len(rhlib.list_jobs(root, c['slug']))}")
    elif a.action == "find":
        found = rhlib.find_companies(root, a.query)
        if not found:
            out(f"No company matches '{a.query}'.")
            nxt("python scripts/rh.py company create --name \"Company Name\" --website <url>")
            return
        for c in found:
            recons = rhlib.recon_list(root, c["slug"])
            last = f"recon {recons[-1]['date']} ({recons[-1]['age_days']} days old)" if recons else "no recon yet"
            out(f"MATCH: {c['slug']}  |  {c['name']}  |  {last}  |  jobs: {len(rhlib.list_jobs(root, c['slug']))}")
        nxt("Ask the user: same company? Then reuse (see 'recon latest'). Different company? create with --allow-duplicate.")
    elif a.action == "create":
        c = rhlib.create_company(root, a.name, a.website, a.alias, a.allow_duplicate)
        reindex(root)
        out(f"Created company: {c['slug']} ({c['name']})")
        nxt(f"Run company recon, then: python scripts/rh.py recon save {c['slug']} --file <markdown file>")
    elif a.action == "show":
        d = rhlib.company_dir(root, a.slug)
        c = rhlib.read_json(d / "company.json")
        out(json.dumps(c, indent=2, ensure_ascii=False))
        for j in rhlib.list_jobs(root, a.slug):
            out(f"job: {j['slug']}  |  {j['title']}")


def cmd_recon(a) -> None:
    root = root_for_write()
    if a.action == "save":
        text = rhlib.read_input(a.file)
        path = rhlib.recon_save(root, a.company, text)
        rhlib.consume_scratch(a.file)
        reindex(root)
        out(f"Recon saved: {path}")
        nxt("Continue with the job description.")
        return
    recons = rhlib.recon_list(root, a.company)
    if a.action == "latest":
        if not recons:
            out("NO RECON on file for this company.")
            nxt("Run the company-recon skill, then 'recon save'.")
            return
        r = recons[-1]
        limit = int(rhlib.settings()["recon_max_age_days"])
        state = "STALE" if r["age_days"] > limit else "FRESH"
        out(f"Latest recon: {r['path']}", f"Date: {r['date']}  Age: {r['age_days']} days  State: {state} (limit {limit} days)")
        nxt("Ask the user: reuse this recon, or refresh it (a refresh is saved as a new file, nothing is overwritten)?")
    elif a.action == "show":
        if not recons:
            raise RHError("No recon saved for this company.")
        r = recons[-1]
        out(r["path"].read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# jobs
# --------------------------------------------------------------------------

def cmd_job(a) -> None:
    root = root_for_write()
    if a.action == "list":
        jobs = rhlib.list_jobs(root, a.company)
        if not jobs:
            out("No jobs saved for this company yet.")
        for j in jobs:
            has = rhlib.latest_version(rhlib.job_dir(root, a.company, j["slug"]), "analysis", "json") is not None
            out(f"{j['slug']}  |  {j['title']}  |  analysis: {'done' if has else 'not done'}")
    elif a.action == "find":
        jd = rhlib.read_input(a.jd_file) if a.jd_file else None
        found = rhlib.find_jobs(root, a.company, a.title, jd)
        for j in found["exact"]:
            out(f"EXACT MATCH (same job description text): {j['slug']}  |  {j['title']}")
        for j in found["similar"]:
            out(f"SIMILAR TITLE (different text): {j['slug']}  |  {j['title']}")
        if not found["exact"] and not found["similar"]:
            out("No existing job matches.")
            nxt(f"python scripts/rh.py job create {a.company} --title \"...\" --jd-file <file>")
        elif found["exact"]:
            nxt("Reuse it. Do not redo the job analysis. Show 'job show' and go on.")
        else:
            nxt("Ask the user: same posting (reuse) or a new posting (create with --allow-similar)?")
    elif a.action == "create":
        jd = rhlib.read_input(a.jd_file)
        job = rhlib.create_job(root, a.company, a.title, jd, a.url, a.allow_similar)
        rhlib.consume_scratch(a.jd_file)
        reindex(root)
        out(f"Created job: {job['slug']}")
        nxt(f"Analyse it, then: python scripts/rh.py job analysis-save {a.company} {job['slug']} --file <json file>")
    elif a.action == "show":
        d = rhlib.job_dir(root, a.company, a.job)
        out(json.dumps(rhlib.read_json(d / "job.json"), indent=2, ensure_ascii=False))
        latest = rhlib.latest_version(d, "analysis", "md")
        if latest:
            out("", f"--- latest analysis ({latest[1].name}) ---", latest[1].read_text(encoding="utf-8"))
        else:
            out("Analysis: not done yet.")
    elif a.action == "analysis-save":
        data = load_json_arg(a.file)
        pj, pm = rhlib.analysis_save(root, a.company, a.job, data)
        rhlib.consume_scratch(a.file)
        reindex(root)
        out(f"Analysis saved: {pj.name} and {pm.name}")
        nxt("Create or continue the application: python scripts/rh.py app find <person> --company <c> --job <j>")


# --------------------------------------------------------------------------
# applications
# --------------------------------------------------------------------------

def cmd_app(a) -> None:
    root = root_for_write()
    if a.action == "list":
        apps = rhlib.list_apps(root, a.person)
        if not apps:
            out("No applications for this person yet.")
        for ap in apps:
            out(f"{ap['id']}  [{ap['status']}]  {ap['company_name']} - {ap['job_title']}  (updated {ap['updated']})")
    elif a.action == "find":
        found = rhlib.find_apps(root, a.person, a.company, a.job)
        if not found:
            out("No existing application matches.")
            nxt("python scripts/rh.py app create <person> --company <c> --job <j>")
            return
        for ap in found:
            out(f"EXISTING: {ap['id']}  [{ap['status']}]  {ap['company_name']} - {ap['job_title']}")
        nxt("Ask the user: continue this application (new saves become the next version) or start a new one (--new)?")
    elif a.action == "create":
        ap = rhlib.create_app(root, a.person, a.company, a.job, a.new)
        reindex(root)
        out(f"Created application: {ap['id']}")
        nxt("Write the strategy and save it: python scripts/rh.py app save <person> <app> strategy --file <file>")
    elif a.action == "show":
        d = rhlib.app_dir(root, a.person, a.app)
        out(json.dumps(rhlib.read_json(d / "app.json"), indent=2, ensure_ascii=False), "", "Files:")
        out(*["  " + x for x in rhlib.app_files(root, a.person, a.app)])
    elif a.action == "files":
        out(*rhlib.app_files(root, a.person, a.app))
    elif a.action == "path":
        out(str(rhlib.app_dir(root, a.person, a.app)))
    elif a.action == "cat":
        latest = rhlib.app_latest(root, a.person, a.app, a.stage)
        if not latest:
            raise RHError(f"Nothing saved yet for stage '{a.stage}'.")
        out(latest[1].read_text(encoding="utf-8"))
    elif a.action == "save":
        text = rhlib.read_input(a.file)
        path = rhlib.app_save(root, a.person, a.app, a.stage, text)
        rhlib.consume_scratch(a.file)
        reindex(root)
        out(f"Saved: {path.name}")
        hints = {"strategy": "STOP. Show the strategy to the user and wait for approval before writing the resume.",
                 "resume-md": "Save the evidence map next (one line per bullet).",
                 "evidence-map": "Run: python scripts/rh.py truth <person> <app>, then: python scripts/rh.py lint <person> <app>",
                 "review": "Apply fixes if needed, then rebuild."}
        nxt(hints.get(a.stage, "Continue."))
    elif a.action == "status":
        rhlib.app_status(root, a.person, a.app, a.status)
        reindex(root)
        out(f"Status set to {a.status}.")
    elif a.action == "settings":
        photo = None if a.photo is None else (a.photo == "on")
        if any(x is not None for x in (a.region, photo, a.pages, a.paper)):
            st = rhlib.app_settings_set(root, a.person, a.app, a.region, photo, a.pages, a.paper, a.force)
            reindex(root)
        else:
            st = rhlib.app_settings(root, a.person, a.app)
        out(f"Region: {st['region']} ({st['region_label']})" + ("" if st["chosen"] else "  [default, not chosen yet]"),
            f"Paper: {st['paper'].upper()}", f"Page target: {st['pages']}", f"Photo version: {'on' if st['photo'] else 'off'}")
        nxt("Continue with the strategy.")


# --------------------------------------------------------------------------
# build / truth / check
# --------------------------------------------------------------------------

def cmd_photo(a) -> None:
    root = root_for_write()
    if a.action == "guide":
        out("Photo standard (a photo is optional and off by default):", *[f"- {x}" for x in rhlib.PHOTO_GUIDE])
        return
    if a.action == "set":
        path, warnings = rhlib.photo_set(root, a.person, a.file)
        reindex(root)
        out(f"Photo saved: {path.name} (private; used only in the optional photo version).",
            "Photo standard:", *[f"- {x}" for x in rhlib.PHOTO_GUIDE])
        for w in warnings:
            out(f"WARN: {w}")
        nxt("Turn it on for one application: python scripts/rh.py app settings <person> <app> --photo on")
    elif a.action == "show":
        latest = rhlib.latest_photo(root, a.person)
        out(f"Saved photo: {latest[1].name}" if latest else "No photo saved for this person.")


def cmd_region(a) -> None:
    regions = rhlib.load_regions()
    if a.action == "list":
        for key, r in regions.items():
            out(f"{key}  |  {r['label']}  |  paper {r['paper'].upper()}  |  photo: {r['photo']}  |  nationality line: {'allowed' if r['nationality'] else 'no'}")
        nxt("Ask the user which country the job is in, then: python scripts/rh.py app settings <person> <app> --region <key>")
    else:
        r = regions.get(a.key)
        if not r:
            raise RHError(f"Unknown region '{a.key}'.", "Regions: " + ", ".join(regions))
        out(f"{a.key}: {r['label']}", f"Paper: {r['paper'].upper()}", f"Photo: {r['photo']}", r["notes"])


def cmd_lint(a) -> None:
    root = root_for_write()
    findings, report = lint_resume.run_lint(root, a.person, a.app)
    _print_findings(findings, report)
    nxt("Fix every FAIL (policy). Fix WARN items that are true problems. Save new versions, then build.")
    sys.exit(1 if any(f["level"] == "FAIL" for f in findings) else 0)


def cmd_export(a) -> None:
    root = root_for_write()
    res = export_resume.export(root, a.person, a.app)
    out(f"Exported to: {res['folder']}", *[f"  {p.name}" for p in res["files"]])
    if res["warning"]:
        out(f"WARN: {res['warning']}")
    out("Send the PDF or DOCX to job portals. Use the _Photo file only for email or print, where a photo is expected.")
    nxt("Tell the user the folder path and which file to use where.")


def cmd_build(a) -> None:
    root = root_for_write()
    res = build_resume.build(root, a.person, a.app, a.paper, a.no_compile, a.pages)
    reindex(root)
    out(f"LaTeX: {res['tex']}", f"Overleaf upload zip: {res['zip']}", f"Word file (DOCX): {res['docx']}")
    for w in res["warnings"]:
        out(f"WARN: {w}")
    if res["status"] == "ok":
        fill = f"{int(res['fill'] * 100)}%" if res["fill"] is not None else "unknown"
        out(f"PDF: {res['pdf']}", f"Pages: {res['pages']} (target {res['target_pages']})  Layout preset: {res['preset']}  Last page fill: {fill}")
        if res["fits"] is False:
            out(f"WARN: The content does not fit {res['target_pages']} page(s) even with the tightest layout. Shorten the content (cut the weakest items).")
        if res.get("photo_pdf"):
            out(f"Photo version PDF: {res['photo_pdf']}", f"Photo version zip: {res['photo_zip']}")
        nxt("Run: python scripts/rh.py check <person> <app>")
    elif res["status"] == "no-engine":
        out("No TeX engine found (pdflatex or tectonic), so no PDF was made.",
            "Options: install TeX Live / MiKTeX / tectonic and rebuild, or upload the zip above to Overleaf. The DOCX was still made.")
    elif res["status"] == "compile-failed":
        out("COMPILE FAILED. TeX log excerpt:", res["log"])
        nxt("Fix the cause in the resume Markdown (usually a special character), save a new resume-md version, and rebuild. Max 3 attempts.")
    else:
        nxt("Compile skipped (--no-compile).")


def _print_findings(findings: List[Dict[str, str]], report: Path) -> None:
    for level in ("FAIL", "WARN", "PASS"):
        for f in findings:
            if f["level"] == level:
                out(f"{level}: {f['msg']}")
    counts = {k: len([x for x in findings if x["level"] == k]) for k in ("FAIL", "WARN", "PASS")}
    out(f"Result: {counts['FAIL']} FAIL, {counts['WARN']} WARN, {counts['PASS']} PASS", f"Report: {report}")


def cmd_truth(a) -> None:
    root = root_for_write()
    findings, report = ats_check.run_truth(root, a.person, a.app)
    _print_findings(findings, report)
    nxt("Fix every FAIL (edit the resume or the evidence map, save new versions). Then: python scripts/rh.py build <person> <app>")
    sys.exit(1 if any(f["level"] == "FAIL" for f in findings) else 0)


def cmd_check(a) -> None:
    root = root_for_write()
    pdf = Path(a.pdf) if a.pdf else None
    findings, report = ats_check.run_ats(root, a.person, a.app, pdf, a.max_pages)
    _print_findings(findings, report)
    nxt("Fix every FAIL. Then run the review pass (see the ats-and-review skill).")
    sys.exit(1 if any(f["level"] == "FAIL" for f in findings) else 0)


# --------------------------------------------------------------------------
# argument parser
# --------------------------------------------------------------------------

def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rh.py", description="Resume Harness data and build tool.")
    p.add_argument("--data-dir", help="Use this data folder instead of the saved/default one.")
    p.add_argument("--version", action="version", version="Resume Harness " + (rhlib.HARNESS_ROOT / "VERSION").read_text().strip())
    sub = p.add_subparsers(dest="group", required=True)

    sub.add_parser("doctor", help="Check that this computer is ready: Python, PDF tools, data folder, AI agent.").set_defaults(fn=cmd_doctor)
    sub.add_parser("where", help="Show the data folder path.").set_defaults(fn=cmd_where)
    s = sub.add_parser("set-data-dir", help="Choose where user data is stored (must be outside the harness).")
    s.add_argument("path"); s.set_defaults(fn=cmd_set_data_dir)
    sub.add_parser("init", help="Create the data folder.").set_defaults(fn=cmd_init)
    sub.add_parser("status", help="Counts of people, companies, jobs, applications.").set_defaults(fn=cmd_status)
    sub.add_parser("index", help="Regenerate INDEX.md and applications.csv.").set_defaults(fn=cmd_index)
    sub.add_parser("clean-scratch", help="Delete temporary input files in scratch/.").set_defaults(fn=cmd_clean_scratch)
    s = sub.add_parser("backup", help="Zip the whole data folder."); s.add_argument("--out"); s.set_defaults(fn=cmd_backup)
    s = sub.add_parser("reset", help="Delete ALL data (fresh install).")
    s.add_argument("--confirm", required=True); s.set_defaults(fn=cmd_reset)
    s = sub.add_parser("forget", help="Delete one person or one company.")
    s.add_argument("kind", choices=["person", "company"]); s.add_argument("slug")
    s.add_argument("--confirm", required=True); s.set_defaults(fn=cmd_forget)

    s = sub.add_parser("person"); s.set_defaults(fn=cmd_person)
    ps = s.add_subparsers(dest="action", required=True)
    ps.add_parser("list")
    x = ps.add_parser("find"); x.add_argument("query")
    x = ps.add_parser("create"); x.add_argument("--name", required=True); x.add_argument("--allow-duplicate", action="store_true")
    x = ps.add_parser("show"); x.add_argument("slug")

    s = sub.add_parser("contact"); s.set_defaults(fn=cmd_contact)
    cs = s.add_subparsers(dest="action", required=True)
    x = cs.add_parser("show"); x.add_argument("person")
    x = cs.add_parser("set"); x.add_argument("person")
    for key in rhlib.CONTACT_FIELDS:
        x.add_argument(f"--{key}")
    x.add_argument("--link", action="append", help="LABEL=URL (repeatable; professional links only, max 3)")
    x.add_argument("--remove-link", action="append", help="LABEL of a saved link to remove (repeatable)")
    x.add_argument("--file")

    s = sub.add_parser("profile"); s.set_defaults(fn=cmd_profile)
    fs = s.add_subparsers(dest="action", required=True)
    x = fs.add_parser("add"); x.add_argument("person"); x.add_argument("--file", required=True)
    x.add_argument("--section"); x.add_argument("--allow-duplicate", action="store_true")
    x = fs.add_parser("update"); x.add_argument("person"); x.add_argument("id"); x.add_argument("--file", required=True)
    x = fs.add_parser("remove"); x.add_argument("person"); x.add_argument("id")
    x = fs.add_parser("show"); x.add_argument("person"); x.add_argument("--section"); x.add_argument("--json", action="store_true")
    x = fs.add_parser("validate"); x.add_argument("person")

    s = sub.add_parser("company"); s.set_defaults(fn=cmd_company)
    ks = s.add_subparsers(dest="action", required=True)
    ks.add_parser("list")
    x = ks.add_parser("find"); x.add_argument("query")
    x = ks.add_parser("create"); x.add_argument("--name", required=True); x.add_argument("--website")
    x.add_argument("--alias", action="append"); x.add_argument("--allow-duplicate", action="store_true")
    x = ks.add_parser("show"); x.add_argument("slug")

    s = sub.add_parser("recon"); s.set_defaults(fn=cmd_recon)
    rs = s.add_subparsers(dest="action", required=True)
    x = rs.add_parser("save"); x.add_argument("company"); x.add_argument("--file", required=True)
    x = rs.add_parser("latest"); x.add_argument("company")
    x = rs.add_parser("show"); x.add_argument("company")

    s = sub.add_parser("job"); s.set_defaults(fn=cmd_job)
    js = s.add_subparsers(dest="action", required=True)
    x = js.add_parser("list"); x.add_argument("company")
    x = js.add_parser("find"); x.add_argument("company"); x.add_argument("--title"); x.add_argument("--jd-file")
    x = js.add_parser("create"); x.add_argument("company"); x.add_argument("--title", required=True)
    x.add_argument("--jd-file", required=True); x.add_argument("--url"); x.add_argument("--allow-similar", action="store_true")
    x = js.add_parser("show"); x.add_argument("company"); x.add_argument("job")
    x = js.add_parser("analysis-save"); x.add_argument("company"); x.add_argument("job"); x.add_argument("--file", required=True)

    s = sub.add_parser("app"); s.set_defaults(fn=cmd_app)
    as_ = s.add_subparsers(dest="action", required=True)
    x = as_.add_parser("list"); x.add_argument("person")
    x = as_.add_parser("find"); x.add_argument("person"); x.add_argument("--company"); x.add_argument("--job")
    x = as_.add_parser("create"); x.add_argument("person"); x.add_argument("--company", required=True)
    x.add_argument("--job", required=True); x.add_argument("--new", action="store_true")
    for name in ("show", "files", "path"):
        x = as_.add_parser(name); x.add_argument("person"); x.add_argument("app")
    x = as_.add_parser("cat"); x.add_argument("person"); x.add_argument("app"); x.add_argument("stage")
    x = as_.add_parser("save"); x.add_argument("person"); x.add_argument("app"); x.add_argument("stage")
    x.add_argument("--file", required=True)
    x = as_.add_parser("status"); x.add_argument("person"); x.add_argument("app"); x.add_argument("status")
    x = as_.add_parser("settings"); x.add_argument("person"); x.add_argument("app")
    x.add_argument("--region"); x.add_argument("--photo", choices=["on", "off"]); x.add_argument("--pages", type=int)
    x.add_argument("--paper", choices=["a4", "letter"]); x.add_argument("--force", action="store_true")

    s = sub.add_parser("photo"); s.set_defaults(fn=cmd_photo)
    hs = s.add_subparsers(dest="action", required=True)
    x = hs.add_parser("set"); x.add_argument("person"); x.add_argument("--file", required=True)
    x = hs.add_parser("show"); x.add_argument("person")
    hs.add_parser("guide")
    s = sub.add_parser("region"); s.set_defaults(fn=cmd_region)
    gs = s.add_subparsers(dest="action", required=True)
    gs.add_parser("list")
    x = gs.add_parser("show"); x.add_argument("key")
    s = sub.add_parser("build", help="Make LaTeX, Overleaf zip, DOCX and PDF from the latest resume Markdown.")
    s.add_argument("person"); s.add_argument("app"); s.add_argument("--paper", choices=["a4", "letter"])
    s.add_argument("--pages", type=int, choices=[1, 2, 3])
    s.add_argument("--no-compile", action="store_true"); s.set_defaults(fn=cmd_build)
    s = sub.add_parser("lint", help="Policy checks (header, links, personal data, photo) and writing lint.")
    s.add_argument("person"); s.add_argument("app"); s.set_defaults(fn=cmd_lint)
    s = sub.add_parser("export", help="Copy final files to exports/vN with employer-ready names.")
    s.add_argument("person"); s.add_argument("app"); s.set_defaults(fn=cmd_export)
    s = sub.add_parser("truth", help="Check bullets, skills and numbers against the profile.")
    s.add_argument("person"); s.add_argument("app"); s.set_defaults(fn=cmd_truth)
    s = sub.add_parser("check", help="ATS check of the built PDF plus the truth check.")
    s.add_argument("person"); s.add_argument("app"); s.add_argument("--pdf"); s.add_argument("--max-pages", type=int)
    s.set_defaults(fn=cmd_check)
    return p


def main(argv: Optional[List[str]] = None) -> None:
    args = make_parser().parse_args(argv)
    rhlib.set_data_override(args.data_dir)
    try:
        args.fn(args)
    except RHError as exc:
        print(f"ERROR: {exc}")
        if exc.hint:
            print(f"HINT: {exc.hint}")
        sys.exit(2)


if __name__ == "__main__":
    main()
