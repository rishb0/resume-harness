# Install the Resume Harness

The Resume Harness is a folder of plain files. Your AI agent reads them and does the work. There is no server, no account of its own, and nothing to compile.

This page assumes you already have an AI coding agent. If you need to choose or install one, read [docs/AGENT-INSTALL.md](AGENT-INSTALL.md) first.

## Before you start

- An agent that can open a local folder, read and write files, and run commands.
- Python 3.9 or newer. Check it with `python --version`, or `python3 --version` if the first one is not found.
- A folder where the program should live. Any folder works. Keep it away from the folder where you keep your own documents.
- Internet access for the download. A cloud model also needs internet; a local model may not.

You do not need a GitHub account. The download is public. Git is optional: if the agent cannot clone the project, download `https://github.com/rishb0/resume-harness/archive/refs/heads/main.zip` and unpack it as `resume-harness`.

## Install the harness with any agent

1. Open the agent in the folder where the program should live, for example:

   ```bash
   cd ~/tools
   ```

   On Windows use `cd %USERPROFILE%\tools`. Create the folder first if it does not exist.

2. Paste this prompt and run it:

   ```text
   Set up the Resume Harness on this computer. Download https://github.com/rishb0/resume-harness into a new folder, read docs/INSTALL.md inside it, and follow it. Tell me when it is ready.
   ```

3. The agent downloads the folder into `resume-harness/` and works through this guide. It stops and asks before it installs anything on the computer.

4. Close the agent, then start it again inside the new folder. This lets it find the instructions and the skills.

5. Confirm that the computer is ready:

   ```bash
   python scripts/rh.py doctor
   ```

   Use `python3 scripts/rh.py doctor` if `python` is not found. `doctor` changes nothing; it only reports.

6. From now on, always start the agent inside the `resume-harness` folder. To begin, paste a job advert and say `Make my resume for this job:`.

> **Do not run `/init`.** It is for creating or updating `AGENTS.md`, and the harness already includes a complete one. If you run it anyway, review the changes and undo anything that removes the harness rules.

Next, use [docs/USAGE.md](USAGE.md) for every copy-paste prompt, or [docs/GETTING-STARTED.md](GETTING-STARTED.md) for the full first-resume walkthrough.

## OpenCode (recommended)

OpenCode is the agent this harness was built and tested on. It also provides access to **OpenCode Zen**, its built-in model provider with free models. Free-model availability and sign-in rules can change; see [https://opencode.ai/zen](https://opencode.ai/zen).

1. Install OpenCode from [https://opencode.ai](https://opencode.ai), or download the desktop app.
2. Open a terminal in the folder where the program should live:

   ```bash
   cd ~/tools
   ```

3. Start OpenCode there:

   ```bash
   opencode
   ```

4. Choose a model with `/connect` or the model picker.
5. Paste the setup prompt from the section above.
6. Close OpenCode, then start it again inside the new folder:

   ```bash
   cd resume-harness
   opencode
   ```

7. Current OpenCode versions read `AGENTS.md` and the skills in `.claude/skills/`. If your version does not find the skills, copy them across once:

   ```bash
   mkdir -p .opencode/skills && cp -r .claude/skills/* .opencode/skills/
   ```

   On Windows, use PowerShell for the same copy:

   ```powershell
   New-Item -ItemType Directory -Force .opencode\skills | Out-Null
   Copy-Item -Recurse -Force .claude\skills\* .opencode\skills\
   ```

8. Run the setup check:

   ```bash
   python scripts/rh.py doctor
   ```

## Claude Code (supported)

Claude Code reads `CLAUDE.md`, which points at `AGENTS.md`, and it finds the skills in `.claude/skills/`.

Claude Code needs a Claude subscription, a Claude Console account, or a supported cloud provider. It does not include the free-model option that OpenCode provides.

1. Install Claude Code from [https://code.claude.com/docs/en/quickstart](https://code.claude.com/docs/en/quickstart).
2. Open a terminal in the folder where the program should live:

   ```bash
   cd ~/tools
   ```

3. Start Claude Code there:

   ```bash
   claude
   ```

4. Sign in when prompted.
5. Paste the setup prompt from the section above.
6. Close Claude Code, then start it again inside the new folder:

   ```bash
   cd resume-harness
   claude
   ```

7. Run the setup check:

   ```bash
   python scripts/rh.py doctor
   ```

## Other agents

Other agents are compatible in principle, but not tested by this project. They can run the harness when they can open a local folder, read `AGENTS.md`, and run commands.

If the agent does not load the skills automatically, tell it:

```text
Read AGENTS.md, then read .claude/skills/resume-workflow/SKILL.md, and follow it.
```

See [docs/AGENT-INSTALL.md](AGENT-INSTALL.md) for official links and setup notes for Cursor, GitHub Copilot, Codex CLI, Gemini CLI, Cline, Roo Code, Aider, Continue, Kiro, Zed, and Devin Desktop.

## What doctor checks

- The Python version.
- A PDF engine: `pdflatex` (TeX Live or MiKTeX) or `tectonic`. Without one you get the Word file and the LaTeX, but no PDF.
- A PDF text tool: `pdftotext` (Poppler) or `pypdf`. Without one, the ATS check cannot read the PDF. The Word file on its own is not checked.
- Where the data folder is, and whether it is writable.
- Whether an OpenCode or Claude Code command is available on the PATH. If you use another agent, that note does not apply to you.

Ask the agent to run it and explain the result. Every check says what to install if something is missing.

## If `python` is not found

Some systems install Python under a different name: `python3` on most Linux and macOS systems, `py` on Windows. Use whichever one works for every command.

`doctor` prints the exact form for your computer, in a line that starts with `Run harness commands as:`. Use that form from then on.

## Where things go

| What | Where |
| --- | --- |
| The program, including the skills and the scripts | The `resume-harness` folder you just downloaded |
| Your profile, saved companies and jobs, and every resume you make | A separate data folder, outside the program |

The harness keeps the two apart on purpose, so you can update or re-download the program without touching your own data. To see the data folder path, ask the agent `Where is my data?`.

## Updating

Ask your agent `Is there a newer version?` The harness reads the project's public version file once a day, so it often already knows. If you say yes, the agent updates this folder: a git clone is updated with `git pull`, a downloaded copy with a fresh download. Your data folder is separate and is not touched.

The daily check can be switched off; just ask the agent.

## Removing it

Delete the `resume-harness` folder to remove the program. Your data folder is separate, so nothing about you is lost. To remove your data as well, ask the agent `Delete all my data.` It will ask you to type a confirmation phrase before it deletes anything.
