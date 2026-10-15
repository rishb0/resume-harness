# ATS rules (what the checks mean)

## What an ATS is, honestly
An Applicant Tracking System stores applications, parses resumes into fields, and lets recruiters search and filter. Many do not reject by score automatically. Some employers add knockout questions (work authorisation, location, required licence). No resume can guarantee a result. This harness controls parseability, relevance, evidence quality, and clarity.

## Format rules the template follows
- One column, real text, standard fonts. No tables, text boxes, images, icons, photos, or graphics.
- Contact details in the body, not in a page header or footer (some parsers skip headers and footers).
- Standard headings (Summary, Experience, Education, Skills, Projects, Certifications, ...). A parser looks for these names.
- One date style across the resume. Dates next to the entry they belong to.
- Entry lines in reading order: title, then organisation, location, dates, then bullets.
- Text-based PDF only. A scanned or image PDF is empty to an ATS.

## Content rules
- Use the posting's own terms when they are true for the candidate. Both the short and long form of an acronym help search.
- Keyword stuffing, hidden white text, and invented skills are detected by humans and damage trust. Never do them.
- File name when uploading: `FirstName_LastName_Resume.pdf`.

## What each check reports
- Text extracted: the PDF contains readable text.
- Page count: matches the length budget.
- Broken characters: fonts or symbols that do not extract (cid codes, private-use characters).
- Email, phone, name found: contact data survives extraction.
- Headings in order and each entry's details next to its heading: reading order is intact. A FAIL here means a parser may attach dates or employers to the wrong entry.
- Header order: the extracted text starts with the name, then the designation, then the contact line.
- Page fill: how full the last page is (a sparse one-page resume is flagged).
- Policy and lint: see `resume-writer/references/resume-policy.md`.
- Keyword coverage: the job's exact phrases that appear in the resume and are backed by the profile. "Missing but supported" are opportunities. "Not supported" are real gaps.
