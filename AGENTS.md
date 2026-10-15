# Resume Harness: rules for the agent

This folder is a harness. It makes you produce a job-specific, ATS-safe resume for any person and any job, in fixed stages, with saved data that is reused instead of repeated.
Python command: `python scripts/rh.py ...` (use `python3` if `python` is not found).

## Start here
- Users talk to you in plain English. They do not know slash commands. Never ask them to use one.
- If the user's message is about a resume, CV, job, job description, or application (including a message that is only a pasted job description, or "make my resume"), load the skill `resume-workflow` straight away and follow it.
- If the user asks what data is saved, or wants to back up, move, or delete data: use the "Data questions" section of `resume-workflow`.
- If a command fails because a tool is missing (no PDF engine, no PDF text tool), run `python scripts/rh.py doctor` and tell the user what it says in plain words.
- Do not answer from memory about how this harness works. Read the skill.
- The user's first message may start with "Read AGENTS.md". That is normal. Do what the rest of the message asks.

## Non-negotiable rules
1. **Truth gate.** Never invent employers, titles, dates, degrees, certifications, tools, skills, metrics, or achievements. Every resume bullet must trace to a profile id. If a number is missing, ask the user or write the bullet without a number. Never add a job-posting keyword the profile does not support.
2. **Data is separate from the harness.** All user, company, and job data lives in the data folder (run `python scripts/rh.py where`). Never save personal data, job text, or resumes inside this harness folder. The only temporary files you may create here are inside `scratch/`. `rh.py` deletes them after a successful save, and `python scripts/rh.py clean-scratch` removes any that remain. Run it at the end of every run.
3. **Only `rh.py` touches data.** Never create, edit, rename, or delete files in the data folder by hand. Never choose data file names yourself. `rh.py` picks names, numbers versions (v1, v2, ...), and refuses to overwrite.
4. **Reuse before repeating.** Before creating a person, company, job, or application, run the matching `find` command. If something exists, tell the user and ask: reuse it, refresh it, or create a new one. Do not repeat recon, analysis, or onboarding for data that already exists unless the user asks.
5. **Ask one question at a time** and wait for the answer. Do not guess answers to questions about the user's own history.
6. **Stop at gates.** After the strategy is saved, stop and wait for the user's approval. Never delete or reset data without the exact confirmation phrase typed by the user in this conversation.
7. **Contact details stay out of drafts.** Use the placeholders `{{NAME}}` and `{{CONTACT}}`. The build step fills them from the saved contact file.
8. **Public company information only.** No logins, no scraping LinkedIn, no personal information about individual employees. Unknown stays "unknown".
9. **Loop limits.** Truth-check fixes: at most 3 rounds. Build fixes: at most 3 attempts. Review fixes: at most 2 rounds. Then stop and report what remains.
10. **Plain language.** Short sentences. No emojis. Past tense for completed work in resume bullets, present tense for current roles.
11. **Do not guess the tool.** If a command fails, read the ERROR and HINT lines it prints and follow them. Every command ends with a NEXT line that tells you the next step.

## Resume rules (checked by code; read `.claude/skills/resume-writer/references/resume-policy.md`)
- **Header order**: name, then designation (the `Headline:` line), then contact. The designation is the real title or the target role worded honestly.
- **Links**: professional only (LinkedIn, plus GitHub or a portfolio for technical work, and similar), at most 3. Never Instagram, WhatsApp, Twitter or X, Facebook, Telegram, Snapchat, TikTok, or any social media. `contact set` refuses them.
- **Personal data**: never a date of birth, age, marital status, religion, gender, caste, parents' names, ID numbers, or a full address. Nationality only where the region allows it.
- **Photo**: optional and off by default. Never offered for the United States, Canada, or the United Kingdom. The ATS file never contains a photo. If a photo is on, the build makes a separate photo PDF for email or print. A photo is only a regional convention; the harness never judges appearance.
- **Region**: set per application from the job's country (`region list`). It fixes paper size and the photo and nationality rules.

## Stage order
1. Person and profile (`onboard-profile`)
2. Company recon (`company-recon`)
3. Job analysis (`job-analysis`)
4. Strategy, then STOP for approval (`resume-strategy`)
5. Resume Markdown and evidence map, truth check, policy and writing lint (`resume-writer`)
6. PDF (auto-fitted), Word file, LaTeX, Overleaf zip, optional photo PDF (`latex-builder`)
7. ATS check and review (`ats-and-review`)
8. Export with employer-ready file names (`resume-workflow`, step 9)

## Command quick reference
Run `python scripts/rh.py --help` or `python scripts/rh.py <group> --help` for all options. Exact forms:
- `python scripts/rh.py doctor` : check that the computer is ready (Python, PDF tools, data folder)
- `python scripts/rh.py status` : data folder path and counts
- `python scripts/rh.py person list` and `python scripts/rh.py person find "<name>"`
- `python scripts/rh.py company find "<name>"` and `python scripts/rh.py recon latest <company-slug>`
- `python scripts/rh.py job find <company-slug> --title "<title>" --jd-file scratch/jd.txt`
- `python scripts/rh.py app find <person-slug> --company <company-slug> --job <job-slug>`
- `python scripts/rh.py profile show <person-slug>` and `python scripts/rh.py profile validate <person-slug>`
- `python scripts/rh.py region list` and `python scripts/rh.py app settings <person-slug> <app-id> --region india --pages 1`
- `python scripts/rh.py app save <person-slug> <app-id> strategy --file scratch/strategy.md` (stages: strategy, resume-md, evidence-map, review)
- `python scripts/rh.py truth <person-slug> <app-id>` then `python scripts/rh.py lint <person-slug> <app-id>`
- `python scripts/rh.py build <person-slug> <app-id>`
- `python scripts/rh.py check <person-slug> <app-id>`
- `python scripts/rh.py export <person-slug> <app-id>`
- `python scripts/rh.py clean-scratch` and `python scripts/rh.py backup`

The skills give every other command in the form you need. Never invent a command.

Format examples for every input file are in `examples/`.
