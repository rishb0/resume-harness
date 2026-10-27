# Resume Harness: rules for the agent

This folder is a harness. It makes you produce a job-specific, ATS-safe resume for any person and any job, in fixed stages, with saved data that is reused instead of repeated.
Python command: `python scripts/rh.py ...`. If the shell says `python: command not found`, use `python3` on macOS or Linux, or `py` on Windows, and keep using that form for the whole run. `python scripts/rh.py doctor` prints the exact form for this machine.

## Start here
- Users talk to you in normal English. They do not know slash commands. Never ask them to use one.
- If the user's message is about a resume, CV, job, job description, or application (including a message that is only a pasted job description, or "make my resume"), load the skill `resume-workflow` straight away and follow it.
- If the user asks how to use the harness, what to say, or where to start: read `docs/USAGE.md` and give the relevant copy-paste prompt. Do not make the user learn internal commands.
- If the user asks to onboard, build a profile, or update their profile: load `resume-workflow` and start at Step 0 through Step 1, or load `onboard-profile` when the profile already exists.
- If the user asks what data is saved, or wants to back up, move, or delete data: use the "Data questions" section of `resume-workflow`.
- If the user asks about updates, or wants to turn off the daily version check, use the update instructions in `resume-workflow`. Never apply an update without asking.
- If a command fails because a tool is missing (no PDF engine, no PDF text tool), run `python scripts/rh.py doctor` and tell the user what it says clearly.
- Do not run `/init` in this folder. `AGENTS.md` is already the harness instruction file, and `/init` can change it.
- Do not answer from memory about how this harness works. Read the skill.
- Lost the thread, or the conversation was resumed? Run `python scripts/rh.py brief` to see every application and how far each has got, or `python scripts/rh.py brief <person-slug> <app-id>` for one. It prints the saved start menu answers, every step with whether it is done, and the next command.
- The user's first message may start with "Read AGENTS.md". That is normal. Do what the rest of the message asks.

## Non-negotiable rules
1. **Truth gate.** Never invent employers, titles, dates, degrees, certifications, tools, skills, metrics, or achievements. Every resume bullet must trace to a profile id. If a number is missing, ask the user or write the bullet without a number. Never add a job-posting keyword the profile does not support.
2. **Data is separate from the harness.** All user, company, and job data lives in the data folder (run `python scripts/rh.py where`). Never save personal data, job text, or resumes inside this harness folder. The only temporary files you may create here are inside `scratch/`. `rh.py` deletes them after a successful save, and `python scripts/rh.py clean-scratch` removes any that remain. Run it at the end of every run.
3. **Only `rh.py` touches data.** Never create, edit, rename, or delete files in the data folder by hand. Never choose data file names yourself. `rh.py` picks names, numbers versions (v1, v2, ...), and refuses to overwrite. Never open `contact.json`, `contact-form.txt`, a photo image, a generated `.tex`/`.pdf`, or an exported file; you need none of them.
4. **Reuse before repeating.** Before creating a person, company, job, or application, run the matching `find` command. If something exists, tell the user and ask: reuse it, refresh it, or create a new one. Do not repeat recon, analysis, or onboarding for data that already exists unless the user asks.
5. **The start menu comes first.** Every application uses the start menu of `resume-strategy`: country, photo, length, cover letter, how to apply, CV version, and anything to leave out. It is asked once for each new application, then read back on later builds, even when the same person applied yesterday. Save all six answers with `app settings` before writing the strategy; a partial answer does not count, and the build refuses until every answer is saved. The answer to "anything to leave out or put first" belongs in the strategy itself.
6. **Ask one question at a time** and wait for the answer. Do not guess answers to questions about the user's own history.
7. **Stop at gates.** After the strategy is saved, stop and wait for the user's approval. Never delete or reset data without the exact confirmation phrase typed by the user in this conversation.
8. **Contact details stay out of the conversation.** In the normal flow the user types their name, phone, email, location and links into the private form (`contact form`), not into this conversation. You are instructed not to read that file or `contact.json`, and never to repeat the values. Drafts use `{{NAME}}` and `{{CONTACT}}`; the build fills them from the saved contact file. If the user pastes contact details into the conversation anyway, do not repeat them.
9. **Public company information only.** No logins, no scraping LinkedIn, no personal information about individual employees. Unknown stays "unknown".
10. **Loop limits.** Truth-check fixes: at most 3 rounds. Build fixes: at most 3 attempts. Review fixes: at most 2 rounds. Then stop and report what remains.
11. **Simple language.** Short sentences. No emojis. Past tense for completed work in resume bullets, present tense for current roles.
12. **Do not guess the tool.** If a command fails, read the ERROR and HINT lines it prints and follow them. The pipeline commands end with a `STAGE:` line (where the run has got to) and a `NEXT:` line (what to do).

