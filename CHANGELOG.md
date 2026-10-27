# Changelog

## 1.3.0
Product release: easier for a first-time user, and safer to keep up to date.

Added
- **The start menu.** Every application now starts with the same short list of questions: country, photo, length, cover letter, how to apply, CV version, and anything to leave out or put first. The first six answers are saved with the application (`rh.py app settings ... --region <key> --pages 1|2|3 --photo on|off --cover-letter on|off --apply-routes on|off --cv on|off`), and every later step reads them, so nothing is asked twice. The seventh is written into the strategy. The menu is asked again for each new application, and read back instead of asked when the answers already exist. A partial answer no longer counts as complete, and the build refuses until all six are saved.
- **Private contact details.** `rh.py contact form <person>` opens a plain-text form in the data folder; the user types their name, email, phone, city and professional links there, and `rh.py contact import` saves them and deletes the form. The agent is told never to read the form or `contact.json`; `contact show` reports only which fields are saved (not link labels), the form's errors never echo a value, and `export` lists file types instead of names, so the person's name is not echoed into the conversation. A saved photo is made readable only by the user where the file system supports permissions (`0600`). The build fills `{{NAME}}` and `{{CONTACT}}` locally. The form prefills an existing contact for edits. If a person was saved under their real name before 1.3, `person rename` moves the folder and applications to a private id; `person label` changes only the display label. The boundary is documented: work history is still part of the conversation because the agent needs it to write.
- **A private label for the person.** `person create --label "Me"` separates "which person this is" from "what is printed on the resume"; the real name stays in the private contact form. `person rename` does the same for a person created before 1.3 under a real-name folder id.
- **LaTeX source and Overleaf zip in the export.** The export folder now holds `FirstName_LastName_Resume.tex` and `FirstName_LastName_Overleaf.zip`, with short steps in `docs/GETTING-STARTED.md` for Overleaf and for `pdflatex` on the computer.
- **Photo help.** `photo guide` now ends with phone instructions for taking a photo and a prompt for a photo editor that keeps the face unchanged, and says plainly not to generate or replace a face.
- **A cover letter, when the menu asks for one.** Written from the saved profile in the same header layout as the resume, built to `cover-letter.vN.pdf`, and exported as `FirstName_LastName_Cover-Letter.pdf`. Guidance: `.claude/skills/resume-writer/references/cover-letter.md`.
- **A longer CV, when the menu asks for one.** The same content format as the resume with room for more of the same true facts, built to `cv.vN.pdf` and `cv.vN.docx`, and exported as `FirstName_LastName_CV.pdf` and `.docx`.
- **How to apply, when the menu asks for it.** A short `apply-routes.md` with the public routes to the employer (careers page, portal, or a published application address) and a source link for each. Public information only; no logins and no guessed addresses.
- **A heartbeat for long runs.** `rh.py brief` prints where a run has got to: the saved start menu answers, every step with whether it is done, and the next command. `rh.py brief` with no arguments lists every application. The pipeline commands now print a `STAGE:` line above the existing `NEXT:` line.
- Continuous integration (`.github/workflows/ci.yml`). On every push and pull request, both maintainer scripts run on Python 3.9 and 3.13 with the PDF tools installed, and the job fails if the run leaves files behind.
- **A version check you control.** `python scripts/rh.py update` reports whether a newer version is published, and says so when this copy is newer than the published one. `python scripts/rh.py update --apply` replaces this copy, and an agent is told to ask the user first: a git clone is updated with `git pull`, anything else with a fresh download that never deletes a file, never replaces `config/data_location.txt`, and keeps the user's `lint.spell_allow` words. The check reads one public file, at most once a day, sends nothing about the user, the machine or the data folder, fails quietly when the computer is offline, and can be switched off for good with `python scripts/rh.py update --off`. A failed attempt is remembered for an hour, so an offline computer does not retry on every command. `python scripts/rh.py status` adds one `UPDATE:` line when a newer version exists. A check never downloads or changes anything.
- **A spelling and wording pass on the resume text.** `python scripts/rh.py lint` now also reports likely typos (a fixed list of about a hundred common ones), a word written twice in a row, a full stop with no space after it, and British and American spellings mixed in one document. All of these are warnings that ask the writer to check something; no build fails on spelling. A word that is correct for the user can be listed in `lint.spell_allow` in `config/settings.json`.
- **Policy and writing checks on the extra documents.** The saved cover letter and longer CV go through the same personal-data, link, photo and region policy checks when `lint` or `check` runs. The CV also gets the writing lint; the cover letter gets spelling and filler checks but not the resume-only pronoun rule, because first person is normal in a letter. Findings are prefixed with the document name. The evidence-map truth gate remains resume-specific and this is stated in the writer skill and the HOW-IT-WORKS guide.
- **The top third of page one, written down.** `resume-writer` now states that the headline, the summary, and the first bullets of the first section carry the strongest evidence for the job, and that nothing the job asks for should appear only on page two. The rule sits in `.claude/skills/resume-writer/references/bullet-writing.md`.
- **Ask once for a missing number.** Before writing an entry with no figures in it, the writer asks the user once, clearly, whether a real number exists, and records the answer with `profile update`. If there is no number, the bullet is written without one. Never guessed, and never asked twice for the same entry.
- **A default section order for each candidate type.** `resume-strategy` now starts from a short table (student, student with real research, experienced professional, moving between fields, researcher or bug bounty hunter, academic, returning after a break) and moves a section only for a reason that can be written down, with Education above Experience under about two years of work.
- **A page-break check.** The ATS check reports any entry that starts on one page and finishes on the next, naming both pages. An entry held together is easier to read and easier for a parser to attach to the right job.

