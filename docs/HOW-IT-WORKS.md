# How the Resume Harness works

This page is for three readers at once: someone deciding whether to use it, someone who wants to know why it can be trusted, and someone who wants to change the code. Sections are marked so you can skip what you do not need.

For copy-paste prompts and day-to-day tasks, use [docs/USAGE.md](USAGE.md). This page explains how the machine behind them works.

## The idea

Writing a resume for one job is mostly judgement, and judgement is what a language model is good at. The problem is that a language model will also happily invent a certification, round a number up, or copy a keyword out of the advert that you cannot back up.

So the work is split:

- The **agent** makes the judgement calls: what to include, what to cut, how to word a bullet, which gap matters.
- The **scripts** hold the facts, the rules, and the files. They refuse to overwrite, refuse to invent, and check the finished output.
- The **rules** tell the agent what it may never do, and every command prints the next step so the agent cannot wander off.

The result is a resume that is tailored to one job, and every claim on it traces back to something the person actually told the harness.

## The four parts

### 1. The rules: `AGENTS.md`

Read automatically by OpenCode and by Claude Code when they open this folder. Other capable agents can read it when you point them to it. It holds twelve non-negotiable rules (the truth gate, the one-question-at-a-time rule, the data separation, the stop gates, and so on), the resume rules that code enforces, the stage order, and a command quick reference.

`CLAUDE.md` is a one-line pointer to it, because Claude Code looks for that name.

### 2. The skills: `.claude/skills/`

One folder per stage, each with a `SKILL.md` that the agent loads when the stage starts. A skill is instructions, not code: it describes what to collect, what to write, and when to stop and ask.

| Skill | Stage |
| --- | --- |
| `onboard-profile` | Collecting the person's history |
| `company-recon` | A short, sourced brief on the employer from public pages |
| `job-analysis` | Must-haves, nice-to-haves, and the employer's exact words |
| `resume-strategy` | The start menu, the gap analysis, and the section plan |
| `resume-writer` | The resume text, the evidence map, and the cover letter |
| `latex-builder` | Turning the Markdown into PDF, Word, LaTeX, and the zip |
| `ats-and-review` | Checking the finished file the way a screening system and a person would |
| `resume-workflow` | The entry point that runs the stages in order |

Skills are stored once, under `.claude/skills/`. OpenCode and Claude Code read that folder. Other agents may need a pointer or a copy. [docs/AGENT-INSTALL.md](AGENT-INSTALL.md) has the copy command and the fallback instruction.

`references/` inside a skill holds the detailed rules for that stage, and `examples/` holds a worked example of every input file.

### 3. The scripts: `scripts/`

Standard-library Python only, Python 3.9 or newer, no dependencies to install.

| Script | What it does |
| --- | --- |
| `scripts/rh.py` | The command line. Every command prints what to do next. |
| `scripts/rhlib.py` | Data: folders, versions, profiles, applications, settings, the index |
| `scripts/build_resume.py` | Markdown to LaTeX to PDF, with the layout fitted to the page target; also the cover letter and the longer CV |
| `scripts/docx_writer.py` | The Word file, written directly as OOXML |
| `scripts/lint_resume.py` | The writing checks: filler, bullet length, tense, dates, gaps |
| `scripts/ats_check.py` | Text extraction, reading order, headings, keyword coverage |
| `scripts/export_resume.py` | Copies the finished files out with employer-ready names |
| `scripts/doctor.py` | Checks Python, the PDF engine, the text tool, and the data folder |

### 4. The data folder

Everything about the user lives here, and nowhere else. It is created on first use and can be moved anywhere on the computer. The harness folder never holds saved personal data. Temporary drafts in `scratch/` are deleted after each save and by `clean-scratch`, so you can delete or re-download the program without losing anything.

```
data/
  resume-harness-data.json      which version wrote the data
  update-check.json             the last version check, and whether it is switched on
  people/<person-slug>/
    profile.json                the person's own history, with an id per entry
    contact.json                name, email, phone, location, links
    applications/<app-id>/
      app.json                  status, the saved start menu answers, build history
      strategy.v1.md
      resume.v1.md              the resume text
      evidence-map.v1.md        one line per bullet, pointing at profile ids
      truth-report.v1.md
      ats-report.v1.md
      review.v1.md
      cover-letter.v1.md
      cv.v1.md
      apply-routes.v1.md
      resume.v1.tex / .pdf / .docx
      overleaf-resume.v1.zip
      exports/v1/               the files to send
  companies/<company-slug>/
    company.json
    recon.v1.md
    jobs/<job-slug>/job.json, analysis.v1.md
  INDEX.md                      a readable index of everything saved
  applications.csv              one row per application
```

Every save is a new version. Nothing is overwritten, ever, and the file list marks the newest of each.

The private `contact-form.txt` appears in a person's folder only while the user is filling it in. `contact import` reads it, saves `contact.json`, and deletes it.

## The stages

