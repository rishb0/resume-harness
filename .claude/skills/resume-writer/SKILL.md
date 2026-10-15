---
name: resume-writer
description: Write the resume as strict Markdown plus an evidence map, using only facts from the profile and the approved strategy, then run the truth check and fix failures. Use after the user approves the strategy.
---

# Resume writer

Inputs: the approved strategy (`python scripts/rh.py app cat <person> <app> strategy`), the profile (`profile show <person>`), the job analysis. Format rules: `references/resume-md-format.md`. Policy rules (header, links, personal data, photo): `references/resume-policy.md`. Bullet rules: `references/bullet-writing.md`. Worked example: `examples/example-resume.md` and `examples/example-evidence-map.md`.

## Steps
1. Write `scratch/resume.md` in the exact format. Use only the sections, items, and order in the approved strategy.
2. Header lines: `# {{NAME}}`, then the required `Headline:` line (the designation from the strategy), then `{{CONTACT}}`. The order is name, designation, contact. Never type the real name, email, phone, or links. Never write a date of birth, marital status, religion, gender, parents' names, ID numbers, an address, or any social media.
3. Every bullet comes from a profile entry. You may shorten, reorder, correct grammar, and use the job posting's wording only when it means the same as the profile's wording. You may not add facts.
4. Numbers in bullets must exist in the cited profile entries.
5. The Skills section lists only items present as `skill` entries (or technologies in cited entries). Group them as `- Category: item, item`.
6. Write `scratch/evidence-map.md`: one line per bullet, the bullet text copied exactly, then ` => ` and the profile ids. One line `SUMMARY => ids` for the summary. See the example.
7. Save both:
   `python scripts/rh.py app save <person> <app> resume-md --file scratch/resume.md`
   `python scripts/rh.py app save <person> <app> evidence-map --file scratch/evidence-map.md`
8. Run the truth check: `python scripts/rh.py truth <person> <app>`
9. Then run the policy and writing lint: `python scripts/rh.py lint <person> <app>`

## Fix loop (at most 3 rounds)
- FAIL "no evidence-map line": the bullet text in the map must match the resume text. Fix the map or the bullet.
- FAIL "Skill not in the profile": remove it, unless the user confirms it is true. If they confirm, add it with `profile add`, then continue.
- FAIL "unknown profile id": correct the id.
- WARN "number not in the cited evidence": ask the user if the number is true. If yes, record it with `profile update`. If no, remove it.
- WARN "does not appear in the profile" for a heading: fix the wording to match the profile.
- Lint FAIL (no Headline, personal detail, social media): fix it. Never argue with a policy FAIL.
- Lint WARN (filler, pronouns, repeated openers, tense, long bullets, date order, gaps): fix those that are real problems using only true facts. A gap warning is information for the user, not something to hide.
After each fix, save a new version of the changed file and run `truth` and `lint` again.
After 3 rounds with FAILs left, stop and tell the user exactly what remains.

## When it passes
Tell the user the resume text is ready (mention any gap or open WARN in plain words) and move on to `latex-builder`.
