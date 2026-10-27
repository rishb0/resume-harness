#!/usr/bin/env python3
"""Version check and update for the Resume Harness. Python 3.9+, standard library only.

The check downloads one small public file: the VERSION file on the project's default
branch. It sends nothing about the user, this machine, or the data folder, and it runs at
most once a day. A failed attempt is remembered for an hour, so an offline computer does
not retry on every command. The answer is cached in the data folder, so a command that asks
for it costs nothing until the next day.

Offline, or with the check switched off, it does nothing and says nothing.

Nothing is ever changed by a check. `rh.py update --apply` is the only thing that writes,
and the caller is expected to have asked the user first.

Two environment variables exist for mirrors and for tests, and are not needed in normal
use: RH_UPDATE_URL (where the version file is read from) and RH_UPDATE_ARCHIVE (where the
download of a fresh copy comes from).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import rhlib
from rhlib import RHError

PROJECT_URL = "https://github.com/rishb0/resume-harness"
VERSION_URL = PROJECT_URL.replace("github.com", "raw.githubusercontent.com") + "/main/VERSION"
ARCHIVE_URL = PROJECT_URL + "/archive/refs/heads/main.zip"
TIMEOUT_SECONDS = 3.0
CHECK_EVERY_HOURS = 24
FAILED_RETRY_HOURS = 1
STATE_NAME = "update-check.json"
# Directories that are never copied out of an archive over an existing install.
SKIP_PARTS = {"__pycache__", ".git"}
# Files inside the harness folder that belong to the user and are never replaced.
KEEP_FILES = {"config/data_location.txt"}


# --------------------------------------------------------------------------
# version numbers
# --------------------------------------------------------------------------

def parse_version(text: str) -> Optional[Tuple[int, ...]]:
    """'1.3.0' gives (1, 3, 0). 'v1.3.0-beta' also gives (1, 3, 0). Anything else gives None."""
    out: List[int] = []
    for part in text.strip().lstrip("vV").split("."):
        digits = ""
        for ch in part:
            if not ch.isdigit():
                break
            digits += ch
        if not digits:
            return None
        out.append(int(digits))
    return tuple(out) if out else None


def newer(candidate: str, current: str) -> bool:
    a, b = parse_version(candidate), parse_version(current)
    if a is None or b is None:
        return False
    return a > b


def current_version() -> str:
    return (rhlib.HARNESS_ROOT / "VERSION").read_text(encoding="utf-8").strip()


# --------------------------------------------------------------------------
# the cached answer, kept in the data folder
# --------------------------------------------------------------------------

def state_path(root: Path) -> Path:
    return root / STATE_NAME


def read_state(root: Path) -> Dict[str, Any]:
    try:
        data = json.loads(state_path(root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_state(root: Path, changes: Dict[str, Any]) -> None:
    """Best effort. A missing or read-only data folder is never an error here."""
    path = state_path(root)
    if not path.exists() and not (root / rhlib.MARKER_NAME).exists():
        return  # do not drop a stray file into a folder that is not a data folder
    state = read_state(root)
    state.update(changes)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        temp.replace(path)
    except OSError:
        pass


def enabled(root: Path) -> bool:
    """The user's choice if they made one, otherwise the default in config/settings.json."""
    state = read_state(root)
    if isinstance(state.get("enabled"), bool):
        return bool(state["enabled"])
    return bool(rhlib.settings().get("update_check", True))


def set_enabled(root: Path, flag: bool) -> None:
    if not (root / rhlib.MARKER_NAME).exists():
        raise RHError(f"There is no data folder at {root} yet.",
                      "Run any other command first, for example: python scripts/rh.py status")
    write_state(root, {"enabled": flag})


def _hours_since(stamp: Any) -> Optional[float]:
    if not isinstance(stamp, str):
        return None
    try:
        when = dt.datetime.fromisoformat(stamp)
    except ValueError:
        return None
    if when.tzinfo is None:
        when = when.astimezone()
    return (dt.datetime.now().astimezone() - when).total_seconds() / 3600.0


