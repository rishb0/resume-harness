# Prompt compliance record

Covers version 1.0 (sections A to E) and the version 1.1 refinements (section F).

This compares the original build prompt, plus the later data requirements, with what this harness contains.
Status words: **Done**, **Changed** (done differently, with the reason), **Not done** (with the reason).
"Tested" means `python scripts/selftest.py` or `python scripts/verify_harness.py` checks it.

## A. Data requirements added later

| Requirement | Status | How |
| --- | --- | --- |
| Save all people, companies, jobs in an organised structure a human can browse | Done | `people/<slug>/`, `companies/<slug>/jobs/<role>--<id>/`, plus a generated `INDEX.md` and `applications.csv`. Tested. |
| Keep data for all people, all companies, all jobs per company | Done | One folder per entity. Two people share one company and one job without duplicating them. Tested. |
| Do not repeat steps for the same person, company, or job | Done | `person find`, `recon latest` (age and FRESH/STALE), `job find` (exact match by text hash), `app find`. Duplicate creation is blocked by the code, so the agent must ask. Tested. |
| Never overwrite same-name files | Done | Create-only writes. Documents get `.v1`, `.v2`. Edited JSON is archived to `history/` first. Scratch files are consumed after saving. Tested. |
| Agent asks whether to use existing data | Done | `resume-workflow` steps 1 to 4 say exactly when to ask; the code errors with a HINT telling the agent to ask. |
| Data separate from the harness, like an installed app; clearing data gives a fresh app | Done | Data folder is outside the harness (refused if inside). Default is `~/resume-harness-data`; changeable. `reset` deletes it and the harness starts fresh. `backup` and `forget` exist. Tested. |
| Verify at the end against the prompt | Done | This file, plus the two automated checks. |

## B. Original prompt: rules

| Rule | Status | How |
| --- | --- | --- |
| 1. Truth gate | Done, with a stated limit | `truth` check fails on bullets with no evidence line, unknown ids, skills not in the profile; warns on numbers and employers not in the cited evidence. It cannot judge whether a reworded sentence is still true, or whether the profile itself is true. Tested, including failure cases. |
| 2. Do not guess how OpenCode works; read the docs | Done for this build | I read the current OpenCode docs for skills (locations, `.claude/skills` support, frontmatter) and commands (`.opencode/commands`, `$ARGUMENTS`). Not run inside OpenCode (see section E). |
| 3. Work in small phases with approval | Changed | I built the harness myself, so the phase rule applies to the workflow instead: the strategy step is a hard stop for approval. |
| 4. No personal data in the harness; contact placeholders | Done | Contact is saved by command into the data folder and filled in only at build time. `verify_harness.py` scans for emails and phone numbers. Tested. |
| 5. No scraping behind logins, no LinkedIn, no employee personal data | Done | In `AGENTS.md` and `company-recon`. |
| 6. Unknown stays "unknown" | Done | In `AGENTS.md`, `company-recon` (Unknown section and confidence labels). |
| 7. Plain language, no emojis, tense rules | Done | In `AGENTS.md` and `bullet-writing.md`. |

## C. Original prompt: seed material and additions

| Item | Status | How |
| --- | --- | --- |
| Use the framework file | Changed | Shipped as `.claude/skills/resume-strategy/references/framework.md` (cleaned of personal details, with a header telling the agent to adapt examples to other professions). There is no `seed/` folder. |
| Keyword matching | Done | `keywords` in the job analysis; coverage report in the ATS check (in resume and supported, supported but missing, unsupported). |
| Gap analysis | Done | Required table in the strategy template. |
| Bullet writing rules | Done | `resume-writer/references/bullet-writing.md`. |
| Length rule (one page under about 10 years) | Done | In the strategy skill; page count checked by the ATS check. |
| Regional norms asked, as overridable defaults | Done | Strategy skill asks country, paper size, page limit. |
| Variants of one profile for different roles | Done | One profile, many applications; `--new` for a separate application on the same job. |

## D. Original prompt: structure, skills, scripts, testing

