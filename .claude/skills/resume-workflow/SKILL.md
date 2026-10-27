---
name: resume-workflow
description: Entry point for making a job-specific resume. Use whenever the user wants a resume, CV, job application, or tailoring to a job, or asks what resume data is saved, or wants to back up, reuse, or delete it. Runs the reuse checks and the fixed stage order.
---

# Resume workflow (entry point)

Follow the steps in order. Run each command, read its output, and obey its NEXT line. Ask the user one question at a time.

## Step 0: Where is the data
Run: `python scripts/rh.py status`
- Tell the user the data folder path and the counts (people, companies, jobs, applications).
- If the user wants a different folder: `python scripts/rh.py set-data-dir <path>` (must be outside this harness folder).
- If the output has a line starting with `UPDATE:`, a newer version of the harness exists. Say so in one sentence and ask whether to update now or later. If the user says yes, run `python scripts/rh.py update`, follow its NEXT line, and only then run `python scripts/rh.py update --apply` if the user has agreed in this conversation. Never update the harness without asking.

## Step 1: Which person
Run: `python scripts/rh.py person list`
- No people: ask for a short, non-private label (for example "Me" or "Partner"). Do not ask for the full name; the private contact form collects it. Run `python scripts/rh.py person create --label "<label>"`, then load skill `onboard-profile`.
- People exist: ask "Is this one of the saved people, or someone new?" A saved person is shown by label and slug; an old folder id may still be a real name until it is renamed below.
  - Saved person: run `python scripts/rh.py person show <slug>`. Ask: use the saved profile as it is, or update it first? Update means load `onboard-profile` (update section).
  - New person: run `person find "<label or slug>"` first. If it prints MATCH, ask whether it is the same person. Only if the user says it is a different person, run `person create --label "<label>" --allow-duplicate`.
- If a saved person's display label is the full real name, you may offer once to relabel it: `python scripts/rh.py person label <slug> --label "Me"`. If the folder id is also the real name, use `python scripts/rh.py person rename <slug> --label "Me"` once so paths and lists stop showing it. Do not repeat the old id in your reply. The private contact name is not changed.
- Check contact exists: `python scripts/rh.py contact show <slug>` (it prints which fields are saved, never the values). If empty, `onboard-profile` opens the private form.

## Step 2: Which company
Ask for the company name (and website if the user has it).
Run: `python scripts/rh.py company find "<name>"`
- MATCH printed: run `python scripts/rh.py recon latest <slug>`.
  - FRESH: tell the user the recon is `<n>` days old and ask "reuse it?" Default is reuse. Skip company-recon.
  - STALE or NO RECON: ask "refresh it?" If yes, load `company-recon` (saves a new dated file; the old one stays).
- No match: `python scripts/rh.py company create --name "<name>" --website <url>`, then load `company-recon`.

## Step 3: Which job
Ask the user to paste the job description (or give the URL, then fetch it if you can). Ask for the exact job title.
Save the pasted text to `scratch/jd.txt` (create the file with your file tool).
Run: `python scripts/rh.py job find <company-slug> --title "<title>" --jd-file scratch/jd.txt`
- `EXACT MATCH`: the same text is already saved. Reuse. Run `python scripts/rh.py job show <company-slug> <job-slug>`. Skip job-analysis.
- `SIMILAR TITLE`: ask "Is this the same posting with edited text, or a new posting?" Same: reuse the old job. New: load `job-analysis` and create with `--allow-similar`.
- `No existing job matches`: load `job-analysis`.
If the job has no saved analysis yet, load `job-analysis`.

## Step 4: Which application
Run: `python scripts/rh.py app find <person-slug> --company <company-slug> --job <job-slug>`
- EXISTING printed: tell the user its status and files (`python scripts/rh.py app files <person-slug> <app-id>`). Ask: continue it (new saves become v2, v3, nothing is overwritten) or start a separate new one (`app create ... --new`)?
- None: `python scripts/rh.py app create <person-slug> --company <company-slug> --job <job-slug>`
Keep the application id. You need it for every later command.

## Step 5: The start menu, then strategy, then STOP
Load `resume-strategy`. It asks the start menu for this application: country, photo, length, cover letter, how to apply, CV version, and anything to leave out. The menu is asked once for a new application and read back on later builds. The first six answers are saved with `python scripts/rh.py app settings <person-slug> <app-id> --region <key> --pages 1|2|3 --photo on|off --cover-letter on|off --apply-routes on|off --cv on|off`; a partial answer does not count, and the build refuses until all six are saved. The seventh is written into the strategy. If the menu is already answered, the saved answers are read back instead of asking again. Then the strategy is written and saved. Show the user a short summary (candidate type, sections and order, gaps, open questions). Ask: "Approve this plan, or what should change?" Do nothing else until the user answers.

