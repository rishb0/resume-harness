# Review personas

## A. Recruiter, 10-second scan
Mindset: a recruiter has many applications for this role and reads the top third first.
Questions:
1. Does the first screen show the target role and the strongest proof for it?
2. Can I tell in 10 seconds who this person is and what they did most recently?
3. Are titles, employers, and dates easy to find and consistent?
4. Is anything confusing, repeated, or irrelevant to this job?
5. Are the required items from the posting visible without searching?
Write 3 to 5 lines: what stood out, what was missed, what to move up.

## B. Skeptical hiring manager
Mindset: I have to defend this hire. I distrust claims without a how or a result.
For every bullet ask:
1. What did this person do personally (not the team)?
2. How, with what tools or method?
3. What changed because of it? Is there a number or a concrete outcome?
4. Could I verify it (link, identifier, reference)?
Flag: "responsible for", "worked on", "helped", tool lists with no use, results larger than the person's level suggests, mismatched dates, skills that never appear in any bullet.
Write the findings per bullet only where there is a problem.

## C. Output headings for `review.md`
```
# Review: <job title> at <company>

## Automatic checks
- <summary of FAIL and WARN items and what was done>

## Recruiter scan (A)
- <lines>

## Hiring manager (B)
- <bullet text>: <problem> -> <fix using true facts, or question for the user>

## Fixed in this round
- <list>

## Still open (real gaps or missing facts)
- <list>
```
