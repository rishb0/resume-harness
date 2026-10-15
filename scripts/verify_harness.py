#!/usr/bin/env python3
"""Consistency check for the harness itself (not for user data).

Checks that the skill and command files are valid, that every file path and skill
they mention exists, that every `python scripts/rh.py ...` command written in the
documents really parses with the real command-line parser, and that the harness
folder contains no personal data.

Run:  python scripts/verify_harness.py
"""
from __future__ import annotations

import io
import re
import shlex
import sys
from contextlib import redirect_stderr
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import rh  # noqa: E402

results = []
CREATED_LATER = {"config/data_location.txt"}  # written only when a user runs set-data-dir


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok))
    print(("PASS  " if ok else "FAIL  ") + name + (f"\n      {detail}" if (detail and not ok) else ""))


def frontmatter(path: Path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    data = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data


def yaml_safe(value: str) -> bool:
    """A plain YAML value must not contain ': ' or ' #' unless it is quoted."""
    if value[:1] in ("'", '"'):
        return value[-1:] == value[:1]
    return ": " not in value and " #" not in value


def main() -> int:
    skills_dir = ROOT / ".claude" / "skills"
    skill_dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir())
    expected = {"resume-workflow", "onboard-profile", "company-recon", "job-analysis",
                "resume-strategy", "resume-writer", "latex-builder", "ats-and-review"}
    check("all 8 skills exist", {d.name for d in skill_dirs} == expected, str({d.name for d in skill_dirs} ^ expected))

    for d in skill_dirs:
        fm = frontmatter(d / "SKILL.md") if (d / "SKILL.md").exists() else None
        ok = bool(fm) and fm.get("name") == d.name and bool(fm.get("description")) and yaml_safe(fm["description"]) \
            and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", d.name) is not None and len(fm["description"]) <= 1024
        check(f"skill '{d.name}' has valid frontmatter (name matches folder, description is valid YAML)", ok, str(fm))

    oc, cc = ROOT / ".opencode" / "commands", ROOT / ".claude" / "commands"
    names = sorted(p.name for p in oc.glob("*.md"))
    check("commands exist for onboard, new-job, build, review, data",
          names == ["build.md", "data.md", "new-job.md", "onboard.md", "review.md"], str(names))
    check("OpenCode and Claude Code command files are identical",
          all((oc / n).read_text(encoding="utf-8") == (cc / n).read_text(encoding="utf-8") for n in names if (cc / n).exists())
          and sorted(p.name for p in cc.glob("*.md")) == names)
    for n in names:
        fm = frontmatter(oc / n)
        check(f"command '{n}' has a YAML-safe description", bool(fm) and "description" in fm and yaml_safe(fm["description"]), str(fm))

    # ---- references: paths and skill names mentioned in documents must exist -----------
    docs = [ROOT / "AGENTS.md", ROOT / "README.md"] + list(skills_dir.glob("*/SKILL.md")) + \
        list(skills_dir.glob("*/references/*.md")) + list(oc.glob("*.md"))
    missing = []
    for doc in docs:
        if not doc.exists():
            missing.append(f"{doc.name} itself is missing")
            continue
        text = doc.read_text(encoding="utf-8")
        for token in re.findall(r"`([^`\n]+)`", text):
            token = token.strip().rstrip(".,:;")
            if re.fullmatch(r"(examples|config|templates|scripts)/[A-Za-z0-9_./-]+\.[a-z]+", token):
                if token not in CREATED_LATER and not (ROOT / token).exists():
                    missing.append(f"{doc.name}: {token}")
            elif re.fullmatch(r"references/[A-Za-z0-9_./-]+\.md", token) and doc.name == "SKILL.md":
                if not (doc.parent / token).exists():
                    missing.append(f"{doc.parent.name}/SKILL.md: {token}")
        for skill in re.findall(r"[Ll]oad (?:the )?skill `([a-z-]+)`", text):
            if skill not in expected:
                missing.append(f"{doc.name}: unknown skill {skill}")
    check("every file path and skill named in the documents exists", not missing, "; ".join(missing))

    # ---- commands written in documents must parse with the real parser -----------------
    parser = rh.make_parser()
    bad, count = [], 0
    for doc in docs:
        if not doc.exists():
            continue
        for span in re.findall(r"`(python scripts/rh\.py [^`\n]+)`", doc.read_text(encoding="utf-8")):
            if " ... " in span or span.endswith("...") or "--help" in span or re.search(r"[a-z]\|[a-z]", span):
                continue  # shorthand in prose, not a runnable command
            cmd = re.sub(r"<[^>]+>", "X", span)
            try:
                argv = shlex.split(cmd)[2:]
            except ValueError:
                bad.append(f"{doc.name}: cannot split: {span}")
                continue
            count += 1
            buf = io.StringIO()
            try:
                with redirect_stderr(buf):
                    parser.parse_args(argv)
            except SystemExit:
                bad.append(f"{doc.name}: {span}  ->  {buf.getvalue().strip().splitlines()[-1] if buf.getvalue() else 'parse error'}")
    # commands inside fenced code blocks (README and others)
    fenced = 0
    for doc in docs:
        if not doc.exists():
            continue
        for block in re.findall(r"```(?:bash|sh|text)?\n(.*?)```", doc.read_text(encoding="utf-8"), re.S):
            for line in block.splitlines():
                line = line.strip()
                if not line.startswith("python scripts/"):
                    continue
                fenced += 1
                script = line.split()[1]
                if not (ROOT / script).exists():
                    bad.append(f"{doc.name}: script missing: {script}")
                    continue
                if script == "scripts/rh.py":
                    cmd = re.sub(r"<[^>]+>", "X", line)
                    try:
                        argv = shlex.split(cmd)[2:]
                    except ValueError:
                        bad.append(f"{doc.name}: cannot split: {line}")
                        continue
                    buf = io.StringIO()
                    try:
                        with redirect_stderr(buf):
                            parser.parse_args(argv)
                    except SystemExit:
                        bad.append(f"{doc.name}: {line}  ->  {buf.getvalue().strip().splitlines()[-1] if buf.getvalue() else 'parse error'}")
    check(f"all {count} inline and {fenced} code-block commands written in the documents parse correctly",
          not bad and count > 20 and fenced >= 8, "\n      ".join(bad))

    # ---- config and template -----------------------------------------------------------
    import json
    try:
        json.loads((ROOT / "config" / "settings.json").read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "config" / "profile_schema.json").read_text(encoding="utf-8"))
        check("config files are valid JSON", True)
        prefixes = [s["prefix"] for s in schema["sections"].values()]
        check("profile section id prefixes are unique", len(prefixes) == len(set(prefixes)))
    except Exception as exc:  # noqa: BLE001
        check("config files are valid JSON", False, str(exc))
    tpl = (ROOT / "templates" / "latex" / "ats-classic" / "template.tex").read_text(encoding="utf-8")
    markers = ["HEADER", "BODY", "PAPER", "PDF_TITLE", "PDF_AUTHOR", "SOURCE", "PRESET", "FONTSIZE", "MARGIN_H",
               "MARGIN_V", "LINESPREAD", "ITEMSEP", "SEC_BEFORE", "SEC_AFTER"]
    check("template has all builder markers", all(f"%%{m}%%" in tpl for m in markers),
          str([m for m in markers if f"%%{m}%%" not in tpl]))
    check("template measures page fill and loads graphicx for the photo", "RH-FILL" in tpl and "graphicx" in tpl)
    conf = json.loads((ROOT / "config" / "settings.json").read_text(encoding="utf-8"))
    regions = json.loads((ROOT / "config" / "regions.json").read_text(encoding="utf-8"))
    check("regions are valid and the default region exists",
          conf["default_region"] in regions and all(r["paper"] in ("a4", "letter") and r["photo"] in ("optional", "never")
                                                    and isinstance(r["nationality"], bool) and r["notes"] for r in regions.values()))
    need = {"name", "font", "margin_h", "margin_v", "linespread", "itemsep", "sec_before", "sec_after"}
    check("autofit presets are complete and ordered roomy to tight (at least 3)",
          len(conf["autofit_presets"]) >= 3 and all(need <= set(x) for x in conf["autofit_presets"]))
    check("social media block list covers the main platforms",
          all(any(d in conf["blocked_link_domains"] for d in group) for group in
              (["instagram.com"], ["wa.me", "whatsapp.com"], ["twitter.com", "x.com"], ["facebook.com"], ["t.me"], ["snapchat.com"])))
    check("every --region key written in the documents is a real region",
          all(k in regions for doc in docs if doc.exists() for k in re.findall(r"--region ([a-z_]+)", doc.read_text(encoding="utf-8"))))
    check("VERSION file matches the README and CHANGELOG",
          (ROOT / "VERSION").read_text().strip() in (ROOT / "README.md").read_text(encoding="utf-8")
          and f"## {(ROOT / 'VERSION').read_text().strip()}" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))

    # ---- no personal data inside the harness -------------------------------------------
    leaks = []
    allowed_email = re.compile(r"@(example\.(com|org)|northwind\.example)$")
    for p in ROOT.rglob("*"):
        if not p.is_file() or "__pycache__" in p.parts or p.suffix in (".pdf", ".zip", ".png"):
            continue
        if p.name == "data_location.txt":
            leaks.append(f"{p.relative_to(ROOT)} exists (local setting; remove before sharing)")
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for email in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
            if not allowed_email.search(email):
                leaks.append(f"{p.relative_to(ROOT)}: email {email}")
        for phone in re.findall(r"\+?\d[\d \-()]{9,}\d", text):
            if phone.replace(" ", "") not in ("+000000000000000",) and not re.fullmatch(r"[0-9a-f]{10,}", phone):
                digits = re.sub(r"\D", "", phone)
                if len(set(digits)) > 1 and "20" not in digits[:2]:
                    leaks.append(f"{p.relative_to(ROOT)}: phone-like number {phone}")
    stray = [d for d in ("people", "companies", "resume-harness-data") if (ROOT / d).exists()]
    scratch_left = [p.name for p in (ROOT / "scratch").iterdir() if p.name != ".gitkeep"] if (ROOT / "scratch").exists() else []
    check("no emails or phone numbers other than the fictional examples", not leaks, "; ".join(leaks[:8]))
    check("no data folders and no leftover scratch files inside the harness", not stray and not scratch_left, f"{stray} {scratch_left}")

    failed = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(failed)} of {len(results)} harness checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
