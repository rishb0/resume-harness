# Interview guide and entry examples

Entry JSON always has `"section"` plus the fields allowed for that section (see `config/profile_schema.json`).
List fields (`bullets`, `metrics`, `technologies`, `evidence`) are lists of short text items.
Dates: `2024`, `2024-06`, `Jun 2024`, or `Present`.

## Questions by topic
- Education: degree and field, school, location, start and end year, grade if the user wants it shown.
- Experience: job title, employer, location, start and end, what the user did day to day, tools used, results with numbers, who the work was for.
- Internships: same as experience.
- Projects: name, what it does, why it was built, the user's role, tools, link, result (users, speed, size, awards).
- Research: what was investigated, what was found, who confirmed it (maintainer, publication, identifier), date, link.
- Publications: title, venue, date, link, status.
- Certifications: name, issuer, date earned or "in progress" (put "in progress" in `status`; never list it as earned), credential id if the user wants it.
- Achievements: what, who gave it, when, why it matters.
- Skills: name, category, level, years, where used.
- Open source and volunteering: project or organisation, role, what was done, link.
- Languages: language and level.

## Examples
Experience:
{"section": "experience", "title": "Support Engineer", "organization": "Example Co", "location": "Remote", "start": "2021-03", "end": "Present", "bullets": ["Resolved customer tickets for a billing product", "Wrote 20 help articles"], "metrics": ["20 help articles"], "technologies": ["Zendesk", "SQL"]}

Certification in progress:
{"section": "certification", "title": "Example Practitioner", "issuer": "Example Org", "status": "in progress"}

Skill with evidence:
{"section": "skill", "name": "SQL", "category": "Data", "level": "Intermediate", "evidence": ["exp-01"]}

## Rules
- Bullets are the user's own facts in plain words. The writer will polish them later; do not polish now.
- Do not record opinions about the user ("strong communicator") unless the user states a concrete fact behind it.
- If the user is unsure of a date or number, record nothing for it and tell them it can be added later.
