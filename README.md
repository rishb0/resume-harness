# Resume Harness

**A job-specific resume, built by talking to your AI agent.**

Paste a job advert. The agent asks about your background, writes only from facts you confirm, checks the result, and gives you a PDF and a Word file.

**Works with any agent that can open a folder, read files, and run commands.** [OpenCode](https://opencode.ai) is recommended and is the agent this project was built and tested on. [Claude Code](https://code.claude.com/) is also supported.

> **Why OpenCode?** It provides access to **OpenCode Zen**, its built-in model provider with free models. That makes it the simplest no-cost way to start. Free-model availability and sign-in rules can change; check [OpenCode Zen](https://opencode.ai/zen).

Version 1.3.0 · GPL-3.0 · Python 3.9+

## What it is

Resume Harness is a local toolkit, not a website. It is a folder of instructions and small Python programs. Your agent reads the instructions and runs the programs on your computer.

Your agent makes the writing decisions. The programs save your facts, keep every version, check the resume, and build the files.

The harness itself needs no account, server, or subscription. Your agent may need an account or model access.

## Who it is for

For job seekers who want a tailored resume and are comfortable using a coding agent. You do not need to edit code. You do need an agent that can work in a folder and run commands.

A chat-only assistant cannot run the local scripts.

## What you need

| Need | Required? | Why it matters |
| --- | --- | --- |
| An AI coding agent | Yes | It reads the instructions, asks questions, and runs the scripts |
| Python 3.9 or newer | Yes | Runs the harness programs |
| Internet access | For setup and cloud models | Downloads the harness and reaches your model provider |
| A PDF engine | For PDF output | Converts the resume layout into a PDF. Examples: TeX Live, MiKTeX, Tectonic |
| A PDF text tool | For the ATS check | Reads the finished PDF. Examples: `pdftotext` from Poppler, or Python `pypdf` |

Without a PDF engine you still get the Word file and the LaTeX source, but no PDF. Without a PDF text tool, the ATS check cannot read the PDF.

Git is optional. A GitHub account is not required.

## Quick start

### 1. Install an agent

Use [OpenCode](https://opencode.ai) (recommended) or [Claude Code](https://code.claude.com/).

If you already have one, skip this step.

For every other agent, see [docs/AGENT-INSTALL.md](docs/AGENT-INSTALL.md). The harness does not install the agent for you.

### 2. Open the agent in an empty folder

Create a folder such as `~/tools`, then start the agent from inside it. The agent must be able to read and write files and run commands there.

### 3. Paste the setup prompt

```text
Set up the Resume Harness on this computer. Download https://github.com/rishb0/resume-harness into a new folder, read docs/INSTALL.md inside it, and follow it. Tell me when it is ready.
```

### 4. Reopen inside the new folder

Close the agent. Start it again from inside `resume-harness`.

This lets it find `AGENTS.md` and the workflow instructions.

> **Do not run `/init`.** It is for creating or updating `AGENTS.md`, and the harness already includes a complete one. If you run it anyway, review the changes and undo anything that removes the harness rules.

### 5. Check the setup

Ask:

```text
Run the setup check and explain what is missing.
```

You can also run the check yourself:

```bash
python scripts/rh.py doctor
```

Use `python3` or `py` if `python` is not found. `doctor` changes nothing; it only reports.

That is the installation. The agent can run every command for you.

## How to use it

Start the agent inside `resume-harness` and talk normally. For a new resume, say:

```text
Read AGENTS.md and follow it. Make my resume for this job:
```

Then paste the job advert underneath. A bare job advert is also treated as a resume request.

| Goal | What to say |
| --- | --- |
| Start a resume | `Read AGENTS.md and follow it. Make my resume for this job:` then the advert |
| Start your profile only | `Read AGENTS.md and follow it. Onboard me.` |
| Start the next job | The same resume prompt, with the new advert |
| Continue where you stopped | `Where did we get to?` |
| Add or correct profile facts | `Add this to my profile:` or `Correct this in my profile:` then the details |
| Change contact details | `Change my contact details.` |
| Change one resume | `Change the summary on my <company> resume to:` then the new text |
| Mark it applied | `Mark this application as applied.` |
| See where your data is | `Where is my data?` |
| Back up your data | `Back up my data.` |
| Move your data | `Move my data to this folder: <path>` |
| Delete everything | `Delete all my data.` |
| Check for an update | `Is there a newer version?` |

For every task and every copy-paste prompt, see [docs/USAGE.md](docs/USAGE.md).

## What happens

1. **Profile.** If you are new, the agent asks about your work history, education, skills, and projects, one question at a time.
2. **Research.** It reads the job advert and looks up the company from public pages. It never logs in anywhere.
3. **Choices.** It asks a short setup menu: country, photo, page length, cover letter, how to apply, longer CV, and anything to leave out.
4. **Plan.** It shows the sections and order it intends to use, saves the plan, and **stops for your approval**. No resume text is written before you approve.
5. **Writing.** It writes the resume and an evidence map showing where each bullet came from. Then it runs truth, policy, and writing checks.
6. **Build.** It creates the PDF, Word file, LaTeX source, and optional cover letter, longer CV, or photo version.
7. **Check and export.** It checks the PDF the way an applicant tracking system would, reviews it once more, and puts the finished files in one folder.

## What you get

The files are named after you:

| File | Use it for |
| --- | --- |
| `YourName_Resume.pdf` | Job websites and application forms. This is the main file to send. |
| `YourName_Resume.docx` | The same resume in Word, for places that ask for Word. |
| `YourName_Cover-Letter.pdf` | Only if you asked for a cover letter. |
| `YourName_CV.pdf` | Only if you asked for a longer CV. |
| `YourName_Resume_Photo.pdf` | Only if you asked for a photo version, for countries where that is normal. |

The folder also contains a `.tex` file and an Overleaf zip. LaTeX is the typesetting format used for the PDF layout. Overleaf is a browser-based LaTeX editor. Use these only if you want to change the layout by hand.

## Accuracy and privacy

**Every resume bullet is checked.** Each bullet must point to a fact in your profile. The truth check rejects unsupported bullets and numbers. If a fact is missing, the agent asks you or leaves it out. Cover letters and longer CVs get the policy and writing checks; the strict evidence map applies to the resume.

**Contact details stay local.** You type your name, phone, email, and links into a private form on your computer. The agent runs the command that opens the form, is instructed not to read the saved file, and the PDF is built locally. This is a strong policy, not a technical lock; use an agent and model you trust.

**Your work history is part of the conversation.** The harness has no server and uploads nothing, but your agent may send the conversation to its model provider. If you need everything to stay on your computer, use a local model.

**It will not:**

- invent experience, dates, degrees, certifications, or numbers;
- add a photo, date of birth, marital status, religion, or social media unless the country rules allow it;
- apply to jobs or fill in application forms;
- promise an ATS score or an interview.

ATS means **applicant tracking system**: software some employers use to read and filter applications.

## Your data

Everything about you is saved in one folder on your computer, separate from the program. Ask `Where is my data?` and the agent will print the path.

You can back up, move, or delete that folder at any time. The agent is instructed not to edit it by hand; the harness manages the versions.

Details: [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md).

## Updates

The harness checks for a new version once a day. It reads one public version file and sends nothing about you or your computer. You can switch the check off.

To update, ask `Is there a newer version?` The agent updates the program files only after you say yes. Your data folder is never touched.

To remove the program, delete the `resume-harness` folder. To remove your saved data too, ask `Delete all my data.` The harness asks you to type a confirmation phrase first.

## If something goes wrong

| Problem | What to do |
| --- | --- |
| Something is missing | Ask `Run the setup check and explain what is missing.` The command is `python scripts/rh.py doctor` |
| The agent ignores the rules | Start your message with `Read AGENTS.md and follow it.` |
| The agent does not load the skills | Say `Read AGENTS.md, then read .claude/skills/resume-workflow/SKILL.md, and follow it.` |
| The agent lost your place | Ask `Where did we get to?` |
| The agent guesses | Stop it: `That is not true. Remove it and check the rest.` If it repeats, use a more capable model |
| You found a bug | Open an issue and paste the setup output. Use made-up details only, never your real ones |

## Which file do I need?

| I want to... | Read |
| --- | --- |
| Choose or install an agent | [docs/AGENT-INSTALL.md](docs/AGENT-INSTALL.md) |
| Install, update, or remove the harness | [docs/INSTALL.md](docs/INSTALL.md) |
| Copy prompts for a specific task | [docs/USAGE.md](docs/USAGE.md) |
| Follow a full first resume | [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) |
| Understand the design and safety rules | [docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md) |
| See what changed | [CHANGELOG.md](CHANGELOG.md) |

## Licence

GPL-3.0. See `LICENSE`.
