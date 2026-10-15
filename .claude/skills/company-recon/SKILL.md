---
name: company-recon
description: Research a target company from public sources (website, careers page, blog, public code, recent news) and save a short dated brief with sources and confidence labels. Use before tailoring a resume to a company, or to refresh an old brief.
---

# Company recon

Goal: learn enough about the company to choose which of the person's evidence to emphasise and which words to use. Not to write an essay.

## Before you start
1. `python scripts/rh.py company find "<name>"`, then `python scripts/rh.py recon latest <company-slug>`.
2. If a FRESH recon exists, ask the user whether to reuse it. Reuse is the default. Only continue if the user asks for a refresh, or the recon is STALE or missing.
3. A refresh is saved as a new dated file. The old one is never overwritten.

## Allowed sources (public, company-level only)
- Official website: home, about, products, careers, blog, press, customers, security or trust pages.
- The job posting itself and the company's other open postings (they show the tech stack and team language).
- Public code repositories of the company.
- Recent news (last 12 months) from reputable outlets.
- Company social pages for announcements only.

## Not allowed
- Anything behind a login. Scraping LinkedIn. Personal information about individual employees (home details, family, private accounts). Guessing.
If you have no web access, ask the user to paste the About and Careers page text. Do not invent.

## What to collect
- What the company does and who its customers are.
- Size and stage, only if a source states it.
- Technology or domain focus (stack, standards, methods, regulations).
- Values and tone words from the company's own writing (to match the register of the resume summary).
- Hiring signals: team names, seniority words, repeated skills across postings.
- Resume implications: 3 to 5 plain statements such as "Emphasise API testing; the company sells an API product."
- Optional, for interview prep only: office location and anything visible about the work environment. Keep it in its own section. It does not affect the resume.

## Output file
Write it to `scratch/recon.md` using `references/recon-template.md`. Every factual line ends with `(source: <url>, confidence: high|medium|low)`.
- high: stated on the company's own site or a primary source.
- medium: reputable third party.
- low: indirect or old.
Lines you could not verify go under "Unknown", written as unknown.

Save: `python scripts/rh.py recon save <company-slug> --file scratch/recon.md`
Then show the user three lines: what the company does, the main emphasis for the resume, and anything unknown that matters. Return to `resume-workflow`.
