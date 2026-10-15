# Resume Harness

Tell your AI coding agent, in plain English, to make your resume for a job. It builds an ATS-safe resume from your own saved facts, checks it, and gives you a PDF and a Word file.

Version 1.2.0 · GPL-3.0 · open source · works with OpenCode and Claude Code

<!--
DEMO: add after recording (see docs/images/README.md). Remove these comment markers when the file exists.
![Making a resume by talking to the agent](docs/images/demo.gif)
-->

## What it does
- **You save your real facts once.** Education, jobs, projects, skills, contact details.
- **For each job, you paste the job description.** The agent researches the company, compares the job with your facts, and proposes a plan: what to show and in what order.
- **You approve the plan.** Then it writes the resume using only your facts, checks it, and builds the files.
- **You get**: an ATS-safe PDF, a Word file (DOCX), LaTeX, an Overleaf-ready zip, and a report that shows which job keywords your record supports and which it does not.

Why it exists: AI resume tools often invent details to fill gaps, and you repeat the same work for every application. Here, every claim must trace back to a fact you saved. Anything unsupported fails a check.

## Quick start
You need three things: Python, an AI coding agent, and (optionally) a PDF engine.

**1. Install Python 3.9 or newer.** Check what you have:

```bash
python --version
```

If that says "command not found", try `python3 --version` and use `python3` wherever this guide says `python`.

**2. Install an AI coding agent.**
- **OpenCode** is an open-source terminal agent. It can work with several free models. Install steps: https://opencode.ai/docs
- **Claude Code** is Anthropic's terminal agent. It needs a Claude plan or API access. Install steps: https://docs.claude.com
- Check each tool's website for current install steps and prices.
- Bigger models follow the steps more reliably. Very small free models can skip steps.

**3. Download this harness.** Use the green **Code** button on GitHub, then **Download ZIP** and unzip it. Or:

```bash
git clone https://github.com/rishb0/resume-harness.git
```

**4. Check your computer.** Open a terminal in the harness folder and run:

```bash
python scripts/rh.py doctor
```

It changes nothing. It tells you in plain words what is ready and what to install. PDF output is optional: without it you still get the Word file and the Overleaf zip.

**5. Open the folder in your agent.**

```bash
cd resume-harness
```

```bash
opencode
```

For Claude Code, run `claude` instead of `opencode`. In OpenCode, press `Tab` until the screen says **Build** (Plan mode cannot change files).

**6. Send this first message** and paste your job description where shown:

```text
Read AGENTS.md and follow it. Make my resume for this job: <paste the job description here>
```

That is all. The agent now asks you questions one at a time.

## How to use it
You never need to learn commands. Write what you want in plain English.

**The first time**, the agent asks for:
- your name and contact details (it keeps them out of the drafts and fills them in only when it builds the file)
- your education, jobs, projects, certifications, and skills, one topic at a time
- the company name and the country of the job
- whether you want a photo version (only offered where a photo is normal)
- the length you want

It saves every answer. **Next time it will not ask again.**

**Then it shows you a plan and waits.** Reply `approved`, or tell it what to change.

**For the next job**, just say:

```text
Make my resume for this other job: <paste the job description here>
```

**Other things you can say:**
- `Show me what you have saved.`
- `Update my profile: I finished a new course.`
- `Make my resume for the Data Analyst job at Example Company.` (it will ask for the job description)
- `Make a version with a photo.` (only where the country allows it)
- `Make it two pages.`
- `Back up my data.`
- `Delete all my data.` (it asks you to type a confirmation first)
- `Make a resume for my friend Priya.` (each person is saved separately)

If the agent does not seem to know about this harness, start your first message with `Read AGENTS.md and follow it.`

## What happens behind the scenes
1. **Your profile**: your facts are saved once and reused for every job.
2. **Company research**: a short, sourced brief from public pages. If the company is already saved and recent, it is reused.
3. **Job analysis**: must-haves, nice-to-haves, and the exact keywords. The same job text pasted twice is recognised and reused.
4. **Plan** (you approve): what to show, in what order, and which job requirements your record does not cover.
5. **Writing**: the resume text plus a map from every bullet to the fact behind it.
6. **Checks**: the truth check, the resume rules, and a writing check.
7. **Build**: PDF, Word file, LaTeX, Overleaf zip. The layout is fitted to your page target.
8. **ATS check and review**: the PDF text is read the way a job portal reads it, and the result is reviewed twice (once as a recruiter, once as a sceptical manager).
9. **Export**: files named `FirstName_LastName_Resume.pdf` and `.docx`, ready to upload.

**You stay in control:**
- Nothing is overwritten. Every save is a new version (`v1`, `v2`, ...).
- The agent asks before it reuses or replaces anything, and it stops for your approval of the plan.
- Deleting data needs a phrase that you type yourself.

