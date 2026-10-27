---
name: ats-and-review
description: Check a built resume the way an ATS and a human reviewer would (extracted text, reading order, headings, keyword coverage, evidence), run a recruiter scan and a skeptical hiring-manager review, and apply fixes. Use after the PDF is built.
---

# ATS check and review

## 1. Automatic checks
Run: `python scripts/rh.py check <person> <app>`
This extracts the PDF text with `pdftotext` (or `pypdf`) and also runs the truth check, the policy checks (header order, links, personal data, photo), and the writing lint. Read every FAIL, WARN, and the keyword coverage section. Rules and meaning: `references/ats-rules.md` and `resume-writer/references/resume-policy.md`.
- FAIL means fix before finishing. A policy FAIL (header order, social media, personal data) is never negotiable.
- WARN "page is only N% full": the content is short. Add more true relevant evidence, never filler.
- WARN "Supported by the profile but missing from the resume": consider adding the keyword where it is true and fits.
- WARN "Not supported by the profile": these are real gaps. Never add them. Tell the user in the final report.
- If no text extractor exists, tell the user: install poppler-utils (provides `pdftotext`) or run `pip install pypdf`.

## 2. Review pass A: recruiter scan (10 seconds)
Read the extracted resume text (`python scripts/rh.py app cat <person> <app> resume-md`). Use the persona and questions in `references/review-personas.md`. Write down what a recruiter would notice in the first 10 seconds and what is unclear.

## 3. Review pass B: skeptical hiring manager
Use the second persona in the same file. For every bullet: what did the person do personally, how, with what result, can it be verified? Flag vague bullets and claims that look bigger than the candidate's level.

## 4. Save the review
Write `scratch/review.md` with the headings in `references/review-personas.md` and save:
`python scripts/rh.py app save <person> <app> review --file scratch/review.md`

## 5. Fix (at most 2 rounds)
For each finding you can fix with true facts: read the latest resume and evidence map back with `python scripts/rh.py app cat <person> <app> resume-md` and `python scripts/rh.py app cat <person> <app> evidence-map`, write them to `scratch/resume.md` and `scratch/evidence-map.md` again (the earlier scratch files were deleted after saving), edit, save new versions (`resume-md`, `evidence-map`), run `truth`, run `lint`, rebuild, run `check`, then write the updated review to `scratch/review.md` and save it again. Do not fix by inventing. If a fix needs a fact you do not have, ask the user one question.
After 2 rounds, stop. List what remains.

## 6. Finish
Set the status: `python scripts/rh.py app status <person> <app> reviewed`
Return to `resume-workflow` step 9 for the final message.
