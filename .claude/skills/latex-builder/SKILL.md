---
name: latex-builder
description: Build the resume files from the saved Markdown, meaning a PDF with an auto-fitted layout, a Word file (DOCX), LaTeX, an Overleaf zip, and an optional separate photo PDF, with contact details filled in from the saved contact file. Use after the resume text passes the truth check and lint.
---

# Builder

The script does the conversion. You run it and handle problems. You never write or edit LaTeX by hand: the `.tex` file is regenerated from the Markdown, so hand edits would be lost.

## Steps
1. Check contact details exist: `python scripts/rh.py contact show <person>` (it prints which fields are saved, not the values). If empty, load `onboard-profile` and open the private contact form; do not ask for the values in the conversation.
2. Check the application settings: `python scripts/rh.py app settings <person> <app>`. This one list holds the region, paper, page target, photo choice, and the cover letter and CV answers from the start menu. If it says the menu is not answered, go back to `resume-strategy` and ask all six questions; the build refuses until every answer is saved.
3. Build: `python scripts/rh.py build <person> <app>`
4. Read the output.

## What the build makes (each build is a new version, nothing is overwritten)
- `resume.vN.pdf`: the ATS file. Single column, real text, never contains a photo. The layout is auto-fitted: the script tries layout presets from roomy to tight and keeps the roomiest one that fits the page target.
- `resume.vN.docx`: a Word file with real headings and bullets. Many portals accept Word. It also keeps non-Latin scripts.
- `resume.vN.tex` and `overleaf-resume.vN.zip`: for manual editing in Overleaf.
- Only if the photo is on: `resume-photo.vN.pdf` and `overleaf-resume-photo.vN.zip`, for email or print.
- Only if the start menu asked: `cover-letter.vN.pdf` from the saved cover letter, and `cv.vN.pdf` plus `cv.vN.docx` from the saved longer CV.

## Outcomes
- `PDF:` printed with `Pages:`, `Layout preset:`, and `Last page fill:` means success.
  - Over the page target (`does not fit`): go back to `resume-writer`, cut the weakest items, save a new version, and rebuild.
  - Fill under about 60% on a one-page resume (the check warns): the content is short. Add more true, relevant evidence from the profile. Never pad with filler.
- `ERROR: ... no 'Headline:' line`: add the designation line to the Markdown, save a new `resume-md` version, rebuild.
- `WARN: Character U+... cannot be typeset`: a symbol or non-Latin letter was replaced with `?` in the PDF and LaTeX. Use plain characters in the Markdown. The DOCX keeps the text; XeLaTeX with a Unicode-capable font can typeset it, but the shipped template uses pdfLaTeX/T1 and will not.
- `COMPILE FAILED` with a log excerpt: read the first `!` line. Usual causes are odd characters or a broken link. Fix the Markdown, save a new `resume-md` version, run `truth` and `lint` if the text changed, and rebuild. Maximum 3 attempts, then stop and report the excerpt.
- `No TeX engine found`: run `python scripts/rh.py doctor` and tell the user, clearly, what it says to install (TeX Live, MiKTeX, or tectonic). Then rebuild. Or the user can upload the zip to Overleaf. The DOCX was still made, so they are never left without a resume file.
- `Contact data missing`, `Social media links are not allowed`, `at most 3 links`: have the user fix the private contact form (`onboard-profile`), import it again, and rebuild.
- `Unknown placeholder`: use only the placeholders listed in `resume-writer/references/resume-md-format.md`.

## Overleaf (manual, optional)
In Overleaf choose New Project, then Upload Project, and pick the zip. Overleaf compiles `main.tex` as it is. Hand edits made in Overleaf are not saved back to the harness.

When the application is exported, the export folder also holds `FirstName_LastName_Resume.tex` and `FirstName_LastName_Overleaf.zip`, so the user can edit a copy by hand without touching the saved build.

## Never
- Never write contact details into any file. The user enters them in the private form; the build fills them locally. Never read the form, `contact.json`, a photo image, or a generated `.tex`/`.pdf`.
- Never copy the PDF, DOCX, or `.tex` into the harness folder. They stay in the application folder in the data folder.
- Never put a photo in the ATS file.

Next: `ats-and-review`.