## What it can and cannot do
**Can do** (the last column says how each item was verified):

| Area | What it does | Verified by |
| --- | --- | --- |
| Reuse | Saves a profile once and reuses it for every job | Automated test |
| Many people and jobs | Keeps people, companies, jobs, and applications without duplicates; two people can share one saved company and job | Automated test |
| No overwriting | Every save is a new version; edited profiles are archived | Automated test |
| Company research | Writes a short, sourced brief from public pages | Agent-dependent; needs web access in the agent |
| Job analysis | Extracts must-haves, nice-to-haves, and exact keywords | Agent-dependent; the saved format is tested |
| Plan | Gap analysis, evidence scoring, section order, then stops for your approval | Agent-dependent; the stop is an instruction |
| Truth check | Fails bullets with no evidence line, skills not in the profile, and numbers not in the cited evidence | Automated test |
| Resume rules | Header order, professional links only (max 3), no personal data that does not belong, region rules, optional photo | Automated test |
| Writing check | Filler words, pronouns, repeated openers, bullet length, tense, date order, employment gaps | Automated test |
| Build | Auto-fitted PDF, Word file, LaTeX, Overleaf zip, optional photo PDF | Automated test (Linux) |
| ATS check | Reads the PDF text the way a parser would; checks reading order, headings, keywords | Automated test (Linux) |
| Export and data | Employer-ready file names; backup; delete one person; full reset | Automated test |

**Cannot do:**
- **Guarantee interviews or an ATS pass.** There is no official ATS score. The checks cover parseability, relevance, and honesty of the content.
- **Prove your facts are true.** It catches claims your saved facts do not support. It cannot catch a false fact, or a reworded sentence that changes the meaning.
- **Apply to jobs, fill in job portals, or send anything.**
- **Write cover letters, optimise a LinkedIn profile, or prepare interviews.**
- **Run without a terminal and an AI coding agent.** There is no website or graphical interface.
- **Offer many designs.** There is one single-column ATS template; no multi-column or creative layouts.
- **Typeset non-Latin scripts in the PDF.** The Word file keeps them.
- **Read behind logins or collect LinkedIn data.** That is a rule, not a gap.
- **Work on Windows or macOS with a tested record.** Only Linux was tested.

**Partly or untested:**
- Importing an existing CV depends on what your agent can read.
- The Word file was checked with python-docx and LibreOffice, not Microsoft Word.
- Output quality depends on the model. Free models can lose track of long steps.

## Resume rules
The harness enforces these. You do not run anything; the agent applies them.
- **Header order**: name, then designation, then contact. The designation is your real title or the target role worded honestly.
- **Links**: professional only, at most 3 (LinkedIn, plus GitHub or a portfolio for technical work, and similar). Instagram, WhatsApp, Twitter or X, Facebook, and other social media are refused.
- **Personal data**: no date of birth, marital status, religion, gender, parents' names, ID numbers, or full address. Nationality only where the region allows it.
- **Regions**: India, US and Canada, UK, EU, Gulf, other. The job's country sets the paper size and the photo and nationality rules.
- **Photo**: optional and off by default; not offered for the US, Canada, or the UK. The ATS PDF never has a photo. If you want one, a separate photo PDF is made for email or print. The standard is a recent, plain, head-and-shoulders photo printed small. It is a regional convention only; the harness never judges appearance.
- **Writing check** (warnings): filler words, first-person pronouns, repeated opening verbs, long or short bullets, tense, date style and order, employment gaps.
- **Layout**: the builder tries layout presets and keeps the roomiest one that fits your page target. A one-page resume that fills under about 60% of the page is flagged as sparse.

Full text: `.claude/skills/resume-writer/references/resume-policy.md`.

## Your data
- All saved data lives in a separate folder on your computer, never inside the harness folder. Ask the agent `Where is my data saved?` or run `python scripts/rh.py where`.
- Default location: a folder named `resume-harness-data` in your home folder. To use another folder, run `python scripts/rh.py set-data-dir /path/to/folder` (it must be outside the harness folder). The environment variable `RESUME_HARNESS_DATA` also works.
- The folder has a readable `INDEX.md` that lists everything saved. Files are named by the tool, never by the agent.
- **Back up**: ask `Back up my data.` **Move to another computer**: copy the whole data folder, then run `set-data-dir` there.

## Privacy
- All saved data stays on your computer, in the data folder. The harness has no server and its scripts make no network calls.
- The AI model you use sees what you type and what the agent reads, such as profile facts and any contact details you enter. Resume drafts use placeholders for name and contact, and the build fills them in locally.
- Free model providers may log prompts. Read their terms before using real personal data, or use a local model.
- A saved photo is copied into your data folder and used only by the local build.

