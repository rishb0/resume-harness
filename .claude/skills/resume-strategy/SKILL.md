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

## Ask the user first: the start menu

This menu is used for every build of an application. Ask it once for a new application; on later builds, read the saved answers back and ask only about changes. Ask one question at a time and wait for the answer.

First run `python scripts/rh.py app settings <person-slug> <app-id>`. If it says the start menu is already answered, read the saved answers back to the user in one short list and ask: "Keep these, or change any?" Only ask the questions below again if the user wants changes.

1. **Country.** "Which country is the job in?" Run `python scripts/rh.py region list`, pick the matching region, and show its rule in one line (`python scripts/rh.py region show <key>`): paper size, photo rule, nationality rule.
2. **Photo.** Offer it only if the region's photo rule is `optional` and the person has a photo or wants one. Say: "A photo is optional. I can make an extra photo version for email or print; the ATS file never has one." If the rule is `never`, say plainly that this country does not use photos and move on.
3. **Length.** One page is the default for under about ten years of experience, two pages otherwise. Ask only if the profile does not make it clear.
4. **Cover letter.** "Do you also want a cover letter for this job?" Yes or no.
5. **How to apply.** "Should I also find how to apply: the careers page, the job portal, and any public email address applications go to?" Public information only. Never guess or invent an address.
6. **CV version.** "Do you also want a longer CV beside the one-page resume?" Yes or no.
7. **Anything to leave out or put first?** (Write the answer into the strategy; it is not a saved setting.)

Save the first six answers in one command:

`python scripts/rh.py app settings <person-slug> <app-id> --region <key> --pages 1 --photo on|off --cover-letter on|off --apply-routes on|off --cv on|off`

The six answers are saved with the application, so no later step asks again and nothing is lost if the conversation is interrupted. Question 7 goes into the strategy itself. Use `--pages 2` or `--pages 3` for a longer resume; three pages is rare (academic or very senior careers). The region fixes the paper size; add `--paper a4` or `--paper letter` only to override it. A photo needs `photo set` first (see `onboard-profile`).

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

## Start from a default order for the candidate type

Method step 5 says to order by the job. Start from the line that matches this candidate (framework section 2 for the type, section 16 for the same idea spelled out), then move a section only for a reason you can write down. Use the standard heading names from `config/settings.json`.

| Candidate type | Start from |
| --- | --- |
| Student or recent graduate | Summary, Education, Projects, Skills, Certifications, Achievements |
| Student with real security or research work | Summary, Internships, Projects, Research, Skills, Education, Certifications |
| Experienced professional | Summary, Experience, Skills, Projects, Education, Certifications |
| Moving from one field into another | Summary, Experience, Projects, Skills, Education, Certifications |
| Researcher or bug bounty hunter | Summary, Research, Vulnerability Research, Projects, Skills, Education, Certifications |
| Academic, or applying for higher studies | Summary, Education, Research, Publications, Skills, Certifications |
| Returning after a break | Summary, Skills, Experience, Projects, Education, Certifications |

Two details that fix the usual mistakes:
- **Under about two years of experience**: Education goes above Experience. The reader wants the training before a short job list.
- **A gap, or a very recent short role**: do not hide it by pushing Experience down the page. Put Experience where the table says and let the summary explain the move in one honest sentence. A recruiter sees the dates anyway.

The candidate type also decides how much space each section gets: the primary evidence in the table gets the most room, and everything else earns its place or is cut.

## Output
Write `scratch/strategy.md` following the template headings exactly, then save:
`python scripts/rh.py app save <person-slug> <app-id> strategy --file scratch/strategy.md`

## Gate: STOP
Show the user a short summary: candidate type, section order, top 3 strengths, the real gaps, open questions. Ask: "Approve this plan, or what should change?"
- Changes: read the saved strategy back with `python scripts/rh.py app cat <person-slug> <app-id> strategy` into `scratch/strategy.md` (the previous scratch file was deleted after saving), edit it, and save again (it becomes the next version; the old one stays).
- Do not start `resume-writer` until the user clearly approves.