## Resume rules (checked by code; read `.claude/skills/resume-writer/references/resume-policy.md`)
- **Header order**: name, then designation (the `Headline:` line), then contact. The designation is the real title or the target role worded honestly.
- **Links**: professional only (LinkedIn, plus GitHub or a portfolio for technical work, and similar), at most 3. Never Instagram, WhatsApp, Twitter or X, Facebook, Telegram, Snapchat, TikTok, or any social media. The contact form and `contact set` refuse them.
- **Personal data**: never a date of birth, age, marital status, religion, gender, caste, parents' names, ID numbers, or a full address. Nationality only where the region allows it.
- **Photo**: optional and off by default. Never offered for the United States, Canada, or the United Kingdom. The ATS file never contains a photo. If a photo is on, the build makes a separate photo PDF for email or print. A photo is only a regional convention; the harness never judges appearance.
- **Region**: set per application from the job's country (`region list`). It fixes paper size and the photo and nationality rules.
- **Spelling**: the lint reports likely typos, a word written twice in a row, a missing space after a full stop, and British and American spelling mixed in one document. These are warnings, never a failed build: fix the real ones, and leave a name or a product alone even if the list flags it.
- **Page breaks**: no entry may start on one page and finish on the next. The ATS check reports it with both page numbers. Fix it by cutting or moving a bullet, never by squeezing the margins (the layout presets have a floor).

## Stage order
1. Person and profile (`onboard-profile`)
2. Company recon (`company-recon`)
3. Job analysis (`job-analysis`)
4. The start menu, then strategy, then STOP for approval (`resume-strategy`)
5. Resume Markdown and evidence map, truth check, policy and writing lint; the cover letter and longer CV when the menu asked for them (`resume-writer`)
6. PDF (auto-fitted), Word file, LaTeX, Overleaf zip, and, when the menu asked for them, a photo PDF, a cover letter PDF and a CV (`latex-builder`)
7. ATS check and review (`ats-and-review`)
8. How to apply, when the menu asked for it (`resume-workflow`, step 9)
9. Export with employer-ready file names (`resume-workflow`, step 10)

## Command quick reference
Run `python scripts/rh.py --help` or `python scripts/rh.py <group> --help` for all options. Exact forms:
- `python scripts/rh.py doctor` : check that the computer is ready (Python, PDF tools, data folder)
- `python scripts/rh.py status` : data folder path and counts
- `python scripts/rh.py brief` and `python scripts/rh.py brief <person-slug> <app-id>` : where a run has got to
- `python scripts/rh.py person list` and `python scripts/rh.py person find "<label or slug>"`
- `python scripts/rh.py person create --label "Me"` : use a short, non-private label, not the full name
- `python scripts/rh.py person rename <person-slug> --label "Me"` : give a person saved under their real name a private folder id as well as a private label; `person label` changes the display label only
- `python scripts/rh.py contact form <person-slug>` then `python scripts/rh.py contact import <person-slug>` : the private contact form; the user fills the file, you never read it
- `python scripts/rh.py contact show <person-slug>` : which fields are saved, never the values
- `python scripts/rh.py company find "<name>"` and `python scripts/rh.py recon latest <company-slug>`
- `python scripts/rh.py job find <company-slug> --title "<title>" --jd-file scratch/jd.txt`
- `python scripts/rh.py app find <person-slug> --company <company-slug> --job <job-slug>`
- `python scripts/rh.py profile show <person-slug>` and `python scripts/rh.py profile validate <person-slug>`
- `python scripts/rh.py region list` and `python scripts/rh.py app settings <person-slug> <app-id> --region india --pages 1 --photo off --cover-letter off --apply-routes on --cv off` (the start menu answers; run it with no flags to read them back)
- `python scripts/rh.py app save <person-slug> <app-id> strategy --file scratch/strategy.md` (stages: strategy, resume-md, evidence-map, review, cover-letter, cv-md, apply-routes)
- `python scripts/rh.py truth <person-slug> <app-id>` then `python scripts/rh.py lint <person-slug> <app-id>`
- `python scripts/rh.py build <person-slug> <app-id>`
- `python scripts/rh.py check <person-slug> <app-id>`
- `python scripts/rh.py export <person-slug> <app-id>`
- `python scripts/rh.py clean-scratch` and `python scripts/rh.py backup`
- `python scripts/rh.py update` (a newer version published? `python scripts/rh.py update --apply` replaces this copy, but only after the user agrees; `python scripts/rh.py update --off` stops the daily check)

The skills give every other command in the form you need. Never invent a command.

Format examples for the main input files are in `examples/`; each skill's `references/` folder gives the rest.
