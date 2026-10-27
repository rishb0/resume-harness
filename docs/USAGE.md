# Copy-paste usage reference

This is the copy-paste reference guide for Resume Harness. Copy a block, replace anything in `<angle brackets>`, and send it to your agent.

You do not need to learn the internal commands. Use normal language. The agent runs the commands for you.

For the full walkthrough, see [docs/GETTING-STARTED.md](GETTING-STARTED.md). For installation, see [docs/INSTALL.md](INSTALL.md). For agent installation, see [docs/AGENT-INSTALL.md](AGENT-INSTALL.md).

## Contents

1. Before you start
2. Install an agent
3. Install the harness
4. Make your first resume
5. Stage-by-stage prompts
6. Common tasks
7. Data and privacy
8. Updates and removal
9. If something goes wrong
10. Which file to read

## 1. Before you start

You need:

- an AI coding agent that can open a folder, read and write files, and run commands;
- Python 3.9 or newer;
- a job advert;
- your work history, education, skills, and projects.

OpenCode is recommended. It is the agent this harness was built and tested on, and it provides free models through OpenCode Zen. Claude Code is also supported.

If you do not have an agent, use [docs/AGENT-INSTALL.md](AGENT-INSTALL.md).

## 2. Install an agent

### OpenCode (recommended)