| Item | Status | How |
| --- | --- | --- |
| `AGENTS.md`, `README.md`, `.gitignore` | Done | `.gitignore` covers scratch, the local data-location file, and a safety net for data folders. |
| Seven skills | Done | `onboard-profile`, `company-recon`, `job-analysis`, `resume-strategy`, `resume-writer`, `latex-builder`, `ats-and-review`. |
| Commands `/onboard /new-job /build /review` | Done | Plus `/data`. Same files for OpenCode and Claude Code. |
| Entry skill | Added | `resume-workflow` holds the stage order and reuse checks so a weaker model has one place to start. |
| Review subagent with its own prompt | Changed | Not created. Two review passes (recruiter, skeptic) are written inside `ats-and-review`. Reason: subagent file formats differ between agents and add failure points for weaker models. |
| `profile/master.example.yaml` | Changed | `examples/example-profile.json`. Reason: standard-library Python has no YAML parser, and the script validates the JSON. The agent never edits the profile by hand; it uses `profile add/update`. |
| `profile/` and `jobs/` folders and `jobs/applications.csv` in the harness | Changed | Moved to the separate data folder, as required in section A. |
| Skills in `.opencode/skills` | Changed | Stored once in `.claude/skills`, which OpenCode also reads (per its docs). README gives the copy command if a version does not. |
| LaTeX: tectonic or latexmk, retry up to 3 times | Changed | Engine is `pdflatex` or `tectonic` (not latexmk). Retries are instruction-driven: the agent fixes the Markdown and rebuilds, maximum 3 attempts. |
| Overleaf-ready zip | Done | `overleaf-resume.vN.zip` with `main.tex`. Tested. |
| ATS: PDF text extraction, headings, order, page count | Done | Plus a check that each entry's dates and organisation stay next to its heading. A negative control proves it catches the old right-aligned layout. Tested. |
| ATS: evidence check | Done | Truth check runs inside `check`. |
| At most 2 review fix rounds | Done | Instruction-driven. |
| Scripts: contact injection, build, text check, tracker | Done | `build_resume.py`, `ats_check.py`, `rhlib.py`, `rh.py`; tracker is `applications.csv` and `INDEX.md`, regenerated after every change. Missing tools are reported, not hidden. |
| Test with fictional persona and job | Done | `selftest.py`: 94 checks (version 1.1), fictional data only. |
| README for a new user, each command in its own block | Done | |

## E. Not verified, and why

- **Not run inside OpenCode or Claude Code.** I have no access to either. The skill and command files follow the current OpenCode docs and Claude conventions, and their frontmatter is checked with a YAML parser. A first run on your machine is the real test.
- **Free-model behavior is untested.** The design reduces what the model must do (the script picks names, blocks duplicates, prints NEXT hints), but I cannot promise a specific model follows every instruction.
- **Only Linux with `pdflatex` and `pdftotext` was tested.** The no-TeX and no-`pdftotext` branches were tested by hiding the tools. macOS, Windows, MiKTeX, and `tectonic` were not tested.
- **Web research quality** depends on the agent having web access. Not testable here.
- **One template** (`ats-classic`). Other designs are not included.


## F. Version 1.1 refinements (requested after the first release)

| Request | Status | How |
| --- | --- | --- |
| Header order: name, then designation, then contact | Done | The builder fixes the order. `Headline:` is now required (build refuses without it). The ATS check confirms the order in the extracted PDF text. Tested. |
| Designation must be honest | Done, with a limit | Lint warns when the designation is neither a title in the profile nor qualified (Aspiring, Graduate, Seeking, ...). It cannot judge every possible wording. |
| No social media links (Instagram, WhatsApp, Twitter, ...) | Done | `contact set` refuses blocked domains and labels; lint fails on links, handles, and mentions in the text; maximum 3 links; `--remove-link`. Tested for Instagram, wa.me, x.com, a WhatsApp label, and a 4th link. |
| Contact line contents | Done | Email, phone, city and country, then links. Warnings for a phone without a country code and for a street-address location. |
| Photo: plain, clear face photo, not fashion style, not oversized, not passport style | Done, with one change | Optional, off by default, small print size (about 2.6 x 3.0 cm), standard printed by `photo set` and `photo guide`, size and shape warnings. **Changed:** the stated reason (checking that a person has no facial disability) was not built in. That is not a legitimate screening reason and may be unlawful in many places. The photo is a regional convention only, and the harness never judges appearance. |
| Photo by region | Done | Never offered or allowed for US, Canada, UK (override only with `--force`). Optional elsewhere. The ATS PDF never has a photo; a separate photo PDF is made for email or print. Tested with `pdfimages`. |
| More rules: personal data | Done | Date of birth, age, marital status, religion, gender, caste, parents' names, ID numbers, and a full address line are FAIL. Nationality only where the region allows it. Tested. |
| Regional profiles | Done | India, US and Canada, UK, EU, Gulf, other (`region list`). They set paper size and the photo and nationality rules, stored per application. These are summaries of common practice, not law; they can differ by employer. |
| DOCX export | Done | Standard-library writer with real headings, bullets, and hyperlinks; keeps non-Latin text. Checked with python-docx and LibreOffice, **not** with Microsoft Word. |
| Automatic file name | Done | `export` makes `FirstName_LastName_Resume.pdf` and `.docx` (and `_Photo.pdf`) in `exports/vN/`. |
| Writing lint | Done | Filler phrases, pronouns, repeated openers, bullet and summary length, tense for finished jobs, date style, bullets per entry. |
| Page fill | Done | The builder tries five layout presets and keeps the roomiest that fits the page target; reports fill; warns when a one-page resume is under 60% full or cannot fit. On the sample, fill rose from about 55% to 78%. Short content stays short; the tool does not pad. |
| Date order and gap check | Done | Newest first; gaps over 6 months and overlaps are flagged as information for the user. |
| The 5 inconsistencies found in the audit | Done | Workflow claim about clean-scratch, links in two places, person slug missing in `/build` and `/review`, README wording about `verify_harness.py`, and code-block commands now checked. |

Not done in 1.1, with reasons
- **A second template or a visual editor.** Out of scope for this round.
- **Interview with the ATS scanner that scored 80%.** I do not know which scanner it was or what it flagged, so no change was tuned to it.
- **Microsoft Word, macOS, Windows, MiKTeX, and tectonic testing.** Not available here.