# --------------------------------------------------------------------------
# the check
# --------------------------------------------------------------------------

def fetch_latest(url: Optional[str] = None, timeout: float = TIMEOUT_SECONDS) -> Optional[str]:
    """The published version string, or None when the computer is offline or the file is missing."""
    target = url or os.environ.get("RH_UPDATE_URL") or VERSION_URL
    try:
        with urllib.request.urlopen(target, timeout=timeout) as response:  # noqa: S310 - fixed https URL
            text = response.read(64).decode("utf-8", "replace").strip()
    except Exception:  # noqa: BLE001 - offline, blocked, proxy, timeout: all the same here
        return None
    return text if parse_version(text) else None


def check(root: Path, force: bool = False) -> Dict[str, Any]:
    """The published version against this one. Uses the cached answer for up to a day."""
    current = current_version()
    if not force:
        state = read_state(root)
        age = _hours_since(state.get("checked_at"))
        latest = state.get("latest")
        latest = latest if isinstance(latest, str) and parse_version(latest) else None
        wait = CHECK_EVERY_HOURS if latest else FAILED_RETRY_HOURS
        if age is not None and age < wait:
            return {"current": current, "latest": latest, "newer": bool(latest and newer(latest, current)),
                    "offline": latest is None, "fresh": False}
    latest = fetch_latest()
    if latest is None:
        write_state(root, {"checked_at": rhlib.now_iso(), "latest": None})
        return {"current": current, "latest": None, "newer": False, "offline": True, "fresh": True}
    write_state(root, {"checked_at": rhlib.now_iso(), "latest": latest})
    return {"current": current, "latest": latest, "newer": newer(latest, current), "offline": False, "fresh": True}


def announce_if_newer(root: Path) -> Optional[str]:
    """One line for the user, or None. Never raises: a command must not break because of this."""
    try:
        if not enabled(root):
            return None
        res = check(root)
    except Exception:  # noqa: BLE001
        return None
    if not res.get("newer"):
        return None
    return (f"UPDATE: version {res['latest']} is available (this is {res['current']}). "
            f"Ask the user whether to update, then run: python scripts/rh.py update")


# --------------------------------------------------------------------------
# applying an update
# --------------------------------------------------------------------------

def is_git_clone() -> bool:
    return (rhlib.HARNESS_ROOT / ".git").exists() and shutil.which("git") is not None


def archive_url() -> str:
    """Where a fresh copy of the project is downloaded from. RH_UPDATE_ARCHIVE overrides it."""
    return os.environ.get("RH_UPDATE_ARCHIVE") or ARCHIVE_URL


def copy_program_files(src: Path, dest: Path) -> Tuple[int, List[str]]:
    """Copy a fresh copy of the harness over an existing install. Never deletes anything."""
    copied = 0
    problems: List[str] = []
    for item in sorted(src.rglob("*")):
        rel = item.relative_to(src)
        if SKIP_PARTS & set(rel.parts) or rel.as_posix() in KEEP_FILES:
            continue
        target = dest / rel
        if item.is_dir():
            continue
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item, target)
            copied += 1
        except OSError as exc:
            problems.append(f"{rel.as_posix()} ({exc})")
    return copied, problems


def apply_git_pull() -> Dict[str, Any]:
    proc = subprocess.run(["git", "-C", str(rhlib.HARNESS_ROOT), "pull", "--ff-only"],
                          capture_output=True, text=True)
    text = (proc.stdout + proc.stderr).strip()
    if proc.returncode == 0:
        return {"ok": True, "detail": "git pull finished. " + text.splitlines()[-1] if text else "git pull finished."}
    first = next((ln for ln in text.splitlines() if ln.strip()), "git pull failed.")
    return {"ok": False, "detail": first + " If you edited files in this folder, keep or commit them first "
                                             "(git status). Nothing was changed."}


