#!/usr/bin/env python3
"""Self-test for the Resume Harness. Uses a temporary data folder and fictional data.

Run:  python scripts/selftest.py
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
RH = [sys.executable, str(HERE / "rh.py")]
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


def run(data: Path, *args: str):
    proc = subprocess.run(RH + ["--data-dir", str(data)] + list(args), capture_output=True, text=True)
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

        run(data, "app", "save", "alex-example", app_id, "resume-md", "--file", str(EX / "example-resume.md"))
        check("corrected resume saved as v2 (v1 kept)", (d / "resume.v1.md").exists() and (d / "resume.v2.md").exists())
        code, o = run(data, "truth", "alex-example", app_id)
        check("truth check passes on the supported resume", code == 0 and "0 FAIL" in o, o)

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
            else:
                print("      (negative-control PDF could not be built; skipped)")

            # stress test: special characters must not break the build
            run(data, "app", "create", "alex-example", "--company", "northwind-example", "--job", job_slug, "--new")
            apps = sorted(p.name for p in (data / "people" / "alex-example" / "applications").iterdir())
            stress_id = [a for a in apps if a != app_id and a.endswith("-2")][0]
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
        make_png(small, 120, 120)
        make_png(big, 520, 640)
        gif.write_bytes(b"GIF89a")
        code, o = run(data, "photo", "set", "alex-example", "--file", str(small))
        check("a small photo is saved with a size warning", code == 0 and "WARN" in o and "small" in o, o)
        code, o = run(data, "photo", "set", "alex-example", "--file", str(big))
        photo_dir = data / "people" / "alex-example" / "photo"
        check("a second photo is saved as v2 and v1 is kept", (photo_dir / "photo.v1.png").exists() and (photo_dir / "photo.v2.png").exists(), o)
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
            code, o = run(data, "export", "alex-example", app_id)
            check("a second export goes to v2 and v1 is untouched", (d / "exports" / "v2" / "Alex_Example_Resume.pdf").exists() and exp1.exists(), o)

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

        # ---- index, backup, reset ----------------------------------------------------
        run(data, "index")
        index = (data / "INDEX.md").read_text(encoding="utf-8")
        check("INDEX.md lists people, companies, jobs and applications",
              "alex-example" in index and "northwind-example" in index and job_slug in index and "blake-sample" in index)
        check("applications.csv exists", (data / "applications.csv").exists())
        code, o = run(data, "backup", "--out", str(tmp / "backup.zip"))
        check("backup zip created", code == 0 and (tmp / "backup.zip").exists(), o)
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