Install OpenCode from [https://opencode.ai](https://opencode.ai), then check it:

```bash
opencode --version
```

Open a terminal in the folder where the harness should live:

```bash
cd ~/tools
```

Start OpenCode there:

```bash
opencode
```

Choose a model with `/connect` or the model picker.

### Claude Code (supported)

Install Claude Code from [https://code.claude.com/docs/en/quickstart](https://code.claude.com/docs/en/quickstart), then check it:

```bash
claude --version
```

Start it in the folder where the harness should live:

```bash
claude
```

Sign in when prompted.

### Other agents

See [docs/AGENT-INSTALL.md](AGENT-INSTALL.md) for official links and the extra skill-loading step.

## 3. Install the harness

Open the agent in the folder where the harness should live, then paste:

```text
Set up the Resume Harness on this computer. Download https://github.com/rishb0/resume-harness into a new folder, read docs/INSTALL.md inside it, and follow it. Tell me when it is ready.
```

When it finishes, close the agent and reopen it inside the new `resume-harness` folder.

Then check the setup:

```text
Run the setup check and explain what is missing.
```

You can also run the check yourself:

```bash
python scripts/rh.py doctor
```

Use `python3` or `py` if `python` is not found.

### Do not run `/init`

`/init` is for creating or updating `AGENTS.md`. The harness already contains a complete `AGENTS.md`.

**Skip `/init`.** If you run it anyway, review the changes and undo anything that removes the harness rules.

## 4. Make your first resume

Start the agent inside `resume-harness`, then paste:

```text
Read AGENTS.md and follow it. Make my resume for this job:
```

Then paste the complete job advert underneath:

```text
<paste the full job advert here>
```

The agent will:

1. create your profile;
2. open the private contact form;
3. research the company;
4. analyse the job;
5. ask the application choices;
6. show you a plan and wait for approval;
7. write, check, and build the resume;
8. export the finished files.

When the plan appears, reply:

```text
Approved.
```

Or ask for a change:

```text
Change the plan: <what you want changed>.
```

## 5. Stage-by-stage prompts

The normal workflow runs these stages automatically. Use these prompts only if you want to drive one stage yourself.

| Stage | Copy and paste |
| --- | --- |
| Onboard or update your profile | `Read AGENTS.md and follow it. Onboard me.` |
| Add an old CV to your profile | `Read AGENTS.md and follow it. Add the details from my old CV to my profile.` |
| Make a resume | `Read AGENTS.md and follow it. Make my resume for this job:` then the job advert |
| Analyse the job | `Analyse this job description and show me the must-haves, gaps, and exact keywords.` |
| See the plan | `Show me the plan before writing anything.` |
| Approve the plan | `Approved.` |
| Change the plan | `Change the plan: <change>.` |
| Write and build | `Write the resume and build the files.` |
| ATS and human review | `Run the ATS check and the recruiter review.` |
| Export the files | `Export the final files and tell me which file to send.` |
| Mark as applied | `Mark this application as applied.` |

If the agent loses its place, say:

```text
Where did we get to?
```

## 6. Common tasks

### Start a new job with your saved profile

Paste the same resume prompt and the new advert:

```text
Read AGENTS.md and follow it. Make my resume for this job:
```

The agent reuses your profile and asks only for the new job's choices.

### Add or correct profile information

Add a fact:

```text
Read AGENTS.md and follow it. Add this to my profile:

<your new fact>
```

Correct a fact:

```text
Read AGENTS.md and follow it. Correct this in my profile:

<what is wrong and what it should say>
```

### Change contact details

```text
Change my contact details.
```

The agent opens the private form. Type the new details there, not in the conversation.

### Choose the resume options

Use these when the agent asks, or when you want to change an answer:

| Choice | Copy and paste |
| --- | --- |
| Country | `The job is in <country>.` |
| One page | `Make it one page.` |
| Two pages | `Make it two pages.` |
| Photo version | `I want a photo version.` |
| No photo | `Do not use a photo.` |
| Cover letter | `Add a cover letter.` |
| No cover letter | `Do not add a cover letter.` |
| Longer CV | `Add a longer CV.` |
| Find how to apply | `Also find how to apply.` |
| Leave something out | `Leave out <thing>.` |
| Put something first | `Put <thing> first.` |

Photo rules depend on the country. The main ATS resume never contains a photo.

### Change one finished resume

```text
Change the summary on my <company> resume to:

<new text>
```

or:

```text
Change the skills section on my <company> resume to:

<new list>
```

The harness saves a new version and keeps the old one.

### See what is saved

```text
What do you have saved about me?
```

```text
What applications do I have?
```

```text
Show me my last application.
```

## 7. Data and privacy

Your data is in a separate folder on your computer. Ask:

```text
Where is my data?
```

Back it up:

```text
Back up my data.
```

Move it:

```text
Move my data to this folder: <path>
```

Delete everything:

```text
Delete all my data.
```

The agent will ask you to type a confirmation phrase before deleting anything.

Your contact details stay in a local form the agent is instructed not to read. Your work history is part of the conversation and may be sent by your agent to its model provider. Use a local model if everything must stay on your computer.

## 8. Updates and removal

Check for a newer version:

```text
Is there a newer version?
```

Install it:

```text
Update it.
```

Stop the daily check:

```text
Turn off update checks.
```

Remove the harness:

- Delete the `resume-harness` folder to remove the program.
- Your data folder is separate. To remove it too, say `Delete all my data.`

Remove an agent:

- Use the official uninstall instructions for that agent.
- Links are in [docs/AGENT-INSTALL.md](AGENT-INSTALL.md).

## 9. If something goes wrong

| Problem | Copy and paste |
| --- | --- |
| Setup is incomplete | `Run the setup check and explain what is missing.` |
| Agent ignores the rules | `Read AGENTS.md and follow it.` |
| Agent lost your place | `Where did we get to?` |
| Agent invented a fact | `That is not true. Remove it and check the rest.` |
| Resume is too long | `Make it one page.` |
| Wrong country rules | `The job is in <country>. Update the paper size and photo rules.` |
| No PDF | `Run the setup check and tell me how to install the PDF engine.` |
| No ATS check | `Run the setup check and tell me how to install the PDF text tool.` |
| Wrong file to send | `Show me the export folder and which file to send.` |
| Agent does not load the skills | `Read AGENTS.md, then read .claude/skills/resume-workflow/SKILL.md, and follow it.` |
| You found a bug | Open an issue and paste the setup output. Use made-up details only. |

## 10. Which file to read

| I want to... | Read |
| --- | --- |
| Understand the project in one page | `README.md` |
| Copy prompts for a task | This guide |
| Follow a full first resume | [docs/GETTING-STARTED.md](GETTING-STARTED.md) |
| Install or remove the harness | [docs/INSTALL.md](INSTALL.md) |
| Install or remove an agent | [docs/AGENT-INSTALL.md](AGENT-INSTALL.md) |
| Understand the design and safety rules | [docs/HOW-IT-WORKS.md](HOW-IT-WORKS.md) |
| See what changed | [CHANGELOG.md](../CHANGELOG.md) |