Changed
- Removed the stale duplicate copies of the maintainer scripts. `scripts/selftest.py` and `scripts/verify_harness.py` (superseded by the `dev/` versions) and `docs/prompt-compliance.md` (superseded by `dev/COMPLIANCE.md`) are gone.
- `rh.py export` now copies the cover letter, the CV, the LaTeX source and the Overleaf zip beside the resume when the current menu asks for them. It uses the files from the recorded build version, so it cannot mix an old cover letter or photo with a new resume, and it warns instead of silently exporting a stale optional file. The command lists file types rather than the person's name, and the closing message says which type is used where.
- The README is rewritten for the person using it rather than for a developer: what it is, what is needed, one line to paste into an agent that does the download and the setup, a table of what to say for each thing you want, the files you get and where to send each one, what it will not do, where the data lives, and what to do when something goes wrong. It links to the guides instead of repeating them.
- The documentation is now agent-agnostic. OpenCode is recommended because the harness was built and tested on it and it provides free models through OpenCode Zen; Claude Code is supported; other capable agents are compatible and may need one extra skill pointer. `docs/AGENT-INSTALL.md` lists official sites and setup notes for the documented agents.
- The privacy wording across the README and guides now matches the mechanism and states the boundary honestly: contact details stay in a local form the agent is instructed not to read, while work history is part of the conversation and may be sent by the agent to its model provider.
- `docs/INSTALL.md` says that git is optional (with the ZIP address), and no longer claims the automatic checks read the Word file when the PDF text tool is missing.
- Five guides replace the old scattered notes. `docs/USAGE.md` is the copy-paste reference for installing, making a resume, changing profile facts, managing data, updating, removing, and recovering from common problems. `docs/AGENT-INSTALL.md` covers choosing and installing an agent. `docs/INSTALL.md` installs the harness with OpenCode or Claude Code and points other agents to the new guide. `docs/GETTING-STARTED.md` walks through one full run from a job advert to a folder of files. `docs/HOW-IT-WORKS.md` covers the design, the safety rules, what is enforced by code and what is left to the agent, and how to work on the code, in one file for users, developers and contributors.
- The docs now say not to run `/init` inside the harness: `AGENTS.md` already contains the project rules, and `/init` can change them. `AGENTS.md` also tells the agent to answer usage questions with the matching copy-paste prompt from `docs/USAGE.md`.
- `dev/verify_harness.py` now reads every file in `docs/`, not only the images guide, so the commands written in the guides are parsed with the real parser and every path they name must exist. It also resolves local Markdown links relative to the file that contains them, so a link like `docs/INSTALL.md` inside `docs/` is caught instead of quietly pointing at `docs/docs/INSTALL.md`.
- `python scripts/rh.py doctor` now names the interpreter it is running under and prints the exact command form for that machine (`python`, `python3` or `py`), and `AGENTS.md` gives the fallback chain in one line. A machine without a plain `python` now gets an instruction that runs, instead of a command that fails.
- The layout presets no longer squeeze the page. The tightest preset now keeps a 0.65in side margin and a 0.6in top and bottom margin, and the inside spacing does the tightening instead. A resume pushed to the edge of the paper reads as cramped and can be clipped by a printer; when the content still does not fit the page target, the build says so and something is cut. `dev/verify_harness.py` fails if a preset goes below the floor.