1. **Person and profile.** Once per person. Every entry gets an id.
2. **Company recon.** A short brief from public pages, with a source for each fact.
3. **Job analysis.** Must-haves, nice-to-haves, and the exact keywords.
4. **Start menu, then strategy, then stop.** The country, photo, length, cover letter, how-to-apply, CV, and anything to leave out. The first six are saved with the application; the seventh is written into the strategy. The menu is asked once for each new application and read back on later builds. The build refuses until all six are saved. Then a plan, shown to the user for approval. Only the strategy is written before that approval; no resume text is written.
5. **Writing.** The resume text and the evidence map, then the truth check and the lint. The cover letter and the longer CV are written here if the menu asked for them.
6. **Build.** The PDF is fitted to the page target by trying layout presets from roomy to tight. Word, LaTeX, and the Overleaf zip are made from the same source.
7. **Check and review.** The finished PDF is extracted and checked as text, then reviewed once as a recruiter and once as a sceptic. Fixes are capped at two rounds.
8. **How to apply.** Optional. Public routes only, each with its source link.
9. **Export.** Copies the finished files out with names like `Alex_Example_Resume.pdf`, into a new folder each time.
10. **Finish.** Mark the application as applied, then clean the scratch folder.

## The safety rules and why they exist

**The truth gate.** Every resume bullet must point at a profile id in the evidence map. `scripts/rh.py truth` fails any bullet with no evidence line, any skill claimed that the profile does not hold, and any number that is not in the evidence. The agent may not add a keyword from the job advert that the profile does not support, and it may not invent a number to fill a gap. A missing number is allowed; a wrong one is not. The cover letter and longer CV get the policy, link, personal-data and writing checks, but the evidence map is enforced only for the resume; their prose must still be traceable to the profile.

**Contact details never enter a draft, and in the normal flow they never enter the conversation.** `rh.py contact form` opens a plain-text file in the data folder. The user types their name, email, phone, city and links there; `rh.py contact import` validates it, saves `contact.json`, and deletes the form. The agent is told never to read that file. `contact show` reports which fields are saved, `export` lists file types instead of names, and the form's errors never echo a value. The older `contact set` maintenance command puts values on the command line; use the form. The build fills `{{NAME}}` and `{{CONTACT}}` locally. If a person was saved under a real name before 1.3, `rh.py person rename <slug> --label "Me"` moves the folder and applications to a private id. Local history files can keep the earlier label; they are not read by the agent, and the data folder should still be treated as private.

This is a policy plus output masking, not a sandbox. The agent runs as the user and could read the file if it disobeyed; the real guarantee is a model the user trusts, or a local one. Work history is different: the agent needs it to write the resume.

**The data folder is separate and locked.** Only `rh.py` writes there. The agent may not create, rename, or delete a file in it by hand, and may not choose file names. Versioning, the index, and the "never overwrite" promise all depend on that.

**Public information only.** Company research reads public pages. No logins, no scraping LinkedIn, and nothing about individual employees. Where something is unknown it stays unknown.

**Stop gates.** After the strategy, the run stops until the user approves. Deleting data needs a confirmation phrase that the user types out in full.

**Loop limits.** Three rounds of truth fixes, three build attempts, two review rounds, and then it stops and reports what is left. This is what stops an agent from grinding on a problem forever.

**Social media never appears.** The contact form and `contact set` refuse a link on the block list, by domain and by label. Professional links only, at most three.

**Region rules are data, not opinion.** `config/regions.json` says, per region, the paper size, whether a photo is ever allowed, and whether a nationality line may appear. The photo is off by default, is never offered for the United States, Canada, or the United Kingdom, and never appears in the file that goes to a screening system.

## What code checks, and what the agent checks

This line matters when you are deciding how much to trust the output.

| Checked by code, fails the run | Checked by the agent, with its judgement |
| --- | --- |
| A bullet with no evidence line | Whether the evidence is strong enough to keep |
| A skill or a number that is not in the evidence | Whether a real gap is worth mentioning in the letter |
| Header order, blocked links, personal data terms | The best order of sections for this candidate type |
| Bullet length, filler words, tense, date order, gaps, likely typos, mixed spelling | How to word a bullet so it reads well |
| Page count, page fill, the margin floor, an entry split across a page break | Which bullet to cut when the page is full |
| Keyword coverage in the extracted PDF text | Which missing keyword is a real gap and which is noise |
| The data folder staying outside the harness folder | Company research quality |

The left column is not all-or-nothing. FAIL lines are broken rules and stop the run; WARN lines are things to look at and to answer in the text. Spelling is always a WARN: a typo list can be wrong about a name or a product, so the harness asks rather than refuses.

Contact values are not printed by commands: `contact show` names the fields that are saved, `export` lists file types, and `dev/selftest.py` asserts that no value appears in either. The instruction never to read the contact files is policy, not code; the boundary is stated above.

