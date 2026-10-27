#!/usr/bin/env python3
"""Self-test for the Resume Harness. Uses a temporary data folder and fictional data.

For maintainers (users run `python scripts/rh.py doctor` instead).
Run:  python dev/selftest.py
It never touches your real data folder. Exit code 0 means every check passed.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
HARNESS = HERE.parent
RH = [sys.executable, str(HARNESS / "scripts" / "rh.py")]
EX = HARNESS / "examples"

results = []


def make_png(path: Path, w: int, h: int) -> None:
    """Write a plain valid PNG (standard library only)."""
    import struct
    import zlib
    raw = b"".join(b"\x00" + bytes((190, 160, 140)) * w for _ in range(h))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append((name, condition))
    print(("PASS  " if condition else "FAIL  ") + name + (f"\n      {detail}" if (detail and not condition) else ""))


def run(data: Path, *args: str, env=None):
    environ = dict(os.environ)
    if env:
        environ.update(env)
    proc = subprocess.run(RH + ["--data-dir", str(data)] + list(args), capture_output=True, text=True,
                          env=environ)
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="rh-selftest-"))
    data = tmp / "data"
    try:
        # ---- data folder is separate -------------------------------------------------
        code, o = run(HARNESS / "inside-harness", "init")
        check("data folder inside the harness is refused", code != 0 and "outside the harness" in o, o)
        code, o = run(data, "init")
        check("init creates the data folder", code == 0 and (data / "resume-harness-data.json").exists(), o)
        check("harness folder holds no people/companies folders", not (HARNESS / "people").exists() and not (HARNESS / "companies").exists())
        not_a_folder = tmp / "not-a-folder"
        not_a_folder.write_text("this is a file\n", encoding="utf-8")
        code, o = run(data, "set-data-dir", str(not_a_folder))
        check("set-data-dir refuses an existing file without changing the saved pointer",
              code != 0 and "file, not a folder" in o and not (HARNESS / "config" / "data_location.txt").exists(), o)
        code, o = run(not_a_folder, "status")
        check("a data path that is a file is reported clearly, not as a crash",
              code != 0 and "file, not a folder" in o and "Traceback" not in o, o)
        code, o = run(not_a_folder, "doctor")
        check("doctor reports a data path that is a file as NOT READY, not a crash",
              code == 1 and "NOT READY" in o and "Traceback" not in o, o)


        # ---- doctor (the user-facing setup check) ------------------------------------
        code, o = run(data, "doctor")
        check("doctor reports READY and prints no traceback", code == 0 and "READY" in o and "Traceback" not in o and "Python" in o, o)
        check("doctor names the exact Python command form for this machine",
              "Run harness commands as:" in o and "scripts/rh.py <command>" in o, o)
        code, o = run(HARNESS / "inside-harness", "doctor")
        check("doctor says NOT READY when the data folder is inside the harness", code == 1 and "NOT READY" in o, o)
        bin_dir = tmp / "bin-no-tex"
        bin_dir.mkdir()
        try:
            (bin_dir / "python3").symlink_to(sys.executable)
            proc = subprocess.run([str(bin_dir / "python3"), str(HARNESS / "scripts" / "rh.py"), "--data-dir", str(data), "doctor"],
                                  capture_output=True, text=True, env=dict(os.environ, PATH=str(bin_dir)))
            out_text = proc.stdout + proc.stderr
            check("doctor treats a missing PDF engine as optional (still READY) and explains how to fix it",
                  proc.returncode == 0 and "No TeX engine found" in out_text and "READY, without PDF output" in out_text, out_text)
        except OSError:
            print("      (symlinks are not available here: the no-TeX doctor check was skipped)")

        # ---- people ------------------------------------------------------------------
        code, o = run(data, "person", "create", "--name", "Alex Example")
        check("person created", code == 0 and (data / "people" / "alex-example" / "profile.json").exists(), o)
        code, o = run(data, "person", "create", "--name", "alex  example")
        check("duplicate person is blocked and the agent must ask", code != 0 and "already exists" in o, o)
        code, o = run(data, "person", "find", "Alex")
        check("person find locates existing person", "MATCH: alex-example" in o, o)
        code, o = run(data, "person", "create", "--name", "Alex Example", "--allow-duplicate")
        check("--allow-duplicate creates a separate folder, never overwrites",
              code == 0 and (data / "people" / "alex-example-2").exists() and (data / "people" / "alex-example").exists(), o)
        run(data, "forget", "person", "alex-example-2", "--confirm", "DELETE alex-example-2")

        # ---- contact + profile -------------------------------------------------------
        code, o = run(data, "contact", "set", "alex-example", "--file", str(EX / "example-contact.json"))
        check("contact saved", code == 0, o)

        # ---- private contact form (v1.3) --------------------------------------------
        code, o = run(data, "person", "create", "--label", "Me")
        check("a person can be created with a private label instead of a real name",
              code == 0 and "me" in o and "Me" in o, o)
        code, o = run(data, "contact", "form", "me", "--no-open")
        form = data / "people" / "me" / "contact-form.txt"
        check("the private contact form is created and the command prints no values",
              code == 0 and form.exists() and "does not read" in o, o)
        form.write_text("name: Private Person\nemail: private.person@example.com\nphone: +1 555 0100\n"
                        "location: Springfield\nlink: LinkedIn | https://www.linkedin.com/in/private-person\n",
                        encoding="utf-8")
        code, o = run(data, "contact", "import", "me")
        check("import saves the contact details and deletes the form",
              code == 0 and not form.exists() and (data / "people" / "me" / "contact.json").exists(), o)
        check("import prints which fields were saved, never the values",
              "name, email, phone, location" in o and "private.person@example.com" not in o and "555 0100" not in o, o)
        code, o = run(data, "contact", "show", "me")
        check("contact show reports saved fields and never the values or link labels",
              "Name: saved" in o and "Links: 1 (labels hidden)" in o and "LinkedIn" not in o
              and "private.person@example.com" not in o and "555 0100" not in o, o)
        code, o = run(data, "person", "label", "me", "--label", "Myself")
        check("a person can be relabelled without touching the private contact",
              code == 0 and "Myself" in o, o)
        check("relabelling archives the previous person file, like other saved-file edits",
              list((data / "people" / "me" / "history").glob("person.*.json")) != [])
        run(data, "contact", "form", "me", "--no-open")
        form.write_text("name: Private Person\nlink: Instagram | https://instagram.com/private.person\n", encoding="utf-8")
        code, o = run(data, "contact", "import", "me")
        check("a blocked link is refused without printing the URL",
              code != 0 and "not allowed" in o and "instagram.com" not in o, o)
        form.unlink()
        code, o = run(data, "contact", "set", "me", "--email", "bad-email-private")
        check("the older contact command refuses a bad value without echoing it",
              code != 0 and "bad-email-private" not in o, o)

        code, o = run(data, "profile", "add", "alex-example", "--file", str(EX / "example-profile.json"))
        check("profile entries saved with ids", code == 0 and "int-01" in o and "skl-05" in o, o)
        code, o = run(data, "profile", "add", "alex-example", "--file", str(EX / "example-profile.json"))
        check("re-adding the same profile is blocked as duplicates", code != 0 and "duplicate" in o and "Nothing was saved" in o, o)
        code, o = run(data, "profile", "validate", "alex-example")
        check("profile validates with no errors", "0 error(s)" in o, o)
        bad = tmp / "bad.json"
        bad.write_text(json.dumps({"section": "experience", "title": "X", "salary": "1"}), encoding="utf-8")
        code, o = run(data, "profile", "add", "alex-example", "--file", str(bad))
        check("invalid fields are rejected and nothing is written", code != 0 and "organization" in o, o)
        before = len(list((data / "people" / "alex-example" / "history").iterdir()))
        upd = tmp / "upd.json"
        upd.write_text(json.dumps({"grade": "8.2 CGPA"}), encoding="utf-8")
        code, o = run(data, "profile", "update", "alex-example", "edu-01", "--file", str(upd))
        after = len(list((data / "people" / "alex-example" / "history").iterdir()))
        check("profile update archives the previous version", code == 0 and after == before + 1, o)

        # scratch files are removed after a successful save
        scratch_file = HARNESS / "scratch" / "selftest-tmp.json"
        scratch_file.write_text(json.dumps({"section": "language", "name": "English", "level": "Fluent"}), encoding="utf-8")
        code, o = run(data, "profile", "add", "alex-example", "--file", str(scratch_file))
        check("scratch input file is deleted after saving", code == 0 and not scratch_file.exists(), o)
        if scratch_file.exists():
            scratch_file.unlink()

        leftover = HARNESS / "scratch" / "selftest-leftover.txt"
        leftover.write_text("temporary text", encoding="utf-8")
        code, o = run(data, "clean-scratch")
        check("clean-scratch removes leftover temporary files and keeps .gitkeep",
              code == 0 and not leftover.exists() and (HARNESS / "scratch" / ".gitkeep").exists(), o)

        # ---- companies and recon -----------------------------------------------------
        code, o = run(data, "company", "create", "--name", "Northwind Example Corp", "--website", "https://northwind.example")
        check("company created", code == 0 and (data / "companies" / "northwind-example").exists(), o)
        code, o = run(data, "company", "create", "--name", "Northwind Example Corporation")
        check("similar company name is blocked (reuse prompt)", code != 0 and "similar company already exists" in o, o)
        code, o = run(data, "company", "find", "northwind")
        check("company find reports existing company", "MATCH: northwind-example" in o, o)
        recon = tmp / "recon.md"
        recon.write_text("# Recon: Northwind Example Corp\n- Builds payroll software (source: https://northwind.example, confidence: high)\n", encoding="utf-8")
        code1, o1 = run(data, "recon", "save", "northwind-example", "--file", str(recon))
        code2, o2 = run(data, "recon", "save", "northwind-example", "--file", str(recon))
        files = sorted(p.name for p in (data / "companies" / "northwind-example" / "recon").iterdir())
        check("two recon saves create two files (no overwrite)", code1 == 0 and code2 == 0 and len(files) == 2, str(files))
        code, o = run(data, "recon", "latest", "northwind-example")
        check("recon latest reports age and FRESH", "FRESH" in o and "0 days" in o, o)

        # ---- jobs --------------------------------------------------------------------
        jd = EX / "example-job-description.md"
        code, o = run(data, "job", "find", "northwind-example", "--title", "Junior Web Application Security Engineer", "--jd-file", str(jd))
        check("job find: nothing yet", "No existing job matches" in o, o)
        code, o = run(data, "job", "create", "northwind-example", "--title", "Junior Web Application Security Engineer", "--jd-file", str(jd))
        job_slug = o.split("Created job: ")[1].split()[0] if "Created job: " in o else ""
        check("job created", code == 0 and job_slug != "", o)
        code, o = run(data, "job", "create", "northwind-example", "--title", "Junior Web Application Security Engineer", "--jd-file", str(jd))
        check("same job description is detected as an exact duplicate", code != 0 and "already saved" in o, o)
        code, o = run(data, "job", "find", "northwind-example", "--jd-file", str(jd))
        check("job find reports EXACT MATCH", "EXACT MATCH" in o, o)
        jd2 = tmp / "jd2.md"
        jd2.write_text(jd.read_text(encoding="utf-8") + "\nUpdated: salary band added.\n", encoding="utf-8")
        code, o = run(data, "job", "create", "northwind-example", "--title", "Junior Web Application Security Engineer", "--jd-file", str(jd2))
        check("same title with different text asks the user (similar)", code != 0 and "similar title" in o, o)
        code, o = run(data, "job", "analysis-save", "northwind-example", job_slug, "--file", str(EX / "example-analysis.json"))
        check("analysis saved as v1 json and md", code == 0 and "analysis.v1.json" in o and "analysis.v1.md" in o, o)
        code, o = run(data, "job", "analysis-save", "northwind-example", job_slug, "--file", str(EX / "example-analysis.json"))
        check("second analysis is v2 (v1 kept)", code == 0 and "analysis.v2.json" in o, o)

        # ---- applications and versioned artifacts ------------------------------------
        code, o = run(data, "app", "create", "alex-example", "--company", "northwind-example", "--job", job_slug)
        app_id = o.split("Created application: ")[1].split()[0] if "Created application: " in o else ""
        check("application created", code == 0 and app_id != "", o)
        code, o = run(data, "app", "settings", "alex-example", app_id, "--region", "other", "--pages", "1",
                      "--photo", "off", "--cover-letter", "off", "--apply-routes", "off", "--cv", "off")
        check("the first full start-menu save says the answers are saved, not already answered",
              code == 0 and "all six answers are saved" in o and "already answered" not in o, o)
        code, o = run(data, "app", "create", "alex-example", "--company", "northwind-example", "--job", job_slug)
        check("second application for the same job is blocked (reuse prompt)", code != 0 and "already has an application" in o, o)
        code, o = run(data, "app", "create", "alex-example", "--company", "northwind-example", "--job", job_slug, "--new")
        check("--new creates a separate application folder", code == 0 and "-2" in o, o)

        s1 = run(data, "app", "save", "alex-example", app_id, "strategy", "--file", str(EX / "example-strategy.md"))
        s2 = run(data, "app", "save", "alex-example", app_id, "strategy", "--file", str(EX / "example-strategy.md"))
        d = data / "people" / "alex-example" / "applications" / app_id
        check("same stage saved twice makes v1 and v2", (d / "strategy.v1.md").exists() and (d / "strategy.v2.md").exists(), s1[1] + s2[1])
        check("strategy save tells the agent to stop for approval", "STOP" in s1[1], s1[1])

        # a bad resume: unsupported skill and unmapped bullet
        bad_resume = (EX / "example-resume.md").read_text(encoding="utf-8").replace(
            "- Programming: Python, Docker", "- Programming: Python, Docker, Kubernetes").replace(
            "## Education", "### Extra | | | 2024\n- Led a team of 12 engineers\n\n## Education")
        bad_path = tmp / "bad-resume.md"
        bad_path.write_text(bad_resume, encoding="utf-8")
        run(data, "app", "save", "alex-example", app_id, "resume-md", "--file", str(bad_path))
        run(data, "app", "save", "alex-example", app_id, "evidence-map", "--file", str(EX / "example-evidence-map.md"))
        code, o = run(data, "truth", "alex-example", app_id)
        check("truth check FAILS on an unsupported skill", code == 1 and 'Skill "Kubernetes" is not in the profile' in o, o)
        check("truth check FAILS on a bullet with no evidence line", "Led a team of 12 engineers" in o, o)
        check("a failed truth check says rerun truth, not lint or build",
              "rerun: python scripts/rh.py truth" in o.split("NEXT:", 1)[-1]
              and "python scripts/rh.py lint" not in o.split("NEXT:", 1)[-1]
              and "python scripts/rh.py build" not in o.split("NEXT:", 1)[-1], o)
        code, o = run(data, "brief", "alex-example", app_id)
        check("brief does not mark a failed truth report done", "[ ] Truth check" in o, o)

        binary = tmp / "not-text.bin"
        binary.write_bytes(b"\xff\xfe\x00\x80")
        code, o = run(data, "app", "save", "alex-example", app_id, "resume-md", "--file", str(binary))
        check("a non-UTF-8 input file gives ERROR, not a traceback",
              code == 2 and "ERROR:" in o and "Traceback" not in o, o)

        run(data, "app", "save", "alex-example", app_id, "resume-md", "--file", str(EX / "example-resume.md"))
        check("corrected resume saved as v2 (v1 kept)", (d / "resume.v1.md").exists() and (d / "resume.v2.md").exists())
        code, o = run(data, "truth", "alex-example", app_id)
        check("truth check passes on the supported resume", code == 0 and "0 FAIL" in o, o)
        check("a passing truth check points to lint before build",
              "python scripts/rh.py lint" in o.split("NEXT:", 1)[-1]
              and "python scripts/rh.py build" not in o.split("NEXT:", 1)[-1], o)
        code, o = run(data, "brief", "alex-example", app_id)
        check("brief marks a current passing truth report done", "[x] Truth check" in o, o)
        truth_report = sorted(d.glob("truth-report.v*.md"))[-1]
        old = truth_report.stat().st_mtime - 60
        os.utime(truth_report, (old, old))
        code, o = run(data, "brief", "alex-example", app_id)
        check("brief does not mark an old truth report done", "[ ] Truth check" in o, o)
        code, o = run(data, "truth", "alex-example", app_id)
        check("rerunning truth makes the step current again", code == 0 and "0 FAIL" in o, o)

        # ---- build + ATS -------------------------------------------------------------
        have_tex = shutil.which("pdflatex") is not None
        code, o = run(data, "build", "alex-example", app_id, "--paper", "a4")
        if have_tex:
            check("PDF built from Markdown with contact injected", code == 0 and (d / "resume.v1.pdf").exists(), o)
            check("Overleaf zip created", (d / "overleaf-resume.v1.zip").exists(), o)
            code, o = run(data, "build", "alex-example", app_id)
            check("second build creates v2 files, v1 untouched",
                  (d / "resume.v2.pdf").exists() and (d / "resume.v1.pdf").exists() and (d / "resume.v1.tex").exists(), o)
            code, o = run(data, "check", "alex-example", app_id)
            check("ATS check passes (0 FAIL) and reports keyword coverage", code == 0 and "Keyword coverage" in o, o)
            check("ATS check reports real keyword gaps without adding them", "penetration testing" in o and "Kubernetes" in o, o)
            check("a passing ATS check points to the review pass",
                  "review pass" in o.split("NEXT:", 1)[-1], o)
            code, o = run(data, "brief", "alex-example", app_id)
            check("brief marks a current passing ATS report done", "[x] ATS check" in o, o)
            ats_report = sorted(d.glob("ats-report.v*.md"))[-1]
            old = ats_report.stat().st_mtime - 60
            os.utime(ats_report, (old, old))
            code, o = run(data, "brief", "alex-example", app_id)
            check("brief does not mark an old ATS report done", "[ ] ATS check" in o, o)
            tex = (d / "resume.v1.tex").read_text(encoding="utf-8")
            check("LaTeX has the contact line filled in and no unreplaced markers",
                  "alex.example@example.com" in tex and "{{" not in tex and "%%" not in tex)
        else:
            check("build without a TeX engine still produces tex + zip and says so",
                  (d / "resume.v1.tex").exists() and (d / "overleaf-resume.v1.zip").exists() and "No TeX engine" in o, o)
            print("      (pdflatex not found: PDF and ATS checks were skipped)")

        if have_tex:
            # negative control: the old right-aligned layout must be caught by the ATS check
            bad_tex = tmp / "bad-layout.tex"
            bad_tex.write_text(r"""\documentclass{article}\usepackage[T1]{fontenc}\usepackage{mathptmx}