Fixed
- `dev/verify_harness.py` no longer reads `.git/`. The personal-data check used to fail on every clone because a git log holds the committer's name and address. Both maintainer scripts now pass with no known failures.
- `rh.py check` now uses the page length chosen in the start menu when it is longer than the old two-page default, so a three-page choice no longer fails its own check; a shorter choice still keeps the two-page safety limit.
- `rh.py update --apply` on a git clone without git now refuses with a clear message instead of trying a download over the clone. A failed `git pull` now names local edits as the likely cause.
- Python 3.9 support is real again. Five `Path.write_text(..., newline=...)` calls and one in the updater used a keyword that Python 3.9 does not accept; they now use an `open(..., newline="\n")` helper. `dev/verify_harness.py` fails if the pattern returns.
- A data folder path that is an existing file is refused by `set-data-dir`, `status` and `doctor` with a clear message instead of a `NotADirectoryError`.
- `doctor` no longer calls `iterdir()` on a data path that is a file.
- Every build outcome, including no TeX engine, a failed compile and `--no-compile`, now prints `STAGE:` and `NEXT:`.
- Piping `rh.py` output into `head` or `less` no longer prints a `BrokenPipeError` traceback.
- The update download is extracted with a zip-slip guard, so a member such as `../file` is refused before anything is copied. If the copy still stops part-way, the message now says some files may have been replaced and tells the user to run the update again; it no longer claims the old version still works.
- `dev/verify_harness.py` now enforces the documented 0.65in side and 0.60in top/bottom margin floor, not the old 0.6in flat floor.
- The `dev/COMPLIANCE.md` note no longer claims a YAML parser; it says the frontmatter is checked for the required fields and YAML-safe text.
- The `truth` command now points to `lint` as the next step, not `build`, matching the documented truth → lint → build order. The first full start-menu save now says the six answers are saved instead of saying "already answered".
- `rh.py brief` now counts a build only while the resume, contact details, photo, cover letter, CV and the build-related start-menu answers it used are unchanged, and the output files its status promises are present. A no-engine build stops counting once an engine is installed; a build with compile skipped on purpose still counts; a failed compile no longer counts because a `.tex` file exists. Export stops counting after a newer build. A review needs a current passing ATS check and must be newer than the built PDF. `brief` also lists Contact details and Lint as steps, and a current passing `check` satisfies the Lint step because `check` includes lint. The build record now keeps its result status and an input snapshot.
- After a failed truth, lint or ATS check, `NEXT:` now says to fix and rerun that check instead of moving to the next stage. The review and how-to-apply save hints now give the correct order: truth, lint, rebuild and check for a review, and export for how-to-apply.
- `rh.py export` now warns when the last ATS report has FAILs. A file that is not UTF-8 text, and a backup path that cannot be written, now give `ERROR:`/`HINT:` instead of a Python traceback. A name with no Latin letters now gets `Candidate` as the export file stem instead of `Resume`.

## 1.2.0
Product release: simpler for users, tidier for maintainers.

Added
- `python scripts/rh.py doctor`: a clear setup check for users. It tests Python, the harness files, the data folder, the PDF engine (with a real test build), the ATS text tool, and whether an OpenCode or Claude Code command is available. It changes nothing. Missing PDF tools are reported as optional because the Word file and the Overleaf zip still work.
- Start with normal English. `AGENTS.md` now routes any resume-related message, including a pasted job description alone, to the `resume-workflow` skill. Users no longer need slash commands.
- `docs/images/` with a guide for adding the demo video and screenshots (fictional data only).

Changed
- README rewritten for first-time users: what it does, a 6-step quick start, a safe first message, what to say, what happens behind the scenes, what it can and cannot do, troubleshooting, and how to start over. Developer material moved to the end.
- `selftest.py` and `verify_harness.py` moved to `dev/` (maintainers). Users are never told to run them. `verify_harness.py` now accepts the maintainer's public contact email in `SECURITY.md`; before, any real email there made both scripts fail.
- The build compliance record moved from `docs/prompt-compliance.md` to `dev/COMPLIANCE.md`.
- Bug report template asks for the output of `doctor`.
- Skills tell the agent to run `doctor` when a tool is missing.

Known issue (fixed in 1.3.0)
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