## Step 6: Write
After approval, load `resume-writer`. It saves the resume Markdown and the evidence map, then runs the truth check and the policy and writing lint (`truth`, then `lint`). If the start menu asked for a cover letter or a longer CV, it writes those as well and saves them as the `cover-letter` and `cv-md` stages, then runs `lint` again so the report covers them.

## Step 7: Build
Load `latex-builder`. It fills in the contact details and makes the PDF (layout fitted to the page target), the Word file (DOCX), the LaTeX, the Overleaf zip, and, only for the documents the start menu asked for, a separate photo PDF, a cover letter PDF and a longer CV PDF.

## Step 8: Check and review
Load `ats-and-review`. It runs the ATS check, the recruiter and skeptic review, and applies fixes (max 2 rounds).

## Step 9: How to apply, only if the menu asked for it
Read the setting: `python scripts/rh.py app settings <person-slug> <app-id>`, the "How to apply" line.
- `off`: skip this step.
- `on`: use the saved recon and public pages only (careers page, job board or portal, and an application email address only if it is published publicly). Write `scratch/apply-routes.md` listing each route, the source URL next to it, and "unknown" where nothing public was found. Save it: `python scripts/rh.py app save <person-slug> <app-id> apply-routes --file scratch/apply-routes.md`. Never log in anywhere, never scrape LinkedIn, and never guess an email address.

## Step 10: Finish
1. Export the final files with employer-ready names: `python scripts/rh.py export <person> <app>`. It prints the folder (`exports/v1`, `exports/v2`, ... so nothing is overwritten) and the file types, not the names: the resume PDF and Word file, plus the cover letter, CV and photo PDF when the start menu asked for them. The names are made from the private contact name, so do not list the folder or repeat them.
2. Tell the user, in this order:
   - The export folder path and which file to use where: the PDF or DOCX for job portals and ATS; the `_Cover-Letter.pdf` for the cover letter box or the email body; the `_CV.pdf` where a longer CV is wanted; the `_Photo` PDF only for email or print where a photo is expected.
   - The application routes from step 9, if they were saved.
   - What the review found that remains unfixed (real gaps, such as a missing certification), clearly.
   - That the `.tex` and the Overleaf zip are in the application folder for manual editing in Overleaf.
3. Ask whether to mark it applied: `python scripts/rh.py app status <person> <app> applied`.
4. Clean up temporary files: `python scripts/rh.py clean-scratch`. Nothing runs this automatically, so always run it yourself at the end of a run.

## Data questions (not part of a resume run)
- What is saved: `python scripts/rh.py status`, then `person list`, `company list`, `job list <company>`, `app list <person>`. The data folder also has a readable `INDEX.md`.
- Contact details: `contact show <slug>` prints which fields are saved, never the values. To change them, open the private form with `contact form <slug>`, tell the user to edit and save it, then run `contact import <slug>`. Never read the form or `contact.json` yourself, and never repeat the values.
- Back up: `python scripts/rh.py backup` (prints the zip path).
- Move to another computer: copy the whole data folder, then on the new computer run `set-data-dir <path>`.
- Delete one person or one company: first tell the user exactly what will be deleted and ask them to type the phrase. Only then run `python scripts/rh.py forget person <slug> --confirm "DELETE <slug>"` (same for `company`).
- Delete everything (fresh install): the user must type `DELETE ALL DATA`. Only then run `python scripts/rh.py reset --confirm "DELETE ALL DATA"`. Suggest a backup first.
- Never run `forget` or `reset` on your own initiative, and never reuse a confirmation phrase from an earlier question.

## If something goes wrong
- `ERROR:` plus `HINT:` lines tell you the fix. Follow them.
- Lost the thread, or the conversation was resumed? `python scripts/rh.py brief <person-slug> <app-id>` prints the saved start menu answers, every step with whether it is done, and the next command. `python scripts/rh.py brief` lists every application and how far each has got.
- Never work around `rh.py` by writing files into the data folder yourself.
- If a tool seems to be missing (no PDF, no ATS check), run `python scripts/rh.py doctor`. It changes nothing and says clearly what to install.