\begin{document}\pagestyle{empty}
Alex Example\par alex.example@example.com\par +00 00000 00000\par
\section*{Summary}Text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text text.\par
\section*{Internships}\textbf{Security Intern}\hfill Jun 2022 - Aug 2022\\ \textit{Sample Securities Ltd}\hfill \textit{Remote}\par
\section*{Research}\textbf{Disclosed an access-control flaw in an open-source web app}\hfill Mar 2024\par
\section*{Projects}\textbf{Vulnerable Lab Builder}\hfill 2023\par
\section*{Education}\textbf{B.Tech in Computer Science}\hfill 2019 - 2023\\ \textit{Example Institute of Technology}\hfill \textit{Springfield}\par
\section*{Certifications}\textbf{Example Web Security Practitioner}\hfill 2023\\ \textit{Example Training Org}\hfill\par
\section*{Skills}Security: Burp Suite\par
\end{document}""", encoding="utf-8")
            subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-output-directory", str(tmp), str(bad_tex)],
                           capture_output=True, cwd=str(tmp))
            if (tmp / "bad-layout.pdf").exists():
                code, o = run(data, "check", "alex-example", app_id, "--pdf", str(tmp / "bad-layout.pdf"))
                check("negative control: a layout that scrambles entry order is flagged", "Reading-order problem" in o or "out of order" in o, o)
                check("a failed ATS check says rerun check, not start the review",
                      "rerun: python scripts/rh.py check" in o.split("NEXT:", 1)[-1]
                      and "review pass" not in o.split("NEXT:", 1)[-1], o)
                code, o = run(data, "brief", "alex-example", app_id)
                check("brief does not mark a failed ATS report done", "[ ] ATS check" in o, o)
            else:
                print("      (negative-control PDF could not be built; skipped)")

            # stress test: special characters must not break the build
            run(data, "app", "create", "alex-example", "--company", "northwind-example", "--job", job_slug, "--new")
            apps = sorted(p.name for p in (data / "people" / "alex-example" / "applications").iterdir())
            stress_id = [a for a in apps if a != app_id and a.endswith("-2")][0]
            run(data, "app", "settings", "alex-example", stress_id, "--region", "other", "--pages", "1",
                "--photo", "off", "--cover-letter", "off", "--apply-routes", "off", "--cv", "off")
            stress = ("# {{NAME}}\nHeadline: Test Designation\n{{CONTACT}}\n\n## Summary\nR&D at 50% cost, item #1, snake_case, $5 budget, 100% {braces} ~tilde ^caret back\\slash. "
                      "Arrow \u2192 check \u2713 dash \u2013 quote \u201chello\u201d \u0928\u092e\n\n## Skills\n- Tools: C#, C++, R&D, [site](https://example.com/a_b?x=1&y=2#top)\n")
            sp = tmp / "stress.md"
            sp.write_text(stress, encoding="utf-8")
            run(data, "app", "save", "alex-example", stress_id, "resume-md", "--file", str(sp))
            code, o = run(data, "build", "alex-example", stress_id)
            check("special characters and non-Latin text build without crashing (non-Latin is replaced and warned)",
                  code == 0 and "PDF:" in o and "cannot be typeset" in o, o)


        # ======================= v1.1: links, regions, photo, lint, DOCX, autofit, export =======================
        code, o = run(data, "contact", "set", "alex-example", "--link", "Instagram=https://instagram.com/alex")
        check("Instagram link is refused", code != 0 and "Social media links are not allowed" in o, o)
        code, o = run(data, "contact", "set", "alex-example", "--link", "Chat=https://wa.me/000")
        check("WhatsApp link is refused even with a harmless label", code != 0 and "Social media" in o, o)
        code, o = run(data, "contact", "set", "alex-example", "--link", "X=https://x.com/alex")
        check("Twitter/X link is refused", code != 0 and "Social media" in o, o)
        code, o = run(data, "contact", "set", "alex-example", "--link", "WhatsApp=https://example.org/me")
        check("a link labelled WhatsApp is refused by label", code != 0 and "Social media" in o, o)
        code, o = run(data, "contact", "set", "alex-example", "--link", "LinkedIn=https://www.linkedin.com/in/alex-example",
                      "--link", "Portfolio=https://alex.example.org")
        check("professional links are accepted up to the limit of 3", code == 0, o)
        code, o = run(data, "contact", "set", "alex-example", "--link", "Behance=https://www.behance.net/alex")
        check("a 4th link is refused", code != 0 and "at most 3" in o, o)
        code, o = run(data, "contact", "set", "alex-example", "--remove-link", "Portfolio", "--remove-link", "LinkedIn")
        check("links can be removed by label", code == 0, o)
        code, o = run(data, "contact", "set", "alex-example", "--phone", "00000 00000", "--location", "12 Main Street, Flat 4")
        check("phone without country code and a street-address location give warnings",
              "country code" in o and "street address" in o, o)
        run(data, "contact", "set", "alex-example", "--phone", "+00 00000 00000", "--location", "Springfield")

        code, o = run(data, "region", "list")
        check("region list shows regions and photo rules", "india" in o and "us_canada" in o and "photo: never" in o, o)
        code, o = run(data, "app", "settings", "alex-example", app_id, "--region", "us_canada", "--photo", "on")
        check("photo is refused for the US and Canada", code != 0 and "not used on resumes" in o, o)
        code, o = run(data, "app", "settings", "alex-example", app_id, "--region", "india", "--photo", "on")
        check("photo cannot be turned on before a photo is saved", code != 0 and "No photo is saved" in o, o)
        code, o = run(data, "app", "settings", "alex-example", app_id)
        check("failed settings changes were not saved (photo still off)", "Photo version: off" in o, o)

        small, big, gif = tmp / "small.png", tmp / "photo.png", tmp / "photo.gif"
        code, o = run(data, "photo", "guide")
        check("photo guide gives phone help and an editor prompt, and says not to generate a face",
              "facing a window" in o and "face exactly as it is" in o and "Do not generate" in o, o)
        make_png(small, 120, 120)
        make_png(big, 520, 640)
        gif.write_bytes(b"GIF89a")
        code, o = run(data, "photo", "set", "alex-example", "--file", str(small))
        check("a small photo is saved with a size warning", code == 0 and "WARN" in o and "small" in o, o)
        code, o = run(data, "photo", "set", "alex-example", "--file", str(big))
        photo_dir = data / "people" / "alex-example" / "photo"
        check("a second photo is saved as v2 and v1 is kept", (photo_dir / "photo.v1.png").exists() and (photo_dir / "photo.v2.png").exists(), o)
        if os.name != "nt":
            photo_mode = (photo_dir / "photo.v2.png").stat().st_mode & 0o777
            check("the saved photo is private (0600)", photo_mode == 0o600, oct(photo_mode))
        code, o = run(data, "photo", "set", "alex-example", "--file", str(gif))
        check("a non-JPEG/PNG photo is refused", code != 0 and ".jpg" in o, o)
        code, o = run(data, "app", "settings", "alex-example", app_id, "--region", "india", "--photo", "on", "--pages", "1")
        check("India allows the photo once one is saved", code == 0 and "Photo version: on" in o and "Paper: A4" in o, o)
        code, o = run(data, "app", "settings", "alex-example", app_id, "--region", "us_canada")
        check("switching a photo-on application to a no-photo region is refused", code != 0 and "not used on resumes" in o, o)

        # ---- DOCX (no TeX needed) ----------------------------------------------------
        code, o = run(data, "build", "alex-example", app_id, "--no-compile")
        docs_found = sorted(d.glob("resume.v*.docx"))
        check("DOCX is created by every build", code == 0 and docs_found != [], o)
        check("build prints STAGE and NEXT even without compiling",
              "STAGE: Build" in o and "NEXT:" in o, o)
        if docs_found:
            import xml.etree.ElementTree as ET
            import zipfile as zf_mod
            with zf_mod.ZipFile(docs_found[-1]) as zf:
                names = set(zf.namelist())
                xml_ok = True
                for part in ("word/document.xml", "word/styles.xml", "word/numbering.xml", "[Content_Types].xml"):
                    try:
                        ET.fromstring(zf.read(part))
                    except Exception:  # noqa: BLE001
                        xml_ok = False
            check("DOCX parts are well-formed XML", xml_ok and {"word/document.xml", "word/styles.xml"} <= names)
            try:
                import docx as pydocx  # optional: only used for a stronger check when installed
                doc = pydocx.Document(str(docs_found[-1]))
                texts = [(p_.style.name, p_.text) for p_ in doc.paragraphs]
                headings = [t for st, t in texts if st == "Heading 1"]
                check("DOCX reads back in order: name, designation, contact, real headings, real bullets",
                      texts[0] == ("Title", "Alex Example") and texts[1][1].startswith("Computer Science Graduate")
                      and "@" in texts[2][1] and "Summary" in headings and any(st == "List Paragraph" for st, _ in texts))
            except ImportError:
                print("      (python-docx not installed: the DOCX read-back check was skipped)")

        # ---- lint and policy on a separate application --------------------------------
        code, o = run(data, "app", "create", "alex-example", "--company", "northwind-example", "--job", job_slug, "--new")
        lint_id = o.split("Created application: ")[1].split()[0] if "Created application: " in o else ""
        run(data, "app", "settings", "alex-example", lint_id, "--region", "other", "--pages", "1",
            "--photo", "off", "--cover-letter", "off", "--apply-routes", "off", "--cv", "off")
        bad_md = tmp / "lint-bad.md"
        bad_md.write_text("# {{NAME}}\n{{CONTACT}}\n\n## Summary\nI am a hard-working graduate. Date of Birth: 01 Jan 2000. Marital status: single. "
                          "Follow me on Instagram or WhatsApp. Nationality: Indian.\n\n## Internships\n"
                          "### Security Intern | Sample Securities Ltd | Remote | Jun 2022 - Aug 2022\n"
                          "- Responsible for testing web applications\n- Testing 4 internal web applications\n- Tests 4 more applications\n"
                          "### Support Intern | Sample Securities Ltd | | Jan 2021 - Feb 2021\n- Helped with tickets\n", encoding="utf-8")
        run(data, "app", "save", "alex-example", lint_id, "resume-md", "--file", str(bad_md))
        code, o = run(data, "lint", "alex-example", lint_id)
        check("lint FAILS when the Headline (designation) is missing", code == 1 and "No 'Headline:' line" in o, o)
        check("lint FAILS on date of birth and marital status", 'Personal detail "date of birth"' in o and 'Personal detail "marital status"' in o, o)
        check("lint FAILS on Instagram and WhatsApp mentions", "instagram" in o.lower() and "whatsapp" in o.lower(), o)
        check("lint FAILS on a nationality line outside regions that use it", "Nationality" in o and "not used on resumes" in o, o)
        check("lint WARNS on filler, pronouns, tense, short bullets and an employment gap",
              "Filler wording" in o and "First-person pronoun" in o and "present tense" in o and "Very short bullet" in o and "months between" in o, o)
        check("a failed lint says rerun lint before build",
              "rerun: python scripts/rh.py lint" in o.split("NEXT:", 1)[-1]
              and "python scripts/rh.py build" not in o.split("NEXT:", 1)[-1], o)
        code, o = run(data, "build", "alex-example", lint_id, "--no-compile")
        check("build refuses a resume without a Headline", code != 0 and "no 'Headline:' line" in o, o)
        run(data, "app", "settings", "alex-example", lint_id, "--region", "gulf")
        code, o = run(data, "lint", "alex-example", lint_id)
        check("a Gulf-region application may keep a nationality line", "Nationality" not in o.split("Result:")[0] or "not used on resumes" not in o, o)

        good_lint = tmp / "lint-good.md"
        good_lint.write_text((EX / "example-resume.md").read_text(encoding="utf-8"), encoding="utf-8")
        run(data, "app", "save", "alex-example", lint_id, "resume-md", "--file", str(good_lint))
        code, o = run(data, "lint", "alex-example", lint_id)
        check("the example resume passes lint with 0 FAIL", code == 0 and "0 FAIL" in o, o)
        check("lint confirms header order, links, personal data", "Header order is name, designation, contact" in o and "Links are professional only" in o, o)
        check("a passing lint points to build", "python scripts/rh.py build" in o.split("NEXT:", 1)[-1], o)
        code, o = run(data, "brief", "alex-example", lint_id)
        check("brief marks a current passing lint report done", "[x] Lint" in o, o)

        if have_tex:
            code, o = run(data, "build", "alex-example", app_id)
            photo_pdfs = sorted(d.glob("resume-photo.v*.pdf"))
            ats_pdfs = sorted(d.glob("resume.v*.pdf"))
            check("build reports layout preset, page target and page fill", code == 0 and "Layout preset:" in o and "Last page fill:" in o, o)
            check("a photo version PDF and zip are made when the photo is on", bool(photo_pdfs) and bool(sorted(d.glob("overleaf-resume-photo.v*.zip"))), o)
            if shutil.which("pdfimages") and photo_pdfs:
                def image_count(pdf: Path) -> int:
                    res = subprocess.run(["pdfimages", "-list", str(pdf)], capture_output=True, text=True)
                    return max(0, len(res.stdout.strip().splitlines()) - 2)
                check("the ATS PDF has no image; the photo PDF has one",
                      image_count(ats_pdfs[-1]) == 0 and image_count(photo_pdfs[-1]) >= 1)
            code, o = run(data, "check", "alex-example", app_id)
            check("ATS check confirms the extracted text starts with name, designation, contact",
                  "starts with name, then designation, then contact" in o, o)
            check("full check passes with 0 FAIL (truth, policy, lint, ATS)", code == 0 and "0 FAIL" in o, o)
            code, o = run(data, "export", "alex-example", app_id)
            exp1 = d / "exports" / "v1"
            check("export makes employer-ready names (PDF, DOCX, photo PDF)",
                  code == 0 and (exp1 / "Alex_Example_Resume.pdf").exists() and (exp1 / "Alex_Example_Resume.docx").exists()
                  and (exp1 / "Alex_Example_Resume_Photo.pdf").exists(), o)
            check("export includes the LaTeX source and the Overleaf zip",
                  (exp1 / "Alex_Example_Resume.tex").exists() and (exp1 / "Alex_Example_Overleaf.zip").exists(), o)
            check("export prints file types, never the person's name",
                  "Alex" not in o and "alex.example@example.com" not in o and "Resume (PDF)" in o, o)
            code, o = run(data, "export", "alex-example", app_id)
            check("a second export goes to v2 and v1 is untouched", (d / "exports" / "v2" / "Alex_Example_Resume.pdf").exists() and exp1.exists(), o)
            code, o = run(data, "brief", "alex-example", app_id)
            check("brief marks a current export done", "[x] Export" in o, o)
            if (tmp / "bad-layout.pdf").exists():
                run(data, "check", "alex-example", app_id, "--pdf", str(tmp / "bad-layout.pdf"))
                code, o = run(data, "export", "alex-example", app_id)
                check("export warns when the last ATS check has FAILs",
                      code == 0 and "WARN: The last ATS check reported" in o and "FAIL" in o, o)

            # content that cannot fit one page, and non-Latin text in the DOCX
            apps_now = sorted(p_.name for p_ in (data / "people" / "alex-example" / "applications").iterdir())
            long_md = tmp / "long.md"
            long_md.write_text("# {{NAME}}\nHeadline: Test Designation\n{{CONTACT}}\n\n## Projects\n" + "".join(
                f"### Project {i} | | | 20{10 + (i % 12):02d}\n- Built part {i} of a long test project with several words in this line\n"
                f"- Wrote notes {i} for the same long test project and kept them with the code\n" for i in range(1, 30)), encoding="utf-8")
            run(data, "app", "save", "alex-example", stress_id, "resume-md", "--file", str(long_md))
            code, o = run(data, "build", "alex-example", stress_id, "--pages", "1")
            check("content that cannot fit the page target is reported", "does not fit 1 page" in o and "tight" in o, o)
            stress_dir = data / "people" / "alex-example" / "applications" / stress_id
            devanagari = tmp / "dev.md"
            devanagari.write_text("# {{NAME}}\nHeadline: Test Designation\n{{CONTACT}}\n\n## Summary\n\u0928\u092e\u0938\u094d\u0924\u0947 world\n", encoding="utf-8")
            run(data, "app", "save", "alex-example", stress_id, "resume-md", "--file", str(devanagari))
            run(data, "build", "alex-example", stress_id, "--no-compile")
            latest_docx = sorted(stress_dir.glob("resume.v*.docx"))[-1]
            import zipfile as zf_mod2
            check("the DOCX keeps non-Latin text as typed", "\u0928\u092e\u0938\u094d\u0924\u0947" in zf_mod2.ZipFile(latest_docx).read("word/document.xml").decode("utf-8"))

        code, o = run(data, "build", "nobody", app_id)
        check("unknown person gives a clear error", code != 0 and "Unknown person" in o, o)

        # ---- a second person shares companies and jobs without duplicating them ------
        run(data, "person", "create", "--name", "Blake Sample")
        code, o = run(data, "app", "create", "blake-sample", "--company", "northwind-example", "--job", job_slug)
        check("second person applies to the same saved job (no repeated recon/analysis)", code == 0, o)
        check("only one company folder and one job folder exist",
              len(list((data / "companies").iterdir())) == 1 and len(list((data / "companies" / "northwind-example" / "jobs").iterdir())) == 1)
        check("people have separate folders", (data / "people" / "blake-sample").exists() and (data / "people" / "alex-example").exists())

        # ---- a real-name folder can be moved to a private id (v1.3) ------------------
        run(data, "person", "create", "--name", "Casey Sample")
        code, o = run(data, "app", "create", "casey-sample", "--company", "northwind-example", "--job", job_slug)
        casey_id = o.split("Created application: ")[1].split()[0] if "Created application: " in o else ""
        code, o = run(data, "person", "rename", "casey-sample", "--label", "Partner")
        check("rename moves the person folder and does not print the old real-name id",
              code == 0 and not (data / "people" / "casey-sample").exists()
              and (data / "people" / "partner").exists() and "casey-sample" not in o, o)
        casey_app = data / "people" / "partner" / "applications" / casey_id / "app.json"
        check("the renamed application points at the private id",
              casey_app.exists() and json.loads(casey_app.read_text(encoding="utf-8")).get("person") == "partner",
              casey_id)
        code, o = run(data, "person", "list")
        check("the private id replaces the real name in person list",
              "partner" in o and "Partner" in o and "casey-sample" not in o, o)
        code, o = run(data, "forget", "person", "partner", "--confirm", "DELETE partner")
        check("a renamed person can be removed cleanly", code == 0 and not (data / "people" / "partner").exists(), o)

        # ---- a missing contact sends the user to the private form, not contact set ---
        run(data, "person", "create", "--label", "No Contact")
        code, o = run(data, "app", "create", "no-contact", "--company", "northwind-example", "--job", job_slug)
        nc_id = o.split("Created application: ")[1].split()[0] if "Created application: " in o else ""
        run(data, "app", "settings", "no-contact", nc_id, "--region", "other", "--pages", "1",
            "--photo", "off", "--cover-letter", "off", "--apply-routes", "off", "--cv", "off")
        run(data, "app", "save", "no-contact", nc_id, "resume-md", "--file", str(EX / "example-resume.md"))
        code, o = run(data, "build", "no-contact", nc_id)
        check("a build with no contact details points to the private form, never contact set",
              code != 0 and "contact form" in o and "contact set" not in o, o)
        run(data, "forget", "person", "no-contact", "--confirm", "DELETE no-contact")

        # ======================= v1.3: the start menu and the extra documents =======================
        code, o = run(data, "app", "settings", "alex-example", app_id)
        check("an application with saved settings reads the start menu back",
              "already answered" in o and "Cover letter: off" in o and "How to apply: off" in o and "CV version: off" in o, o)
        code, o = run(data, "app", "settings", "alex-example", app_id, "--cover-letter", "on", "--apply-routes", "on")
        check("start menu answers are saved", code == 0 and "Cover letter: on" in o and "How to apply: on" in o, o)
        code, o = run(data, "app", "settings", "alex-example", app_id)
        check("the saved menu is read back and the prompt is gone",
              "already answered" in o and "not answered yet" not in o
              and "Cover letter: on" in o and "How to apply: on" in o and "CV version: off" in o, o)
        code, o = run(data, "app", "settings", "alex-example", app_id, "--cv", "on")
        check("one menu answer can be changed without changing the others",
              code == 0 and "CV version: on" in o and "Cover letter: on" in o and "How to apply: on" in o, o)
        code, o = run(data, "app", "settings", "alex-example", app_id, "--cover-letter", "maybe")
        check("a menu answer outside on/off is refused", code != 0, o)

        # ---- the heartbeat: brief, and the STAGE line on the pipeline commands --------
        code, o = run(data, "brief")
        check("brief lists the applications, what is done and the top rules",
              code == 0 and app_id in o and "steps done" in o and "Rules that matter most" in o, o)
        code, o = run(data, "brief", "alex-example", app_id)
        check("brief for one application shows the saved menu, every step and the next command",
              code == 0 and "Start menu answers" in o and "[x] Profile" in o and "[x] Contact details" in o
              and "Cover letter: on" in o and "Next: python scripts/rh.py" in o, o)
        code, o = run(data, "app", "settings", "alex-example", app_id)
        check("pipeline commands print a STAGE line above the NEXT line",
              "STAGE: Start menu" in o and "NEXT:" in o, o)

        code, o = run(data, "app", "create", "alex-example", "--company", "northwind-example", "--job", job_slug, "--new")
        second_id = o.split("Created application: ")[1].split()[0] if "Created application: " in o else ""
        code, o = run(data, "app", "settings", "alex-example", second_id)
        check("the menu starts unanswered again on a second application",
              "not answered yet" in o and "Cover letter: off" in o, o)
        code, o = run(data, "build", "alex-example", second_id)
        check("build refuses to run until the start menu is saved",
              code != 0 and "start menu is not saved" in o and "Traceback" not in o, o)
        code, o = run(data, "app", "settings", "alex-example", second_id, "--pages", "2")
        check("saving one menu answer alone does not mark the menu answered",
              code == 0 and "not answered yet" in o and "Page target: 2" in o, o)
        code, o = run(data, "app", "settings", "alex-example", second_id, "--region", "other", "--pages", "2",
                      "--photo", "off", "--cover-letter", "off", "--apply-routes", "off", "--cv", "off")
        check("saving all six marks the menu answered", code == 0 and "all six answers are saved" in o, o)

        if os.name != "nt":
            second_dir = d.parent / second_id
            fake_bin = tmp / "bin-fail-tex"
            fake_bin.mkdir()
            fake_engine = fake_bin / "pdflatex"
            fake_engine.write_text("#!/bin/sh\necho '! Fatal error' >&2\nexit 1\n", encoding="utf-8")
            fake_engine.chmod(0o755)
            run(data, "app", "save", "alex-example", second_id, "resume-md", "--file", str(EX / "example-resume.md"))
            code, o = run(data, "build", "alex-example", second_id,
                          env={"PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", "")})
            check("a failed compile still writes TeX and says COMPILE FAILED",
                  code == 0 and "COMPILE FAILED" in o and (second_dir / "resume.v1.tex").exists()
                  and (second_dir / "resume.v1.docx").exists(), o)
            second_record = json.loads((second_dir / "app.json").read_text(encoding="utf-8"))
            check("the build record keeps the compile-failed status",
                  second_record.get("build", {}).get("status") == "compile-failed", str(second_record.get("build")))
            code, o = run(data, "brief", "alex-example", second_id)
            check("brief does not mark a failed build done even when TeX exists", "[ ] Build" in o, o)

        if os.name != "nt":
            empty_bin = tmp / "bin-no-engine"
            empty_bin.mkdir()
            run(data, "app", "save", "alex-example", second_id, "resume-md", "--file", str(EX / "example-resume.md"))
            code, o = run(data, "build", "alex-example", second_id, env={"PATH": str(empty_bin)})
            check("a build with no TeX engine records the no-engine result",
                  code == 0 and "No TeX engine" in o and "Word file" in o, o)
            code, o = run(data, "brief", "alex-example", second_id, env={"PATH": str(empty_bin)})
            check("brief marks a no-engine build done while no engine is installed", "[x] Build" in o, o)
            engine_bin = tmp / "bin-engine"
            engine_bin.mkdir()
            fake_engine = engine_bin / "pdflatex"
            fake_engine.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake_engine.chmod(0o755)
            code, o = run(data, "brief", "alex-example", second_id, env={"PATH": str(engine_bin)})
            check("a no-engine build stops counting after an engine is installed", "[ ] Build" in o, o)

        (tmp / "cover-letter.md").write_text(
            "# {{NAME}}\n\nHeadline: Junior Web Application Security Engineer\n\n{{CONTACT}}\n\n"
            "Dear Hiring Team,\n\nMy lab work covers the OWASP Top 10.\n", encoding="utf-8")
        (tmp / "cv-long.md").write_text(
            "# {{NAME}}\n\nHeadline: Junior Web Application Security Engineer\n\n{{CONTACT}}\n\n"
            "## Experience\n\n- A bullet taken from the profile.\n", encoding="utf-8")
        (tmp / "apply-routes.md").write_text(
            "Careers page: https://northwind.example/careers (source: company site)\n", encoding="utf-8")
        code, o = run(data, "app", "save", "alex-example", app_id, "cover-letter", "--file", str(tmp / "cover-letter.md"))
        check("the cover letter saves as its own stage", code == 0 and "cover-letter.v1.md" in o, o)
        code, o = run(data, "app", "save", "alex-example", app_id, "cv-md", "--file", str(tmp / "cv-long.md"))
        check("the longer CV saves as its own stage", code == 0 and "cv.v1.md" in o, o)
        (tmp / "review.md").write_text("## Recruiter scan\nClear.\n", encoding="utf-8")
        code, o = run(data, "app", "save", "alex-example", app_id, "review", "--file", str(tmp / "review.md"))
        check("the review save hint sends the agent through truth, lint, rebuild and check",
              code == 0 and "truth" in o and "lint" in o and "rebuild" in o and "check" in o, o)
        code, o = run(data, "app", "save", "alex-example", app_id, "apply-routes", "--file", str(tmp / "apply-routes.md"))
        check("the application routes save as their own stage", code == 0 and "apply-routes.v1.md" in o, o)
        check("the apply-routes hint continues with the export, not a rebuild",
              "Continue with the export." in o and "python scripts/rh.py build" not in o.split("NEXT:", 1)[-1], o)
        code, o = run(data, "app", "cat", "alex-example", app_id, "cover-letter")
        check("the saved cover letter can be read back", "OWASP Top 10" in o, o)
        bad_letter = tmp / "cover-letter-bad.md"
        bad_letter.write_text(
            "# {{NAME}}\n\nHeadline: Junior Web Application Security Engineer\n\n{{CONTACT}}\n\n"
            "Dear Hiring Team,\n\nDate of Birth: 01 Jan 2000. I recieve the OWASP Top 10 training.\n",
            encoding="utf-8")
        run(data, "app", "save", "alex-example", app_id, "cover-letter", "--file", str(bad_letter))
        code, o = run(data, "lint", "alex-example", app_id)
        check("lint fails a cover letter with personal data and caps a spelling warning",
              code == 1 and "Cover letter: Personal detail" in o and "Cover letter: Spelling" in o, o)
        run(data, "app", "save", "alex-example", app_id, "cover-letter", "--file", str(tmp / "cover-letter.md"))
        code, o = run(data, "app", "save", "alex-example", app_id, "not-a-stage", "--file", str(tmp / "cv-long.md"))
        check("an unknown stage is still refused", code != 0 and "Unknown stage" in o, o)

        # ---- the two extra documents are built only when the menu asked for them ------
        code, o = run(data, "build", "alex-example", app_id)
        code, o = run(data, "brief", "alex-example", app_id)
        check("brief does not mark an export done after a newer build", "[ ] Export" in o, o)
        letters = sorted(d.glob("cover-letter.v*.pdf"))
        letter_tex = sorted(d.glob("cover-letter.v*.tex"))
        if have_tex:
            check("the cover letter is built as its own PDF", code == 0 and letters != [], o)
            check("the longer CV is built as its own PDF and Word file",
                  sorted(d.glob("cv.v*.pdf")) != [] and sorted(d.glob("cv.v*.docx")) != [], o)
        else:
            check("without a TeX engine the cover letter still produces LaTeX",
                  code == 0 and letter_tex != [], o)
        if letter_tex:
            tex = letter_tex[-1].read_text(encoding="utf-8")
            check("the cover letter uses the resume header and has no unreplaced markers",
                  "alex.example@example.com" in tex and "{{" not in tex and "%%" not in tex, tex[:400])
        code, o = run(data, "export", "alex-example", app_id)
        newest_export = sorted((d / "exports").iterdir())[-1]
        names = sorted(p.name for p in newest_export.iterdir())
        check("export copies the cover letter and the CV with employer-ready names",
              any(n.endswith("_Cover-Letter.pdf") for n in names) and any(n.endswith("_CV.pdf") for n in names),
              str(names))

        before = len(letters)
        run(data, "app", "settings", "alex-example", app_id, "--cover-letter", "off", "--cv", "off")
        code, o = run(data, "build", "alex-example", app_id)
        check("with the menu options off, the next build makes no new cover letter or CV",
              code == 0 and len(sorted(d.glob("cover-letter.v*.pdf"))) == before, o)
        run(data, "app", "settings", "alex-example", app_id, "--photo", "off")
        code, o = run(data, "build", "alex-example", app_id)
        code, o = run(data, "export", "alex-example", app_id)
        newest_export = sorted((d / "exports").iterdir())[-1]
        names = sorted(p.name for p in newest_export.iterdir())
        check("export follows the current menu and does not copy stale photo, cover letter or CV files",
              code == 0 and not any(n.endswith("_Resume_Photo.pdf") or n.endswith("_Cover-Letter.pdf")
                                    or "_CV." in n for n in names)
              and any(n.endswith("_Resume.docx") or n.endswith("_Resume.pdf") for n in names), str(names))

        # ---- résumé quality: spelling, page breaks, and the layout floor -------------
        sys.path.insert(0, str(HARNESS / "scripts"))
        import ats_check as ac
        import build_resume as br
        import export_resume as er
        import lint_resume as lr

        check("a name with no Latin letters gets a neutral export file name",
              er.file_stem_from_name("\u674e\u96f7") == "Candidate",
              er.file_stem_from_name("\u674e\u96f7"))

        typo_md = ("# X\nHeadline: Analyst\n\n## Summary\nExperiance in testing web applications.\n\n"
                   "## Experience\n### Tester | Example Org | | 2020 - 2021\n"
                   "- Organised the logs and organized the reports for the release team\n"
                   "- Fixed the the broken import in the nightly job\n")
        msgs = [f["msg"] for f in lr.lint_findings(typo_md)]
        check("the lint reports likely typos, repeated words and mixed spelling without failing anything",
              any("experiance" in m for m in msgs) and any("the the" in m for m in msgs)
              and any("British" in m for m in msgs), str(msgs))
        example_text = (EX / "example-resume.md").read_text(encoding="utf-8")
        check("the lint stays quiet on the worked example (no false alarms)",
              not [f for f in lr.lint_findings(example_text) if f["level"] == "WARN"],
              str([f["msg"] for f in lr.lint_findings(example_text) if f["level"] == "WARN"]))

        split_doc = {"name": "X", "headline": "Y", "sections": [{"title": "Experience", "blocks": [
            ("entry", ["First Role", "Acme Ltd", "", "2020 - 2021"]),
            ("bullets", ["Wrote the first release notes for the platform",
                         "Reviewed the second release notes for the platform and sent them on"]),
            ("entry", ["Second Role", "Beta Corp", "", "2021 - 2022"]),
            ("bullets", ["Led the migration of the billing service to the new platform",
                         "Trained four analysts on the new release process"]),
        ]}]}
        page_one = "First Role\nAcme Ltd | 2020 - 2021\nWrote the first release notes for the platform"
        page_two = ("Second Role\nBeta Corp | 2021 - 2022\nReviewed the second release notes for the platform and sent them on\n"
                    "Led the migration of the billing service to the new platform\nTrained four analysts on the new release process")
        split = ac.page_break_findings(split_doc, page_one + "\f" + page_two + "\f", 2)
        check("an entry that runs over a page break is reported",
              any("runs onto page 2" in f["msg"] for f in split), str(split))
        check("a one-page document cannot split an entry", ac.page_break_findings(split_doc, page_two, 1) == [])

        two_page_md = tmp / "two-page.md"
        two_page_md.write_text("# {{NAME}}\nHeadline: Test Designation\n{{CONTACT}}\n\n## Experience\n" + "".join(
            f"### Test Engineer {i} | Example Company {i} | Springfield | Jan 20{23 - i:02d} - Dec 20{24 - i:02d}\n"
            f"- Tested part {i} of the release process and wrote the findings for the platform team\n"
            f"- Reviewed the checks for part {i} with two analysts and closed every open item\n"
            for i in range(1, 16)), encoding="utf-8")
        run(data, "app", "save", "alex-example", app_id, "resume-md", "--file", str(two_page_md))
        code, o = run(data, "build", "alex-example", app_id, "--pages", "2")
        if shutil.which("pdftotext") and code == 0:
            two_pdf = sorted((data / "people" / "alex-example" / "applications" / app_id).glob("resume.v*.pdf"))[-1]
            t_text, t_pages, _ = ac.extract_pdf_text(two_pdf)
            t_doc = br.parse_resume_md(two_page_md.read_text(encoding="utf-8"))
            found = ac.page_break_findings(t_doc, t_text, t_pages)
            pass_msg = next((f["msg"] for f in found if f["level"] == "PASS"), "")
            check("every entry is located on a real two-page PDF, and no split is reported that is not there",
                  (t_pages or 0) >= 2 and "entries checked" in pass_msg
                  and not [f for f in found if f["level"] == "WARN"], f"{t_pages} pages: {found}")

        # the page length chosen in the start menu is the limit the check uses (v1.3)
        run(data, "app", "settings", "alex-example", app_id, "--pages", "3")
        code, o = run(data, "build", "alex-example", app_id)
        if code == 0:
            check("the build uses the chosen 3-page target", "target 3" in o, o)
            code, o = run(data, "check", "alex-example", app_id)
            check("check uses the chosen 3-page target, not a hard-coded 2",
                  "(limit 3)" in o or "the limit for this check is 3" in o, o)
            check("check no longer reports the old 2-page limit", "limit is 2" not in o, o)
        run(data, "app", "settings", "alex-example", app_id, "--pages", "1")

        # ---- build, export and review freshness --------------------------------------
        # The build above used a three-page target; the page target has just changed.
        code, o = run(data, "brief", "alex-example", app_id)
        check("brief marks a build and ATS report stale after a start-menu change",
              "[ ] Build" in o and "[ ] ATS check" in o, o)

        run(data, "app", "save", "alex-example", app_id, "resume-md", "--file", str(EX / "example-resume.md"))
        code, o = run(data, "build", "alex-example", app_id)
        if have_tex:
            code, o = run(data, "check", "alex-example", app_id)
            run(data, "app", "save", "alex-example", app_id, "review", "--file", str(tmp / "review.md"))
            code, o = run(data, "brief", "alex-example", app_id)
            check("brief marks review done only after the current build and ATS check",
                  "[x] Build" in o and "[x] ATS check" in o and "[x] Review" in o, o)
            code, o = run(data, "export", "alex-example", app_id)
            code, o = run(data, "brief", "alex-example", app_id)
            check("brief marks a current export done after a current build",
                  "[x] Export" in o, o)
            run(data, "app", "save", "alex-example", app_id, "resume-md", "--file", str(EX / "example-resume.md"))
            code, o = run(data, "brief", "alex-example", app_id)
            check("a new resume version makes build, ATS, review and export stale",
                  "[ ] Build" in o and "[ ] ATS check" in o and "[ ] Review" in o and "[ ] Export" in o, o)
            code, o = run(data, "build", "alex-example", app_id)

        # Cover, photo and contact changes are build inputs too. A build is made
        # after each setting change, so only the last edit is what makes it stale.
        run(data, "app", "settings", "alex-example", app_id, "--cover-letter", "on")
        run(data, "build", "alex-example", app_id)
        run(data, "app", "save", "alex-example", app_id, "cover-letter", "--file", str(tmp / "cover-letter.md"))
        code, o = run(data, "brief", "alex-example", app_id)
        check("saving a new cover letter makes the build stale", "[ ] Build" in o, o)

        run(data, "app", "settings", "alex-example", app_id, "--photo", "on")
        run(data, "build", "alex-example", app_id)
        photo_files = sorted((data / "people" / "alex-example" / "photo").glob("photo.v*.*"))
        if photo_files:
            when = photo_files[-1].stat().st_mtime + 5
            os.utime(photo_files[-1], (when, when))
        code, o = run(data, "brief", "alex-example", app_id)
        check("saving a new photo makes the build stale", "[ ] Build" in o, o)

        run(data, "build", "alex-example", app_id)
        code, o = run(data, "app", "settings", "alex-example", app_id, "--apply-routes", "on")
        check("changing only how-to-apply does not make the build stale",
              "Rebuild" not in o and "next pending step" in o, o)
        code, o = run(data, "brief", "alex-example", app_id)
        check("the build stays current after only how-to-apply changes", "[x] Build" in o, o)
        code, o = run(data, "app", "settings", "alex-example", app_id, "--pages", "2")
        check("changing a start-menu answer after a build tells the agent to rebuild",
              "Rebuild" in o and "check again" in o, o)
        run(data, "build", "alex-example", app_id)
        when = (data / "people" / "alex-example" / "contact.json").stat().st_mtime + 5
        os.utime(data / "people" / "alex-example" / "contact.json", (when, when))
        code, o = run(data, "brief", "alex-example", app_id)
        check("changing contact details makes the build stale", "[ ] Build" in o, o)

        # ---- the version check -------------------------------------------------------
        import zipfile

        sys.path.insert(0, str(HARNESS / "scripts"))
        import update_check as uc
        import rh as rh_cli

        secret_contact = {
            "name": "Private Person", "email": "private.person@example.com",
            "phone": "+1 555 0100", "location": "Springfield",
            "links": [{"label": "LinkedIn", "url": "https://www.linkedin.com/in/private-person"}],
        }
        log_line = ("name Private Person email private.person@example.com phone +1 555 0100 "
                    "location Springfield link https://www.linkedin.com/in/private-person")
        redacted = rh_cli._redact_contact(log_line, secret_contact)
        check("a TeX log excerpt redacts name, email, phone, location and links",
              all(value not in redacted for value in ("Private Person", "private.person@example.com",
                                                       "555 0100", "Springfield", "private-person"))
              and "[private]" in redacted and "[private link]" in redacted, redacted)

        check("version comparison orders releases correctly",
              uc.newer("1.4.0", "1.3.0") and not uc.newer("1.3.0", "1.3.0") and not uc.newer("1.2.9", "1.3.0")
              and uc.parse_version("v1.3.0-beta") == (1, 3, 0) and uc.parse_version("master") is None,
              str(uc.parse_version("v1.3.0-beta")))

        src = tmp / "published-folder"
        (src / "scripts" / "__pycache__").mkdir(parents=True)
        (src / "scripts" / "rh.py").write_text("# new\n", encoding="utf-8")
        (src / "scripts" / "__pycache__" / "junk.pyc").write_text("junk", encoding="utf-8")
        (src / "VERSION").write_text("99.0.1\n", encoding="utf-8")
        (src / "config").mkdir()
        (src / "config" / "data_location.txt").write_text("/somewhere/else\n", encoding="utf-8")
        dest = tmp / "install"
        (dest / "scripts").mkdir(parents=True)
        (dest / "scripts" / "rh.py").write_text("# old\n", encoding="utf-8")
        (dest / "config").mkdir()
        (dest / "config" / "data_location.txt").write_text("/my/real/data\n", encoding="utf-8")
        (dest / "my-notes.txt").write_text("mine\n", encoding="utf-8")
        copied, problems = uc.copy_program_files(src, dest)
        check("an update replaces program files, keeps the data pointer and copies no __pycache__",
              copied == 2 and not problems
              and (dest / "scripts" / "rh.py").read_text(encoding="utf-8") == "# new\n"
              and (dest / "config" / "data_location.txt").read_text(encoding="utf-8") == "/my/real/data\n"
              and not (dest / "scripts" / "__pycache__").exists()
              and (dest / "my-notes.txt").read_text(encoding="utf-8") == "mine\n",
              str((copied, problems)))

        (tmp / "published-version.txt").write_text("99.0.1\n", encoding="utf-8")
        fake = {"RH_UPDATE_URL": (tmp / "published-version.txt").as_uri()}
        silent = {"RH_UPDATE_URL": "http://127.0.0.1:9/VERSION"}

        code, o = run(data, "update", "--off")
        check("the daily version check can be switched off", code == 0 and "off." in o, o)
        code, o = run(data, "status")
        check("with the check off, status says nothing about versions", code == 0 and "UPDATE:" not in o, o)
        code, o = run(data, "update", "--on")
        check("the daily version check can be switched on again", code == 0 and "on." in o, o)
        code, o = run(data, "update", "check", env=fake)
        check("update reports a newer published version and asks before changing anything",
              code == 0 and "99.0.1" in o and "Ask the user" in o, o)
        code, o = run(data, "status", env=fake)
        check("status tells the user that a newer version exists", "UPDATE: version 99.0.1" in o, o)
        (tmp / "older-version.txt").write_text("0.0.1\n", encoding="utf-8")
        older = {"RH_UPDATE_URL": (tmp / "older-version.txt").as_uri()}
        code, o = run(data, "update", "check", env=older)
        check("a copy newer than the published version says so instead of calling itself newest",
              code == 0 and "newer than the published version" in o and "newest published" not in o, o)
        code, o = run(data, "update", "check", env=silent)
        check("an unreachable project fails quietly, with no traceback",
              code == 0 and "WARN" in o and "Traceback" not in o, o)
        state = uc.read_state(data)
        check("a failed version check is remembered, so an offline computer does not retry every command",
              bool(state.get("checked_at")) and state.get("latest") is None, str(state))

        # A real update, applied to a throwaway copy of the harness, so that this folder
        # (a git clone) is never touched. The copy has no .git, so the download path runs.
        copy = tmp / "harness-copy"
        shutil.copytree(HARNESS, copy, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        (copy / "config" / "data_location.txt").write_text("/my/real/data\n", encoding="utf-8")
        (copy / "config" / "settings.json").write_text(
            json.dumps({"lint": {"spell_allow": ["Zyzzyva"]}}, indent=2) + "\n", encoding="utf-8")
        release = tmp / "release" / "resume-harness-main"
        (release / "scripts").mkdir(parents=True)
        (release / "scripts" / "rh.py").write_text("# 99.0.1\n", encoding="utf-8")
        (release / "VERSION").write_text("99.0.1\n", encoding="utf-8")
        (release / "config").mkdir()
        (release / "config" / "data_location.txt").write_text("/somewhere/else\n", encoding="utf-8")
        (release / "config" / "settings.json").write_text(
            json.dumps({"lint": {"spell_allow": ["Newword"]}}, indent=2) + "\n", encoding="utf-8")
        (release / "NEW-IN-99.txt").write_text("new\n", encoding="utf-8")
        zip_path = tmp / "release.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for item in sorted(release.rglob("*")):
                zf.write(item, item.relative_to(release.parent))
        env = dict(fake, RH_UPDATE_ARCHIVE=zip_path.as_uri())
        proc = subprocess.run([sys.executable, str(copy / "scripts" / "rh.py"), "--data-dir", str(data),
                               "update", "check", "--apply"],
                              capture_output=True, text=True, env={**os.environ, **env})
        check("--apply updates a downloaded copy, keeps the data pointer and adds the new files",
              proc.returncode == 0 and (copy / "VERSION").read_text(encoding="utf-8") == "99.0.1\n"
              and (copy / "scripts" / "rh.py").read_text(encoding="utf-8") == "# 99.0.1\n"
              and (copy / "NEW-IN-99.txt").exists()
              and (copy / "config" / "data_location.txt").read_text(encoding="utf-8") == "/my/real/data\n",
              proc.stdout + proc.stderr)
        merged_settings = json.loads((copy / "config" / "settings.json").read_text(encoding="utf-8"))
        check("an archive update keeps the user's spelling allow-list words",
              set(merged_settings.get("lint", {}).get("spell_allow", [])) == {"Newword", "Zyzzyva"}
              and "spelling allow-list words were kept" in (proc.stdout + proc.stderr),
              json.dumps(merged_settings))

        evil_zip = tmp / "evil.zip"
        with zipfile.ZipFile(evil_zip, "w") as zf:
            zf.writestr("resume-harness-main/scripts/rh.py", "# evil\n")
            zf.writestr("resume-harness-main/../escaped.txt", "escaped\n")
        evil_unpack = tmp / "evil-unpack"
        evil_unpack.mkdir()
        blocked = False
        try:
            with zipfile.ZipFile(evil_zip) as zf:
                uc.safe_extract(zf, evil_unpack)
        except ValueError:
            blocked = True
        check("update extraction refuses a zip path that tries to escape the folder",
              blocked and not (tmp / "escaped.txt").exists(), str(list(evil_unpack.rglob("*"))))

        # ---- index, backup, reset ----------------------------------------------------
        run(data, "index")
        index = (data / "INDEX.md").read_text(encoding="utf-8")
        check("INDEX.md lists people, companies, jobs and applications",
              "alex-example" in index and "northwind-example" in index and job_slug in index and "blake-sample" in index)
        check("applications.csv exists", (data / "applications.csv").exists())
        code, o = run(data, "backup", "--out", str(tmp / "backup.zip"))
        check("backup zip created", code == 0 and (tmp / "backup.zip").exists(), o)
        blocked_backup = not_a_folder / "backup.zip"
        code, o = run(data, "backup", "--out", str(blocked_backup))
        check("a backup path under a file gives ERROR, not a traceback",
              code == 2 and "ERROR:" in o and "Traceback" not in o and not blocked_backup.exists(), o)
        code, o = run(data, "reset", "--confirm", "wrong")
        check("reset with a wrong phrase deletes nothing", code != 0 and data.exists(), o)
        code, o = run(data, "forget", "person", "blake-sample", "--confirm", "DELETE blake-sample")
        check("forget removes one person only", code == 0 and not (data / "people" / "blake-sample").exists() and (data / "people" / "alex-example").exists(), o)
        code, o = run(data, "reset", "--confirm", "DELETE ALL DATA")
        check("reset deletes the whole data folder (fresh install)", code == 0 and not data.exists(), o)
        code, o = run(data, "person", "list")
        check("after reset the harness starts fresh", "No people saved yet" in o, o)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    proc = subprocess.run([sys.executable, str(HERE / "verify_harness.py")], capture_output=True, text=True)
    check("verify_harness.py passes (skills, commands, docs, no personal data)", proc.returncode == 0, proc.stdout[-1500:])

    failed = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(failed)} of {len(results)} checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
