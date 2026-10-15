---
name: job-analysis
description: Turn a pasted job description into a saved, structured analysis (must-have and nice-to-have requirements, exact keywords, responsibilities, constraints, red flags). Use when a job posting has not been analysed yet.
---

# Job analysis

## Before you start
- The company must exist (`python scripts/rh.py company find "<name>"`). If not, create it first (see `resume-workflow`).
- The pasted description is in `scratch/jd.txt`. Do not rewrite it. It is saved as written.

## Steps
1. Make sure the job exists:
   `python scripts/rh.py job find <company-slug> --title "<title>" --jd-file scratch/jd.txt`
   - EXACT MATCH: it is already saved. Use `python scripts/rh.py job show <company-slug> <job-slug>`. If an analysis exists, stop here and reuse it.
   - SIMILAR TITLE: ask the user whether it is the same posting. Same: reuse the old job. New: create with `--allow-similar`.
   - No match: create it:
     `python scripts/rh.py job create <company-slug> --title "<title>" --jd-file scratch/jd.txt --url "<posting url if any>"`
2. Read the description carefully. Fill the analysis JSON (see `references/analysis-guide.md` and `examples/example-analysis.json`).
3. Save it from a file in `scratch/`:
   `python scripts/rh.py job analysis-save <company-slug> <job-slug> --file scratch/analysis.json`
4. Show the user a short summary: role family, seniority, the top 4 must-haves, and anything unclear. Return to `resume-workflow`.

## Rules
- `keywords`: 8 to 20 exact phrases copied from the posting (skills, tools, methods, standards). Copy the posting's wording. Do not add words that are not in the posting.
- `must_have` versus `nice_to_have`: use the posting's own signals. "Required", "must", "you have" mean must-have. "Preferred", "nice to have", "a plus", "bonus" mean nice-to-have. If the posting does not say, treat it as must-have and note that in `red_flags`.
- `constraints`: location, on-site or hybrid, work authorisation, clearances, travel, shifts, language.
- `red_flags`: vague duties, unrealistic requirement lists, missing salary only if relevant, contradictions. Plain statements, not accusations.
- Do not judge the candidate here. Matching to the profile happens in the strategy step.
