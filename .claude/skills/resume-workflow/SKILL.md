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

## Step 1: Which person
Run: `python scripts/rh.py person list`
- No people: ask for the person's full name, run `person create --name "<name>"`, then load skill `onboard-profile`.
- People exist: ask "Is this one of the saved people, or someone new?"
  - Saved person: run `python scripts/rh.py person show <slug>`. Ask: use the saved profile as it is, or update it first? Update means load `onboard-profile` (update section).
  - New person: run `person find "<name>"` first. If it prints MATCH, ask whether it is the same person. Only if the user says it is a different person, run `person create --name "<name>" --allow-duplicate`.
- Check contact exists: `python scripts/rh.py contact show <slug>`. If empty, `onboard-profile` collects it.

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

## Step 5: Region and settings, then strategy, then STOP
Load `resume-strategy`. It asks for the job's country, picks the region (paper size, photo rule, nationality rule), asks about a photo only where the region allows one, and saves the choices with `python scripts/rh.py app settings <person-slug> <app-id> --region <key>`. Save the strategy. Show the user a short summary (candidate type, sections and order, gaps, questions). Ask: "Approve this plan, or what should change?" Do nothing else until the user answers.

## Step 6: Write
After approval, load `resume-writer`. It saves the resume Markdown and the evidence map, then runs the truth check and the policy and writing lint (`truth`, then `lint`).

## Step 7: Build
Load `latex-builder`. It fills in the contact details and makes the PDF (layout fitted to the page target), the Word file (DOCX), the LaTeX, the Overleaf zip, and, only if the photo is on, a separate photo PDF.

## Step 8: Check and review
Load `ats-and-review`. It runs the ATS check, the recruiter and skeptic review, and applies fixes (max 2 rounds).

## Step 9: Finish
1. Export the final files with employer-ready names: `python scripts/rh.py export <person> <app>`. It prints the folder (`exports/v1`, `exports/v2`, ... so nothing is overwritten) and the files: `FirstName_LastName_Resume.pdf`, `FirstName_LastName_Resume.docx`, and `FirstName_LastName_Resume_Photo.pdf` only if a photo version exists.
2. Tell the user, in this order:
   - The export folder path and which file to use where: the PDF or DOCX for job portals and ATS; the `_Photo` PDF only for email or print where a photo is expected.
   - What the review found that remains unfixed (real gaps, such as a missing certification), in plain words.
   - That the `.tex` and the Overleaf zip are in the application folder for manual editing in Overleaf.
3. Ask whether to mark it applied: `python scripts/rh.py app status <person> <app> applied`.
4. Clean up temporary files: `python scripts/rh.py clean-scratch`. Nothing runs this automatically, so always run it yourself at the end of a run.

## Data questions (not part of a resume run)
- What is saved: `python scripts/rh.py status`, then `person list`, `company list`, `job list <company>`, `app list <person>`. The data folder also has a readable `INDEX.md`.
- Back up: `python scripts/rh.py backup` (prints the zip path).
- Move to another computer: copy the whole data folder, then on the new computer run `set-data-dir <path>`.
- Delete one person or one company: first tell the user exactly what will be deleted and ask them to type the phrase. Only then run `python scripts/rh.py forget person <slug> --confirm "DELETE <slug>"` (same for `company`).
- Delete everything (fresh install): the user must type `DELETE ALL DATA`. Only then run `python scripts/rh.py reset --confirm "DELETE ALL DATA"`. Suggest a backup first.
- Never run `forget` or `reset` on your own initiative, and never reuse a confirmation phrase from an earlier question.

## If something goes wrong
- `ERROR:` plus `HINT:` lines tell you the fix. Follow them.
- Never work around `rh.py` by writing files into the data folder yourself.
- If a tool seems to be missing (no PDF, no ATS check), run `python scripts/rh.py doctor`. It changes nothing and says in plain words what to install.