## Troubleshooting
- **First step for any problem**: run `python scripts/rh.py doctor`. It says what is missing.
- **The agent ignores this harness**: start your message with `Read AGENTS.md and follow it.`
- **The agent says it cannot find skills (OpenCode)**: copy them into OpenCode's own folder:

```bash
mkdir -p .opencode/skills && cp -r .claude/skills/* .opencode/skills/
```

- **No PDF**: install a PDF engine. On Debian or Ubuntu:

```bash
sudo apt install texlive-latex-base texlive-latex-extra poppler-utils
```

  On macOS with Homebrew run `brew install --cask mactex-no-gui` and `brew install poppler`. On Windows install MiKTeX and let it install missing packages. You can also upload the Overleaf zip to overleaf.com. The Word file works without any of this.
- **The agent invents a command, writes files by hand, or skips questions**: switch to a larger model and remind it: `Follow AGENTS.md exactly.`
- **`ERROR:` and `HINT:` lines** from the tool say what to do.
- **A bug**: open an issue and paste the output of `python scripts/rh.py doctor`. Use fictional data only.

## Start over or remove everything
- **Delete all saved data** (a fresh install): ask the agent `Delete all my data.` It will ask you to type `DELETE ALL DATA`.
- **Delete one person**: ask `Delete the data for <name>.`
- **Remove the program**: delete the harness folder. Your data folder is separate, so delete it too if you want everything gone.

## For developers
Everything below is for people changing the harness. Users can skip it.

**Run the full test suite** (uses a temporary folder and fictional data, never your real data):

```bash
python dev/selftest.py
```

**Check that skills, commands, and docs agree with the code, and that no personal data is in the repository:**

```bash
python dev/verify_harness.py
```

**Try the data tool without an AI agent**, using the fictional example files. Create the person:

```bash
python scripts/rh.py --data-dir /tmp/rh-demo person create --name "Alex Example"
```

Save contact details and the profile:

```bash
python scripts/rh.py --data-dir /tmp/rh-demo contact set alex-example --file examples/example-contact.json
```

```bash
python scripts/rh.py --data-dir /tmp/rh-demo profile add alex-example --file examples/example-profile.json
```

Save the company and the job posting:

```bash
python scripts/rh.py --data-dir /tmp/rh-demo company create --name "Northwind Example Corp"
```

```bash
python scripts/rh.py --data-dir /tmp/rh-demo job create northwind-example --title "Junior Web Application Security Engineer" --jd-file examples/example-job-description.md
```

Save the job analysis (use the job slug printed by the previous command):

```bash
python scripts/rh.py --data-dir /tmp/rh-demo job analysis-save northwind-example <job-slug> --file examples/example-analysis.json
```

Create the application (it prints the application id):

```bash
python scripts/rh.py --data-dir /tmp/rh-demo app create alex-example --company northwind-example --job <job-slug>
```

Save the resume text and its evidence map:

```bash
python scripts/rh.py --data-dir /tmp/rh-demo app save alex-example <app-id> resume-md --file examples/example-resume.md
```

```bash
python scripts/rh.py --data-dir /tmp/rh-demo app save alex-example <app-id> evidence-map --file examples/example-evidence-map.md
```

Build the files, run all checks, and export:

```bash
python scripts/rh.py --data-dir /tmp/rh-demo build alex-example <app-id>
```

```bash
python scripts/rh.py --data-dir /tmp/rh-demo check alex-example <app-id>
```

```bash
python scripts/rh.py --data-dir /tmp/rh-demo export alex-example <app-id>
```

Delete the demo data:

```bash
python scripts/rh.py --data-dir /tmp/rh-demo reset --confirm "DELETE ALL DATA"
```

**Optional slash-command shortcuts** exist for people who prefer them: `/onboard`, `/new-job`, `/build`, `/review`, `/data`. Plain English does the same.

**Folder map**
- `AGENTS.md` and `CLAUDE.md`: the rules the agent reads.
- `.claude/skills/`: the 8 skills (OpenCode reads this folder too). `.claude/commands/` and `.opencode/commands/`: the shortcuts.
- `scripts/`: the data tool (`rh.py`) and its modules.
- `config/`: settings, regions, and the profile schema. `templates/`: the LaTeX template. `examples/`: fictional data.
- `dev/`: tests and maintainer notes. `docs/images/`: screenshots for this README.

**Known limits**
- **Truth is bounded by the profile.** The checks catch claims the profile does not support. They cannot know whether the profile itself is true.
- **Regional rules are defaults, not law.** They summarise common practice and can differ by employer. The user decides.
- **Recon needs web access** in the agent. Without it, the user pastes the company's About and Careers text.
- **Overleaf is manual**: upload the zip yourself.
- **Not tested** on Windows, macOS, `tectonic`, or Microsoft Word.

## License
GPL-3.0. See the `LICENSE` file.
