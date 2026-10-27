#!/usr/bin/env python3
"""Resume Harness core library. Python 3.9+, standard library only.

Design rules enforced here (the agent never touches data files directly):
  1. User data lives in a separate data folder, never inside the harness folder.
  2. Nothing is overwritten silently. New files are create-only; saved documents
     get version numbers (name.v1.md, name.v2.md); edited JSON files are archived
     into a history/ folder first.
  3. File and folder names are chosen by this code, not by the agent.
  4. Duplicate people, companies, jobs and applications are detected and the
     caller must decide (reuse or create new) before anything is created.
"""
from __future__ import annotations

import csv
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import shutil
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

HARNESS_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = HARNESS_ROOT / "config"
SCRATCH_DIR = HARNESS_ROOT / "scratch"
POINTER_FILE = CONFIG_DIR / "data_location.txt"
MARKER_NAME = "resume-harness-data.json"
DATA_FORMAT_VERSION = 1
DEFAULT_DATA_DIRNAME = "resume-harness-data"


def python_command() -> str:
    """The Python command name that works on this machine: python, python3 or py.

    Used when printing the command a reader should run, so that a machine without a
    plain `python` does not turn every printed instruction into a failed command.
    """
    name = Path(sys.executable).name.lower()
    for candidate in ("python3", "python", "py"):
        if name.startswith(candidate):
            return candidate
    return "python"


class RHError(Exception):
    """A problem the user or agent can fix. Printed as ERROR plus HINT."""

    def __init__(self, message: str, hint: Optional[str] = None):
        super().__init__(message)
        self.hint = hint


# --------------------------------------------------------------------------
# small utilities
# --------------------------------------------------------------------------

def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def today() -> str:
    return dt.date.today().isoformat()


def stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def file_stamp(path: Optional[Path]) -> Optional[List[int]]:
    """A cheap content-change marker for a file: (mtime in ns, byte size).

    Build freshness compares these markers rather than timestamps with second
    precision, so a save made in the same second still counts as a change.
    """
    if path is None:
        return None
    try:
        stat = path.stat()
        return [stat.st_mtime_ns, stat.st_size]
    except OSError:
        return None


def iso_stamp(value: Any) -> Optional[float]:
    """Turn a stored ISO timestamp into epoch seconds, or None when it is absent/bad."""
    if not isinstance(value, str) or not value:
        return None
    try:
        when = dt.datetime.fromisoformat(value)
    except ValueError:
        return None
    if when.tzinfo is None:
        when = when.astimezone()
    return when.timestamp()


def _ascii_lower(text: str) -> str:
    t = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    return t.lower()


def slugify(text: str, maxlen: int = 50) -> str:
    t = re.sub(r"[^a-z0-9]+", "-", _ascii_lower(text)).strip("-")
    return t[:maxlen].strip("-") or "item"


_COMPANY_SUFFIXES = {
    "inc", "llc", "ltd", "limited", "pvt", "private", "corp", "corporation", "co",
    "company", "gmbh", "plc", "llp", "lp", "sa", "ag", "bv",
}


def norm_key(text: str, strip_suffix: bool = False) -> str:
    toks = [t for t in re.split(r"[^a-z0-9]+", _ascii_lower(text)) if t]
    if strip_suffix:
        toks = [t for t in toks if t not in _COMPANY_SUFFIXES] or toks
    return " ".join(toks)


def match_score(query: str, names: List[str], strip_suffix: bool = False) -> int:
    """3 = same name, 2 = one contains the other, 1 = shares a word, 0 = no match."""
    qk = norm_key(query, strip_suffix)
    if not qk:
        return 0
    best = 0
    for name in names:
        ck = norm_key(name, strip_suffix)
        if not ck:
            continue
        if qk == ck:
            best = max(best, 3)
        elif (len(qk) >= 3 and qk in ck) or (len(ck) >= 3 and ck in qk):
            best = max(best, 2)
        elif set(qk.split()) & set(ck.split()):
            best = max(best, 1)
    return best


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def create_text(path: Path, text: str) -> Path:
    """Create a new file. Refuses to overwrite an existing one."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except FileExistsError:
        raise RHError(f"Refusing to overwrite existing file: {path}")
    return path


def write_text_lf(path: Path, text: str) -> Path:
    """Replace a text file with LF line endings. Python 3.9-safe (Path.write_text has no newline)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return path


def create_json(path: Path, obj: Any) -> Path:
    return create_text(path, _dump(obj))


def archive_file(path: Path, history_dir: Path) -> Path:
    history_dir.mkdir(parents=True, exist_ok=True)
    dest = history_dir / f"{path.stem}.{stamp()}{path.suffix}"
    n = 2
    while dest.exists():
        dest = history_dir / f"{path.stem}.{stamp()}-{n}{path.suffix}"
        n += 1
    shutil.copy2(path, dest)
    return dest


def update_json(path: Path, obj: Any, history_dir: Path) -> None:
    """Archive the current file into history/, then replace it atomically."""
    if path.exists():
        archive_file(path, history_dir)
    tmp = path.with_name(path.name + ".tmp")
    write_text_lf(tmp, _dump(obj))
    os.replace(tmp, path)


def version_files(directory: Path, stem: str, ext: str) -> List[Tuple[int, Path]]:
    if not directory.exists():
        return []
    rx = re.compile(r"^" + re.escape(stem) + r"\.v(\d+)\." + re.escape(ext) + r"$")
    found = []
    for item in directory.iterdir():
        m = rx.match(item.name)
        if m:
            found.append((int(m.group(1)), item))
    return sorted(found)


def next_version(directory: Path, stem: str, ext: str) -> int:
    existing = version_files(directory, stem, ext)
    return (existing[-1][0] + 1) if existing else 1


def latest_version(directory: Path, stem: str, ext: str) -> Optional[Tuple[int, Path]]:
    existing = version_files(directory, stem, ext)
    return existing[-1] if existing else None


def report_fail_count(path: Path) -> Optional[int]:
    """The number of FAIL findings in a truth/ATS/lint report, or None if it cannot be read."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    match = re.search(r"^Result:\s*(\d+)\s+FAIL\b", text, re.MULTILINE)
    return int(match.group(1)) if match else None


def save_versioned(directory: Path, stem: str, ext: str, text: str) -> Path:
    n = next_version(directory, stem, ext)
    return create_text(directory / f"{stem}.v{n}.{ext}", text)


def read_input(path_str: str) -> str:
    """Read the text for --file. '-' means standard input."""
    if path_str == "-":
        import sys
        return sys.stdin.read()
    p = Path(path_str).expanduser()
    if not p.exists():
        raise RHError(f"Input file not found: {p}",
                      "Write the content to a file inside the harness 'scratch' folder first, then pass that path.")
    try:
        return p.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        raise RHError(f"Input file is not plain UTF-8 text: {p}",
                      "Save it as a UTF-8 text file. A PDF, image, or Word file cannot be read this way.") from None
    except OSError as exc:
        raise RHError(f"Could not read input file: {p} ({exc})",
                      "Check that the file exists and that you can read it, then retry.") from None


def consume_scratch(path_str: str) -> None:
    """Delete a temporary input file after it was saved, if it is inside scratch/."""
    if path_str == "-":
        return
    try:
        p = Path(path_str).expanduser().resolve()
        if SCRATCH_DIR.resolve() in p.parents and p.name != ".gitkeep":
            p.unlink()
    except OSError:
        pass


def clean_scratch() -> int:
    """Delete every temporary input file in scratch/ (the .gitkeep placeholder stays)."""
    removed = 0
    if SCRATCH_DIR.exists():
        for item in SCRATCH_DIR.iterdir():
            if item.name == ".gitkeep":
                continue
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink()
            removed += 1
    return removed


def settings() -> Dict[str, Any]:
    defaults = {
        "recon_max_age_days": 30, "default_region": "other", "default_pages": 1, "default_max_pages": 2,
        "statuses": ["draft", "built", "reviewed", "applied", "interview", "offer", "rejected", "withdrawn"],
        "standard_headings": [], "max_links": 3, "blocked_link_domains": [], "blocked_link_words": [],
        "photo": {"height_cm": 3.0, "width_cm": 2.6, "max_mb": 3, "min_short_side_px": 400},
    }
    path = CONFIG_DIR / "settings.json"
    if path.exists():
        defaults.update(read_json(path))
    return defaults


# --------------------------------------------------------------------------
# data folder (kept separate from the harness, like an installed app's user data)
# --------------------------------------------------------------------------

_DATA_OVERRIDE: Optional[str] = None


def set_data_override(path: Optional[str]) -> None:
    global _DATA_OVERRIDE
    _DATA_OVERRIDE = path


def resolve_data_root() -> Path:
    """Order: --data-dir flag, RESUME_HARNESS_DATA env var, config/data_location.txt, default."""
    if _DATA_OVERRIDE:
        return Path(_DATA_OVERRIDE).expanduser().resolve()
    env = os.environ.get("RESUME_HARNESS_DATA")
    if env:
        return Path(env).expanduser().resolve()
    if POINTER_FILE.exists():
        text = POINTER_FILE.read_text(encoding="utf-8").strip()
        if text:
            return Path(text).expanduser().resolve()
    return (Path.home() / DEFAULT_DATA_DIRNAME).resolve()


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


DATA_README = """RESUME HARNESS DATA FOLDER
==========================
This folder holds all personal data used by the resume harness.
The harness program folder holds no personal data, so:
  - deleting this folder resets the harness to a fresh install,
  - copying this folder to another computer moves all your data.

