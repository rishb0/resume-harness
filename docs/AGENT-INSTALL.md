# Install an agent for Resume Harness

Resume Harness is not an agent. It is a set of instructions and Python scripts that runs inside one.

This page helps you choose, install, and start an agent. After that, [docs/INSTALL.md](INSTALL.md) installs the harness itself.

## What a capable agent must do

An agent can run Resume Harness if it can:

- open a local folder;
- read and write files in that folder;
- run terminal commands;
- connect to a model.

A chat-only assistant cannot run the harness. It needs access to the folder and the local Python programs.

## Recommended: OpenCode

**Official site:** [https://opencode.ai](https://opencode.ai)  
**Documentation:** [https://opencode.ai/docs](https://opencode.ai/docs)  
**Models:** [https://opencode.ai/zen](https://opencode.ai/zen)

OpenCode is the recommended choice for two reasons:

1. This harness was built and tested on OpenCode.
2. OpenCode provides access to **OpenCode Zen**, its built-in model provider with free models. That lets you start without a paid API subscription. Free-model availability and sign-in rules can change.

### Install and start OpenCode

1. Install OpenCode from the official site, or download the desktop app. Follow the official instructions for your operating system.
2. Open a terminal and check that the command works:

   ```text
   opencode --version
   ```

3. Move to the folder where the harness should live:

   ```text
   cd ~/tools
   ```

   On Windows, use `cd %USERPROFILE%\tools`. Create the folder first if it does not exist.

4. Start OpenCode inside that folder:

   ```text
   opencode
   ```

5. Choose a model. Use `/connect` or the model picker, then choose an OpenCode Zen model or connect another provider.

6. Follow [docs/INSTALL.md](INSTALL.md) to install the harness.

OpenCode reads `AGENTS.md` directly. Claude Code reads `CLAUDE.md`, which points to it. Both read the skills in `.claude/skills/`. If your OpenCode version does not find the skills, copy them once:

```bash
mkdir -p .opencode/skills && cp -r .claude/skills/* .opencode/skills/
```

On Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force .opencode\skills | Out-Null
Copy-Item -Recurse -Force .claude\skills\* .opencode\skills\
```

## Supported: Claude Code

**Official quickstart:** [https://code.claude.com/docs/en/quickstart](https://code.claude.com/docs/en/quickstart)

Claude Code is supported. It reads `CLAUDE.md`, which points at `AGENTS.md`, and it reads the skills in `.claude/skills/`.

Claude Code needs a Claude subscription, a Claude Console account, or a supported cloud provider. It does not include the free-model option that OpenCode provides.

### Install and start Claude Code

1. Install Claude Code from the official quickstart.
2. Check that the command works:

   ```text
   claude --version
   ```

3. Move to the folder where the harness should live:

   ```text
   cd ~/tools
   ```

4. Start Claude Code inside that folder:

   ```text
   claude
   ```

5. Sign in when prompted.

6. Follow [docs/INSTALL.md](INSTALL.md) to install the harness.

## Other agents

These agents are **compatible in principle, but not tested by this project**. They need the same things: a folder, file access, terminal access, and a model.

| Agent | Official page | How to start in the folder |
| --- | --- | --- |
| Cursor | [https://cursor.com](https://cursor.com) | Open Folder, then open Agent or Chat |
| GitHub Copilot | [https://docs.github.com/en/copilot](https://docs.github.com/en/copilot) | Open the folder in VS Code, then use Copilot Chat in agent mode |
| OpenAI Codex CLI | [https://github.com/openai/codex](https://github.com/openai/codex) | Run `codex` in the folder |
| Gemini CLI | [https://github.com/google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) | Run `gemini` in the folder |
| Cline | [https://cline.bot](https://cline.bot) | Open the folder, then open the Cline panel |
| Roo Code | [https://roocode.com](https://roocode.com) | Open the folder, then open the Roo Code panel |
| Aider | [https://aider.chat](https://aider.chat) | Run `aider` in the folder |
| Continue | [https://continue.dev](https://continue.dev) | Open the folder, then open the Continue panel |
| Kiro | [https://kiro.dev](https://kiro.dev) | Open the folder, then open the agent panel |
| Zed | [https://zed.dev](https://zed.dev) | Open the folder, then open the Agent panel |
| Devin Desktop (formerly Windsurf) | [https://devin.ai](https://devin.ai) | Open the folder, then open the agent panel |

Windsurf was renamed Devin Desktop in 2026. The old `wind.surf` address is not the current official page.

If an agent is not in this table, it can still work when it can open a folder, read `AGENTS.md`, and run commands.

## Install the harness with any of them

1. Open the agent inside a new, empty folder.
2. Paste this prompt:

   ```text
   Set up the Resume Harness on this computer. Download https://github.com/rishb0/resume-harness into a new folder, read docs/INSTALL.md inside it, and follow it. Tell me when it is ready.
   ```

3. Reopen the agent inside the new `resume-harness` folder.
4. Run the setup check:

   ```bash
   python scripts/rh.py doctor
   ```

Use `python3` or `py` if `python` is not found.

> **Do not run `/init`.** It is for creating or updating `AGENTS.md`, and the harness already includes a complete one. If you run it anyway, review the changes and undo anything that removes the harness rules.

Next, use [docs/USAGE.md](USAGE.md) for the copy-paste prompts.

## If the agent does not load the instructions

Current OpenCode versions and Claude Code load the rules and skills automatically. Other agents may not.

If the agent ignores the workflow, tell it:

```text
Read AGENTS.md, then read .claude/skills/resume-workflow/SKILL.md, and follow it.
```

If the agent supports its own skills folder, copy `.claude/skills/` into that folder. There is no single skills-folder name that works for every agent, so the safe fallback is the sentence above.

For OpenCode, the copy command is in the OpenCode section of this page.

## Managing and removing an agent

- **Update:** use the official installer or package manager for your agent. The links above are the starting point.
- **Remove:** follow the vendor's uninstall instructions. For a desktop app, use the operating system's uninstaller; for a CLI, use the package manager that installed it; for a VS Code extension, remove the extension from the editor.
- Removing the agent does not remove the harness or your resume data. To remove the harness, see [docs/INSTALL.md](INSTALL.md). To remove your data too, ask the agent `Delete all my data.`

Vendors change installers and menu names. Use the official page rather than copying an old command from a blog post.

## Safety, accounts, and cost

- An agent with file and terminal access can read files and run commands. Install it from the official site, and use a model you trust.
- The harness is free and open source. The agent or model may cost money.
- OpenCode provides free models through OpenCode Zen; availability can change.
- Claude Code needs an account or subscription.
- No agent can promise an ATS score or an interview.

## Official links change

The links above are starting points. Vendors change installers, commands, menus, and product names. Follow the official page for your operating system, and use this page only to choose the agent and understand the extra skill step.