The honest summary: the mechanical rules are enforced and tested; the writing quality depends on the model you use. A more capable model writes better resumes. The code stops the resume from asserting a skill or number that the profile does not hold; the cover letter and longer CV still need the writer's care.

## Working on it

The two maintainer scripts are the gate. Run both from the harness folder:

```bash
python dev/verify_harness.py
```

```bash
python dev/selftest.py
```

- `dev/verify_harness.py` checks the repository itself: every path and skill named in the documents exists, every command written in the documents parses with the real parser, the version agrees across `VERSION`, `README.md`, and `CHANGELOG.md`, the templates carry every marker the builder needs, the settings are complete, and no real email address or phone number has leaked into the repository.
- `dev/selftest.py` runs the whole harness end to end on made-up data in a temporary folder: create a person, build a profile, save a job, run every stage, build the PDF, check it, export it, back it up, and reset it. It skips the PDF checks when no TeX engine is installed.

`dev/COMPLIANCE.md` explains what each check is for and how much of the behaviour is enforced by code rather than by instruction.

### Commands while you are testing

Run these in the harness folder. The first one needs no data at all.

```bash
python scripts/rh.py doctor
python scripts/rh.py status
python scripts/rh.py brief
python scripts/rh.py brief <person-slug> <app-id>
python scripts/rh.py app files <person-slug> <app-id>
```

`doctor` checks the machine. `status` shows the data folder and the counts. `brief` prints every application and how far each one has got. If the conversation has lost its context, run this first: it reads the saved state instead of relying on memory. A check counts as done only when its latest report has 0 FAIL and is newer than the files it describes. A build counts only while the resume, contact details, photo, cover letter, CV and the build-related start-menu answers it used have not changed, and its output files are present; a build made without a TeX engine also stops counting once an engine is installed, and a build with compile skipped on purpose still counts. Export and review stop counting after a newer build, and a review also needs a current passing ATS check. `brief <person-slug> <app-id>` prints one application in full: the saved start menu answers, every step, and the next command. `app files` lists the saved files of one application and marks the newest of each.

To test a change without touching real data, point the tool at a throwaway folder:

```bash
python scripts/rh.py --data-dir /tmp/rh-test init
```

Anything else: `python scripts/rh.py --help`.

### Adding a skill

Create `.claude/skills/<name>/SKILL.md`. The frontmatter `name` must match the folder name, and the `description` must say when to use it, because that is what the agent reads when deciding whether to load it. Then name the skill in a stage of `AGENTS.md` and in the relevant workflow step, and run both maintainer scripts: the verifier fails if a skill is named in a document but does not exist, or the other way round.

### Changing a rule or a setting

- Behaviour the agent must follow: `AGENTS.md`, and the skill that owns that stage.
- Numbers, lists, and switches: `config/settings.json`. Layout presets (side and top margins may never go below 0.65in and 0.6in), the lint rules including `lint.spell_allow` for a word the spelling check should leave alone, the banned phrases, the link block list, the region defaults, the status list. This is a program file: a download update replaces it, but keeps the words you added to `lint.spell_allow`.
- Profile sections and their id prefixes: `config/profile_schema.json`. The prefixes must stay unique.
- A new region or a change to a region's paper, photo, or nationality rule: `config/regions.json`. Adding a key there is enough; the commands read it.

### Commands stay in sync

`.claude/commands/*.md` and `.opencode/commands/*.md` must stay byte-identical, and the verifier fails if they drift. Users never need them; they exist for people who prefer slash commands.

### Versioning

`VERSION`, the version line in `README.md`, and a matching `## x.y.z` heading in `CHANGELOG.md` must agree, or the verifier fails. A release is a commit that moves all three together.

## Tests and continuous integration

`.github/workflows/ci.yml` runs both maintainer scripts on every push and pull request, on Python 3.9 and 3.13, with the PDF tools installed so that the PDF checks really run. Bytecode writing is turned off for the run, and the last step fails if the run leaves a tracked or untracked file, a `__pycache__` folder or `.pyc` file, a scratch file, a data folder, or a local `config/data_location.txt` behind.

## What it deliberately does not do

No graphical interface, no server, no cloud storage, and no accounts of its own. Your agent may need an account or model access. No npm or build step: it is Python files, Markdown, and one LaTeX template.

The only request the harness makes on its own is one version check a day. It reads one public file on the project's default branch, caches the answer in the data folder for a day, and sends nothing about the user, the machine, or the data folder. A failed attempt is remembered for an hour, so an offline computer does not retry on every command. Offline, it fails quietly. `python scripts/rh.py update --off` stops it for good.

No automatic updates. A new version is offered, never applied behind your back: `python scripts/rh.py update` only reports, and `python scripts/rh.py update --apply` replaces program files, run by an agent that has asked the user first. A git clone is updated with `git pull`, anything else with a fresh download. User data is never in this folder, so it is never part of an update.

And it will not promise an interview, an ATS score, or a perfect match: it makes an honest, tailored document and tells you what was left out.