def _kept_spell_allow() -> List[str]:
    """The user's own spelling words, read before an archive update replaces settings."""
    path = rhlib.HARNESS_ROOT / "config" / "settings.json"
    try:
        data = rhlib.read_json(path)
    except (RHError, OSError, ValueError):
        return []
    lint = data.get("lint") if isinstance(data, dict) else None
    allow = lint.get("spell_allow") if isinstance(lint, dict) else None
    if not isinstance(allow, list):
        return []
    return [word.strip() for word in allow if isinstance(word, str) and word.strip()]


def _merge_spell_allow(words: List[str]) -> bool:
    """Put the user's spelling words back into the freshly copied settings file."""
    path = rhlib.HARNESS_ROOT / "config" / "settings.json"
    try:
        data = rhlib.read_json(path)
    except (RHError, OSError, ValueError):
        return False
    if not isinstance(data, dict):
        return False
    lint = data.setdefault("lint", {})
    if not isinstance(lint, dict):
        return False
    allow = lint.get("spell_allow")
    current = [word for word in allow if isinstance(word, str)] if isinstance(allow, list) else []
    merged = sorted(set(current) | set(words))
    if merged == current:
        return False
    lint["spell_allow"] = merged
    try:
        rhlib.write_text_lf(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    except OSError:
        return False
    return True


def safe_extract(zf: zipfile.ZipFile, target: Path) -> None:
    """Extract a zip without letting a member escape the target folder (zip slip)."""
    base = target.resolve()
    for info in zf.infolist():
        name = info.filename.replace("\\", "/")
        parts = [part for part in name.split("/") if part not in ("", ".")]
        if not parts or ".." in parts or name.startswith("/") or parts[0].endswith(":"):
            raise ValueError("unsafe path in the download")
        dest = base.joinpath(*parts).resolve()
        if dest != base and base not in dest.parents:
            raise ValueError("unsafe path in the download")
        zf.extract(info, base)


def apply_archive() -> Dict[str, Any]:
    """Download the published folder and copy its files over this install."""
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "harness.zip"
        try:
            with urllib.request.urlopen(archive_url(), timeout=TIMEOUT_SECONDS * 10) as response, \
                    open(zip_path, "wb") as handle:
                shutil.copyfileobj(response, handle)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "detail": f"the download failed ({type(exc).__name__}). Try again later."}
        try:
            with zipfile.ZipFile(zip_path) as zf:
                safe_extract(zf, Path(tmp) / "unpacked")
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            return {"ok": False, "detail": f"the download is not safe to open ({exc}). Nothing was changed."}
        roots = [p for p in (Path(tmp) / "unpacked").iterdir() if p.is_dir()]
        if len(roots) != 1 or not (roots[0] / "scripts" / "rh.py").exists():
            return {"ok": False, "detail": "the download did not look like the harness. Nothing was changed."}
        published = (roots[0] / "VERSION").read_text(encoding="utf-8").strip() \
            if (roots[0] / "VERSION").exists() else ""
        if published and not newer(published, current_version()) and published != current_version():
            return {"ok": False, "detail": f"the download holds version {published}, which is not newer. Nothing was changed."}
        kept_words = _kept_spell_allow()
        copied, problems = copy_program_files(roots[0], rhlib.HARNESS_ROOT)
        if problems:
            return {"ok": False, "copied": copied, "partial": copied > 0,
                    "detail": "some files could not be replaced: " + "; ".join(problems[:3])}
        detail = f"{copied} file(s) replaced with version {published or 'the newest'}."
        if kept_words and _merge_spell_allow(kept_words):
            detail += " Your spelling allow-list words were kept."
        return {"ok": True, "copied": copied, "detail": detail}


def apply_update() -> Dict[str, Any]:
    if (rhlib.HARNESS_ROOT / ".git").exists() and shutil.which("git") is None:
        return {"ok": False, "detail": "This folder is a git clone, but git is not installed. "
                                       "Install git, or delete the .git folder to use the download update. "
                                       "Nothing was changed."}
    return apply_git_pull() if is_git_clone() else apply_archive()
