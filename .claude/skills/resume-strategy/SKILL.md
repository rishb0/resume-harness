---
name: resume-strategy
description: Decide what a resume should contain and in what order for one person and one job, using the evidence-based framework, a gap analysis against the job, and regional norms. Ends by stopping for the user's approval. Use after the profile, company recon, and job analysis exist.
---

# Resume strategy

You decide the content and order. You do not write the resume yet.

## Inputs (read all of them)
- Profile: `python scripts/rh.py profile show <person-slug>`
- Company recon: `python scripts/rh.py recon show <company-slug>`
- Job and analysis: `python scripts/rh.py job show <company-slug> <job-slug>`
- The framework: `references/framework.md` (read it fully; it is the decision method)
- The output template: `references/strategy-template.md`

## Ask the user first (one question at a time, skip what you already know)
1. "Which country is the job in?" Run `python scripts/rh.py region list`, pick the matching region, and show the user its rule in one line (`python scripts/rh.py region show <key>`): paper size, photo rule, nationality rule.
2. Photo: only if the region's photo rule is `optional`, and only if the person has a photo or wants one. Say: "A photo is optional. I can make an extra photo version for email or print; the ATS file never has one." If the rule is `never`, do not offer a photo.
3. Page limit: default one page for under about 10 years of experience, two pages otherwise.
4. "Is there anything you want left out or put first?"
Then save the choices:
`python scripts/rh.py app settings <person-slug> <app-id> --region <key> --pages 1` (use 2 or 3 for longer resumes) and, if a photo is wanted, `--photo on` (it needs `photo set` first; see `onboard-profile`).
The region fixes the paper size. Add `--paper a4` or `--paper letter` only to override it.

## Designation (the Headline line)
Decide the header designation here and write it in the strategy. It must be the person's real title or the target role worded honestly (for example "Computer Science Graduate | Web Application Security" or "Aspiring Data Analyst"). Never a title the profile does not support. Details: `resume-writer/references/resume-policy.md`.

## Method
1. Classify the candidate type (framework section 2) and name the target role precisely (framework section 6, step 1).
2. Gap analysis: for each must-have and nice-to-have in the job analysis, mark matched, partial, or missing, and list the profile ids that support it. A requirement with no supporting profile id is missing. Never mark something matched without ids.
3. Score every profile entry: relevance, ability proof, credibility, recency, uniqueness (framework section 6, step 3). Decide include, shorten, or cut, with a one-line reason.
4. Pick the structure: experience-led, project and research-led, or hybrid (framework sections 13 and 14). Choose only sections that have real content. No empty sections.
5. Choose section order by the job, not by habit (framework sections 3 to 5). Use standard heading names (see the list in `config/settings.json`).
6. Use the company recon only to choose emphasis and wording that is true for this person.
7. Missing requirements: say so plainly. Suggest honest ways to show related real evidence. Never suggest inventing anything. A certification that is in progress is shown as in progress only.
8. List open questions for the user (for example a missing number).

## Output
Write `scratch/strategy.md` following the template headings exactly, then save:
`python scripts/rh.py app save <person-slug> <app-id> strategy --file scratch/strategy.md`

## Gate: STOP
Show the user a short summary: candidate type, section order, top 3 strengths, the real gaps, open questions. Ask: "Approve this plan, or what should change?"
- Changes: update `scratch/strategy.md` and save again (it becomes the next version; the old one stays).
- Do not start `resume-writer` until the user clearly approves.
