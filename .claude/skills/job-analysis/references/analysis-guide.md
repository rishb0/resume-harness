# Analysis fields

All fields are plain text or lists of plain text. Saved as `analysis.vN.json` and a readable `analysis.vN.md`.

- `title`: the job title as posted.
- `seniority`: junior, mid, senior, lead, or what the posting says; empty if not stated.
- `role_family`: a short label for the field of work (for example application security, data analysis, nursing, accounting, front-end development).
- `summary`: one or two sentences on what the job is.
- `must_have`: full requirement sentences, shortened but faithful.
- `nice_to_have`: same for preferred items.
- `keywords`: exact phrases from the posting, 8 to 20. Include tools, methods, standards, and domain terms. Include a term in both its short and long form only if the posting uses both.
- `responsibilities`: what the person will do, as short statements.
- `constraints`: location, authorisation, schedule, travel, language, clearances.
- `red_flags`: unclear or suspicious parts.

Example: `examples/example-analysis.json`.
