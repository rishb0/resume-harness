# Changelog

## 1.2.0
Product release: simpler for users, tidier for maintainers.

Added
- `python scripts/rh.py doctor`: a plain-words setup check for users. It tests Python, the harness files, the data folder, the PDF engine (with a real test build), the ATS text tool, and whether an AI agent is installed. It changes nothing. Missing PDF tools are reported as optional because the Word file and the Overleaf zip still work.
- Plain-English start. `AGENTS.md` now routes any resume-related message, including a pasted job description alone, to the `resume-workflow` skill. Users no longer need slash commands.
- `docs/images/` with a guide for adding the demo video and screenshots (fictional data only).

Changed
- README rewritten for first-time users: what it does, a 6-step quick start, a safe first message, what to say, what happens behind the scenes, what it can and cannot do, troubleshooting, and how to start over. Developer material moved to the end.
- `selftest.py` and `verify_harness.py` moved to `dev/` (maintainers). Users are never told to run them. `verify_harness.py` now accepts the maintainer's public contact email in `SECURITY.md`; before, any real email there made both scripts fail.
- The build compliance record moved from `docs/prompt-compliance.md` to `dev/COMPLIANCE.md`.
- Bug report template asks for the output of `doctor`.
- Skills tell the agent to run `doctor` when a tool is missing.

Known issue (unchanged)
- Piping the output of `rh.py` into `head` or `less` can print a `BrokenPipeError` traceback. No data is lost, because every command saves before it prints.

## 1.1.0
Added
- Header order enforced: name, designation (`Headline:` line, now required), contact. Checked in the extracted PDF text.
- Link policy: social media (Instagram, WhatsApp, Twitter or X, Facebook, and similar) is refused; at most 3 professional links. `contact set --remove-link`.
- Personal-data policy: date of birth, marital status, religion, gender, parents' names, ID numbers, and full address are flagged as FAIL. Nationality only where the region allows it.
- Regions (`region list`): India, US and Canada, UK, EU, Gulf, other. Each sets paper size and the photo and nationality rules, stored per application (`app settings`).
- Optional photo: off by default, never offered where the region says `never`. Separate photo PDF; the ATS file never has a photo. `photo set`, `photo guide`.
- DOCX export built with the standard library only (real headings, bullets, hyperlinks; keeps non-Latin text).
- Auto-fit layout: tries layout presets and keeps the roomiest that fits the page target; reports page fill; warns when a one-page resume is sparse.
- Writing lint: filler words, pronouns, repeated openers, bullet length, summary length, tense, date style, date order, employment gaps.
- `export`: copies final files to `exports/vN/` as `FirstName_LastName_Resume.pdf` and `.docx` (and `_Photo.pdf`).
- `lint` command; `check` now runs truth, policy, lint, and ATS checks together.

Fixed
- Workflow said clean-scratch runs automatically on abandoned runs; it does not. The workflow now says to run it.
- Onboarding skill treated links as both contact details and a profile topic; links are now contact details only.
- `/build` and `/review` now state that the person slug is needed as well as the application id.
- README said `verify_harness.py` warns about `config/data_location.txt`; it fails.
- `verify_harness.py` now also checks commands written inside code blocks.

## 1.0.0
First release: separated data folder, create-only versioned saves, duplicate detection and reuse prompts, eight skills, truth check, ATS check, PDF and Overleaf zip build.
