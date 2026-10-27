---
name: onboard-profile
description: Build or update a person's master profile (all facts about education, experience, projects, research, certifications, skills) and save their private contact details. Use when a person has no saved profile, wants to add or correct facts, or has an old CV to import.
---

# Onboard or update a profile

The profile is the only source of facts for every resume. Record what the user says, exactly. Never infer, never fill blanks, never add skills the user did not claim.

## Before you start
- Run `python scripts/rh.py person show <slug>` to see what is already saved. Do not ask again for anything already saved.
- Input files go in `scratch/` (create them with your file tool). `rh.py` deletes them after saving.
- JSON format example: `examples/example-profile.json`. Allowed sections and fields are in `config/profile_schema.json`. See `references/interview-guide.md` for the question list and entry examples.

## Contact details (private)
Never ask for the name, email, phone, location or links in the conversation. Run:
`python scripts/rh.py contact form <slug>`
Tell the user: "A private file has opened. Fill in your details, save it, and close it. I do not read that file." When they say it is done:
`python scripts/rh.py contact import <slug>`
The command prints only which fields were saved, never the values.
Rules (the form enforces them and prints WARN or ERROR lines):
- Professional links only: LinkedIn, plus GitHub or a portfolio for technical work, Behance or Dribbble for design, Google Scholar or ORCID for research. At most 3.
- Social media is refused (Instagram, WhatsApp, Twitter or X, Facebook, Telegram, Snapchat, TikTok, and similar). A WhatsApp number may be the phone number, without the label.
- City and country only. No street address.
- To change a link, edit the form; delete its line to remove it.
`contact show` prints only which fields are saved. Never read `contact.json` or the form file; never repeat the values.
If an existing person's folder id is their real name, rename it once to a private label: `python scripts/rh.py person rename <slug> --label "Me"`. It moves the folder and updates the applications, so the old id no longer appears in the folder path or person lists. `person label` changes only the display label and does not rename the folder. The command needs the old id once; do not repeat it in your reply.
If the user pastes contact details into the conversation anyway, do not repeat them. Ask the user to use `contact form` so the values stay out of the conversation; `contact set` is a last resort and puts the values on the command line.
Contact details and header links go only here. Never put them in a strategy or a resume draft.
Profile entries of the section `link` are extra references for evidence (for example a write-up URL). They are never shown in the header.

## Photo (only if the user asks for one)
A photo is optional and off by default. Do not suggest one unless the job's region expects it. If the user wants one:
1. Run `python scripts/rh.py photo guide` and read the standard to the user.
2. If they have no suitable photo, give them the phone instructions and the editor prompt from the same output. Never generate or replace a face; say plainly that a generated face is a misrepresentation and a photo is optional.
3. `python scripts/rh.py photo set <slug> --file <image path>`
4. Heed any WARN (small or oddly shaped image). Turning it on for an application happens in `resume-strategy`.
Never open, view, or attach the image yourself; `photo set` is the only thing that reads it.

## Interview, one topic at a time
Order: education, experience, internships, projects, research and publications, certifications, achievements, skills, open source and volunteering, languages. (Header links are contact details, asked above, not a profile topic.)
For each topic:
1. Ask one open question ("Tell me about your education: degree, school, years").
2. Ask follow-ups for missing basics (dates, location) and for results: "What was the result? Any numbers: how many, how much, how fast?" Record numbers only if the user gives them. If there are none, record none.
3. Write one JSON file in `scratch/` with the entries (see the guide).
4. Save it: `python scripts/rh.py profile add <slug> --file scratch/<name>.json`
5. Read the printed ids back to the user in one line. Move on.
Save after every topic so nothing is lost if the conversation stops.

## Skills
Ask for skills and tools the user can honestly use. Record each as its own `skill` entry with `category` and, if the user says so, `level` and `years`. Where a skill was used in a project or job, add `evidence` listing that entry's id.

## Importing an existing CV
If the user pastes or attaches a CV: read it, turn it into entries, show the list clearly, and ask "Is this correct? Anything wrong or missing?" Save only after the user confirms. Do not keep wording you cannot back with the CV.

## Updating
- Add new facts: `profile add`.
- Fix a fact: `python scripts/rh.py profile update <slug> <id> --file scratch/<name>.json` (the file contains only the fields to change; use `null` to delete a field).
- Remove a fact: `python scripts/rh.py profile remove <slug> <id>`. Old versions are kept in history.
- `profile add` blocks duplicates. If it says an item looks like a duplicate, use `profile update` instead. Use `--allow-duplicate` only if the user says it is a separate item.

## Finish
Run `python scripts/rh.py profile show <slug>` and `python scripts/rh.py profile validate <slug>`.
- Fix every ERROR.
- For each WARN about missing results, ask the user once whether a true number exists. Do not push if they say no.
Then return to `resume-workflow`.