Layout:
  INDEX.md                      human-readable list of everything stored (regenerated automatically)
  applications.csv              one row per application
  people/<person>/              one folder per person
      person.json  profile.json  contact.json  history/ applications/
  companies/<company>/          one folder per company
      company.json  recon/  jobs/<role>--<id>/
Nothing is overwritten: saved documents are numbered .v1, .v2 ...
Old versions of edited JSON files are kept in each history/ folder.
Do not rename or edit these files by hand unless you know what you are doing.
"""


def ensure_root(create: bool = True) -> Path:
    root = resolve_data_root()
    if root == HARNESS_ROOT or _inside(root, HARNESS_ROOT):
        raise RHError(f"The data folder must be outside the harness folder: {root}",
                      "Run: python scripts/rh.py set-data-dir <folder outside the harness>")
    if root.exists() and not root.is_dir():
        raise RHError(f"The data folder path is a file, not a folder: {root}",
                      "Choose a folder path with: python scripts/rh.py set-data-dir <folder>")
    marker = root / MARKER_NAME
    if marker.exists():
        return root
    if root.exists() and any(root.iterdir()):
        raise RHError(f"{root} exists, is not empty, and is not a resume-harness data folder.",
                      "Choose another folder with: python scripts/rh.py set-data-dir <path>")
    if not create:
        raise RHError(f"No data folder yet at {root}.", "It is created automatically by the first save, or run: python scripts/rh.py init")
    root.mkdir(parents=True, exist_ok=True)
    (root / "people").mkdir(exist_ok=True)
    (root / "companies").mkdir(exist_ok=True)
    create_json(marker, {"app": "resume-harness-data", "format_version": DATA_FORMAT_VERSION, "created": now_iso()})
    create_text(root / "README.txt", DATA_README)
    return root


# --------------------------------------------------------------------------
# people
# --------------------------------------------------------------------------

def _people_dir(root: Path) -> Path:
    return root / "people"


def list_people(root: Path) -> List[Dict[str, Any]]:
    out = []
    base = _people_dir(root)
    if base.exists():
        for d in sorted(base.iterdir()):
            if (d / "person.json").exists():
                out.append(read_json(d / "person.json"))
    return out


def find_people(root: Path, query: str) -> List[Dict[str, Any]]:
    scored = []
    for p in list_people(root):
        s = match_score(query, [p["name"], p["slug"]])
        if s:
            scored.append((s, p))
    scored.sort(key=lambda x: -x[0])
    return [p for _, p in scored]


def person_dir(root: Path, slug: str) -> Path:
    d = _people_dir(root) / slug
    if not (d / "person.json").exists():
        names = ", ".join(p["slug"] for p in list_people(root)) or "none yet"
        raise RHError(f"Unknown person '{slug}'. Existing people: {names}",
                      "Use the exact slug from: python scripts/rh.py person list")
    return d


def empty_profile(slug: str) -> Dict[str, Any]:
    return {"format_version": DATA_FORMAT_VERSION, "person": slug, "updated": now_iso(),
            "counters": {}, "entries": [], "removed": []}


def create_person(root: Path, name: str, allow_duplicate: bool = False) -> Dict[str, Any]:
    name = name.strip()
    if not name:
        raise RHError("The person label is empty.", 'Use a short, non-private label such as "Me".')
    matches = [p for p in find_people(root, name) if norm_key(p["name"]) == norm_key(name)]
    if matches and not allow_duplicate:
        listing = ", ".join(f"{p['slug']} ({p['name']})" for p in matches)
        raise RHError(f"A person with this label already exists: {listing}",
                      "Ask the user: reuse the existing person, or is this a different person? "
                      "If different, re-run with --allow-duplicate.")
    base = slugify(name, 40)
    slug, n = base, 2
    while (_people_dir(root) / slug).exists():
        slug = f"{base}-{n}"
        n += 1
    d = _people_dir(root) / slug
    for sub in ("history", "applications"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    person = {"slug": slug, "name": name, "created": now_iso(), "updated": now_iso()}
    create_json(d / "person.json", person)
    create_json(d / "profile.json", empty_profile(slug))
    return person


def touch_person(root: Path, slug: str) -> None:
    d = person_dir(root, slug)
    person = read_json(d / "person.json")
    person["updated"] = now_iso()
    write_text_lf(d / "person.json", _dump(person))


def set_person_label(root: Path, slug: str, label: str) -> Dict[str, Any]:
    """Change the display label only. The private contact name and folder id are not touched."""
    label = label.strip()
    if not label:
        raise RHError("The label is empty.", 'Use a short, non-private label such as "Me".')
    d = person_dir(root, slug)
    person = read_json(d / "person.json")
    person["name"] = label
    person["updated"] = now_iso()
    update_json(d / "person.json", person, d / "history")
    return person


def rename_person(root: Path, slug: str, label: str) -> Dict[str, Any]:
    """Give a person saved under a real name a private folder id as well as a label.

    The person folder is moved, so the old id disappears from paths and lists.
    Every application and the profile are updated to the new id.
    """
    label = label.strip()
    if not label:
        raise RHError("The label is empty.", 'Use a short, non-private label such as "Me".')
    old = person_dir(root, slug)
    new_slug = slugify(label, 40)
    if not new_slug:
        raise RHError("That label cannot be used as a folder id.",
                      'Use letters or numbers, for example: --label "Me"')
    if new_slug == slug:
        return set_person_label(root, slug, label)
    new = _people_dir(root) / new_slug
    if new.exists():
        raise RHError(f"A person folder named '{new_slug}' already exists.",
                      "Use a different label, or keep the current folder id.")
    try:
        old.rename(new)
    except OSError:
        raise RHError("The person folder could not be moved. Nothing was changed.",
                      "Close any program using the data folder and try again.") from None
    person = read_json(new / "person.json")
    person["slug"] = new_slug
    person["name"] = label
    person["updated"] = now_iso()
    update_json(new / "person.json", person, new / "history")
    profile_path = new / "profile.json"
    if profile_path.exists():
        profile = read_json(profile_path)
        if profile.get("person") != new_slug:
            profile["person"] = new_slug
            update_json(profile_path, profile, new / "history")
    apps = new / "applications"
    if apps.exists():
        for app_file in sorted(apps.glob("*/app.json")):
            app = read_json(app_file)
            if app.get("person") != new_slug:
                app["person"] = new_slug
                app["updated"] = now_iso()
                update_json(app_file, app, app_file.parent / "history")
    return person


# --------------------------------------------------------------------------
# contact (private; used locally at build and export time, never printed)
# --------------------------------------------------------------------------

CONTACT_FIELDS = ["name", "email", "phone", "location"]

CONTACT_FORM_NAME = "contact-form.txt"

CONTACT_FORM_HELP = """\
# Private contact details. The assistant does not read this file.
# Fill in what you want on the resume, save the file, and close it.
# location: city and country only, no street address.
# link: write it as   label | https://...   (at most 3; professional links only)
# Leave a field empty to keep it unchanged. Delete a link line to remove that link.
"""


def load_contact(root: Path, slug: str) -> Dict[str, Any]:
    path = person_dir(root, slug) / "contact.json"
    return read_json(path) if path.exists() else {}


def contact_form_path(root: Path, slug: str) -> Path:
    return person_dir(root, slug) / CONTACT_FORM_NAME


def write_contact_form(root: Path, slug: str) -> Path:
    """Create (or keep) the private form the user edits. The agent never reads it."""
    path = contact_form_path(root, slug)
    if path.exists():
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        return path
    contact = load_contact(root, slug)
    lines = CONTACT_FORM_HELP.splitlines()
    for key in CONTACT_FIELDS:
        lines.append(f"{key}: {contact.get(key, '')}")
    for link in contact.get("links", []):
        lines.append(f"link: {link['label']} | {link['url']}")
    write_text_lf(path, "\n".join(lines) + "\n")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return path


def _host(url: str) -> str:
    u = url.strip()
    parsed = urlparse(u if "://" in u else "https://" + u)
    return re.sub(r"^www\.", "", (parsed.hostname or "").lower())


LINK_HINT = ("Use professional links only: LinkedIn, plus GitHub or a portfolio site for technical work, "
             "Behance or Dribbble for design, Google Scholar or ORCID for research. "
             "A WhatsApp number may be the phone number, but never a link or a label.")


def check_link(label: str, url: str) -> None:
    """Reject social media links. Raises RHError."""
    conf = settings()
    host = _host(url)
    if not host or "." not in host:
        raise RHError("That is not a valid web address.", "Use a full address such as https://www.linkedin.com/in/your-name")
    for domain in conf.get("blocked_link_domains", []):
        if host == domain or host.endswith("." + domain):
            raise RHError(f"Social media links are not allowed on a resume (saved link: {host}).", LINK_HINT)
    words = set(re.split(r"[^a-z0-9]+", label.lower()))
    for word in conf.get("blocked_link_words", []):
        if word in words:
            raise RHError("Social media links are not allowed on a resume (a link label uses a blocked word).", LINK_HINT)


def validate_contact_links(contact: Dict[str, Any]) -> None:
    links = contact.get("links", [])
    for link in links:
        check_link(link["label"], link["url"])
    limit = int(settings().get("max_links", 3))
    if len(links) > limit:
        raise RHError(f"A resume may show at most {limit} links; this contact has {len(links)}.",
                      "Ask the user which to keep, then open the contact form, delete the other link lines, "
                      "and run: python scripts/rh.py contact import <person>")


def parse_contact_form(text: str) -> Tuple[Dict[str, str], List[Tuple[str, str]]]:
    """Read the private form. Errors never include a value or a URL."""
    fields: Dict[str, str] = {}
    links: List[Tuple[str, str]] = []
    for number, raw in enumerate(text.lstrip("\ufeff").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise RHError(f"Line {number} of the contact form is not written as 'key: value'.",
                          "Use name:, email:, phone:, location:, or link: Label | https://...")
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key == "link":
            if "|" not in value:
                raise RHError(f"Line {number}: a link must be written as Label | https://...")
            label, url = (part.strip() for part in value.split("|", 1))
            if not label or not url:
                raise RHError(f"Line {number}: a link needs a label and a full web address.")
            try:
                check_link(label, url)
            except RHError:
                raise RHError(f"Line {number}: that link is not allowed on a resume.",
                              "Use a professional link only: LinkedIn, GitHub, a portfolio, Behance or Dribbble, "
                              "Google Scholar or ORCID. No social media.") from None
            links.append((label, url))
        elif key in CONTACT_FIELDS:
            if value:
                fields[key] = value
        else:
            raise RHError(f"Line {number}: unknown field '{key}'.",
                          "Allowed fields: name, email, phone, location, link.")
    limit = int(settings().get("max_links", 3))
    if len(links) > limit:
        raise RHError(f"The contact form has {len(links)} links; at most {limit} are allowed.",
                      "Delete the extra link lines and import again.")
    if fields.get("email") and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", fields["email"]):
        raise RHError("The email in the contact form does not look valid.",
                      "Fix the email line and import again.")
    return fields, links


def contact_warnings(contact: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    phone = contact.get("phone", "")
    if phone and not phone.strip().startswith("+"):
        out.append("The phone number has no country code. Add it, for example +91 followed by the number.")
    loc = contact.get("location", "")
    if loc and (re.search(r"\d{3,}", loc) or re.search(
            r"\b(street|st\.|road|rd\.|nagar|colony|flat|house no|plot|apartment|apt|lane|block|sector)\b", loc, re.I)):
        out.append("The location looks like a street address. Use city and country only (for example 'Pune, India').")
    return out


def set_contact(root: Path, slug: str, fields: Dict[str, str], links: List[Tuple[str, str]],
                remove_links: Optional[List[str]] = None) -> Tuple[Dict[str, Any], List[str]]:
    d = person_dir(root, slug)
    contact = load_contact(root, slug)
    for key, value in fields.items():
        if key not in CONTACT_FIELDS:
            raise RHError(f"Unknown contact field '{key}'.", "Allowed: " + ", ".join(CONTACT_FIELDS))
        value = (value or "").strip()
        if key == "email" and value and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
            raise RHError("The email does not look valid.", "Fix the email value and run the command again.")
        if value:
            contact[key] = value
    current = list(contact.get("links", []))
    for label in remove_links or []:
        kept = [x for x in current if x["label"].lower() != label.strip().lower()]
        if len(kept) == len(current):
            raise RHError(f"No saved link is labelled '{label}'.", "See saved links with: python scripts/rh.py contact show <person>")
        current = kept
    for label, url in links:
        label, url = label.strip(), url.strip()
        if not label or not url:
            raise RHError("A link needs a label and a url, written as LABEL=URL.")
        check_link(label, url)
        current = [x for x in current if x["label"].lower() != label.lower()]
        current.append({"label": label, "url": url})
    if current:
        contact["links"] = current
    elif "links" in contact:
        del contact["links"]
    validate_contact_links(contact)
    path = d / "contact.json"
    if path.exists():
        update_json(path, contact, d / "history")
    else:
        create_json(path, contact)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    touch_person(root, slug)
    return contact, contact_warnings(contact)


# --------------------------------------------------------------------------
# photo (optional, off by default, private)
# --------------------------------------------------------------------------

PHOTO_GUIDE = [
    "Recent photo, head and shoulders, face fully visible and facing the camera.",
    "Plain, light, uncluttered background. Even lighting, no harsh shadows.",
    "Neutral or slight natural smile. Smart, simple clothing.",
    "No filters, no heavy editing, no sunglasses, no hat, no group photo, no selfie angle.",
    "Not a fashion, party, or social-media style photo. Not oversized: it is printed small (about 2.6 x 3.0 cm).",
    "A tight, natural crop. It does not need to look like an official ID or passport photo.",
]

PHOTO_HELP = [
    "No suitable photo? Take one with a phone: stand facing a window, plain wall behind you, "
    "head and shoulders, no filter, no sunglasses.",
    "Want an editor to clean up a real photo? Use this prompt: \"Crop to head and shoulders, straighten, "
    "replace the background with plain light grey, even the lighting, keep the face exactly as it is, "
    "no beauty retouching, no filters, no watermark.\"",
    "Do not generate or replace the face. A generated face is a misrepresentation and can be rejected. "
    "A photo is optional.",
]


def _photo_dir(root: Path, slug: str) -> Path:
    return person_dir(root, slug) / "photo"


def latest_photo(root: Path, slug: str) -> Optional[Tuple[int, Path]]:
    d = _photo_dir(root, slug)
    if not d.exists():
        return None
    rx = re.compile(r"^photo\.v(\d+)\.(jpg|jpeg|png)$")
    found = []
    for item in d.iterdir():
        m = rx.match(item.name)
        if m:
            found.append((int(m.group(1)), item))
    return sorted(found)[-1] if found else None


def image_size(path: Path) -> Optional[Tuple[int, int]]:
    """Width and height of a PNG or JPEG, read from the file header (no extra libraries)."""
    data = path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            length = int.from_bytes(data[i + 2:i + 4], "big")
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                return int.from_bytes(data[i + 7:i + 9], "big"), int.from_bytes(data[i + 5:i + 7], "big")
            i += 2 + length
    return None


def photo_set(root: Path, slug: str, src: str) -> Tuple[Path, List[str]]:
    source = Path(src).expanduser()
    if not source.exists():
        raise RHError(f"Photo file not found: {source}")
    ext = source.suffix.lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        raise RHError("The photo must be a .jpg, .jpeg, or .png file.")
    conf = settings()["photo"]
    size_mb = source.stat().st_size / (1024 * 1024)
    if size_mb > float(conf["max_mb"]):
        raise RHError(f"The photo is {size_mb:.1f} MB; the limit is {conf['max_mb']} MB.", "Resize or compress it first.")
    dims = image_size(source)
    if not dims:
        raise RHError("Could not read the image size. The file may be damaged.", "Export it again as a normal JPEG or PNG.")
    warnings: List[str] = []
    w, h = dims
    if min(w, h) < int(conf["min_short_side_px"]):
        warnings.append(f"The photo is small ({w} x {h} px). It may look blurry in print; use at least {conf['min_short_side_px']} px on the short side.")
    ratio = w / h
    if ratio < 0.6 or ratio > 1.2:
        warnings.append(f"The photo shape is unusual ({w} x {h}). Crop it closer to head and shoulders (roughly square or slightly tall).")
    d = _photo_dir(root, slug)
    d.mkdir(parents=True, exist_ok=True)
    latest = latest_photo(root, slug)
    n = (latest[0] + 1) if latest else 1
    dest = d / f"photo.v{n}{'.jpg' if ext in ('.jpg', '.jpeg') else '.png'}"
    with open(dest, "xb") as handle:
        handle.write(source.read_bytes())
    try:
        os.chmod(dest, 0o600)
    except OSError:
        pass
    touch_person(root, slug)
    return dest, warnings


# --------------------------------------------------------------------------
# regions and per-application settings
# --------------------------------------------------------------------------

def load_regions() -> Dict[str, Any]:
    return read_json(CONFIG_DIR / "regions.json")


# --------------------------------------------------------------------------
# profile (master evidence database)
# --------------------------------------------------------------------------

def load_schema() -> Dict[str, Any]:
    return read_json(CONFIG_DIR / "profile_schema.json")


def profile_path(root: Path, slug: str) -> Path:
    return person_dir(root, slug) / "profile.json"


def load_profile(root: Path, slug: str) -> Dict[str, Any]:
    return read_json(profile_path(root, slug))


def save_profile(root: Path, slug: str, prof: Dict[str, Any]) -> None:
    prof["updated"] = now_iso()
    update_json(profile_path(root, slug), prof, person_dir(root, slug) / "history")
    touch_person(root, slug)


def validate_entry(section: str, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    sec = schema["sections"].get(section)
    if not sec:
        raise RHError(f"Unknown section '{section}'.", "Valid sections: " + ", ".join(schema["sections"]))
    problems: List[str] = []
    clean: Dict[str, Any] = {}
    for key, value in data.items():
        if key == "section":
            continue
        if key in schema["reserved"]:
            problems.append(f"'{key}' is set automatically; remove it.")
            continue
        if key not in sec["allowed"]:
            problems.append(f"'{key}' is not allowed in '{section}'. Allowed: {', '.join(sec['allowed'])}")
            continue
        if key in schema["list_fields"]:
            if isinstance(value, str):
                value = [value]
            if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
                problems.append(f"'{key}' must be a list of text items.")
                continue
            value = [x.strip() for x in value if x.strip()]
            if value:
                clean[key] = value
        else:
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                value = str(value)
            if not isinstance(value, str):
                problems.append(f"'{key}' must be text.")
                continue
            value = value.strip()
            if value:
                clean[key] = value
    for req in sec["required"]:
        if req not in clean:
            problems.append(f"Missing required field '{req}' for section '{section}'.")
    if problems:
        raise RHError(f"Invalid '{section}' entry:\n  - " + "\n  - ".join(problems))
    return clean


def _identity(section: str, entry: Dict[str, Any]) -> str:
    first = entry.get("title") or entry.get("degree") or entry.get("name") or entry.get("label") or ""
    second = entry.get("organization") or entry.get("issuer") or entry.get("venue") or entry.get("url") or ""
    return "|".join([section, norm_key(first), norm_key(second), norm_key(entry.get("start", ""))])


def profile_add(root: Path, slug: str, items: List[Tuple[str, Dict[str, Any]]],
                allow_duplicate: bool = False) -> List[str]:
    """Validate everything first; write nothing unless every entry is valid."""
    schema = load_schema()
    prof = load_profile(root, slug)
    existing = {_identity(e["section"], e): e["id"] for e in prof["entries"]}
    prepared: List[Tuple[str, Dict[str, Any]]] = []
    seen = set()
    errors: List[str] = []
    for i, (section, data) in enumerate(items, 1):
        try:
            clean = validate_entry(section, data, schema)
        except RHError as exc:
            errors.append(f"Item {i}: {exc}")
            continue
        ident = _identity(section, clean)
        if not allow_duplicate and (ident in existing or ident in seen):
            errors.append(f"Item {i}: looks like a duplicate of {existing.get(ident, 'another item in this file')} "
                          f"({clean.get('title') or clean.get('name') or clean.get('degree') or clean.get('label')}).")
            continue
        seen.add(ident)
        prepared.append((section, clean))
    if errors:
        raise RHError("Nothing was saved.\n" + "\n".join(errors),
                      "Fix the items, or use 'profile update <id>' for an existing entry. "
                      "Use --allow-duplicate only if the user confirms it is a separate item.")
    ids = []
    for section, clean in prepared:
        prefix = schema["sections"][section]["prefix"]
        n = prof["counters"].get(prefix, 0) + 1
        prof["counters"][prefix] = n
        entry_id = f"{prefix}-{n:02d}"
        entry = {"id": entry_id, "section": section}
        entry.update(clean)
        entry["created"] = now_iso()
        prof["entries"].append(entry)
        ids.append(entry_id)
    save_profile(root, slug, prof)
    return ids


def profile_update(root: Path, slug: str, entry_id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
    schema = load_schema()
    prof = load_profile(root, slug)
    for entry in prof["entries"]:
        if entry["id"] == entry_id:
            section = entry["section"]
            merged = {k: v for k, v in entry.items() if k not in ("id", "section", "created", "updated")}
            for key, value in changes.items():
                if key == "section":
                    continue
                if value is None:
                    merged.pop(key, None)
                else:
                    merged[key] = value
            clean = validate_entry(section, merged, schema)
            created = entry.get("created")
            entry.clear()
            entry.update({"id": entry_id, "section": section})
            entry.update(clean)
            entry["created"] = created
            entry["updated"] = now_iso()
            save_profile(root, slug, prof)
            return entry
    raise RHError(f"No profile entry with id '{entry_id}'.", "List ids with: python scripts/rh.py profile show <person>")


def profile_remove(root: Path, slug: str, entry_id: str) -> None:
    prof = load_profile(root, slug)
    for i, entry in enumerate(prof["entries"]):
        if entry["id"] == entry_id:
            entry["removed"] = now_iso()
            prof["removed"].append(entry)
            del prof["entries"][i]
            save_profile(root, slug, prof)
            return
    raise RHError(f"No profile entry with id '{entry_id}'.")


def entry_text(entry: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key, value in entry.items():
        if key in ("id", "section", "created", "updated"):
            continue
        if isinstance(value, list):
            parts.extend(str(v) for v in value)
        else:
            parts.append(str(value))
    return "\n".join(parts)


def profile_text(prof: Dict[str, Any]) -> str:
    return "\n".join(entry_text(e) for e in prof["entries"])


def render_profile(prof: Dict[str, Any], section: Optional[str] = None) -> str:
    schema = load_schema()
    lines: List[str] = []
    for sec_key, sec in schema["sections"].items():
        if section and sec_key != section:
            continue
        entries = [e for e in prof["entries"] if e["section"] == sec_key]
        if not entries:
            continue
        lines.append(f"== {sec['title'].upper()} ({len(entries)}) ==")
        for e in entries:
            head = [e.get(k) for k in ("title", "degree", "name", "label", "role", "organization", "issuer", "venue", "start", "end", "date")]
            head_txt = " | ".join(str(x) for x in head if x)
            lines.append(f"[{e['id']}] {head_txt}")
            for key, value in e.items():
                if key in ("id", "section", "created", "updated", "title", "degree", "name", "label", "role",
                           "organization", "issuer", "venue", "start", "end", "date"):
                    continue
                if isinstance(value, list):
                    lines.append(f"    {key}:")
                    lines.extend(f"      - {v}" for v in value)
                else:
                    lines.append(f"    {key}: {value}")
        lines.append("")
    return "\n".join(lines).rstrip() or "(profile has no entries yet)"


def profile_counts(prof: Dict[str, Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for e in prof["entries"]:
        counts[e["section"]] = counts.get(e["section"], 0) + 1
    return counts


def profile_validate(root: Path, slug: str) -> Tuple[List[str], List[str]]:
    schema = load_schema()
    prof = load_profile(root, slug)
    errors: List[str] = []
    warnings: List[str] = []
    ids = {e["id"] for e in prof["entries"]}
    date_rx = re.compile(r"^(\d{4}([-/]\d{1,2})?|[A-Za-z]{3,9}\.? \d{4}|present|current|ongoing)$", re.I)
    for e in prof["entries"]:
        data = {k: v for k, v in e.items() if k not in ("id", "created", "updated")}
        try:
            validate_entry(e["section"], data, schema)
        except RHError as exc:
            errors.append(f"{e['id']}: {exc}")
        for ref in e.get("evidence", []):
            if ref not in ids:
                errors.append(f"{e['id']}: evidence refers to unknown id '{ref}'")
        for key in ("start", "end", "date"):
            if key in e and not date_rx.match(e[key]):
                warnings.append(f"{e['id']}: '{key}' = '{e[key]}' is not a clear date (use 2024, 2024-06, 'Jun 2024' or 'Present').")
        if e["section"] in ("experience", "internship", "project") and not e.get("bullets") and not e.get("description"):
            warnings.append(f"{e['id']}: no bullets or description yet; the writer will have little to use.")
        if e["section"] in ("experience", "internship", "project") and not e.get("metrics"):
            warnings.append(f"{e['id']}: no measurable results recorded (add 'metrics' if any are true).")
    if not any(e["section"] == "education" for e in prof["entries"]):
        warnings.append("No education entry recorded.")
    return errors, warnings


# --------------------------------------------------------------------------
# companies and recon
# --------------------------------------------------------------------------

def _companies_dir(root: Path) -> Path:
    return root / "companies"


def list_companies(root: Path) -> List[Dict[str, Any]]:
    out = []
    base = _companies_dir(root)
    if base.exists():
        for d in sorted(base.iterdir()):
            if (d / "company.json").exists():
                out.append(read_json(d / "company.json"))
    return out


def find_companies(root: Path, query: str) -> List[Dict[str, Any]]:
    scored = []
    for c in list_companies(root):
        s = match_score(query, [c["name"], c["slug"]] + c.get("aliases", []), strip_suffix=True)
        if s:
            scored.append((s, c))
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored]


def company_dir(root: Path, slug: str) -> Path:
    d = _companies_dir(root) / slug
    if not (d / "company.json").exists():
        names = ", ".join(c["slug"] for c in list_companies(root)) or "none yet"
        raise RHError(f"Unknown company '{slug}'. Existing companies: {names}",
                      "Use the exact slug from: python scripts/rh.py company list")
    return d


def create_company(root: Path, name: str, website: Optional[str] = None,
                   aliases: Optional[List[str]] = None, allow_duplicate: bool = False) -> Dict[str, Any]:
    name = name.strip()
    if not name:
        raise RHError("Company name is empty.")
    matches = [c for c in find_companies(root, name) if match_score(name, [c["name"]] + c.get("aliases", []), True) >= 2]
    if matches and not allow_duplicate:
        listing = ", ".join(f"{c['slug']} ({c['name']})" for c in matches)
        raise RHError(f"A similar company already exists: {listing}",
                      "Ask the user: is it the same company? If yes, reuse it. "
                      "If it is a different company, re-run with --allow-duplicate.")
    base = slugify(norm_key(name, True) or name, 40)
    slug, n = base, 2
    while (_companies_dir(root) / slug).exists():
        slug = f"{base}-{n}"
        n += 1
    d = _companies_dir(root) / slug
    for sub in ("recon", "jobs", "history"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    company = {"slug": slug, "name": name, "website": website or "", "aliases": aliases or [],
               "created": now_iso(), "updated": now_iso()}
    create_json(d / "company.json", company)
    return company


def recon_list(root: Path, slug: str) -> List[Dict[str, Any]]:
    d = company_dir(root, slug) / "recon"
    rx = re.compile(r"^recon-(\d{4}-\d{2}-\d{2})\.v(\d+)\.md$")
    out = []
    for item in d.iterdir():
        m = rx.match(item.name)
        if m:
            date = dt.date.fromisoformat(m.group(1))
            out.append({"path": item, "date": m.group(1), "version": int(m.group(2)),
                        "age_days": (dt.date.today() - date).days})
    out.sort(key=lambda x: (x["date"], x["version"]))
    return out


def recon_save(root: Path, slug: str, text: str) -> Path:
    d = company_dir(root, slug) / "recon"
    path = save_versioned(d, f"recon-{today()}", "md", text)
    return path


# --------------------------------------------------------------------------
# jobs (one posting at one company, shared by every person who applies)
# --------------------------------------------------------------------------

def jd_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _jobs_dir(root: Path, company_slug: str) -> Path:
    return company_dir(root, company_slug) / "jobs"


def list_jobs(root: Path, company_slug: str) -> List[Dict[str, Any]]:
    out = []
    base = _jobs_dir(root, company_slug)
    for d in sorted(base.iterdir()):
        if (d / "job.json").exists():
            out.append(read_json(d / "job.json"))
    return out


def job_dir(root: Path, company_slug: str, job_slug: str) -> Path:
    d = _jobs_dir(root, company_slug) / job_slug
    if not (d / "job.json").exists():
        names = ", ".join(j["slug"] for j in list_jobs(root, company_slug)) or "none yet"
        raise RHError(f"Unknown job '{job_slug}' at '{company_slug}'. Existing jobs: {names}")
    return d


def find_jobs(root: Path, company_slug: str, title: Optional[str] = None,
              jd_text: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    jobs = list_jobs(root, company_slug)
    exact, similar = [], []
    h = jd_hash(jd_text) if jd_text else None
    for j in jobs:
        if h and j.get("jd_hash") == h:
            exact.append(j)
        elif title and match_score(title, [j["title"]]) >= 2:
            similar.append(j)
    return {"exact": exact, "similar": similar, "all": jobs}


def create_job(root: Path, company_slug: str, title: str, jd_text: str,
               url: Optional[str] = None, allow_similar: bool = False) -> Dict[str, Any]:
    title = title.strip()
    if not title:
        raise RHError("Job title is empty.")
    if not jd_text.strip():
        raise RHError("The job description text is empty.")
    found = find_jobs(root, company_slug, title, jd_text)
    if found["exact"]:
        j = found["exact"][0]
        raise RHError(f"This exact job description is already saved as '{j['slug']}'.",
                      "Reuse it: its analysis does not need to be redone. Run: python scripts/rh.py job show "
                      f"{company_slug} {j['slug']}")
    if found["similar"] and not allow_similar:
        listing = ", ".join(f"{j['slug']} ({j['title']})" for j in found["similar"])
        raise RHError(f"A job with a similar title exists but its description text differs: {listing}",
                      "Ask the user: is this the same posting with edited text (reuse the old one), "
                      "or a new posting? If new, re-run with --allow-similar.")
    h = jd_hash(jd_text)
    slug = f"{slugify(title, 40)}--{h[:6]}"
    d = _jobs_dir(root, company_slug) / slug
    d.mkdir(parents=True, exist_ok=True)
    job = {"slug": slug, "company": company_slug, "title": title, "url": url or "",
           "jd_hash": h, "created": now_iso(), "updated": now_iso()}
    create_json(d / "job.json", job)
    create_text(d / "jd.md", jd_text.strip() + "\n")
    return job


ANALYSIS_LISTS = ["must_have", "nice_to_have", "keywords", "responsibilities", "constraints", "red_flags"]
ANALYSIS_STRINGS = ["title", "seniority", "role_family", "summary"]


def validate_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    problems = []
    clean: Dict[str, Any] = {}
    for key in ANALYSIS_STRINGS:
        value = data.get(key, "")
        if not isinstance(value, str):
            problems.append(f"'{key}' must be text.")
        else:
            clean[key] = value.strip()
    for key in ANALYSIS_LISTS:
        value = data.get(key, [])
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            problems.append(f"'{key}' must be a list of text items.")
        else:
            clean[key] = [x.strip() for x in value if x.strip()]
    unknown = set(data) - set(ANALYSIS_STRINGS) - set(ANALYSIS_LISTS)
    if unknown:
        problems.append("Unknown keys: " + ", ".join(sorted(unknown)))
    for req in ("title", "role_family"):
        if not clean.get(req):
            problems.append(f"Missing '{req}'.")
    for req in ("must_have", "keywords"):
        if not clean.get(req):
            problems.append(f"'{req}' must not be empty.")
    if problems:
        raise RHError("Invalid job analysis:\n  - " + "\n  - ".join(problems))
    return clean


def render_analysis_md(data: Dict[str, Any]) -> str:
    lines = [f"# Job analysis: {data['title']}", "",
             f"- Role family: {data['role_family']}", f"- Seniority: {data['seniority'] or 'not stated'}", ""]
    if data.get("summary"):
        lines += [data["summary"], ""]
    titles = {"must_have": "Must-have requirements", "nice_to_have": "Nice-to-have requirements",
              "keywords": "Keywords (exact phrases from the posting)", "responsibilities": "Responsibilities",
              "constraints": "Location / work-authorization constraints", "red_flags": "Unclear or suspicious parts"}
    for key in ANALYSIS_LISTS:
        lines.append(f"## {titles[key]}")
        items = data.get(key, [])
        lines.extend([f"- {x}" for x in items] if items else ["- none stated"])
        lines.append("")
    return "\n".join(lines)


def analysis_save(root: Path, company_slug: str, job_slug: str, data: Dict[str, Any]) -> Tuple[Path, Path]:
    d = job_dir(root, company_slug, job_slug)
    clean = validate_analysis(data)
    n = max(next_version(d, "analysis", "json"), next_version(d, "analysis", "md"))
    pj = create_json(d / f"analysis.v{n}.json", clean)
    pm = create_text(d / f"analysis.v{n}.md", render_analysis_md(clean))
    return pj, pm


def analysis_latest(root: Path, company_slug: str, job_slug: str) -> Optional[Tuple[Path, Dict[str, Any]]]:
    d = job_dir(root, company_slug, job_slug)
    latest = latest_version(d, "analysis", "json")
    if not latest:
        return None
    return latest[1], read_json(latest[1])


# --------------------------------------------------------------------------
# applications (one person applying to one job)
# --------------------------------------------------------------------------

APP_TEXT_STAGES = {
    "strategy": ("strategy", "md"),
    "resume-md": ("resume", "md"),
    "evidence-map": ("evidence-map", "md"),
    "review": ("review", "md"),
    "cover-letter": ("cover-letter", "md"),
    "cv-md": ("cv", "md"),
    "apply-routes": ("apply-routes", "md"),
}
APP_READONLY_STAGES = {
    "tex": ("resume", "tex"),
    "truth-report": ("truth-report", "md"),
    "lint-report": ("lint-report", "md"),
    "ats-report": ("ats-report", "md"),
}

# Settings that change the built files or the policy/ATS checks. The how-to-apply
# choice does not: it only decides whether a later text file is written.
APP_BUILD_SETTING_KEYS = ("region", "paper", "pages", "photo", "cover_letter", "cv")


def _apps_dir(root: Path, person_slug: str) -> Path:
    return person_dir(root, person_slug) / "applications"


def list_apps(root: Path, person_slug: str) -> List[Dict[str, Any]]:
    out = []
    base = _apps_dir(root, person_slug)
    for d in sorted(base.iterdir()):
        if (d / "app.json").exists():
            out.append(read_json(d / "app.json"))
    return out


def app_dir(root: Path, person_slug: str, app_id: str) -> Path:
    d = _apps_dir(root, person_slug) / app_id
    if not (d / "app.json").exists():
        names = ", ".join(a["id"] for a in list_apps(root, person_slug)) or "none yet"
        raise RHError(f"Unknown application '{app_id}'. Existing applications: {names}")
    return d


def find_apps(root: Path, person_slug: str, company: Optional[str] = None,
              job: Optional[str] = None) -> List[Dict[str, Any]]:
    return [a for a in list_apps(root, person_slug)
            if (not company or a["company"] == company) and (not job or a["job"] == job)]


def create_app(root: Path, person_slug: str, company_slug: str, job_slug: str,
               new: bool = False) -> Dict[str, Any]:
    person_dir(root, person_slug)
    cdata = read_json(company_dir(root, company_slug) / "company.json")
    jdata = read_json(job_dir(root, company_slug, job_slug) / "job.json")
    existing = find_apps(root, person_slug, company_slug, job_slug)
    if existing and not new:
        listing = ", ".join(f"{a['id']} [{a['status']}]" for a in existing)
        raise RHError(f"This person already has an application for this job: {listing}",
                      "Ask the user: continue the existing application (reuse its files; new saves become v2, v3...), "
                      "or start a separate new application? For a separate one, re-run with --new.")
    base = f"{company_slug}--{job_slug}--{today()}"
    app_id, n = base, 2
    while (_apps_dir(root, person_slug) / app_id).exists():
        app_id = f"{base}-{n}"
        n += 1
    d = _apps_dir(root, person_slug) / app_id
    d.mkdir(parents=True)
    app = {"id": app_id, "person": person_slug, "company": company_slug, "company_name": cdata["name"],
           "job": job_slug, "job_title": jdata["title"], "created": now_iso(), "updated": now_iso(),
           "status": "draft", "status_history": [{"status": "draft", "at": now_iso()}]}
    create_json(d / "app.json", app)
    return app


def _write_app(d: Path, app: Dict[str, Any]) -> None:
    app["updated"] = now_iso()
    tmp = d / "app.json.tmp"
    write_text_lf(tmp, _dump(app))
    os.replace(tmp, d / "app.json")


# Extra choices the user makes when a build starts. They are stored with the
# application, so a build keeps them even if the conversation is interrupted.
APP_OPTION_KEYS = ("cover_letter", "apply_routes", "cv")
APP_OPTION_LABELS = {"cover_letter": "Cover letter", "apply_routes": "How to apply", "cv": "CV version"}
APP_MENU_KEYS = ("region", "pages", "photo", "cover_letter", "apply_routes", "cv")


def app_settings(root: Path, person_slug: str, app_id: str) -> Dict[str, Any]:
    d = app_dir(root, person_slug, app_id)
    app = read_json(d / "app.json")
    regions = load_regions()
    conf = settings()
    cur = dict(app.get("settings", {}))
    region = cur.get("region", conf["default_region"])
    if region not in regions:
        region = conf["default_region"]
    out = {"region": region, "region_label": regions[region]["label"],
           "paper": cur.get("paper") or regions[region]["paper"],
           "pages": int(cur.get("pages", conf["default_pages"])),
           "photo": bool(cur.get("photo", False)), "chosen": "region" in cur,
           "settings_updated_at": app.get("settings_updated_at"),
           "menu_answered": bool(cur.get("menu_answered", False))
                             and all(key in cur for key in APP_MENU_KEYS)}
    for key in APP_OPTION_KEYS:
        out[key] = bool(cur.get(key, False))
    return out


def app_settings_set(root: Path, person_slug: str, app_id: str, region: Optional[str] = None,
                     photo: Optional[bool] = None, pages: Optional[int] = None,
                     paper: Optional[str] = None, force: bool = False,
                     cover_letter: Optional[bool] = None, apply_routes: Optional[bool] = None,
                     cv: Optional[bool] = None) -> Dict[str, Any]:
    d = app_dir(root, person_slug, app_id)
    app = read_json(d / "app.json")
    regions = load_regions()
    conf = settings()
    cur = app.setdefault("settings", {})

    def build_snapshot() -> Dict[str, Any]:
        region_key = cur.get("region", conf["default_region"])
        return {
            "region": region_key,
            "paper": cur.get("paper") or regions[region_key]["paper"],
            "pages": int(cur.get("pages", conf["default_pages"])),
            "photo": bool(cur.get("photo", False)),
            "cover_letter": bool(cur.get("cover_letter", False)),
            "cv": bool(cur.get("cv", False)),
        }

    before = build_snapshot()
    if region is not None:
        if region not in regions:
            raise RHError(f"Unknown region '{region}'.", "Regions: " + ", ".join(regions))
        cur["region"] = region
        if paper is None:
            cur["paper"] = regions[region]["paper"]
    if paper is not None:
        if paper not in ("a4", "letter"):
            raise RHError("Paper must be 'a4' or 'letter'.")
        cur["paper"] = paper
    if pages is not None:
        if pages not in (1, 2, 3):
            raise RHError("Pages must be 1, 2, or 3.")
        cur["pages"] = pages
    if photo is not None:
        cur["photo"] = bool(photo)
    eff_region = cur.get("region", settings()["default_region"])
    if cur.get("photo"):
        if regions.get(eff_region, {}).get("photo") == "never" and not force:
            raise RHError(f"Photos are not used on resumes in this region ({regions[eff_region]['label']}); "
                          "they can cause bias and many employers reject them.",
                          "Leave the photo off. If the user insists and the posting asks for one, repeat with --force.")
        if not latest_photo(root, person_slug):
            raise RHError("No photo is saved for this person.", "Save one first: python scripts/rh.py photo set <person> --file <image>")
    changed = any(value is not None for value in
                  (region, photo, pages, paper, cover_letter, apply_routes, cv))
    for key, value in (("cover_letter", cover_letter), ("apply_routes", apply_routes), ("cv", cv)):
        if value is not None:
            cur[key] = bool(value)
    if changed:
        # The menu is complete only when every answer has been saved. A later
        # change keeps it complete because the old answers remain in the record.
        cur["menu_answered"] = all(key in cur for key in APP_MENU_KEYS)
        # Only effective changes that affect a build or a policy/ATS check
        # invalidate those reports. Changing "how to apply" alone does not
        # affect either file, and explicitly saving an unchanged default is
        # not a change.
        after = build_snapshot()
        if any(after[key] != before[key] for key in APP_BUILD_SETTING_KEYS):
            # Microseconds matter here: a report written earlier in the same second
            # must still be older than the settings change.
            app["settings_updated_at"] = dt.datetime.now().astimezone().isoformat(timespec="microseconds")
    _write_app(d, app)
    return app_settings(root, person_slug, app_id)


def app_record_build(root: Path, person_slug: str, app_id: str, info: Dict[str, Any]) -> None:
    d = app_dir(root, person_slug, app_id)
    app = read_json(d / "app.json")
    app["build"] = info
    _write_app(d, app)


def app_save(root: Path, person_slug: str, app_id: str, stage: str, text: str) -> Path:
    if stage not in APP_TEXT_STAGES:
        raise RHError(f"Unknown stage '{stage}'.", "Stages: " + ", ".join(APP_TEXT_STAGES))
    if not text.strip():
        raise RHError("The content to save is empty.")
    d = app_dir(root, person_slug, app_id)
    stem, ext = APP_TEXT_STAGES[stage]
    path = save_versioned(d, stem, ext, text.rstrip() + "\n")
    _write_app(d, read_json(d / "app.json"))
    return path


def app_status(root: Path, person_slug: str, app_id: str, status: str) -> None:
    allowed = settings()["statuses"]
    if status not in allowed:
        raise RHError(f"Unknown status '{status}'.", "Allowed: " + ", ".join(allowed))
    d = app_dir(root, person_slug, app_id)
    app = read_json(d / "app.json")
    app["status"] = status
    app["status_history"].append({"status": status, "at": now_iso()})
    _write_app(d, app)


def app_latest(root: Path, person_slug: str, app_id: str, stage: str) -> Optional[Tuple[int, Path]]:
    d = app_dir(root, person_slug, app_id)
    table = dict(APP_TEXT_STAGES)
    table.update(APP_READONLY_STAGES)
    if stage not in table:
        raise RHError(f"Unknown stage '{stage}'.", "Stages: " + ", ".join(table))
    stem, ext = table[stage]
    return latest_version(d, stem, ext)


def app_files(root: Path, person_slug: str, app_id: str) -> List[str]:
    d = app_dir(root, person_slug, app_id)
    rx = re.compile(r"^(.+)\.v(\d+)\.(.+)$")
    latest: Dict[Tuple[str, str], int] = {}
    for item in d.iterdir():
        m = rx.match(item.name)
        if m:
            key = (m.group(1), m.group(3))
            latest[key] = max(latest.get(key, 0), int(m.group(2)))
    lines = []
    for item in sorted(d.iterdir()):
        if item.is_dir():
            continue
        m = rx.match(item.name)
        mark = ""
        if m and latest[(m.group(1), m.group(3))] == int(m.group(2)):
            mark = "   <- latest"
        lines.append(f"{item.name}{mark}")
    return lines


def _save_cmd(person_slug: str, app_id: str, stage: str, path: str) -> str:
    return f"python scripts/rh.py app save {person_slug} {app_id} {stage} --file {path}"


def app_progress(root: Path, person_slug: str, app_id: str) -> List[Dict[str, Any]]:
    """The steps of one application, in order, each with whether it is done and its next command.

    `wanted` marks a step that only happens when the start menu asked for it. Everything else is
    part of a finished application. Used by `rh.py brief` to say where a run has got to.

    This is also the context-rollover mechanism: after a new conversation, it reports the saved
    state and the exact next command without asking the user to remember the stages.
    """
    d = app_dir(root, person_slug, app_id)
    app = read_json(d / "app.json")
    st = app_settings(root, person_slug, app_id)
    settings_time = iso_stamp(st.get("settings_updated_at"))

    def has(stage: str) -> bool:
        return app_latest(root, person_slug, app_id, stage) is not None

    def stamp(path: Optional[Path]) -> Optional[float]:
        if path is None:
            return None
        try:
            return path.stat().st_mtime
        except OSError:
            return None

    def report_done(stage: str, inputs: List[Optional[Path]],
                    not_before: Optional[float] = None) -> bool:
        """A report counts only when it passed and is newer than every input it describes."""
        report = app_latest(root, person_slug, app_id, stage)
        if not report or report_fail_count(report[1]) != 0:
            return False
        report_time = stamp(report[1])
        if report_time is None:
            return False
        if not_before is not None and report_time < not_before:
            return False
        for path in inputs:
            input_time = stamp(path)
            if input_time is None or input_time > report_time:
                return False
        return True

    def build_files(version: int) -> bool:
        return all((d / name).exists() for name in (
            f"resume.v{version}.tex", f"resume.v{version}.docx", f"overleaf-resume.v{version}.zip"))

    resume = app_latest(root, person_slug, app_id, "resume-md")
    evidence = app_latest(root, person_slug, app_id, "evidence-map")
    profile = profile_path(root, person_slug)
    contact_path = person_dir(root, person_slug) / "contact.json"
    contact_data = load_contact(root, person_slug)
    analysis = analysis_latest(root, app["company"], app["job"])
    cover = app_latest(root, person_slug, app_id, "cover-letter")
    cv = app_latest(root, person_slug, app_id, "cv-md")
    photo = latest_photo(root, person_slug) if st["photo"] else None

    def build_done() -> bool:
        build = app.get("build") or {}
        version = build.get("version")
        status = build.get("status")
        if not isinstance(version, int) or version < 1:
            # A legacy record without a version can still be proved by a PDF.
            return latest_version(d, "resume", "pdf") is not None
        if not build_files(version):
            return False
        inputs = build.get("inputs")
        if isinstance(inputs, dict):
            # New records carry the exact source versions and settings they used.
            if not resume or inputs.get("resume_md") != resume[0]:
                return False
            snapshot = inputs.get("settings")
            if not isinstance(snapshot, dict) or any(
                    snapshot.get(key) != st.get(key) for key in APP_BUILD_SETTING_KEYS):
                return False
            if inputs.get("contact") != file_stamp(contact_path):
                return False
            if st["photo"] and (not photo or inputs.get("photo") != file_stamp(photo[1])):
                return False
            if st["cover_letter"] and (not cover or inputs.get("cover_letter") != cover[0]):
                return False
            if st["cv"] and (not cv or inputs.get("cv_md") != cv[0]):
                return False
        if status == "ok":
            if not (d / f"resume.v{version}.pdf").exists():
                return False
            if st["cover_letter"] and not (d / f"cover-letter.v{version}.pdf").exists():
                return False
            if st["cv"] and not (d / f"cv.v{version}.pdf").exists():
                return False
            if st["photo"] and not (d / f"resume-photo.v{version}.pdf").exists():
                return False
            return True
        if status == "tex-only":
            if st["cover_letter"] and not (d / f"cover-letter.v{version}.tex").exists():
                return False
            if st["cv"] and not (d / f"cv.v{version}.tex").exists():
                return False
            if st["photo"] and not (d / f"resume-photo.v{version}.tex").exists():
                return False
            return True
        if status == "no-engine":
            # The recorded build is valid while the machine still has no engine. If one
            # is installed later, the user should rebuild to get the PDF.
            if any(shutil.which(name) for name in ("pdflatex", "tectonic")):
                return False
            if st["cover_letter"] and not (d / f"cover-letter.v{version}.tex").exists():
                return False
            if st["cv"] and not (d / f"cv.v{version}.tex").exists():
                return False
            if st["photo"] and not (d / f"resume-photo.v{version}.tex").exists():
                return False
            return True
        if status is None:
            # A record from an older release: a PDF is the only proof of a finished build.
            if (d / f"resume.v{version}.pdf").exists():
                return True
            return not any(shutil.which(name) for name in ("pdflatex", "tectonic"))
        return False

    def export_done() -> bool:
        if not build_done():
            return False
        exports = d / "exports"
        if not exports.is_dir():
            return False
        folders = [p for p in exports.iterdir() if p.is_dir() and any(p.iterdir())]
        if not folders:
            return False
        export_time = max((stamp(p) or 0.0) for p in folders)
        built = [p for p in (latest_version(d, "resume", "pdf"),
                             latest_version(d, "resume", "docx")) if p]
        return bool(built) and all((stamp(p[1]) or 0.0) <= export_time for p in built)

    def current_pdf() -> Optional[Path]:
        """The PDF produced by the recorded build, never a PDF from an older build."""
        build = app.get("build") or {}
        version = build.get("version")
        status = build.get("status")
        if not isinstance(version, int) or version < 1:
            return latest_version(d, "resume", "pdf")
        if status not in (None, "ok"):
            return None
        path = d / f"resume.v{version}.pdf"
        return path if path.exists() else None

    pdf = current_pdf()
    truth_inputs = [resume[1] if resume else None, evidence[1] if evidence else None, profile]
    ats_inputs = [pdf, resume[1] if resume else None,
                  evidence[1] if evidence else None, profile, contact_path]
    if analysis:
        ats_inputs.append(analysis[0])
    if st["cover_letter"]:
        ats_inputs.append(cover[1] if cover else None)
    elif cover:
        ats_inputs.append(cover[1])
    if st["cv"]:
        ats_inputs.append(cv[1] if cv else None)
    elif cv:
        ats_inputs.append(cv[1])
    if st["photo"]:
        ats_inputs.append(photo[1] if photo else None)

    lint_inputs = [resume[1] if resume else None, profile, contact_path]
    if cover:
        lint_inputs.append(cover[1])
    if cv:
        lint_inputs.append(cv[1])
    if st["photo"] and photo:
        lint_inputs.append(photo[1])

    build_ok = build_done()
    ats_ok = build_ok and report_done("ats-report", ats_inputs, settings_time)
    # `check` includes the policy and writing lint. A passing, current ATS report
    # therefore also proves that lint passed; otherwise use the separate lint report.
    lint_ok = report_done("lint-report", lint_inputs, settings_time) or ats_ok

    review = app_latest(root, person_slug, app_id, "review")
    review_time = stamp(review[1]) if review else None
    build_time = stamp(pdf) if pdf else None
    review_ok = bool(review and ats_ok and review_time is not None and build_time is not None
                     and review_time >= build_time)

    steps = [
        ("Profile", True, sum(profile_counts(load_profile(root, person_slug)).values()) > 0,
         f"python scripts/rh.py profile show {person_slug}"),
        ("Contact details", True, bool(contact_data.get("name")),
         f"python scripts/rh.py contact form {person_slug}"),
        ("Company recon", True, bool(recon_list(root, app["company"])),
         f"python scripts/rh.py recon latest {app['company']}"),
        ("Job analysis", True, analysis is not None,
         f"python scripts/rh.py job show {app['company']} {app['job']}"),
        ("Start menu", True, bool(st["menu_answered"]),
         f"python scripts/rh.py app settings {person_slug} {app_id}"),
        ("Strategy", True, has("strategy"), _save_cmd(person_slug, app_id, "strategy", "scratch/strategy.md")),
        ("Resume text", True, has("resume-md"), _save_cmd(person_slug, app_id, "resume-md", "scratch/resume.md")),
        ("Evidence map", True, has("evidence-map"),
         _save_cmd(person_slug, app_id, "evidence-map", "scratch/evidence-map.md")),
        ("Truth check", True, report_done("truth-report", truth_inputs),
         f"python scripts/rh.py truth {person_slug} {app_id}"),
        ("Lint", True, lint_ok, f"python scripts/rh.py lint {person_slug} {app_id}"),
        ("Cover letter", st["cover_letter"], has("cover-letter"),
         _save_cmd(person_slug, app_id, "cover-letter", "scratch/cover-letter.md")),
        ("Longer CV", st["cv"], has("cv-md"), _save_cmd(person_slug, app_id, "cv-md", "scratch/cv.md")),
        ("Build", True, build_ok, f"python scripts/rh.py build {person_slug} {app_id}"),
        ("ATS check", True, ats_ok, f"python scripts/rh.py check {person_slug} {app_id}"),
        ("Review", True, review_ok, _save_cmd(person_slug, app_id, "review", "scratch/review.md")),
        ("How to apply", st["apply_routes"], has("apply-routes"),
         _save_cmd(person_slug, app_id, "apply-routes", "scratch/apply-routes.md")),
        ("Export", True, export_done(),
         f"python scripts/rh.py export {person_slug} {app_id}"),
    ]
    return [{"step": step, "wanted": wanted, "done": done, "next": nxt}
            for step, wanted, done, nxt in steps]


# --------------------------------------------------------------------------
# index, backup, reset
# --------------------------------------------------------------------------

def _md_row(cells: List[str]) -> str:
    return "| " + " | ".join(str(c).replace("|", "/") for c in cells) + " |"


def write_index(root: Path) -> Path:
    """Regenerate INDEX.md and applications.csv. These two files are rebuilt, never edited."""
    people = list_people(root)
    companies = list_companies(root)
    lines = ["# Resume Harness data index", "",
             f"Generated: {now_iso()}", f"Data folder: {root}", "",
             "This file is regenerated automatically. Do not edit it.", "", "## People", "",
             _md_row(["slug", "name", "profile entries", "contact saved", "applications", "updated"]),
             _md_row(["---"] * 6)]
    apps_rows: List[List[str]] = []
    for p in people:
        prof = read_json(person_dir(root, p["slug"]) / "profile.json")
        apps = list_apps(root, p["slug"])
        has_contact = (person_dir(root, p["slug"]) / "contact.json").exists()
        lines.append(_md_row([p["slug"], p["name"], len(prof["entries"]), "yes" if has_contact else "no",
                              len(apps), p.get("updated", "")]))
        for a in apps:
            pdf = latest_version(app_dir(root, p["slug"], a["id"]), "resume", "pdf")
            apps_rows.append([p["slug"], a["id"], a["company_name"], a["job_title"], a["status"],
                              a["created"], a["updated"], pdf[1].name if pdf else ""])
    lines += ["", "## Companies", "",
              _md_row(["slug", "name", "latest recon", "recon age (days)", "jobs"]), _md_row(["---"] * 5)]
    job_rows: List[List[str]] = []
    for c in companies:
        recons = recon_list(root, c["slug"])
        jobs = list_jobs(root, c["slug"])
        lines.append(_md_row([c["slug"], c["name"], recons[-1]["date"] if recons else "none",
                              recons[-1]["age_days"] if recons else "", len(jobs)]))
        for j in jobs:
            has_analysis = latest_version(job_dir(root, c["slug"], j["slug"]), "analysis", "json") is not None
            job_rows.append([c["slug"], j["slug"], j["title"], j["created"], "yes" if has_analysis else "no"])
    lines += ["", "## Jobs", "", _md_row(["company", "job slug", "title", "saved", "analysis done"]),
              _md_row(["---"] * 5)] + [_md_row(r) for r in job_rows]
    lines += ["", "## Applications", "",
              _md_row(["person", "application id", "company", "job", "status", "created", "updated", "latest pdf"]),
              _md_row(["---"] * 8)] + [_md_row(r) for r in apps_rows]
    index_path = root / "INDEX.md"
    write_text_lf(index_path, "\n".join(lines) + "\n")
    with open(root / "applications.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["person", "application_id", "company", "job_title", "status", "created", "updated", "latest_pdf"])
        writer.writerows(apps_rows)
    return index_path


def backup(root: Path, out: Optional[str] = None) -> Path:
    target = Path(out).expanduser() if out else root.parent / f"resume-harness-backup-{stamp()}.zip"
    if target.exists():
        raise RHError(f"Backup file already exists: {target}")
    base = target.with_suffix("")
    try:
        made = shutil.make_archive(str(base), "zip", root_dir=str(root))
        final = Path(made)
        if final != target:
            os.replace(final, target)
    except OSError as exc:
        for stale in {base.with_name(base.name + ".zip"), target}:
            try:
                stale.unlink()
            except OSError:
                pass
        raise RHError(f"Could not write the backup: {target} ({exc})",
                      "Choose a folder that exists and that you can write to, then run backup again.") from None
    return target


def _assert_ours(root: Path) -> None:
    if not (root / MARKER_NAME).exists():
        raise RHError(f"{root} is not a resume-harness data folder (marker file missing). Nothing was deleted.")
    if root == Path.home().resolve() or root == Path(root.anchor):
        raise RHError("Refusing to delete a home or root folder.")


def reset_all(root: Path, confirm: str) -> None:
    if confirm != "DELETE ALL DATA":
        raise RHError("Confirmation phrase is wrong. Nothing was deleted.",
                      'Ask the user to confirm, then pass: --confirm "DELETE ALL DATA"')
    _assert_ours(root)
    shutil.rmtree(root)


def forget(root: Path, kind: str, slug: str, confirm: str) -> int:
    expected = f"DELETE {slug}"
    if confirm != expected:
        raise RHError("Confirmation phrase is wrong. Nothing was deleted.",
                      f'Ask the user to confirm, then pass: --confirm "{expected}"')
    _assert_ours(root)
    if kind == "person":
        shutil.rmtree(person_dir(root, slug))
        return 0
    if kind == "company":
        d = company_dir(root, slug)
        dangling = 0
        for p in list_people(root):
            dangling += len([a for a in list_apps(root, p["slug"]) if a["company"] == slug])
        shutil.rmtree(d)
        return dangling
    raise RHError("Kind must be 'person' or 'company'.")
